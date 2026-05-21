"""
WhatsApp notifications via Twilio.
Called after picks are saved to DynamoDB in complete_daily_analysis.py.

Setup:
  1. Sign up at https://console.twilio.com
  2. Get Account SID + Auth Token from the Twilio console dashboard
  3. Enable the WhatsApp Sandbox: Messaging → Try it out → Send a WhatsApp message
     Each recipient must send "join <sandbox-word>" to +14155238886 first (one-time)
  4. Fill in twilio-creds.json with your SID, auth token, and from_number

Once you have an approved WhatsApp Business number, update from_number to whatsapp:+<your_number>
"""
import hashlib
import json
import os
from datetime import datetime

# File that stores the hash of the last set of picks we notified about.
# Prevents duplicate WhatsApp blasts when auto_refresh re-runs multiple times/day.
_SENT_HASH_FILE = os.path.join(os.path.dirname(__file__), '.notify_sent_hash.json')


def _picks_hash(picks):
    """Stable hash of (race_time, horse, score) tuples for change detection."""
    key = json.dumps(
        sorted(
            [(str(p.get('race_time', ''))[:16], str(p.get('horse', '')),
              float(p.get('comprehensive_score', p.get('combined_confidence', 0))))
             for p in picks]
        ),
        sort_keys=True
    )
    return hashlib.md5(key.encode()).hexdigest()


def _already_sent_today(picks):
    """Return True if we already sent a notification for this exact pick set today."""
    try:
        if not os.path.exists(_SENT_HASH_FILE):
            return False
        with open(_SENT_HASH_FILE) as f:
            data = json.load(f)
        today = datetime.now().strftime('%Y-%m-%d')
        return data.get('date') == today and data.get('hash') == _picks_hash(picks)
    except Exception:
        return False


def _mark_sent(picks):
    """Save today's sent hash so subsequent runs skip duplicates."""
    try:
        with open(_SENT_HASH_FILE, 'w') as f:
            json.dump({'date': datetime.now().strftime('%Y-%m-%d'),
                       'hash': _picks_hash(picks)}, f)
    except Exception:
        pass


def _load_creds():
    creds_path = os.path.join(os.path.dirname(__file__), 'twilio-creds.json')
    if not os.path.exists(creds_path):
        return None
    with open(creds_path) as f:
        return json.load(f)


def _confidence_bar(score):
    """Visual confidence indicator."""
    if score >= 90:
        return '🟢🟢🟢 STRONG'
    elif score >= 75:
        return '🟢🟢⚪ GOOD'
    elif score >= 60:
        return '🟢⚪⚪ FAIR'
    return '⚪⚪⚪'


def send_pick_notifications(picks):
    """
    Send a WhatsApp message for a list of picks.
    Each pick should have: horse, course, race_time, odds, score, confidence_label

    Returns (sent_count, error_message_or_None)
    """
    creds = _load_creds()
    if not creds:
        print('[WhatsApp] twilio-creds.json not found — skipping notifications')
        return 0, 'No credentials file'

    sid   = creds.get('account_sid', '')
    token = creds.get('auth_token', '')
    if sid.startswith('FILL_IN') or token.startswith('FILL_IN'):
        print('[WhatsApp] Credentials not configured — skipping notifications')
        return 0, 'Credentials not configured'

    try:
        from twilio.rest import Client
    except ImportError:
        print('[WhatsApp] twilio package not installed — run: pip install twilio')
        return 0, 'twilio not installed'

    if not picks:
        return 0, None

    # Build message
    today  = datetime.now().strftime('%a %d %b')
    lines  = [f"🏇 *SureBet Picks — {today}*\n"]

    for i, p in enumerate(picks, 1):
        horse  = p.get('horse', '?')
        course = p.get('course', '?')
        rt     = str(p.get('race_time', '') or '')
        # Format time as HH:MM
        try:
            from datetime import datetime as dt, timezone, timedelta
            race_dt = dt.fromisoformat(rt.replace('Z', '+00:00'))
            # Convert UTC → UK local time (BST = UTC+1 in summer, GMT in winter)
            d = race_dt.date()
            year = d.year
            from datetime import date as _date
            bst_start = _date(year, 3, 31)
            while bst_start.weekday() != 6:
                bst_start = _date(bst_start.year, bst_start.month, bst_start.day - 1)
            bst_end = _date(year, 10, 31)
            while bst_end.weekday() != 6:
                bst_end = _date(bst_end.year, bst_end.month, bst_end.day - 1)
            uk_offset = timedelta(hours=1) if bst_start <= d < bst_end else timedelta(0)
            time_str = (race_dt + uk_offset).strftime('%H:%M')
        except Exception:
            time_str = rt[11:16] if len(rt) >= 16 else rt

        odds_dec = float(p.get('odds', 0))
        # Convert decimal to nearest fractional approximation for readability
        odds_frac = _dec_to_frac(odds_dec)
        score     = float(p.get('comprehensive_score', p.get('score', 0)))
        conf      = _confidence_bar(score)

            # Enhanced signal tags from score_breakdown
        bd = p.get('score_breakdown', {})
        tags = []
        if float(bd.get('cd_bonus', 0)) >= 9:  tags.append('C&D winner')
        elif float(bd.get('cd_bonus', 0)) > 0:  tags.append('Course winner')
        if float(bd.get('deep_form', 0)) >= 16: tags.append(f"Deep form: {int(float(bd.get('deep_form',0)))}")
        if float(bd.get('trainer_hot_form', 0)) > 0: tags.append('Trainer hot')
        if float(bd.get('jockey_hot_form', 0)) > 0:  tags.append('Jockey hot')
        if float(bd.get('price_steam', 0)) > 0:      tags.append(f"Steaming ({int(float(bd.get('price_steam',0)))}pts)")
        if float(bd.get('market_leader', 0)) >= 16:  tags.append('Fav')
        signals = '  ·  '.join(tags) if tags else 'No standout signals'

        lines.append(
            f"*#{i} {horse}*\n"
            f"📍 {course}  ⏰ {time_str}\n"
            f"💰 {odds_frac}  |  Score: {score:.0f}  {conf}\n"
            f"✨ {signals}\n"
        )

    lines.append("_Good luck! 🤞_")
    message_body = '\n'.join(lines)

    client    = Client(sid, token)
    from_num  = creds.get('from_number', 'whatsapp:+14155238886')
    to_numbers = creds.get('to_numbers', [])

    sent = 0
    for to in to_numbers:
        try:
            msg = client.messages.create(
                from_=from_num,
                to=to,
                body=message_body,
            )
            print(f'[WhatsApp] Sent to {to}  sid={msg.sid}')
            sent += 1
        except Exception as e:
            print(f'[WhatsApp] Failed to send to {to}: {e}')

    return sent, None


def _dec_to_frac(dec):
    """Convert decimal odds to a clean fractional string (best-effort)."""
    if dec <= 1:
        return str(dec)
    net = dec - 1
    # Common fractions lookup
    common = {
        0.5: '1/2', 0.333: '1/3', 0.25: '1/4', 0.2: '1/5',
        0.667: '2/3', 0.75: '3/4', 0.8: '4/5',
        1.0: 'Evs', 1.25: '5/4', 1.333: '4/3', 1.5: '6/4',
        1.667: '5/3', 1.75: '7/4', 2.0: '2/1', 2.25: '9/4',
        2.5: '5/2', 2.667: '8/3', 3.0: '3/1', 3.333: '10/3',
        3.5: '7/2', 4.0: '4/1', 4.5: '9/2', 5.0: '5/1',
        5.5: '11/2', 6.0: '6/1', 7.0: '7/1', 8.0: '8/1',
        9.0: '9/1', 10.0: '10/1', 12.0: '12/1', 14.0: '14/1',
        16.0: '16/1', 20.0: '20/1', 25.0: '25/1', 33.0: '33/1',
    }
    for k, v in common.items():
        if abs(net - k) < 0.04:
            return v
    # Fallback: simplify as n/d
    from math import gcd
    n = round(net * 100)
    d = 100
    g = gcd(n, d)
    return f'{n // g}/{d // g}'


def fetch_todays_picks():
    """Fetch today's show_in_ui=True picks from DynamoDB, sorted by race time."""
    import boto3
    from boto3.dynamodb.conditions import Key, Attr
    from datetime import date
    db  = boto3.resource('dynamodb', region_name='eu-west-1')
    tbl = db.Table('SureBetBets')
    today = date.today().strftime('%Y-%m-%d')
    resp  = tbl.query(
        KeyConditionExpression=Key('bet_date').eq(today),
        FilterExpression=Attr('show_in_ui').eq(True)
    )
    items = sorted(resp.get('Items', []), key=lambda x: str(x.get('race_time', '')))
    # De-duplicate: keep the highest-scored entry per race_time+horse
    seen = {}
    for it in items:
        key = (str(it.get('race_time', ''))[:16], str(it.get('horse', '')))
        prev = seen.get(key)
        cur_score = float(it.get('comprehensive_score', it.get('combined_confidence', 0)))
        if prev is None or cur_score > float(prev.get('comprehensive_score', prev.get('combined_confidence', 0))):
            seen[key] = it
    return list(seen.values())


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        # Quick connectivity test with a dummy pick
        test_picks = [{
            'horse': 'Test Horse',
            'course': 'Doncaster',
            'race_time': '2026-03-29T14:55:00+00:00',
            'odds': 4.333,
            'comprehensive_score': 93,
            'score_breakdown': {'cd_bonus': 9, 'deep_form': 24, 'market_leader': 16},
        }]
        sent, err = send_pick_notifications(test_picks)
        print(f'Test sent: {sent}  Error: {err}')
    else:
        # Normal run: fetch real picks and notify (once per unique pick set per day)
        picks = fetch_todays_picks()
        print(f'[notify] Found {len(picks)} picks for today')
        if not picks:
            print('[notify] No UI picks today — nothing sent')
        elif _already_sent_today(picks):
            print('[notify] Picks unchanged since last notification — skipping duplicate send')
        else:
            sent, err = send_pick_notifications(picks)
            if sent:
                _mark_sent(picks)
            print(f'[notify] Sent: {sent}  Error: {err}')
