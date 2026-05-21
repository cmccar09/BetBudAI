"""
Lambda: surebet-notify
==========================
Phase : Morning / Refresh
Input : {"date": "YYYY-MM-DD", "valid_picks": N}
Output: {"success": true, "date": "...", "notifications_sent": N, "skipped": bool}

Reads today's show_in_ui=True picks from DynamoDB, builds a WhatsApp
message, and sends it via Twilio.

Deduplication: a hash of (race_time, horse, score) tuples is stored in
DynamoDB under bet_date='NOTIFY_HASHES' so duplicate blasts are skipped even
if the Lambda re-executes (e.g. on retry).

Credentials: AWS Secrets Manager → 'twilio-credentials'
             {account_sid, auth_token, from_number, to_numbers: [...]}
"""

import os
import sys
import json
import hashlib
import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')

sys.path.insert(0, '/var/task')


# ── helpers ──────────────────────────────────────────────────────────────────

def _float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _picks_hash(picks):
    items = sorted([
        (str(p.get('race_time', ''))[:16],
         str(p.get('horse', p.get('horse_name', ''))),
         _float(p.get('comprehensive_score', p.get('analysis_score', 0))))
        for p in picks
    ])
    return hashlib.md5(json.dumps(items, sort_keys=True).encode()).hexdigest()


def _confidence_bar(score):
    if score >= 90: return '🟢🟢🟢 STRONG'
    if score >= 75: return '🟢🟢⚪ GOOD'
    if score >= 60: return '🟢⚪⚪ FAIR'
    return '⚪⚪⚪'


def _build_message(picks, date_str):
    lines = [f"🏇 *SureBet Picks — {date_str}*\n"]
    for i, p in enumerate(picks, 1):
        horse  = p.get('horse', p.get('horse_name', 'Unknown'))
        course = p.get('course', '')
        rtime  = str(p.get('race_time', ''))[:16].replace('T', ' ')
        score  = _float(p.get('comprehensive_score', p.get('analysis_score', 0)))
        odds   = _float(p.get('odds', 0))
        why    = p.get('why_now', '')
        lines.append(
            f"*{i}. {horse}* @ {odds-1:.0f}/1\n"
            f"   📍 {course}  ⏰ {rtime}\n"
            f"   {_confidence_bar(score)} ({score:.0f}/100)\n"
            f"   _{why}_\n"
        )
    lines.append("_Good luck! 🍀_")
    return "\n".join(lines)


# ── already-sent check (DynamoDB, not local file) ────────────────────────────

def _already_sent(table, date_str, picks_hash):
    try:
        resp = table.get_item(Key={'bet_date': 'NOTIFY_HASHES', 'bet_id': date_str})
        item = resp.get('Item', {})
        return item.get('hash') == picks_hash
    except Exception:
        return False


def _mark_sent(table, date_str, picks_hash):
    try:
        table.put_item(Item={
            'bet_date'  : 'NOTIFY_HASHES',
            'bet_id'    : date_str,
            'hash'      : picks_hash,
            'sent_at'   : datetime.datetime.utcnow().isoformat(),
        })
    except Exception as e:
        print(f"[sf_notify] Warning: could not persist sent-hash: {e}")


# ── main handler ──────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    # ── 1PM BST GATE ─────────────────────────────────────────────────────────
    # Hold notifications until 12:00 UTC (1:00pm BST).
    # The morning pipeline runs at 08:30 UTC but picks may be re-scored by the
    # 12:00 UTC refresh as going/flags update.  Only the 12:00+ runs should
    # actually fire WhatsApp messages so users always see the settled final pick.
    _now_utc = datetime.datetime.utcnow()
    if _now_utc.hour < 12:
        print(f"[sf_notify] Before 1pm BST ({_now_utc.strftime('%H:%M')} UTC) — skipping notifications until 12:00 UTC refresh")
        return {'success': True, 'date': date_str, 'notifications_sent': 0, 'skipped': True,
                'skip_reason': f'Before 1pm BST gate ({_now_utc.strftime("%H:%M")} UTC)'}

    # Get Twilio credentials
    sm = boto3.client('secretsmanager', region_name=REGION)
    try:
        raw   = sm.get_secret_value(SecretId='twilio-credentials')['SecretString']
        creds = json.loads(raw)
    except Exception as e:
        print(f"[sf_notify] Twilio credentials not found — skipping notifications ({e})")
        return {'success': True, 'date': date_str, 'notifications_sent': 0, 'skipped': True}

    account_sid  = creds.get('account_sid', '')
    auth_token   = creds.get('auth_token', '')
    from_number  = creds.get('from_number', '')   # e.g. 'whatsapp:+14155238886'
    to_numbers   = creds.get('to_numbers', [])

    if not (account_sid and auth_token and from_number and to_numbers):
        print("[sf_notify] Incomplete Twilio credentials — skipping")
        return {'success': True, 'date': date_str, 'notifications_sent': 0, 'skipped': True}

    # Load today's UI picks from DynamoDB
    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')

    resp  = table.query(
        KeyConditionExpression = Key('bet_date').eq(date_str),
        FilterExpression       = Attr('show_in_ui').eq(True),
    )
    picks = resp.get('Items', [])

    if not picks:
        print(f"[sf_notify] No picks for {date_str} — skipping")
        return {'success': True, 'date': date_str, 'notifications_sent': 0, 'skipped': True}

    picks_hash = _picks_hash(picks)
    if _already_sent(table, date_str, picks_hash):
        print(f"[sf_notify] Already sent identical picks for {date_str} — skipping duplicates")
        return {'success': True, 'date': date_str, 'notifications_sent': 0, 'skipped': True}

    message = _build_message(picks, date_str)

    # Send via Twilio REST API (no twilio SDK required — direct HTTPS call)
    import urllib.request, urllib.parse, base64
    sent = 0
    for to_number in to_numbers:
        url  = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
        data = urllib.parse.urlencode({
            'To'  : f'whatsapp:{to_number}' if not to_number.startswith('whatsapp:') else to_number,
            'From': from_number,
            'Body': message,
        }).encode('utf-8')
        auth = base64.b64encode(f'{account_sid}:{auth_token}'.encode()).decode()
        req  = urllib.request.Request(url, data=data, method='POST',
                                      headers={'Authorization': f'Basic {auth}'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp_body = json.loads(r.read().decode())
                print(f"[sf_notify] Sent to {to_number}: SID={resp_body.get('sid')}")
                sent += 1
        except Exception as e:
            print(f"[sf_notify] Failed to send to {to_number}: {e}")

    _mark_sent(table, date_str, picks_hash)
    print(f"[sf_notify] Done — {sent}/{len(to_numbers)} notification(s) sent")
    return {
        'success'            : True,
        'date'               : date_str,
        'notifications_sent' : sent,
        'skipped'            : False,
    }
