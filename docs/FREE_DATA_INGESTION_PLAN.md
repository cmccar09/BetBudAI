# Free Data Ingestion Plan (Phase 1)

This plan adds missing high-impact signals using free sources first, with graceful fallback.

## What is implemented now

1. New enricher: `backend/core/enrichment/free_feeds.py`
- Adds course-level weather snapshot from Open-Meteo (free, no key):
  - `rain_next_3h_mm`
  - `max_wind_next_3h_kmh`
  - `avg_temp_next_3h_c`
  - `weather_volatility_score`
- Adds runner-level field-relative market context from existing odds:
  - `field_median_odds`
  - `relative_value_vs_field_median`
  - `market_position_bucket`

2. Pipeline hook: `backend/core/enrichment/pipeline.py`
- New optional Step 5 executes `enrich_races_with_free_signals`.
- Safe behavior: if provider fails, pipeline continues.

3. Environment support: `.env.example`
- `FEATURE_FREE_FEEDS=true`
- `OPEN_METEO_BASE_URL=...`
- optional `MET_OFFICE_DATAPOINT_KEY=`

## Free sources and cadence

## A) Open-Meteo (weather)
- Endpoint: `https://api.open-meteo.com/v1/forecast`
- Polling cadence:
  - Morning pipeline: once per run
  - Refresh pipeline: every refresh cycle
- Use in model:
  - Penalize confidence when `weather_volatility_score >= 1`
  - Stronger penalty when `rain_next_3h_mm >= 3` or `max_wind_next_3h_kmh >= 35`

## B) Sporting Life racecards (runner status)
- Source already used in your stack for form/results.
- Add a diff check every 10 minutes between 10:00-20:00 UTC:
  - non-runners
  - late rider changes
- Model usage:
  - downgrade confidence on late rider change
  - re-rank if non-runner materially changes field shape

## C) Odds snapshots (free scrape fallback)
- Source: existing odds feeds + public pages where allowed.
- Snapshot cadence:
  - T-180 to T-60: every 15 min
  - T-60 to T-10: every 5 min
  - T-10 to off: every 2 min
- Features:
  - `odds_drift_10m`
  - `odds_drift_30m`
  - `steam_flag` (tightening beyond threshold)

## Scoring integration (next patch)

Add these lightweight rules in scoring stage:

1. Weather volatility adjustment
- `weather_volatility_score == 1`: `-4`
- `weather_volatility_score >= 2`: `-8`

2. Field-relative market adjustment
- `market_position_bucket == "mid"` and `relative_value_vs_field_median < 0.85`: `+3`
- `market_position_bucket == "very_long"` and `relative_value_vs_field_median > 1.8`: `-4`

3. Late status changes
- late rider change: `-3`
- non-runner in top-3 market ranks: trigger re-rank for race

## Validation checklist

1. Confirm enrichment output includes `free_weather` on races with known coordinates.
2. Confirm runners include `free_market_context`.
3. Confirm no pipeline failures when Open-Meteo is unavailable.
4. Compare 14-day A/B:
- baseline vs baseline+free-feeds
- metrics: strike rate, calibration, false-positive rate in odds 3.0-8.0 band

## Why this is free-first and safe

- No paid API required for phase 1.
- No blocking dependencies added.
- Existing enrichment flow remains intact if free feeds fail.
- Creates a clean path to swap in paid sectionals/exchange stream later.
