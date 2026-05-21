"""
ourhub_enricher.py
==================
Enriches race/runner data with OurHub Racing API data:
  - course-info  → confirmed going, distance, race class
  - performance-stats → trainer win rate, jockey win rate (14-day)
  - predictionsV3 → win/place probabilities per runner

Called in complete_daily_analysis.py Stage 1b, before scoring begins.
Free tier: 80 requests/day, 10/min — uses 3 calls per enrichment run.
"""

import os
import json
import time
import requests
from datetime import datetime

_API_BASE = 'https://api.ourhub.site/api'
_API_KEY  = os.environ.get('OURHUB_API_KEY', 'oh_dfxqN2ufYVjFvLiK8-FHMnKO3svNbbkP')
_HEADERS  = {'X-API-Key': _API_KEY}
_TIMEOUT  = 15


def _get(endpoint, date_str):
    """Call OurHub API with rate-limit-safe retry."""
    url = f'{_API_BASE}/{endpoint}/{date_str}'
    try:
        r = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code == 429:
            print(f'  [OurHub] Rate limited on {endpoint} — skipping')
            return None
        if r.status_code == 404:
            print(f'  [OurHub] No data for {endpoint}/{date_str}')
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f'  [OurHub] Error fetching {endpoint}: {e}')
        return None


def _normalise_name(name):
    """Lowercase, strip whitespace for matching."""
    return (name or '').strip().lower()


def _utc_to_uk_local(race_time_str):
    """Convert ISO UTC race time to UK local HH:MM (handles BST)."""
    try:
        from datetime import timezone as _tz
        dt = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        dt_utc = dt.astimezone(_tz.utc)
        # Compute BST: last Sunday of March to last Sunday of October
        import calendar
        def _last_sun(y, m):
            last = calendar.monthrange(y, m)[1]
            return next(d for d in range(last, last - 7, -1) if datetime(y, m, d).weekday() == 6)
        bst_on = datetime(dt_utc.year, 3, _last_sun(dt_utc.year, 3), 1, tzinfo=_tz.utc)
        bst_off = datetime(dt_utc.year, 10, _last_sun(dt_utc.year, 10), 1, tzinfo=_tz.utc)
        uk_offset = 1 if bst_on <= dt_utc < bst_off else 0
        from datetime import timedelta
        local = dt_utc + timedelta(hours=uk_offset)
        return f'{local.hour:02d}:{local.minute:02d}'
    except Exception:
        import re
        m = re.search(r'(\d{1,2}):(\d{2})', race_time_str)
        return f'{int(m.group(1)):02d}:{m.group(2)}' if m else ''


def _match_race_key(ourhub_key, course, race_time_str):
    """Match OurHub race key like 'Fakenham 02:40 Race Name' to our course+time.
    
    OurHub has inconsistent time formats:
      - course-info/perf-stats: "02:40" (sometimes strips leading "1" from 14:40)
      - predictionsV3: "14:40" (correct 24hr UK local)
    Our data: UTC ISO "2026-04-13T13:40:00+00:00"
    """
    key_lower = ourhub_key.lower()
    course_lower = course.lower().strip()
    if course_lower not in key_lower:
        return False
    
    uk_time = _utc_to_uk_local(race_time_str)
    if not uk_time:
        return False
    
    # Direct match (e.g. "14:40" in "Fakenham 14:40 Race Name")
    if uk_time in key_lower:
        return True
    
    # OurHub sometimes drops the leading "1" from times >= 10:00
    # e.g. 14:40 becomes "02:40", 15:10 becomes "03:10"
    # Try matching with the leading digit stripped
    if len(uk_time) == 5 and uk_time[0] == '1':
        stripped = '0' + uk_time[2:]  # "14:40" -> "04:40"... no
        # Actually "14:40" -> "02:40" means they subtract 12 (12hr format)
        try:
            hour = int(uk_time[:2])
            if hour >= 13:
                h12 = hour - 12
                time_12h = f'{h12:02d}:{uk_time[3:]}'
                if time_12h in key_lower:
                    return True
        except ValueError:
            pass
    
    return False


def fetch_ourhub_data(date_str):
    """Fetch all 3 endpoints and return consolidated dict keyed by normalised race identifier.

    Returns: {
        'course_info': { 'Newmarket': [{race_time, going, distance, race_class, ...}] },
        'perf_stats':  { '<race_key>': [{ horse_name, stats: {jockey_runs, jockey_wins, ...} }] },
        'predictions': { '<race_key>': { predicted_winner, runners: [{horse, win_prob, ...}] } },
    }
    """
    print(f'  [OurHub] Fetching data for {date_str}...')
    t0 = time.time()

    course_info = _get('course-info', date_str) or {}
    perf_stats  = _get('performance-stats', date_str) or {}
    preds_raw   = _get('predictionsV3', date_str)
    predictions = {}
    if preds_raw and isinstance(preds_raw, dict):
        for race in preds_raw.get('races', []):
            key = f"{race.get('meeting', '')} {race.get('off_time', '')} {race.get('race_name', '')}"
            predictions[key] = race

    elapsed = time.time() - t0
    print(f'  [OurHub] Done in {elapsed:.1f}s — '
          f'{sum(len(v) for v in course_info.values())} course entries, '
          f'{len(perf_stats)} perf-stat races, '
          f'{len(predictions)} prediction races')

    return {
        'course_info': course_info,
        'perf_stats':  perf_stats,
        'predictions': predictions,
    }


def enrich_races(races, ourhub_data):
    """Inject OurHub data into race/runner dicts before scoring.

    Adds to each runner:
      - ourhub_trainer_win_rate  (float, 0-100)
      - ourhub_trainer_runs      (int)
      - ourhub_jockey_win_rate   (float, 0-100)
      - ourhub_jockey_runs       (int)
      - ourhub_win_prob          (float, 0-1)
      - ourhub_place_prob        (float, 0-1)

    Adds to each race:
      - ourhub_going             (str, e.g. 'Good to Soft')
      - ourhub_distance          (str, e.g. '12f')
      - ourhub_race_class        (str, e.g. 'Class 2')
    """
    if not ourhub_data:
        return races

    course_info = ourhub_data.get('course_info', {})
    perf_stats  = ourhub_data.get('perf_stats', {})
    predictions = ourhub_data.get('predictions', {})
    enriched_runners = 0

    for race in races:
        course    = race.get('course') or race.get('venue') or ''
        race_time = race.get('start_time', '')
        runners   = race.get('runners', [])

        # ── Match course info (going) ───────────────────────────────────
        # Fuzzy match: OurHub may use "Newcastle (AW)" while Betfair uses "Newcastle"
        course_races = course_info.get(course, [])
        if not course_races:
            course_lower = course.lower().strip()
            for ci_key, ci_races in course_info.items():
                if course_lower in ci_key.lower() or ci_key.lower() in course_lower:
                    course_races = ci_races
                    break
        matched_course = None
        uk_time = _utc_to_uk_local(race_time) if race_time else ''
        for cr in course_races:
            cr_time = cr.get('race_time', '')
            if uk_time and cr_time:
                # Try direct match and 12hr-stripped match
                if cr_time == uk_time:
                    matched_course = cr
                    break
                # OurHub course-info sometimes uses 12hr format (14:40 -> 02:40)
                try:
                    h = int(uk_time[:2])
                    if h >= 13:
                        h12 = h - 12
                        if cr_time == f'{h12:02d}:{uk_time[3:]}':
                            matched_course = cr
                            break
                except (ValueError, IndexError):
                    pass
        if matched_course:
            race['ourhub_going']       = matched_course.get('going', '')
            race['ourhub_distance']    = matched_course.get('distance', '')
            race['ourhub_race_class']  = matched_course.get('race_class', '')

        # ── Match performance stats and predictions ─────────────────────
        matched_perf = None
        matched_pred = None
        for key in perf_stats:
            if _match_race_key(key, course, race_time):
                matched_perf = perf_stats[key]
                break
        for key in predictions:
            if _match_race_key(key, course, race_time):
                matched_pred = predictions[key]
                break

        # ── Enrich each runner ──────────────────────────────────────────
        perf_by_horse = {}
        if matched_perf and isinstance(matched_perf, list):
            for entry in matched_perf:
                perf_by_horse[_normalise_name(entry.get('horse_name', ''))] = entry

        pred_by_horse = {}
        if matched_pred and isinstance(matched_pred, dict):
            for runner in matched_pred.get('runners', []):
                pred_by_horse[_normalise_name(runner.get('horse', ''))] = runner

        for runner in runners:
            horse_name = _normalise_name(runner.get('name', runner.get('runnerName', '')))

            # Performance stats
            perf = perf_by_horse.get(horse_name, {})
            stats = perf.get('stats', {})
            if stats:
                runner['ourhub_trainer_win_rate'] = stats.get('trainer_win_rate', 0)
                runner['ourhub_trainer_runs']     = stats.get('trainer_runs', 0)
                runner['ourhub_jockey_win_rate']  = stats.get('jockey_win_rate', 0)
                runner['ourhub_jockey_runs']      = stats.get('jockey_runs', 0)

            # Predictions
            pred = pred_by_horse.get(horse_name, {})
            if pred:
                runner['ourhub_win_prob']   = pred.get('win_prob', 0)
                runner['ourhub_place_prob'] = pred.get('place_prob', 0)

            if stats or pred:
                enriched_runners += 1

    print(f'  [OurHub] Enriched {enriched_runners} runners across {len(races)} races')
    return races
