"""
Lambda: surebet-betfair-fetch
===================================
Phase : Morning / Refresh
Input : {"date": "YYYY-MM-DD"}   (optional — defaults to today UTC)
Output: {"success": true, "date": "...", "race_count": N, "s3_key": "..."}

Fetches UK/IRE horse-racing markets from Betfair Exchange (next 24h),
writes price-movement data, then uploads
  s3://surebet-pipeline-data/daily/{date}/response_horses.json
for the downstream analysis Lambda.

Credentials: AWS Secrets Manager  → 'betfair-credentials'
             {username, password, app_key}
"""

import os
import sys
import json
import datetime
import boto3
from botocore.exceptions import ClientError

# ── env ──────────────────────────────────────────────────────────────────────
BUCKET  = os.environ.get('PIPELINE_BUCKET', 'surebet-pipeline-data')
REGION  = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')

# ── module path ──────────────────────────────────────────────────────────────
sys.path.insert(0, '/var/task')   # bundled source files land here


def _serialize(obj):
    """JSON-serialise datetime objects produced by betfair_odds_fetcher."""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    raise TypeError(f"Cannot serialise {type(obj)}")


def _extract_prices(races):
    """Return {selectionId_str: odds} snapshot across all runners in all races."""
    snapshot = {}
    for race in races:
        for runner in race.get('runners', []):
            sid = str(runner.get('selectionId', ''))
            odds = float(runner.get('odds', 0) or 0)
            if sid and odds > 1.0:
                snapshot[sid] = odds
    return snapshot


def _apply_price_movement(races, morning_prices):
    """
    Compare current runner odds against the morning_prices snapshot.
    Sets runner['price_movement'] and runner['price_move_pct'] using the same
    logic as betfair_odds_fetcher.py's steam/drift detection — but keyed against
    the MORNING price rather than the previous Lambda invocation's price.
    This gives a true morning-vs-now comparison that works across Lambda invocations.
    """
    steam_count = drift_count = 0
    for race in races:
        for runner in race.get('runners', []):
            sid = str(runner.get('selectionId', ''))
            cur = float(runner.get('odds', 0) or 0)
            if not sid or cur <= 1.0:
                continue
            morning = morning_prices.get(sid)
            if morning and morning > 1.0:
                pct_move = (morning - cur) / morning   # positive = price shortened (backed)
                if pct_move >= 0.20:
                    runner['price_movement'] = 'steaming'
                    runner['price_move_pct'] = round(pct_move * 100)
                    steam_count += 1
                elif pct_move <= -0.25:
                    runner['price_movement'] = 'drifting'
                    runner['price_move_pct'] = round(pct_move * 100)
                    drift_count += 1
                else:
                    runner['price_movement'] = 'stable'
                    runner['price_move_pct'] = round(pct_move * 100)
    print(f"[sf_betfair_fetch] Price movement: {steam_count} steaming, {drift_count} drifting")
    return races


def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))
    # run_type is injected by the step function: 'morning' or 'refresh'
    run_type = event.get('run_type', 'morning')

    # Work in /tmp so any local file writes land there (read-only /var/task)
    os.makedirs('/tmp', exist_ok=True)
    os.chdir('/tmp')

    from betfair_odds_fetcher import get_live_betfair_races

    print(f"[sf_betfair_fetch] run_type={run_type} — Fetching races for {date_str}...")
    races = get_live_betfair_races()

    if not races:
        raise RuntimeError(f"Betfair returned 0 races for {date_str} — aborting pipeline")

    s3 = boto3.client('s3', region_name=REGION)
    morning_key = f'daily/{date_str}/morning_prices.json'

    # ── PRICE MOVEMENT: morning snapshot vs now ───────────────────────────────
    # Morning run  → morning_prices.json does not exist → save current prices as snapshot.
    # Refresh run  → morning_prices.json exists → compare and annotate steam/drift on runners.
    # Using S3 means the comparison works correctly across separate Lambda invocations.
    try:
        s3.head_object(Bucket=BUCKET, Key=morning_key)
        morning_exists = True
    except ClientError:
        morning_exists = False
    except Exception:
        morning_exists = False

    if morning_exists:
        # Refresh run — load morning snapshot, compute price movement
        try:
            obj = s3.get_object(Bucket=BUCKET, Key=morning_key)
            morning_prices = json.loads(obj['Body'].read().decode('utf-8'))
            races = _apply_price_movement(races, morning_prices)
            print(f"[sf_betfair_fetch] Loaded morning snapshot ({len(morning_prices)} runners)")
        except Exception as e:
            print(f"[sf_betfair_fetch] Warning: could not load morning snapshot: {e}")
    else:
        # Morning run — save current prices as the morning snapshot
        snapshot = _extract_prices(races)
        try:
            s3.put_object(
                Bucket      = BUCKET,
                Key         = morning_key,
                Body        = json.dumps(snapshot).encode('utf-8'),
                ContentType = 'application/json',
            )
            print(f"[sf_betfair_fetch] Saved morning snapshot ({len(snapshot)} runners) → {morning_key}")
        except Exception as e:
            print(f"[sf_betfair_fetch] Warning: could not save morning snapshot: {e}")

    payload_bytes = json.dumps({'races': races}, default=_serialize).encode('utf-8')

    key = f'daily/{date_str}/response_horses.json'
    s3.put_object(
        Bucket      = BUCKET,
        Key         = key,
        Body        = payload_bytes,
        ContentType = 'application/json',
    )

    print(f"[sf_betfair_fetch] Saved {len(races)} races → s3://{BUCKET}/{key}")
    return {
        'success'   : True,
        'date'      : date_str,
        'race_count': len(races),
        's3_key'    : key,
        'run_type'  : run_type,
    }
