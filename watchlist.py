"""
watchlist.py — AI Improver Watchlist System

After each race settles, the AI evaluates runners for improvement potential
and adds promising horses to a persistent watchlist in DynamoDB.

Next time the horse appears in the morning analysis, the watchlist signal
fires: +15 pts bonus + WATCHLIST badge in the output.

Watchlist criteria (any one qualifies):
  1. Close 2nd/3rd beaten < 3 lengths with our model score >= 75
  2. Ran on strongly at finish (form text signals: "ran on", "kept on", "stayed on")
  3. Going mismatch on the day (sire prefers different ground — may improve when conditions suit)
  4. First time over the distance (may improve for step up/down)
  5. Prominent/led until close home then faded — fitness issue or too far, try shorter
  6. Hampered / no run / unlucky — beaten by circumstances not ability

Watchlist entries expire after 90 days or after 3 runs without winning.

Storage: SureBetBets table, bet_date='WATCHLIST', bet_id='{horse_slug}#{date_added}'
"""

import re
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal

_TABLE_NAME = 'SureBetBets'
_WATCHLIST_DATE = 'WATCHLIST'
_EXPIRY_DAYS = 90
_MAX_RUNS_WITHOUT_WIN = 3


def _slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', (name or '').lower().strip()).strip('_')


def _table():
    return boto3.resource('dynamodb', region_name='eu-west-1').Table(_TABLE_NAME)


# ── Criteria evaluation ────────────────────────────────────────────────────────

def _close_finish(position: int, beaten_lengths: float, score: float) -> tuple[bool, str]:
    """Close 2nd or 3rd with high model score."""
    if position in (2, 3) and beaten_lengths is not None and beaten_lengths <= 3.0 and score >= 75:
        return True, f'Beaten {beaten_lengths:.1f}L in {_ordinal(position)} — unlucky, model scored {score:.0f}'
    return False, ''


def _ran_on_strongly(form_text: str) -> tuple[bool, str]:
    """Horse ran on at finish — likely improve over further or next time."""
    if not form_text:
        return False, ''
    signals = ['ran on', 'kept on', 'stayed on', 'ran on well', 'stayed on well',
               'ran on strongly', 'finished well', 'nearest finish', 'closing']
    for s in signals:
        if s in form_text.lower():
            return True, f'Form note: "{s}" — likely improver next time or at longer trip'
    return False, ''


def _unlucky(form_text: str) -> tuple[bool, str]:
    """Hampered, no room, or circumstances cost the horse the race."""
    if not form_text:
        return False, ''
    signals = ['hampered', 'no room', 'short of room', 'checked', 'squeezed',
               'badly hampered', 'knocked sideways', 'switched', 'unlucky',
               'bumped', 'ridden out', 'carried wide']
    for s in signals:
        if s in form_text.lower():
            return True, f'Unlucky in running: "{s}" — clear air next time'
    return False, ''


def _prominent_then_faded(form_text: str, position: int) -> tuple[bool, str]:
    """Led or prominent then faded — fitness/trip issue, worth watching."""
    if not form_text or position is None or position > 5:
        return False, ''
    led = any(s in form_text.lower() for s in ['led', 'disputed lead', 'prominent'])
    faded = any(s in form_text.lower() for s in ['faded', 'weakened', 'tired', 'no extra'])
    if led and faded:
        return True, 'Led then faded — likely needed the run, watch next start'
    return False, ''


def _going_mismatch(sire: str, going: str) -> tuple[bool, str]:
    """Sire prefers different going — note for conditions that suit."""
    try:
        from bloodstock import sire_going_signal, GOING_BUCKET, SIRE_GOING_PREFS
        pts, reason = sire_going_signal(sire, going)
        if pts < -5:
            sire_pref = SIRE_GOING_PREFS.get((sire or '').lower().strip(), 'any')
            going_bucket = next((v for k, v in GOING_BUCKET.items() if k.lower() in going.lower()), 'any')
            ideal = 'good-to-firm/firm' if sire_pref == 'fast' else 'soft/heavy' if sire_pref == 'soft' else 'good'
            return True, f'Sire {sire} dislikes {going} — watch on {ideal} ground'
    except Exception:
        pass
    return False, ''


def _ordinal(n: int) -> str:
    return {1: '1st', 2: '2nd', 3: '3rd'}.get(n, f'{n}th')


# ── Core watchlist functions ────────────────────────────────────────────────────

def evaluate_for_watchlist(
    horse: str,
    course: str,
    race_time: str,
    race_type: str,
    position: int,
    beaten_lengths: float,
    score: float,
    form_text: str,
    sire: str,
    going: str,
) -> tuple[bool, str, str]:
    """
    Evaluate whether a horse should be added to the watchlist.
    Returns (should_add: bool, reason: str, category: str).

    Categories:
      'close_finish'    — beaten narrowly, model liked it
      'ran_on'          — stayed on at finish, likely improver
      'unlucky'         — hampered/no room, circumstances
      'prominent_faded' — needed the run or wrong trip
      'going_mismatch'  — ground didn't suit, watch on better conditions
    """
    checks = [
        ('close_finish',    _close_finish(position, beaten_lengths, score)),
        ('ran_on',          _ran_on_strongly(form_text)),
        ('unlucky',         _unlucky(form_text)),
        ('prominent_faded', _prominent_then_faded(form_text, position)),
        ('going_mismatch',  _going_mismatch(sire, going)),
    ]
    for category, (qualifies, reason) in checks:
        if qualifies:
            return True, reason, category
    return False, '', ''


def add_to_watchlist(
    horse: str,
    course: str,
    race_time: str,
    race_type: str,
    going: str,
    sire: str,
    reason: str,
    category: str,
    position: int,
    beaten_lengths: float,
    score: float,
    odds: float,
) -> bool:
    """
    Add a horse to the watchlist in DynamoDB.
    Returns True if added, False if already on the list or failed.
    """
    try:
        tbl = _table()
        horse_slug = _slug(horse)
        now = datetime.now(timezone.utc)
        date_added = now.strftime('%Y-%m-%d')
        bet_id = f'{horse_slug}#{date_added}'
        expiry = int((now + timedelta(days=_EXPIRY_DAYS)).timestamp())

        # Check if already on watchlist
        existing = tbl.get_item(Key={'bet_date': _WATCHLIST_DATE, 'bet_id': bet_id}).get('Item')
        if existing:
            print(f'  [WATCHLIST] {horse} already on watchlist since {existing.get("date_added")}')
            return False

        item = {
            'bet_date':          _WATCHLIST_DATE,
            'bet_id':            bet_id,
            'horse':             horse,
            'horse_slug':        horse_slug,
            'course':            course,
            'last_race_time':    race_time,
            'last_race_type':    race_type,
            'last_going':        going,
            'sire':              sire or '',
            'date_added':        date_added,
            'watchlist_reason':  reason,
            'watchlist_category': category,
            'last_position':     position or 0,
            'beaten_lengths':    Decimal(str(round(beaten_lengths or 0, 2))),
            'model_score':       Decimal(str(round(score or 0, 1))),
            'last_odds':         Decimal(str(round(odds or 0, 2))),
            'runs_since_added':  0,
            'active':            True,
            'ttl':               expiry,
        }
        tbl.put_item(Item=item)
        print(f'  [WATCHLIST] ✅ Added {horse} — {category}: {reason}')
        return True
    except Exception as e:
        print(f'  [WATCHLIST] Error adding {horse}: {e}')
        return False


def check_watchlist(horse: str) -> dict | None:
    """
    Check if a horse is on the active watchlist.
    Returns the watchlist entry dict or None.
    Called during morning analysis for each runner.
    """
    try:
        tbl = _table()
        horse_slug = _slug(horse)

        # Scan watchlist for this horse (slug match)
        resp = tbl.scan(
            FilterExpression='bet_date = :wl AND horse_slug = :hs AND active = :a',
            ExpressionAttributeValues={
                ':wl': _WATCHLIST_DATE,
                ':hs': horse_slug,
                ':a': True,
            },
            ProjectionExpression='bet_id, horse, date_added, watchlist_reason, watchlist_category, runs_since_added, last_going, last_race_type, beaten_lengths, model_score'
        )
        items = resp.get('Items', [])
        if not items:
            return None
        # Return most recent entry
        return sorted(items, key=lambda x: str(x.get('date_added', '')), reverse=True)[0]
    except Exception as e:
        print(f'  [WATCHLIST] check error for {horse}: {e}')
        return None


def increment_runs(horse: str, won: bool = False):
    """
    Called after each run: increment runs_since_added counter.
    If won, mark as converted. If exceeded max runs, deactivate.
    """
    try:
        tbl = _table()
        horse_slug = _slug(horse)
        resp = tbl.scan(
            FilterExpression='bet_date = :wl AND horse_slug = :hs AND active = :a',
            ExpressionAttributeValues={':wl': _WATCHLIST_DATE, ':hs': horse_slug, ':a': True}
        )
        for item in resp.get('Items', []):
            runs = int(item.get('runs_since_added', 0)) + 1
            if won:
                tbl.update_item(
                    Key={'bet_date': _WATCHLIST_DATE, 'bet_id': item['bet_id']},
                    UpdateExpression='SET active = :f, converted = :t, runs_since_added = :r',
                    ExpressionAttributeValues={':f': False, ':t': True, ':r': runs}
                )
                print(f'  [WATCHLIST] 🏆 {horse} WON — watchlist CONVERTED! ({runs} runs)')
            elif runs >= _MAX_RUNS_WITHOUT_WIN:
                tbl.update_item(
                    Key={'bet_date': _WATCHLIST_DATE, 'bet_id': item['bet_id']},
                    UpdateExpression='SET active = :f, runs_since_added = :r',
                    ExpressionAttributeValues={':f': False, ':r': runs}
                )
                print(f'  [WATCHLIST] ⏰ {horse} expired after {runs} runs without winning')
            else:
                tbl.update_item(
                    Key={'bet_date': _WATCHLIST_DATE, 'bet_id': item['bet_id']},
                    UpdateExpression='SET runs_since_added = :r',
                    ExpressionAttributeValues={':r': runs}
                )
    except Exception as e:
        print(f'  [WATCHLIST] increment_runs error for {horse}: {e}')


def get_active_watchlist() -> list[dict]:
    """Return all active watchlist entries, newest first."""
    try:
        tbl = _table()
        resp = tbl.scan(
            FilterExpression='bet_date = :wl AND active = :a',
            ExpressionAttributeValues={':wl': _WATCHLIST_DATE, ':a': True}
        )
        items = resp.get('Items', [])
        return sorted(items, key=lambda x: str(x.get('date_added', '')), reverse=True)
    except Exception as e:
        print(f'  [WATCHLIST] get_active_watchlist error: {e}')
        return []
