"""
Free data feeds enrichment (phase 1).

This module adds low-cost/free signals that improve pick quality:
- Open-Meteo short-horizon weather volatility per course
- Derived market context from existing runner odds (field-relative value proxy)

Design goals:
- Safe no-op on network/API failure
- No paid dependencies
- Compatible with existing race dict shape
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from statistics import median
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    from ...utils.weather_going_inference import TRACK_LOCATIONS
except Exception:
    TRACK_LOCATIONS = {}

logger = logging.getLogger(__name__)

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _extract_coords(course_name: str) -> Optional[Tuple[float, float]]:
    if not course_name:
        return None

    # Exact key lookup first.
    row = TRACK_LOCATIONS.get(course_name)
    if row and "lat" in row and "lon" in row:
        return float(row["lat"]), float(row["lon"])

    # Loose case-insensitive fallback.
    target = str(course_name).strip().lower()
    for key, value in TRACK_LOCATIONS.items():
        if str(key).strip().lower() == target and "lat" in value and "lon" in value:
            return float(value["lat"]), float(value["lon"])

    return None


def _fetch_open_meteo_snapshot(lat: float, lon: float) -> Dict[str, Any]:
    """
    Return short-horizon weather metrics for model features.

    Uses free Open-Meteo endpoint (no key required).
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "forecast_days": 1,
        "timezone": "UTC",
    }

    response = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=12)
    response.raise_for_status()
    payload = response.json()

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    rain = hourly.get("precipitation", [])
    wind = hourly.get("wind_speed_10m", [])
    temp = hourly.get("temperature_2m", [])

    if not times:
        return {}

    now_utc = datetime.now(timezone.utc)
    idx_now = 0
    for idx, ts in enumerate(times):
        try:
            ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if ts_dt >= now_utc:
                idx_now = idx
                break
        except Exception:
            continue

    end_idx = min(idx_now + 3, len(times) - 1)

    rain_next_3h = sum(_to_float(rain[i], 0.0) for i in range(idx_now, end_idx + 1)) if rain else 0.0
    wind_next_3h = max((_to_float(wind[i], 0.0) for i in range(idx_now, end_idx + 1)), default=0.0) if wind else 0.0
    temp_next_3h = (
        sum(_to_float(temp[i], 0.0) for i in range(idx_now, end_idx + 1)) / max(1, (end_idx - idx_now + 1))
        if temp
        else 0.0
    )

    # Simple volatility indicator useful for confidence gating.
    weather_volatility = 0
    if rain_next_3h >= 2.0:
        weather_volatility += 1
    if wind_next_3h >= 28.0:
        weather_volatility += 1

    return {
        "provider": "open_meteo",
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "rain_next_3h_mm": round(rain_next_3h, 2),
        "max_wind_next_3h_kmh": round(wind_next_3h, 1),
        "avg_temp_next_3h_c": round(temp_next_3h, 1),
        "weather_volatility_score": weather_volatility,
    }


def _runner_decimal_odds(runner: Dict[str, Any]) -> float:
    for key in ("odds", "odds_decimal", "decimal_odds"):
        value = runner.get(key)
        if value is not None and value != "":
            return _to_float(value, 0.0)

    frac = str(runner.get("odds_fraction") or "").strip()
    if "/" in frac:
        try:
            num, den = frac.split("/", 1)
            den_f = float(den)
            if den_f == 0:
                return 0.0
            return 1.0 + (float(num) / den_f)
        except Exception:
            return 0.0

    return 0.0


def _inject_field_relative_odds_features(race: Dict[str, Any]) -> None:
    """
    Add runner-level free market context using existing odds.

    This is not true exchange microstructure, but it is a useful free proxy:
    - field_median_odds
    - relative_value_vs_field_median
    - market_position_bucket
    """
    runners = race.get("runners") or []
    if not isinstance(runners, list) or not runners:
        return

    odds_values = [
        _runner_decimal_odds(r)
        for r in runners
        if _runner_decimal_odds(r) > 0
    ]
    if not odds_values:
        return

    med = median(odds_values)

    for runner in runners:
        dec = _runner_decimal_odds(runner)
        if dec <= 0:
            continue

        rel = dec / med if med > 0 else 1.0
        if dec <= 2.5:
            bucket = "short"
        elif dec <= 5.0:
            bucket = "mid"
        elif dec <= 9.0:
            bucket = "long"
        else:
            bucket = "very_long"

        runner["free_market_context"] = {
            "field_median_odds": round(med, 2),
            "runner_decimal_odds": round(dec, 2),
            "relative_value_vs_field_median": round(rel, 3),
            "market_position_bucket": bucket,
        }


def enrich_races_with_free_signals(races: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mutates races in-place with free weather + market-proxy signals.
    """
    if not races:
        return races

    enabled = str(os.getenv("FEATURE_FREE_FEEDS", "true")).strip().lower() in ("1", "true", "yes", "on")
    if not enabled:
        logger.info("[free-feeds] FEATURE_FREE_FEEDS disabled")
        return races

    # Cache weather by course to minimize external calls.
    weather_cache: Dict[str, Dict[str, Any]] = {}

    for race in races:
        course = str(race.get("course") or "").strip()
        if not course:
            continue

        if course not in weather_cache:
            coords = _extract_coords(course)
            if coords:
                try:
                    weather_cache[course] = _fetch_open_meteo_snapshot(coords[0], coords[1])
                except Exception as exc:
                    logger.warning(f"[free-feeds] Weather fetch failed for {course}: {exc}")
                    weather_cache[course] = {}
            else:
                weather_cache[course] = {}

        if weather_cache[course]:
            race["free_weather"] = weather_cache[course]

        _inject_field_relative_odds_features(race)

        status = race.get("enrichment_status") or {}
        status["free_feeds"] = True
        race["enrichment_status"] = status

    logger.info("[free-feeds] enrichment complete")
    return races
