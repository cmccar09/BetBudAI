"""
Lambda: surebet-analysis
============================
Phase : Morning / Refresh
Input : {"date": "YYYY-MM-DD", "s3_key": "daily/.../response_horses.json"}
Output: {"success": true, "date": "...", "picks_count": N}

1. Downloads response_horses.json from S3 → /tmp/
2. Runs comprehensive 7-factor scoring engine (complete_daily_analysis.py)
3. Saves all horses + top-5 UI picks to DynamoDB SureBetBets
4. Returns count of show_in_ui=True picks saved

Bundled source files required in zip:
  complete_daily_analysis.py, comprehensive_pick_logic.py,
  form_enricher.py, notify_picks.py, weather_going_inference.py
"""

import os
import sys
import json
import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr

BUCKET = os.environ.get('PIPELINE_BUCKET', 'surebet-pipeline-data')
REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')

sys.path.insert(0, '/var/task')


def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))
    # Accept s3_key from upstream or build it
    s3_key   = event.get('s3_key', f'daily/{date_str}/response_horses.json')

    # /tmp is writable; chdir there so relative paths in complete_daily_analysis work
    os.makedirs('/tmp', exist_ok=True)
    os.chdir('/tmp')

    # ── Download races from S3 ────────────────────────────────────────────────
    s3 = boto3.client('s3', region_name=REGION)
    print(f"[sf_analysis] Downloading s3://{BUCKET}/{s3_key} ...")
    obj        = s3.get_object(Bucket=BUCKET, Key=s3_key)
    races_data = json.loads(obj['Body'].read().decode('utf-8'))

    with open('/tmp/response_horses.json', 'w') as fh:
        json.dump(races_data, fh)

    # ── Run analysis ─────────────────────────────────────────────────────────
    # complete_daily_analysis reads 'response_horses.json' from cwd (/tmp)
    from complete_daily_analysis import analyze_and_save_all
    print(f"[sf_analysis] Scoring all horses and selecting top picks for {date_str} ...")
    analyze_and_save_all()

    # ── Count saved UI picks ──────────────────────────────────────────────────
    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')
    resp  = table.query(
        KeyConditionExpression = Key('bet_date').eq(date_str),
        FilterExpression       = Attr('show_in_ui').eq(True),
    )
    picks_count = len(resp.get('Items', []))
    print(f"[sf_analysis] Done — {picks_count} UI pick(s) saved for {date_str}")

    return {
        'success'     : True,
        'date'        : date_str,
        'picks_count' : picks_count,
    }
