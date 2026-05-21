"""
favs_run.py  —  Parallel "Lay the Favourite" Analysis
======================================================
READ-ONLY side-script. Does NOT update weights or UI.

Scans today (and optionally N future days) from SureBetBets,
identifies the market favourite in each race, applies a
"Suspect Favourite" scoring model, and reports lay candidates.

Usage:
    python favs_run.py                     # today only, text output
    python favs_run.py --days 3            # today + next 2 days
    python favs_run.py --date 2026-03-26   # specific date
    python favs_run.py --json              # JSON output
    python favs_run.py --html              # save HTML to favs-run.html
    python favs_run.py --threshold 4       # only show score >= 4

Scheduled daily at 14:00 via Windows Task Scheduler (favs_run_daily task).

Suspect Favourite Scoring (higher = more layable):
  +4  Class    — moving up in class
  +2  Trip     — new distance (up or down, unproven)
  +2  Going    — unproven on current going
  +1  Draw     — poor draw on track record
  +1  Layoff   — 30-90 day absence (recent form stale)
  +1  Pace     — going_suitability=0 & score relies on other factors
  +2  Rivals   — 2nd/3rd fav have score within 25% of favourite
  +1  Drift    — price drifted since open (score gap < 10)
  +1  Price    — 5/4 or less (overshortened)

  0-3  = LEAVE ALONE  (green)
  4-8  = CAUTION / TAKE A LOOK  (yellow)
  9+   = STRONG LAY CANDIDATE  (red)
"""

import sys
import os
import re
import json
import argparse
from datetime import date, timedelta, datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

# ── helpers ────────────────────────────────────────────────────────────────

def dec(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, dict):
        return {k: dec(v) for k, v in o.items()}
    if isinstance(o, list):
        return [dec(v) for v in o]
    return o


def odds_to_decimal(odds):
    """Convert fractional (5/4) or decimal (2.25) odds to float decimal."""
    if odds is None:
        return None
    try:
        odds = float(odds)
        return odds
    except (TypeError, ValueError):
        pass
    try:
        s = str(odds).strip()
        if '/' in s:
            n, d = s.split('/')
            return float(n) / float(d) + 1.0
    except Exception:
        pass
    return None


def parse_form(form_str):
    """Return list of recent positions (int where parseable) from form string."""
    if not form_str:
        return []
    digits = []
    for ch in str(form_str).replace('-', '').replace('/', ''):
        if ch.isdigit():
            digits.append(int(ch))
        elif ch.upper() in ('U', 'F', 'P', 'R'):
            digits.append(99)   # treated as non-finish
    return digits[-6:]   # last 6 runs


# ── Suspect Favourite Scoring ───────────────────────────────────────────────

SCORE_LABELS = {
    'class_up':              ('Class',         '+4  Moving up in class'),
    'trip_new':              ('Trip',          '+2  Unproven at this distance'),
    'going_unproven':        ('Going',         '+2  Unproven on current going'),
    'draw_poor':             ('Draw',          '+1  Poor draw position'),
    'layoff':                ('Layoff',        '+1  30-90 days off (stale form)'),
    'pace_doubt':            ('Pace',          '+1  Pace may not suit'),
    'rivals_close':          ('Rivals',        '+2  2nd/3rd fav within 25% of favourite score'),
    'drift':                 ('Drift',         '+1  Market drift — open vs current price'),
    'short_price':           ('Price',         '+1  5/4 or less / odds-on'),
    'trainer_track':         ('Trainer@Track', '+1  Trainer win rate at this track'),
    'trainer_cold':          ('TrainerCold',   '+1  Trainer cold last 14 days'),
    'trainer_multiple':      ('MultiRunner',   '+1  Trainer with multiple runners in race'),
    'current_form_no_wins':  ('FormNoWins',    '+1  No wins in last 4 races'),
}

SCORE_WEIGHTS = {
    'class_up':              4,
    'trip_new':              2,
    'going_unproven':        2,
    'draw_poor':             1,
    'layoff':                1,
    'pace_doubt':            1,
    'rivals_close':          2,
    'drift':                 1,
    'short_price':           1,
    'trainer_track':         1,
    'trainer_cold':          1,
    'trainer_multiple':      1,
    'current_form_no_wins':  1,
}


def score_favourite(fav, all_horses_sorted, race_going=''):
    """
    Score how 'suspect' this favourite is for laying.
    fav              — dict from DynamoDB (the pick record for the favourite)
    all_horses_sorted — all horses sorted by odds ascending
    race_going       — going string if available

    Returns (total_score, flags_dict, details_list)
    """
    sb = fav.get('score_breakdown') or {}
    flags = {}
    details = []

    fav_score = float(fav.get('comprehensive_score') or fav.get('score', 0))
    fav_odds = odds_to_decimal(fav.get('odds') or fav.get('decimal_odds'))

    # --- Short price (+1) ---
    if fav_odds is not None and fav_odds <= 2.25:   # <= 5/4
        flags['short_price'] = True
        details.append('Short price (5/4 or less) — market may overshorten')

    # --- Rivals close (+2) ---
    rivals = [h for h in all_horses_sorted if h.get('horse') != fav.get('horse')]
    if rivals:
        r2_score = float(rivals[0].get('score', 0)) if len(rivals) >= 1 else 0
        r3_score = float(rivals[1].get('score', 0)) if len(rivals) >= 2 else 0
        # If nearest rival is within 25% of fav score
        if fav_score > 0 and (r2_score / fav_score) >= 0.75:
            flags['rivals_close'] = True
            details.append(f'Rivals close: 2nd ({rivals[0].get("horse","")}) scored {r2_score:.0f} vs fav {fav_score:.0f} ({r2_score/fav_score*100:.0f}%)')
        elif fav_score > 0 and len(rivals) >= 2 and (r3_score / fav_score) >= 0.70:
            flags['rivals_close'] = True
            details.append(f'3rd fav ({rivals[1].get("horse","")}) scored {r3_score:.0f} — field competitive')

    # --- Going unproven (+2) ---
    going_pts = float(sb.get('going_suitability', 0))
    heavy_pts = float(sb.get('heavy_going_penalty', 0))
    if going_pts == 0 and heavy_pts == 0:
        flags['going_unproven'] = True
        details.append('Going suitability = 0 — unproven on today\'s ground')

    # --- Trip unproven (+2) ---
    dist_pts = float(sb.get('distance_suitability', 0))
    cd_pts = float(sb.get('cd_bonus', 0))
    if dist_pts == 0 and cd_pts == 0:
        flags['trip_new'] = True
        details.append('Distance suitability = 0 & no CD bonus — unproven at this trip')

    # --- Class up (+4) ---
    # Proxy: no cd_bonus, no course_performance, no database_history, but has official_rating_bonus
    or_pts = float(sb.get('official_rating_bonus', 0))
    db_pts = float(sb.get('database_history', 0))
    course_pts = float(sb.get('course_performance', 0))
    if or_pts > 0 and cd_pts == 0 and course_pts == 0 and db_pts == 0:
        flags['class_up'] = True
        details.append('No prior wins at course/class — stepping up in class')

    # --- Layoff (+1) ---
    form_str = str(fav.get('form') or '')
    # Check selection_reasons for layoff signals
    reasons_text = ' '.join(str(r) for r in (fav.get('selection_reasons') or fav.get('reasons') or []))
    if 'days off' in reasons_text.lower() or 'days since' in reasons_text.lower():
        flags['layoff'] = True
        details.append('Significant layoff flagged in selection reasons')
    else:
        # Heuristic: form string contains '-' or '//' indicating break
        if '--' in form_str or form_str.count('-') >= 2:
            flags['layoff'] = True
            details.append(f'Form string suggests recent layoff: {form_str}')

    # --- Draw poor (+1) ---
    draw = fav.get('draw')
    total_runners = float(fav.get('race_total_count') or fav.get('total_runners') or 0)
    if draw and total_runners > 0:
        draw_n = float(draw)
        # High draw in large field flat races (draw bias heuristic for large fields)
        if total_runners >= 10 and draw_n >= total_runners * 0.7:
            flags['draw_poor'] = True
            details.append(f'High draw ({draw_n:.0f}/{total_runners:.0f}) — potential draw disadvantage')

    # --- Pace doubt (+1) ---
    # If pace-related score contributions are zero and horse has no recent win
    recent_win_pts = float(sb.get('recent_win', 0))
    if going_pts == 0 and recent_win_pts == 0:
        flags['pace_doubt'] = True
        details.append('No going suitability or recent win signal — pace may not suit')

    # --- Trainer at track win rate (+1) ---
    fav_trainer = str(fav.get('trainer') or '').strip()
    trainer_rep_pts = float(sb.get('trainer_reputation', 0))
    if fav_trainer and trainer_rep_pts == 0:
        flags['trainer_track'] = True
        details.append(f'Trainer ({fav_trainer}) — no quality tier status at this track (win rate unverified)')

    # --- Trainer cold last 14 days (+1) ---
    meeting_pts = float(sb.get('meeting_focus', 0))
    recent_form = form_str[-4:] if len(form_str) >= 4 else form_str
    recent_wins_in_form = sum(1 for c in recent_form if c == '1')
    if fav_trainer and meeting_pts == 0 and recent_wins_in_form == 0:
        flags['trainer_cold'] = True
        details.append(f'Trainer ({fav_trainer}) — no meeting focus & no win in recent form (cold indicator)')

    # --- Trainer with multiple runners (+1) ---
    if fav_trainer and all_horses_sorted:
        multi_count = sum(
            1 for h in all_horses_sorted
            if (str(h.get('trainer') or '').strip().lower() == fav_trainer.lower()
                and (h.get('horse') or '') != (fav.get('horse') or ''))
        )
        if multi_count >= 1:
            flags['trainer_multiple'] = True
            details.append(f'Trainer ({fav_trainer}) has {multi_count + 1} runners in race — possible divided loyalties')

    # --- Drift (+1) ---
    # Proxy: score_gap < 10 means rivals are close on our model = market may be drifting
    score_gap = float(fav.get('score_gap') or 0)
    if 0 < score_gap < 10:
        flags['drift'] = True
        details.append(f'Low score gap ({score_gap:.0f}) — field competitive, possible drift')
    elif score_gap == 0 and fav_score > 0:
        flags['drift'] = True
        details.append('Score gap = 0 — our model does not separate the favourite clearly')

    # --- Current form – no wins (+1) ---
    # Horse with 2nd or worse over last 4 races
    form_digits = _parse_form(form_str)
    last_4 = form_digits[-4:] if len(form_digits) >= 4 else form_digits
    if last_4 and all(pos >= 2 for pos in last_4):
        flags['current_form_no_wins'] = True
        details.append(f'No wins in last 4 races (form: {form_str[-8:]}) — 2nd or worse throughout')

    total = sum(SCORE_WEIGHTS[f] for f in flags)
    return total, flags, details


# ── Verdict helpers ──────────────────────────────────────────────────────────

def verdict(score):
    if score >= 13:
        return 'STRONG LAY CANDIDATE', 'RED'
    elif score >= 9:
        return 'STRONG LAY', 'AMBER'
    elif score >= 4:
        return 'CAUTION / TAKE A LOOK', 'YELLOW'
    else:
        return 'DO NOT SHOW', 'GREEN'


ANSI = {
    'RED':    '\033[91m',
    'AMBER':  '\033[38;5;208m',
    'YELLOW': '\033[93m',
    'GREEN':  '\033[92m',
    'BOLD':   '\033[1m',
    'RESET':  '\033[0m',
}


def colour(text, colour_key):
    return ANSI.get(colour_key, '') + text + ANSI['RESET']


# ── Main Analysis ──────────────────────────────────────────────────────────

def _utc_to_local_hhmm(utc_hhmm: str, date_str: str) -> str:
    """Convert UTC HH:MM string to UK local time (BST = UTC+1, late Mar – late Oct)."""
    try:
        d = date.fromisoformat(date_str[:10])
        bst_start = date(d.year, 3, 31)
        while bst_start.weekday() != 6:
            bst_start = date(bst_start.year, bst_start.month, bst_start.day - 1)
        bst_end = date(d.year, 10, 31)
        while bst_end.weekday() != 6:
            bst_end = date(bst_end.year, bst_end.month, bst_end.day - 1)
        if not (bst_start <= d < bst_end):
            return utc_hhmm
        h, mn = map(int, utc_hhmm.split(':'))
        total = h * 60 + mn + 60
        return f'{(total // 60) % 24:02d}:{total % 60:02d}'
    except Exception:
        return utc_hhmm


def _fetch_sl_winner_map():
    """
    Fetch https://www.sportinglife.com/racing/fast-results/all and return a lookup:
        { (course_lower, local_hhmm): winner_name }
    Used to determine if the favourite won or lost after the race.
    Returns an empty dict on any network/parse error.
    """
    try:
        import urllib.request as _ur
        req = _ur.Request(
            'https://www.sportinglife.com/racing/fast-results/all',
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0.0.0 Safari/537.36'
                ),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-GB,en;q=0.5',
                'Referer': 'https://www.sportinglife.com/',
            },
        )
        with _ur.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'[favs_run] _fetch_sl_winner_map fetch error: {e}')
        return {}

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        print('[favs_run] __NEXT_DATA__ not found in SL fast-results page')
        return {}

    try:
        data = json.loads(m.group(1))
    except Exception as e:
        print(f'[favs_run] SL fast-results JSON parse error: {e}')
        return {}

    fast = data.get('props', {}).get('pageProps', {}).get('fastResults', [])
    winner_map = {}
    for fr in fast:
        top_horses = fr.get('top_horses')
        if not top_horses:
            continue
        course = fr.get('courseName', '')
        off_time = fr.get('time', '')   # local HH:MM
        if not course or not off_time:
            continue
        sorted_h = sorted(top_horses, key=lambda h: h.get('position', 99))
        winner = sorted_h[0].get('horse_name', '') if sorted_h else ''
        winner = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', winner).strip()
        if winner:
            key = (course.lower().replace('-', ' ').strip(), off_time)
            winner_map[key] = winner

    print(f'[favs_run] SL winner_map: {len(winner_map)} races with results')
    return winner_map


def analyse_date(target_date_str, db_table, winner_map=None):
    """Return list of race analysis dicts for one date."""
    resp = db_table.query(
        KeyConditionExpression=Key('bet_date').eq(target_date_str)
    )
    all_items = [dec(it) for it in resp.get('Items', [])]

    if not all_items:
        return []

    # Group by race_time + course
    races = {}
    for it in all_items:
        rt = str(it.get('race_time', ''))[:16]
        course = it.get('course', '') or it.get('race_course', '')
        key = f'{rt}|{course}'
        if key not in races:
            races[key] = []
        races[key].append(it)

    results = []
    for race_key, runners in sorted(races.items()):
        rt, course = race_key.split('|', 1)

        # Sort by odds ascending — lowest odds = favourite
        def sort_odds(h):
            o = odds_to_decimal(h.get('odds') or h.get('decimal_odds'))
            return o if o else 99.0

        runners_sorted = sorted(runners, key=sort_odds)
        fav = runners_sorted[0]
        fav_odds_dec = sort_odds(fav)

        # Only analyse if favourite is 5/4 (2.25) or less
        if fav_odds_dec > 2.25:
            continue

        # Build all_horses_sorted for rival scoring
        # Use the all_horses array from the favourite's own record if available
        # otherwise use the race runners list
        all_horses_raw = fav.get('all_horses') or []
        if all_horses_raw:
            all_horses_sorted = sorted(all_horses_raw, key=lambda h: float(h.get('odds') or 99))
        else:
            all_horses_sorted = [
                {'horse': h.get('horse', ''), 'score': h.get('comprehensive_score', 0), 'odds': sort_odds(h)}
                for h in runners_sorted
            ]

        lay_score, flags, details = score_favourite(fav, all_horses_sorted)

        verd, verd_colour = verdict(lay_score)

        race_name = fav.get('race_name') or f'{course} {rt[11:16]}'
        fav_sys_score = float(fav.get('comprehensive_score') or fav.get('score', 0))

        # Determine if favourite won/lost.
        # Priority 1: SL fast-results winner map (most reliable — any finished race)
        # Priority 2: scan DynamoDB runners for a pick with outcome='win'
        # Priority 3: the favourite's own outcome field (only if it was a pick)
        fav_name = fav.get('horse', '') or ''
        fav_outcome = None

        if winner_map:
            # Convert UTC race_time to UK local for SL time matching.
            # race_time may contain a Betfair UTC Z-suffix or tz offset — extract UTC time
            # before converting to local so BST conversion is applied only once.
            rt_raw = str(fav.get('race_time', '') or rt)
            date_part = rt[:10] if len(rt) >= 10 else target_date_str
            try:
                tz_m = re.search(r'([+-])(\d{2}):(\d{2})\s*$', rt_raw)
                if tz_m:
                    # Has explicit offset (+01:00 BST or +00:00 UTC) — convert to UTC
                    sign = 1 if tz_m.group(1) == '+' else -1
                    offset_mins = sign * (int(tz_m.group(2)) * 60 + int(tz_m.group(3)))
                    raw_hm = rt_raw[11:16]
                    h2, m2 = map(int, raw_hm.split(':'))
                    utc_total = h2 * 60 + m2 - offset_mins
                    utc_hhmm = f'{(utc_total // 60) % 24:02d}:{utc_total % 60:02d}'
                else:
                    # No offset — Betfair UTC Z format or bare datetime, treat as UTC
                    utc_hhmm = rt[11:16] if len(rt) >= 16 else ''
            except Exception:
                utc_hhmm = rt[11:16] if len(rt) >= 16 else ''
            local_hhmm = _utc_to_local_hhmm(utc_hhmm, date_part)
            # Normalise course: SL may return "Kempton Park" while DB stores "Kempton"
            # Use substring matching in both directions to handle these variants.
            course_key = course.lower().replace('-', ' ').strip()
            fav_name_norm = re.sub(r"['\-]+", ' ', fav_name).strip().lower()
            try:
                lh, lm = map(int, local_hhmm.split(':'))
                local_mins = lh * 60 + lm
                best_diff = 999
                best_winner = None
                for (c_key, t_key), w_name in winner_map.items():
                    # Fuzzy course match: exact OR one name contains the other
                    if c_key != course_key and c_key not in course_key and course_key not in c_key:
                        continue
                    wh, wm = map(int, t_key.split(':'))
                    diff = abs((wh * 60 + wm) - local_mins)
                    if diff < best_diff:
                        best_diff = diff
                        best_winner = w_name.strip()
                if best_winner and best_diff <= 10:
                    w_norm = re.sub(r"['\-]+", ' ', best_winner).strip().lower()
                    fav_outcome = 'win' if w_norm == fav_name_norm else 'loss'
            except Exception:
                pass

        if fav_outcome is None:
            # Fallback: scan all runners in this race for a settled outcome='win'
            winner_name = None
            for h in runners:
                if (h.get('outcome') or '').lower() == 'win':
                    winner_name = h.get('horse', '')
                    break
            if winner_name:
                w_norm2 = re.sub(r"['\-]+", ' ', winner_name).strip().lower()
                fn_norm2 = re.sub(r"['\-]+", ' ', fav_name).strip().lower()
                fav_outcome = 'win' if w_norm2 == fn_norm2 else 'loss'
            else:
                fav_outcome = fav.get('outcome') or None

        results.append({
            'date':       target_date_str,
            'race_time':  rt,
            'course':     course,
            'race_name':  race_name,
            'favourite':  fav_name or '?',
            'fav_odds':   fav_odds_dec,
            'fav_sys_score': fav_sys_score,
            'score_gap':  float(fav.get('score_gap') or 0),
            'runners':    len(runners),
            'lay_score':  lay_score,
            'flags':      list(flags.keys()),
            'details':    details,
            'verdict':    verd,
            'verdict_colour': verd_colour,
            'form':       fav.get('form', ''),
            'trainer':    fav.get('trainer', ''),
            'jockey':     fav.get('jockey', ''),
            'our_pick':   fav.get('show_in_ui', False),
            'outcome':    fav_outcome,
        })

    results.sort(key=lambda r: r['lay_score'], reverse=True)
    return results


# ── Output ──────────────────────────────────────────────────────────────────

def print_results(all_results, threshold=0):
    total_races = len(all_results)
    lay_candidates = [r for r in all_results if r['lay_score'] >= 4]
    amber_lays    = [r for r in all_results if r['lay_score'] >= 9]
    strong_lays   = [r for r in all_results if r['lay_score'] >= 13]

    print()
    print(colour('=' * 72, 'BOLD'))
    print(colour('  FAVS-RUN  —  Suspect Favourite Lay Analysis', 'BOLD'))
    print(colour('=' * 72, 'BOLD'))
    print(f'  Short-price favourites analysed:    {total_races}')
    print(f'  Caution candidates (score 4+):      {len(lay_candidates)}')
    print(f'  Strong lay candidates (9–12):       {len(amber_lays) - len(strong_lays)}')
    print(f'  Red flag candidates (13+):          {len(strong_lays)}')
    print()

    filtered = [r for r in all_results if r['lay_score'] >= threshold]

    if not filtered:
        print('  No favourites above the score threshold today.')
        return

    for r in filtered:
        vd = colour(f"[{r['verdict']}]", r['verdict_colour'])
        print(colour('-' * 72, 'BOLD'))
        print(f"  {r['race_time'][11:16]}  {r['course']}  |  {r['race_name'][:45]}")
        print(f"  Favourite: {colour(r['favourite'], 'BOLD')}  @ {r['fav_odds']:.2f}  "
              f"(SysScore:{r['fav_sys_score']:.0f}  Gap:{r['score_gap']:.0f}  "
              f"Form:{r['form']}  Runners:{r['runners']})")
        print(f"  Trainer:   {r['trainer']}   Jockey: {r['jockey']}")
        print(f"  OUR PICK?  {'YES — our system also backed this horse' if r['our_pick'] else 'No'}")
        print()
        print(f"  LAY SCORE: {colour(str(r['lay_score']), r['verdict_colour'])} / 15   {vd}")
        print()
        if r['flags']:
            flag_parts = []
            for f in r['flags']:
                label = SCORE_LABELS.get(f, (f, ''))[0]
                pts = SCORE_WEIGHTS.get(f, 0)
                flag_parts.append(f"{label}(+{pts})")
            print(f"  Flags:  {', '.join(flag_parts)}")
        print()
        for d in r['details']:
            print(f"    • {d}")
        print()

    # Summary table
    print(colour('=' * 72, 'BOLD'))
    print(colour('  SUMMARY TABLE', 'BOLD'))
    print(colour('=' * 72, 'BOLD'))
    print(f"  {'Date':<12} {'Time':<6} {'Course':<14} {'Favourite':<22} {'Odds':>5} {'LayScore':>9} {'Verdict'}")
    print(f"  {'-'*12} {'-'*6} {'-'*14} {'-'*22} {'-'*5} {'-'*9} {'-'*22}")
    for r in all_results:
        vline = colour(f"{r['lay_score']:>3}  {r['verdict']}", r['verdict_colour'])
        print(f"  {r['date']:<12} {r['race_time'][11:16]:<6} {r['course']:<14} "
              f"{r['favourite']:<22} {r['fav_odds']:>5.2f}         {vline}")
    print()


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Favs-Run: Lay the Favourite Analysis')
    parser.add_argument('--days', type=int, default=1,
                        help='Number of days to analyse starting today (default: 1)')
    parser.add_argument('--date', default=None,
                        help='Specific start date YYYY-MM-DD (default: today)')
    parser.add_argument('--json', action='store_true', dest='json_out',
                        help='Output JSON instead of text')
    parser.add_argument('--threshold', type=int, default=0,
                        help='Minimum lay score to show (default: 0 = show all)')
    args = parser.parse_args()

    start_date = date.fromisoformat(args.date) if args.date else date.today()
    dates = [
        (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(args.days)
    ]

    db = boto3.resource('dynamodb', region_name='eu-west-1')
    tbl = db.Table('SureBetBets')

    all_results = []
    for d in dates:
        day_results = analyse_date(d, tbl)
        all_results.extend(day_results)

    if args.json_out:
        print(json.dumps(all_results, indent=2, default=str))
        return

    print_results(all_results, threshold=args.threshold)

    # Win/loss tracking hook (read-only comparison against outcomes)
    settled = [r for r in all_results if r.get('outcome') not in (None, 'pending', '')]
    if settled:
        print(colour('  OUTCOME TRACKING (settled races)', 'BOLD'))
        correct_lays = 0
        for r in settled:
            outcome = r.get('outcome', '')
            lay_correct = outcome != 'win' and r['lay_score'] >= 4
            correct_lays += 1 if lay_correct else 0
            icon = 'OK' if lay_correct else '--'
            print(f"  [{icon}] {r['course']} {r['race_time'][11:16]} "
                  f"{r['favourite']} (lay:{r['lay_score']}) -> {outcome}")
        print(f"\n  Lay accuracy: {correct_lays}/{len(settled)} = "
              f"{correct_lays/len(settled)*100:.0f}%")
        print()


# ── HTML Output ─────────────────────────────────────────────────────────────

def build_html(all_results, generated_at=None):
    if generated_at is None:
        generated_at = datetime.now().strftime('%d %b %Y %H:%M')

    total    = len(all_results)
    caution  = sum(1 for r in all_results if r['lay_score'] >= 4)
    strong   = sum(1 for r in all_results if r['lay_score'] >= 9)
    red_flag = sum(1 for r in all_results if r['lay_score'] >= 13)

    COLOUR_MAP = {
        'RED':    ('#f85149', '#2d1b1b'),
        'AMBER':  ('#f97316', '#2a1508'),
        'YELLOW': ('#d29922', '#2a1f0a'),
        'GREEN':  ('#3fb950', '#0d2318'),
    }

    def flag_chips(flags):
        chips = []
        for f in flags:
            label = SCORE_LABELS.get(f, (f, ''))[0]
            pts   = SCORE_WEIGHTS.get(f, 0)
            chips.append(f'<span class="chip chip-{f}">{label} +{pts}</span>')
        return ''.join(chips)

    def details_list(details):
        items = ''.join(f'<li>{d}</li>' for d in details)
        return f'<ul class="detail-list">{items}</ul>' if items else ''

    def score_bar(score, max_score=18):
        pct = min(100, int(score / max_score * 100))
        if score >= 13:
            bar_colour = '#f85149'
        elif score >= 10:
            bar_colour = '#f97316'
        elif score >= 4:
            bar_colour = '#d29922'
        else:
            bar_colour = '#3fb950'
        return (f'<div class="score-bar-wrap"><div class="score-bar" '
                f'style="width:{pct}%;background:{bar_colour}"></div></div>')

    cards_html = ''
    for r in all_results:
        fg, bg = COLOUR_MAP.get(r['verdict_colour'], ('#8b949e', '#161b22'))
        our_pick_badge = (
            '<span class="our-pick-badge">⚡ OUR SYSTEM PICK</span>'
            if r['our_pick'] else ''
        )
        cards_html += f"""
  <div class="race-card vc-{r['verdict_colour'].lower()}">
    <div class="card-header">
      <div class="card-time">{r['race_time'][11:16]}</div>
      <div class="card-course">{r['course']}</div>
      <div class="card-race">{r['race_name'][:60]}</div>
      {our_pick_badge}
      <div class="card-verdict" style="color:{fg};background:{bg};border-color:{fg}">
        {r['verdict']}
      </div>
    </div>
    <div class="card-body">
      <div class="card-main">
        <div class="horse-name">{r['favourite']}</div>
        <div class="horse-meta">
          <span class="meta-item">@ <b>{r['fav_odds']:.2f}</b></span>
          <span class="meta-item">Sys&nbsp;Score: <b>{r['fav_sys_score']:.0f}</b></span>
          <span class="meta-item">Score&nbsp;Gap: <b>{r['score_gap']:.0f}</b></span>
          <span class="meta-item">Form: <b>{r['form'] or '—'}</b></span>
          <span class="meta-item">Runners: <b>{r['runners']}</b></span>
        </div>
        <div class="horse-meta" style="margin-top:4px">
          <span class="meta-item">Trainer: <b>{r['trainer'] or '—'}</b></span>
          <span class="meta-item">Jockey: <b>{r['jockey'] or '—'}</b></span>
        </div>
      </div>
      <div class="card-score-block">
        <div class="lay-score" style="color:{fg}">{r['lay_score']}</div>
        <div class="lay-score-denom">/ 18</div>
        {score_bar(r['lay_score'])}
      </div>
    </div>
    <div class="card-flags">{flag_chips(r['flags'])}</div>
    {details_list(r['details'])}
  </div>"""

    # Summary table rows
    table_rows = ''
    for r in all_results:
        fg, bg = COLOUR_MAP.get(r['verdict_colour'], ('#8b949e', '#161b22'))
        table_rows += f"""
    <tr>
      <td>{r['date']}</td>
      <td>{r['race_time'][11:16]}</td>
      <td>{r['course']}</td>
      <td><b>{r['favourite']}</b></td>
      <td>{r['fav_odds']:.2f}</td>
      <td>{r['fav_sys_score']:.0f}</td>
      <td>{r['score_gap']:.0f}</td>
      <td style="color:{fg};font-weight:700">{r['lay_score']}</td>
      <td><span class="verdict-pill" style="color:{fg};background:{bg};border-color:{fg}">{r['verdict']}</span></td>
    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Favs-Run — Lay the Favourite Report</title>
<style>
  :root {{
    --bg:        #0d1117;
    --panel:     #161b22;
    --border:    #30363d;
    --accent:    #58a6ff;
    --green:     #3fb950;
    --amber:     #d29922;
    --red:       #f85149;
    --muted:     #8b949e;
    --text:      #e6edf3;
    --text2:     #c9d1d9;
    --tag-bg:    #21262d;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px; line-height: 1.6; }}

  /* Header */
  .header {{
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1c2333 100%);
    border-bottom: 1px solid var(--border);
    padding: 32px 48px 24px;
  }}
  .header-logo {{ font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }}
  .header h1 {{ font-size: 28px; font-weight: 700; }}
  .header h1 span {{ color: var(--red); }}
  .header-sub {{ margin-top: 6px; color: var(--muted); font-size: 13px; }}
  .header-meta {{ margin-top: 16px; display: flex; gap: 16px; flex-wrap: wrap; }}
  .meta-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--tag-bg); border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px; font-size: 12px; color: var(--muted);
  }}
  .meta-pill b {{ color: var(--text2); }}

  /* Legend */
  .legend {{ display: flex; gap: 24px; padding: 16px 48px; border-bottom: 1px solid var(--border); flex-wrap: wrap; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

  /* Scoring table */
  .scoring-panel {{ margin: 24px 48px; background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 20px 24px; }}
  .scoring-panel h3 {{ font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 12px; }}
  .scoring-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 6px 24px; }}
  .scoring-row {{ display: flex; align-items: baseline; gap: 8px; font-size: 12px; }}
  .scoring-pts {{ color: var(--amber); font-weight: 700; min-width: 24px; }}
  .scoring-label {{ color: var(--text2); font-weight: 600; }}
  .scoring-desc {{ color: var(--muted); }}

  /* Cards */
  .cards-section {{ padding: 24px 48px; }}
  .section-title {{ font-size: 13px; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 16px; }}

  .race-card {{
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 10px; margin-bottom: 16px; overflow: hidden;
  }}
  .race-card.vc-red    {{ border-left: 4px solid #f85149; }}
  .race-card.vc-amber  {{ border-left: 4px solid #f97316; }}
  .race-card.vc-yellow {{ border-left: 4px solid #d29922; }}
  .race-card.vc-green  {{ border-left: 4px solid #3fb950; }}

  .card-header {{
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 12px 20px; border-bottom: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
  }}
  .card-time {{ font-weight: 700; color: var(--accent); font-size: 15px; min-width: 40px; }}
  .card-course {{ font-weight: 600; color: var(--text); }}
  .card-race {{ flex: 1; color: var(--muted); font-size: 12px; }}
  .our-pick-badge {{
    background: #1a3a52; color: var(--accent); border: 1px solid #2d5a80;
    border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;
  }}
  .card-verdict {{
    border: 1px solid; border-radius: 5px; padding: 3px 10px;
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
  }}

  .card-body {{ display: flex; align-items: center; padding: 16px 20px; gap: 20px; }}
  .card-main {{ flex: 1; }}
  .horse-name {{ font-size: 20px; font-weight: 700; color: var(--text); margin-bottom: 6px; }}
  .horse-meta {{ display: flex; flex-wrap: wrap; gap: 4px 16px; }}
  .meta-item {{ font-size: 12px; color: var(--muted); }}
  .meta-item b {{ color: var(--text2); }}

  .card-score-block {{ text-align: center; min-width: 80px; }}
  .lay-score {{ font-size: 40px; font-weight: 700; line-height: 1; }}
  .lay-score-denom {{ font-size: 12px; color: var(--muted); margin-bottom: 6px; }}
  .score-bar-wrap {{ width: 70px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }}
  .score-bar {{ height: 100%; border-radius: 3px; transition: width 0.3s; }}

  .card-flags {{ padding: 8px 20px 12px; display: flex; flex-wrap: wrap; gap: 6px; }}
  .chip {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 600;
    background: var(--tag-bg); color: var(--text2); border: 1px solid var(--border);
  }}
  .chip-short_price {{ background: #1a1a2e; color: #a78bfa; border-color: #4c1d95; }}
  .chip-rivals_close {{ background: #1f2d3d; color: #60a5fa; border-color: #1d4ed8; }}
  .chip-trip_new     {{ background: #1f2a1f; color: #6ee7b7; border-color: #065f46; }}
  .chip-going_unproven {{ background: #1f2a1f; color: #34d399; border-color: #064e3b; }}
  .chip-draw_poor    {{ background: #2a1f0a; color: #fbbf24; border-color: #92400e; }}
  .chip-layoff       {{ background: #271a1a; color: #fca5a5; border-color: #7f1d1d; }}
  .chip-pace_doubt   {{ background: #1a1f27; color: #93c5fd; border-color: #1e3a5f; }}
  .chip-drift           {{ background: #271f0a; color: #fcd34d; border-color: #78350f; }}
  .chip-class_up        {{ background: #2d1b3d; color: #c084fc; border-color: #6b21a8; }}
  .chip-trainer_track   {{ background: #1a2040; color: #a5b4fc; border-color: #4338ca; }}
  .chip-trainer_cold    {{ background: #1a1a30; color: #818cf8; border-color: #3730a3; }}
  .chip-trainer_multiple {{ background: #200a2a; color: #e879f9; border-color: #7e22ce; }}

  .detail-list {{ padding: 0 20px 14px 36px; }}
  .detail-list li {{ font-size: 12px; color: var(--muted); margin-bottom: 3px; }}
  .detail-list li::marker {{ color: var(--amber); }}

  /* Summary table */
  .table-section {{ padding: 0 48px 40px; }}
  .summary-table {{ width: 100%; border-collapse: collapse; background: var(--panel); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }}
  .summary-table th {{ background: var(--tag-bg); color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
  .summary-table td {{ padding: 10px 14px; border-bottom: 1px solid rgba(48,54,61,0.5); font-size: 13px; }}
  .summary-table tr:last-child td {{ border-bottom: none; }}
  .summary-table tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .verdict-pill {{ border: 1px solid; border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; white-space: nowrap; }}

  .footer {{ text-align: center; padding: 24px; color: var(--muted); font-size: 11px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>

<div class="header">
  <div class="header-logo">SureBet System &nbsp;·&nbsp; Favs-Run</div>
  <h1>Lay the <span>Favourite</span> Report</h1>
  <div class="header-sub">Read-only parallel analysis — does not affect picks, weights or UI</div>
  <div class="header-meta">
    <div class="meta-pill"><span class="dot" style="background:#58a6ff"></span>Generated <b>{generated_at}</b></div>
    <div class="meta-pill"><span class="dot" style="background:#8b949e"></span>Analysed <b>{total}</b> short-price favourites</div>
    <div class="meta-pill"><span class="dot" style="background:#d29922"></span>Caution+ <b>{caution}</b></div>
    <div class="meta-pill"><span class="dot" style="background:#f97316"></span>Strong Lay <b>{strong}</b></div>
    <div class="meta-pill"><span class="dot" style="background:#f85149"></span>Red Flag <b>{red_flag}</b></div>
  </div>
</div>

<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#3fb950"></div>0–3 = Leave alone</div>
  <div class="legend-item"><div class="legend-dot" style="background:#d29922"></div>4–9 = Caution / take a look</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f97316"></div>10–12 = Strong lay</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f85149"></div>13+ = Strong lay candidate</div>
</div>

<div class="scoring-panel">
  <h3>Scoring Factors</h3>
  <div class="scoring-grid">
    <div class="scoring-row"><span class="scoring-pts">+4</span><span class="scoring-label">Class</span><span class="scoring-desc">Moving up in class</span></div>
    <div class="scoring-row"><span class="scoring-pts">+2</span><span class="scoring-label">Trip</span><span class="scoring-desc">New distance (up or down)</span></div>
    <div class="scoring-row"><span class="scoring-pts">+2</span><span class="scoring-label">Going</span><span class="scoring-desc">Unproven on current going</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">Draw</span><span class="scoring-desc">Poor draw on this track</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">Layoff</span><span class="scoring-desc">30–90 days off</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">Pace</span><span class="scoring-desc">Pace may not suit</span></div>
    <div class="scoring-row"><span class="scoring-pts">+2</span><span class="scoring-label">Rivals</span><span class="scoring-desc">Creditable threats (2nd/3rd favs)</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">Drift</span><span class="scoring-desc">Market drift — open vs current</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">Price</span><span class="scoring-desc">5/4 or less / odds-on</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">Trainer@Track</span><span class="scoring-desc">Trainer win rate at that track</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">TrainerCold</span><span class="scoring-desc">Trainer cold last 14 days</span></div>
    <div class="scoring-row"><span class="scoring-pts">+1</span><span class="scoring-label">MultiRunner</span><span class="scoring-desc">Trainer with multiple runners</span></div>
  </div>
</div>

<div class="cards-section">
  <div class="section-title">Race-by-Race Analysis — sorted by Lay Score</div>
  {cards_html}
</div>

<div class="table-section">
  <div class="section-title" style="padding-bottom:12px">Summary Table</div>
  <table class="summary-table">
    <thead>
      <tr>
        <th>Date</th><th>Time</th><th>Course</th><th>Favourite</th>
        <th>Odds</th><th>Sys Score</th><th>Score Gap</th><th>Lay Score</th><th>Verdict</th>
      </tr>
    </thead>
    <tbody>
      {table_rows}
    </tbody>
  </table>
</div>

<div class="footer">
  Favs-Run v1.0 &nbsp;·&nbsp; Weights v4.5 &nbsp;·&nbsp; Read-only parallel run &nbsp;·&nbsp; {generated_at}
</div>
</body>
</html>"""


def save_html(all_results, output_path):
    html = build_html(all_results)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'HTML saved -> {output_path}')


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Favs-Run: Lay the Favourite Analysis')
    parser.add_argument('--days', type=int, default=1,
                        help='Number of days to analyse starting today (default: 1)')
    parser.add_argument('--date', default=None,
                        help='Specific start date YYYY-MM-DD (default: today)')
    parser.add_argument('--json', action='store_true', dest='json_out',
                        help='Output JSON instead of text')
    parser.add_argument('--html', action='store_true', dest='html_out',
                        help='Save HTML report to favs-run.html')
    parser.add_argument('--threshold', type=int, default=0,
                        help='Minimum lay score to show in text output (default: 0 = show all)')
    args = parser.parse_args()

    start_date = date.fromisoformat(args.date) if args.date else date.today()
    dates = [
        (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(args.days)
    ]

    db = boto3.resource('dynamodb', region_name='eu-west-1')
    tbl = db.Table('SureBetBets')

    all_results = []
    for d in dates:
        day_results = analyse_date(d, tbl)
        all_results.extend(day_results)

    if args.json_out:
        print(json.dumps(all_results, indent=2, default=str))
        return

    # Always print text summary
    print_results(all_results, threshold=args.threshold)

    # Save HTML if requested (also always saved when run via scheduler)
    if args.html_out:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favs-run.html')
        save_html(all_results, out_path)

    # Win/loss tracking hook (read-only comparison against outcomes)
    settled = [r for r in all_results if r.get('outcome') not in (None, 'pending', '')]
    if settled:
        print(colour('  OUTCOME TRACKING (settled races)', 'BOLD'))
        correct_lays = 0
        for r in settled:
            outcome = r.get('outcome', '')
            lay_correct = outcome != 'win' and r['lay_score'] >= 4
            correct_lays += 1 if lay_correct else 0
            icon = 'OK' if lay_correct else '--'
            print(f"  [{icon}] {r['course']} {r['race_time'][11:16]} "
                  f"{r['favourite']} (lay:{r['lay_score']}) -> {outcome}")
        print(f"\n  Lay accuracy: {correct_lays}/{len(settled)} = "
              f"{correct_lays/len(settled)*100:.0f}%")
        print()


if __name__ == '__main__':
    main()
