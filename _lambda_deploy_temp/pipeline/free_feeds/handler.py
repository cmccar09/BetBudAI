"""
Lambda handler for free phase-1/phase-2 signal enrichment.

Phase 1:
- Free weather volatility from Open-Meteo (course-level)
- Free market context from field-relative odds (race-level median odds)

Phase 2:
- Score adjustment rules for pick selection:
  - weather_volatility_score == 1  -> -4
  - weather_volatility_score >= 2  -> -8
  - market bucket == mid and relative < 0.85 -> +3
  - market bucket == very_long and relative > 1.8 -> -4

Writes back to SureBetBets for the target date and unresolved races.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from statistics import median
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import urlopen

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = "SureBetBets"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

TRACK_LOCATIONS = {
    "Carlisle": (54.89, -2.94), "Taunton": (51.02, -3.10), "Fairyhouse": (53.47, -6.45),
    "Wolverhampton": (52.59, -2.13), "Kempton": (51.42, -0.34), "Punchestown": (53.19, -6.63),
    "Ludlow": (52.37, -2.72), "Newcastle": (54.97, -1.62), "Sedgefield": (54.66, -1.43),
    "Ffos Las": (51.82, -4.10), "Exeter": (50.72, -3.53), "Warwick": (52.28, -1.58),
    "Southwell": (53.08, -0.95), "Dundalk": (54.00, -6.40), "Doncaster": (53.52, -1.10),
    "Navan": (53.65, -6.68), "Newbury": (51.40, -1.33), "Lingfield": (51.17, -0.00),
    "Cheltenham": (51.90, -2.07), "Ascot": (51.41, -0.68), "Sandown": (51.37, -0.35),
    "Haydock": (53.46, -2.62), "Leicester": (52.63, -1.13), "Leopardstown": (53.28, -6.18),
    "Naas": (53.22, -6.66), "Cork": (51.90, -8.54), "Galway": (53.27, -9.08),
    "York": (53.96, -1.08), "Newton Abbot": (50.53, -3.61), "Yarmouth": (52.62, 1.73),
    "Killarney": (52.05, -9.52), "Hereford": (52.05, -2.71),
}


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None or v == "":
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def _decimal(v: float) -> Decimal:
    return Decimal(str(round(float(v), 4)))


def _ddb_safe(value: Any) -> Any:
    """Convert nested float values into Decimal for DynamoDB compatibility."""
    if isinstance(value, float):
        return _decimal(value)
    if isinstance(value, dict):
        return {k: _ddb_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_ddb_safe(v) for v in value]
    return value


def _decimal_odds(item: Dict[str, Any]) -> float:
    raw = item.get("odds")
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float, Decimal)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return 0.0
    if "/" in text:
        try:
            num, den = text.split("/", 1)
            den_f = float(den)
            if den_f == 0:
                return 0.0
            return 1.0 + (float(num) / den_f)
        except Exception:
            return 0.0
    return _to_float(text, 0.0)


def _fetch_weather(lat: float, lon: float) -> Dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation,wind_speed_10m,temperature_2m",
        "forecast_days": 1,
        "timezone": "UTC",
    }
    url = f"{OPEN_METEO_URL}?{urlencode(params)}"
    with urlopen(url, timeout=12) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    rain = hourly.get("precipitation", [])
    wind = hourly.get("wind_speed_10m", [])
    temp = hourly.get("temperature_2m", [])
    if not times:
        return {}

    now_utc = datetime.now(timezone.utc)
    idx_now = 0
    for i, ts in enumerate(times):
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if dt >= now_utc:
                idx_now = i
                break
        except Exception:
            continue

    end_idx = min(idx_now + 3, len(times) - 1)
    rain_3h = sum(_to_float(rain[i], 0.0) for i in range(idx_now, end_idx + 1)) if rain else 0.0
    wind_3h = max((_to_float(wind[i], 0.0) for i in range(idx_now, end_idx + 1)), default=0.0) if wind else 0.0
    temp_3h = (
        sum(_to_float(temp[i], 0.0) for i in range(idx_now, end_idx + 1)) / max(1, end_idx - idx_now + 1)
        if temp
        else 0.0
    )

    vol = 0
    if rain_3h >= 2.0:
        vol += 1
    if wind_3h >= 28.0:
        vol += 1

    return {
        "rain_next_3h_mm": round(rain_3h, 2),
        "max_wind_next_3h_kmh": round(wind_3h, 1),
        "avg_temp_next_3h_c": round(temp_3h, 1),
        "weather_volatility_score": int(vol),
    }


def _get_course_coords(course: str) -> Optional[Tuple[float, float]]:
    if not course:
        return None
    if course in TRACK_LOCATIONS:
        return TRACK_LOCATIONS[course]
    target = course.strip().lower()
    for key, value in TRACK_LOCATIONS.items():
        if key.strip().lower() == target:
            return value
    return None


def lambda_handler(event, context):
    target_date = event.get("target_date") or event.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.info("free-feeds phase run target_date=%s", target_date)

    db = boto3.resource("dynamodb", region_name="eu-west-1")
    table = db.Table(TABLE_NAME)

    # Load all rows for date.
    response = table.query(KeyConditionExpression=Key("bet_date").eq(target_date))
    items = response.get("Items", [])
    while response.get("LastEvaluatedKey"):
        response = table.query(
            KeyConditionExpression=Key("bet_date").eq(target_date),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))

    horse_rows = [
        i for i in items
        if str(i.get("sport", "horses")).strip().lower() in ("horses", "horse racing", "")
        and i.get("horse") and i.get("course") and i.get("race_time")
    ]

    # Keep unresolved rows for adjustment.
    unresolved = [
        i for i in horse_rows
        if not i.get("outcome") or str(i.get("outcome", "")).lower() in ("pending", "won", "lost", "loss")
    ]

    by_race: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in unresolved:
        key = (str(row.get("course", "")).strip(), str(row.get("race_time", "")).strip())
        by_race[key].append(row)

    weather_cache: Dict[str, Dict[str, Any]] = {}
    updated = 0

    for (course, race_time), race_rows in by_race.items():
        # Phase 1: free weather snapshot.
        weather = weather_cache.get(course)
        if weather is None:
            weather = {}
            coords = _get_course_coords(course)
            if coords:
                try:
                    weather = _fetch_weather(coords[0], coords[1])
                except Exception as exc:
                    logger.warning("weather fetch failed for %s: %s", course, exc)
            weather_cache[course] = weather

        # Phase 1: field-relative market context.
        odds_vals = [_decimal_odds(r) for r in race_rows if _decimal_odds(r) > 0]
        med = median(odds_vals) if odds_vals else 0.0

        for row in race_rows:
            base = _to_float(row.get("comprehensive_score") or row.get("analysis_score"), 0.0)
            if base <= 0:
                continue

            dec_odds = _decimal_odds(row)
            rel = (dec_odds / med) if (med > 0 and dec_odds > 0) else 1.0

            if dec_odds <= 2.5:
                bucket = "short"
            elif dec_odds <= 5.0:
                bucket = "mid"
            elif dec_odds <= 9.0:
                bucket = "long"
            else:
                bucket = "very_long"

            # Phase 2: score adjustments.
            delta = 0
            vol = int(weather.get("weather_volatility_score", 0) or 0)
            if vol == 1:
                delta -= 4
            elif vol >= 2:
                delta -= 8

            if bucket == "mid" and rel < 0.85:
                delta += 3
            if bucket == "very_long" and rel > 1.8:
                delta -= 4

            adjusted = max(0.0, base + float(delta))

            update_expr = (
                "SET free_phase1_weather = :w, "
                "free_phase1_market_context = :m, "
                "free_phase2_adjustment = :d, "
                "comprehensive_score_adjusted = :s, "
                "free_phase_updated_at = :t"
            )
            values = {
                ":w": _ddb_safe(weather if weather else {"weather_volatility_score": 0}),
                ":m": {
                    "field_median_odds": _decimal(med) if med else Decimal("0"),
                    "runner_decimal_odds": _decimal(dec_odds) if dec_odds else Decimal("0"),
                    "relative_value_vs_field_median": _decimal(rel),
                    "market_position_bucket": bucket,
                },
                ":d": Decimal(str(int(delta))),
                ":s": _decimal(adjusted),
                ":t": datetime.now(timezone.utc).isoformat(),
            }

            table.update_item(
                Key={"bet_date": target_date, "bet_id": row["bet_id"]},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=values,
            )
            updated += 1

    return {
        "statusCode": 200,
        "success": True,
        "target_date": target_date,
        "rows_loaded": len(items),
        "rows_unresolved": len(unresolved),
        "races_processed": len(by_race),
        "rows_updated": updated,
    }
