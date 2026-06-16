# -*- coding: utf-8 -*-
"""
COMPLETE DAILY WORKFLOW -- 5-PICK SELECTION ENGINE
===================================================
Strategy:
  1. Score EVERY horse in EVERY race with the comprehensive 7-factor model
  2. For each race, identify the single best-scoring horse  (race winner candidate)
  3. Across all races, rank those race-bests by score — select TOP 5
  4. Mark exactly those 5 as show_in_ui=True; everything else is learning data
  5. Minimum confidence gate: a race-best must score >= 60 to be eligible as a UI pick
     (if a race has no horse above 60, we consider it too unpredictable and skip it)

This ensures:
  - Exactly 3 picks per day (or fewer if fewer than 3 races have enough confidence)
  - Each pick comes from a DIFFERENT race (no duplicates)
  - We always back the BEST horse in each race, not any horse above an arbitrary threshold
  - The self-learning system (daily_learning.py) continues to refine weights nightly
"""

import json
import os
import re
import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from comprehensive_pick_logic import analyze_horse_comprehensive, should_skip_race
from notify_picks import send_pick_notifications

# ── Form enricher (deep per-run history from Racing Post/Sporting Life) ──────
# Unlocks: exact_course_win (+20), exact_distance_win (+20), going_win_match
# (+16/32), close_2nd_last_time (+14), fresh_days_optimal (+10), OR trajectory
try:
    from form_enricher import enrich_runners as _form_enrich
    _FORM_ENRICHER_AVAILABLE = True
except ImportError:
    _FORM_ENRICHER_AVAILABLE = False
    def _form_enrich(races, **kw): return races

# ── OurHub Racing API enricher ──────────────────────────────────────────────
# Injects trainer/jockey win rates, confirmed going, and win probabilities
# into each runner dict so the scoring engine can use real stats instead of
# hardcoded tier lists for unknowns.
try:
    from ourhub_enricher import fetch_ourhub_data, enrich_races as _ourhub_enrich
    _OURHUB_AVAILABLE = True
except ImportError:
    _OURHUB_AVAILABLE = False

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

TARGET_PICKS   = 2      # 2026-06-16: data-driven reset. 75 settled picks show 66.7% WR only in
                        # non-handicap 2.0-3.5 odds band. 2 high-quality picks beats 5 speculative ones.
MIN_CONFIDENCE = 60     # Soft floor — race-type + odds window do the real filtering now.


def load_horse_history():
    """
    Query analysis_type-bet_date-index GSI for settled picks in the last 180 days.
    Returns dict: horse_name -> {wins: int, runs: int, win_rate: float}.
    Falls back to full scan if the GSI is unavailable (e.g. still backfilling).
    """
    from boto3.dynamodb.conditions import Key
    print("Loading horse history from DynamoDB (GSI, 180-day window)...")
    history = {}
    today  = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    cutoff = (datetime.now(timezone.utc) - timedelta(days=180)).strftime('%Y-%m-%d')
    try:
        kwargs = {
            'IndexName': 'analysis_type-bet_date-index',
            'KeyConditionExpression': (
                Key('analysis_type').eq('comprehensive_7factor') &
                Key('bet_date').between(cutoff, today)
            ),
            'FilterExpression': Attr('result_won').exists(),
        }
        while True:
            resp = table.query(**kwargs)
            for item in resp.get('Items', []):
                name = item.get('horse', item.get('horse_name', ''))
                if not name:
                    continue
                won = item.get('result_won') in (True, 'true', 'True', 1, '1')
                rec = history.setdefault(name, {'wins': 0, 'runs': 0})
                rec['runs'] += 1
                if won:
                    rec['wins'] += 1
            lk = resp.get('LastEvaluatedKey')
            if not lk:
                break
            kwargs['ExclusiveStartKey'] = lk
    except Exception as _gsi_err:
        print(f"  [WARN] GSI query failed ({_gsi_err}), falling back to full scan")
        history = {}
        scan_kwargs = {'FilterExpression': Attr('analysis_type').eq('comprehensive_7factor') & Attr('result_won').exists()}
        while True:
            resp = table.scan(**scan_kwargs)
            for item in resp.get('Items', []):
                name = item.get('horse', item.get('horse_name', ''))
                if not name:
                    continue
                won = item.get('result_won') in (True, 'true', 'True', 1, '1')
                rec = history.setdefault(name, {'wins': 0, 'runs': 0})
                rec['runs'] += 1
                if won:
                    rec['wins'] += 1
            lk = resp.get('LastEvaluatedKey')
            if not lk:
                break
            scan_kwargs['ExclusiveStartKey'] = lk
    for name, rec in history.items():
        rec['win_rate'] = rec['wins'] / rec['runs'] if rec['runs'] > 0 else 0.0
    print(f"  Horse history loaded: {len(history)} horses tracked in DB")
    return history


def load_races():
    """Load races from Betfair fetch (response_horses.json)."""
    try:
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
        return data.get('races', [])
    except FileNotFoundError:
        print("ERROR: Run 'python betfair_odds_fetcher.py' first")
        return []


def _merge_racing_api_races(betfair_races: list[dict], api_key: str) -> list[dict]:
    """
    Option 3: Supplement Betfair races with any UK/Irish races from Racing API
    that are not already in our Betfair pool (e.g. small meetings, AW cards not
    yet showing in Betfair, or races where Betfair fetch had a gap).

    Matching logic: normalise course name + HH:MM race time.  If a Racing API
    race matches an existing Betfair race we skip it (Betfair has live odds and
    takes priority).  Unmatched races are appended with source='racing_api' so
    form enrichment and scoring still run on them; they are excluded from the
    final UI picks if odds are 0 (no Betfair market confirmed yet).
    """
    try:
        from form_enricher import fetch_racing_api_race_list
    except ImportError:
        return betfair_races

    ra_races = fetch_racing_api_race_list(
        datetime.now(timezone.utc).strftime('%Y-%m-%d'), api_key
    )
    if not ra_races:
        return betfair_races

    def _race_key(course: str, race_time: str) -> str:
        course_slug = re.sub(r'[^a-z0-9]', '', (course or '').lower())
        # Normalise time to HH:MM
        t = re.search(r'(\d{2}):?(\d{2})', str(race_time or ''))
        time_str = f"{t.group(1)}:{t.group(2)}" if t else ''
        return f"{course_slug}_{time_str}"

    existing_keys = {_race_key(r.get('course', ''), r.get('race_time', ''))
                     for r in betfair_races}

    added = 0
    merged = list(betfair_races)
    for ra_race in ra_races:
        key = _race_key(ra_race.get('course', ''), ra_race.get('race_time', ''))
        if key not in existing_keys:
            merged.append(ra_race)
            existing_keys.add(key)
            added += 1

    if added:
        print(f"  [Option 3] Racing API added {added} races not in Betfair pool "
              f"(total: {len(merged)} races)")
    else:
        print(f"  [Option 3] Racing API race pool check: all {len(ra_races)} RA races "
              f"already covered by Betfair")
    return merged


def load_sl_declared_field_sizes():
    """
    Load the SL racecard to get the DECLARED runner count per race.
    Returns dict: (course_lower, time_hhmm) -> declared_count

    LESSON (2026-04-01): Kingcormac (Wincanton 15:20) was picked from a field
    where 1 runner was missing from Betfair — the winner never appeared in
    response_horses.json.  Betfair sometimes omits non-runner substitutes or
    late declarations.  We must cross-reference the SL racecard to know the
    true declared field size and block picks from incomplete fields.
    """
    import os
    result = {}
    try:
        cache_path = 'racecard_cache.json'
        if not os.path.exists(cache_path):
            return result
        with open(cache_path, 'r', encoding='utf-8') as f:
            rc = json.load(f)
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        racecard_today = rc.get(today_str, {})
        if not racecard_today:
            # Try yesterday (DST boundary) and nearest date
            for d in rc:
                if abs((datetime.fromisoformat(d) - datetime.now(timezone.utc).replace(tzinfo=None)).days) <= 1:
                    racecard_today = rc[d]
                    break
        for course, course_races in racecard_today.items():
            course_key = course.lower().strip()
            for race in course_races:
                time_str = race.get('time', '')  # UTC HH:MM from SL
                runners  = race.get('runners', [])
                if time_str and runners:
                    result[(course_key, time_str)] = len(runners)
        if result:
            print(f"  [S8] SL racecard loaded: {len(result)} races, declared field sizes known")
        else:
            print("  [S8] SL racecard not available — field completeness check skipped")
    except Exception as e:
        print(f"  [S8] racecard_cache.json unavailable: {e} — S8 gate skipped")
    return result


def tier_from_score(score):
    # UPDATED 2026-04-03: Raised thresholds. 85-89 is historically -21.8% ROI (losing band).
    # Only 90+ scores should be recommended picks. 90-94 = STRONG, 95+ = ELITE.
    if score >= 95: return "ELITE",   "ELITE (Top-tier confidence)", "green"
    if score >= 90: return "STRONG",  "STRONG (High confidence)",    "green"
    if score >= 80: return "GOOD",    "GOOD (Solid pick)",           "light-green"
    if score >= 65: return "FAIR",    "FAIR (Decent chance)",        "light-amber"
    if score >= 50: return "RISKY",   "RISKY (Lower confidence)",    "dark-amber"
    return              "POOR",   "POOR (Very unlikely)",        "red"


def _win_prob_pct(score: float) -> int:
    """Calibrated score-to-win-probability mapping.
    FIXED 2026-04-17: Must be monotonic (higher score = higher probability).
    Based on actuals: 100+ ≈ 30-35% wins, 90-99 ≈ 25%, 80-89 ≈ 20%.
    Capped at 38% — model cannot reliably claim >38% in any conditions."""
    if score >= 130: return 38
    if score >= 110: return 35
    if score >= 100: return 32
    if score >= 95:  return 28
    if score >= 90:  return 25
    if score >= 85:  return 22
    if score >= 80:  return 19
    if score >= 75:  return 16
    if score >= 70:  return 14
    return 12


def _expected_value(win_prob_pct: int, decimal_odds: float) -> float:
    """Expected Value (EV) per unit staked.
    EV = p × (d - 1) - (1 - p)  =  p × d - 1
    EV > 0  → positive value bet (mathematically sound to back)
    EV ≤ 0  → negative expected return (book has the edge)
    Source: value betting theory (Sharp Sports Betting / Efficiency of Racetrack Markets)
    """
    p = win_prob_pct / 100.0
    return round(p * decimal_odds - 1.0, 4)


def _kelly_fraction(win_prob_pct: int, decimal_odds: float, fraction: float = 0.5) -> float:
    """Half-Kelly optimal stake as a fraction of bankroll.
    f* = (b×p - q) / b  where b = decimal_odds - 1, q = 1 - p
    Returns 0.0 for negative EV bets (never bet negative Kelly).
    Capped at 0.12 (12% of bankroll max — prevents ruin risk).
    Half-Kelly (fraction=0.5) is standard professional practice:
      full Kelly maximises long-run growth but creates extreme variance.
    Source: Kelly (1956), widely adopted by professional gambling syndicates.
    """
    p = win_prob_pct / 100.0
    q = 1.0 - p
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    k = (b * p - q) / b
    if k <= 0:
        return 0.0
    return round(min(fraction * k, 0.12), 4)


def _classify_race_type(market_name: str) -> str:
    """Classify Betfair market_name into a standardised race type string."""
    mn = str(market_name or '').upper()
    if 'CHS' in mn or 'CHASE' in mn:
        if 'NOV' in mn:   return 'Novice Chase'
        if 'HCAP' in mn:  return 'Handicap Chase'
        return 'Chase'
    if 'HRD' in mn or 'HURDLE' in mn:
        if 'NOV' in mn:   return 'Novice Hurdle'
        if 'JUV' in mn:   return 'Juvenile Hurdle'
        if 'HCAP' in mn or mn.endswith(' H'):  return 'Handicap Hurdle'
        return 'Hurdle'
    if 'NHF' in mn or 'BUMPER' in mn:  return 'NH Flat/Bumper'
    if 'MDN' in mn or 'MAIDEN' in mn:  return 'Maiden'
    if 'HCAP' in mn:                   return 'Flat Handicap'
    if 'GRP' in mn or 'GROUP' in mn:   return 'Group Race'
    if 'LIST' in mn or 'LISTED' in mn: return 'Listed Race'
    if 'STKS' in mn or 'STAKES' in mn: return 'Conditions Stakes'
    if 'CLMR' in mn or 'CLAIM' in mn:  return 'Claimer'
    if 'SELL' in mn:                   return 'Seller'
    return 'Flat'


def analyze_and_save_all(force_reanalyse: bool = False):
    """
    Two-pass algorithm:
      Pass 1 — Score every horse, collect per-race bests.
      Select top-5 cross-race bests.
      Pass 2 — Save everything with correct show_in_ui flag.
    force_reanalyse: bypass the 12:00 UTC pick lock (use when scoring logic has changed).
    """
    races = load_races()
    if not races:
        print("No races found — run betfair_odds_fetcher.py first")
        return

    # ── Option 3: Expand race pool with Racing API races not in Betfair ──────
    _racing_api_key_early = os.environ.get('RACING_API_KEY', '')
    if _racing_api_key_early:
        races = _merge_racing_api_races(races, _racing_api_key_early)

    # Load SL declared field sizes for S8 completeness gate
    sl_declared = load_sl_declared_field_sizes()

    # ── STAGE 0: Load learning insights + structured signals ─────────────────
    # sf_learning writes insights AND structured odds_roi / best_courses to
    # DynamoDB nightly. We consume both here: text insights for logging, structured
    # signals from the nightly learning cycle (used for logging).
    import json as _json
    _learning_odds_roi    = {}   # cat -> {roi, win_rate, n}  e.g. 'favorite': {roi:-19.6, n:18}
    _learning_best_courses = []  # venue names with ≥40% WR and ≥5 bets
    try:
        _insights_resp = table.get_item(Key={'bet_date': 'LEARNING_INSIGHTS', 'bet_id': 'latest'})
        _learning_item = _insights_resp.get('Item', {})
        if _learning_item:
            _updated       = _learning_item.get('updated_at', 'unknown')
            _raw_insights  = _learning_item.get('insights', '[]')
            _insights_list = _json.loads(_raw_insights) if isinstance(_raw_insights, str) else _raw_insights
            _raw_odds_roi  = _learning_item.get('odds_roi', '{}')
            _learning_odds_roi = _json.loads(_raw_odds_roi) if isinstance(_raw_odds_roi, str) else (_raw_odds_roi or {})
            _raw_courses   = _learning_item.get('best_courses', '[]')
            _learning_best_courses = _json.loads(_raw_courses) if isinstance(_raw_courses, str) else (_raw_courses or [])

            print(f"\n[STAGE 0] Learning insights (updated {_updated}):")
            if _insights_list:
                for _ins in _insights_list[:10]:
                    print(f"  ▶ {_ins}")
            else:
                print("  (no actionable text insights yet)")
            if _learning_odds_roi:
                for _cat, _d in _learning_odds_roi.items():
                    print(f"  📊 {_cat}: ROI {_d.get('roi',0):+.1f}%  WR {_d.get('win_rate',0):.0f}%  n={_d.get('n',0)}")
            if _learning_best_courses:
                print(f"  🏟  Best courses: {', '.join(_learning_best_courses)}")
        else:
            print("\n[STAGE 0] No learning insights found — learning cycle may not have run yet")
    except Exception as _li_e:
        print(f"\n[STAGE 0] Could not load learning insights (non-fatal): {_li_e}")

    # ── STAGE 1: Deep form enrichment ────────────────────────────────────────
    # Fetches last-6-race run history from Racing Post / Sporting Life for every
    # runner and injects it as 'form_runs'. The scoring engine reads this to fire
    # exact_course_win (+20), exact_distance_win (+20), going_win_match (+32),
    # close_2nd_last_time (+14), fresh_days_optimal (+10), or_trajectory (+10).
    # Without this step all deep_form signals score 0 for every horse.
    _form_total_horses = sum(len(r.get('runners', [])) for r in races)
    _form_enriched_count = 0
    _final_form_pct = 0  # set after enrichment passes; stored on every saved pick
    # Minimum form coverage before selections are locked in.
    # If the first pass is below this threshold the enricher retries once with a
    # fresh cache — this catches transient SL scraping failures at pipeline start.
    _FORM_COVERAGE_GATE = 25   # percent of field that must have SL form data

    if _FORM_ENRICHER_AVAILABLE:
        _racing_api_key = os.environ.get('RACING_API_KEY', '')
        _source_label = "SL + Racing API" if _racing_api_key else "SL only (set RACING_API_KEY for full coverage)"
        print(f"\n[STAGE 1/5] Deep form enrichment (parallel fan-out) — {_form_total_horses} horses | {_source_label}")

        races = _form_enrich(races, verbose=True, racing_api_key=_racing_api_key)
        _form_enriched_count = sum(
            1 for race in races for runner in race.get('runners', [])
            if runner.get('form_runs')
        )
        _form_pct_pass1 = round(100 * _form_enriched_count / _form_total_horses) if _form_total_horses else 0
        print(f"  Pass 1 total: {_form_enriched_count}/{_form_total_horses} horses enriched ({_form_pct_pass1}%)")

        _final_form_pct = _form_pct_pass1
        if _form_pct_pass1 < _FORM_COVERAGE_GATE:
            print(f"  ⚠ Coverage {_form_pct_pass1}% below {_FORM_COVERAGE_GATE}% gate — retrying (pass 2)…")
            import form_enricher as _fe_mod
            _fe_mod._today_form.clear()
            _fe_mod._today_tf_stars.clear()
            races = _form_enrich(races, verbose=False, racing_api_key=_racing_api_key)
            _form_enriched_count = sum(
                1 for race in races for runner in race.get('runners', [])
                if runner.get('form_runs')
            )
            _form_pct_pass2 = round(100 * _form_enriched_count / _form_total_horses) if _form_total_horses else 0
            _final_form_pct = _form_pct_pass2
            print(f"  Pass 2 total: {_form_enriched_count}/{_form_total_horses} horses enriched ({_form_pct_pass2}%)")
            if _form_pct_pass2 < _FORM_COVERAGE_GATE:
                _cov_msg = (f"COVERAGE STILL LOW ({_form_pct_pass2}%) after 2 passes — "
                            f"picks today are built on sparse form data.\n"
                            f"Total horses: {_form_total_horses} | Enriched: {_form_enriched_count}\n"
                            f"{'Racing API may be rate-limited.' if _racing_api_key else 'RACING_API_KEY not set.'}")
                print(f"  ⚠ {_cov_msg}")
                try:
                    import boto3 as _boto3
                    _ses = _boto3.client('ses', region_name='eu-west-1')
                    _ses.send_email(
                        Source='charles.mccarthy@gmail.com',
                        Destination={'ToAddresses': ['charles.mccarthy@gmail.com']},
                        Message={
                            'Subject': {'Data': f'⚠ BetBudAI: Low form coverage ({_form_pct_pass2}%) — picks at risk'},
                            'Body': {'Text': {'Data': _cov_msg}},
                        }
                    )
                    print("  [ALERT] Low-coverage email sent via SES")
                except Exception as _ses_e:
                    print(f"  [ALERT] SES send failed (non-fatal): {_ses_e}")
            else:
                print(f"  ✓ Coverage gate passed after retry ({_form_pct_pass2}%)")
        else:
            print(f"  ✓ Coverage gate passed ({_form_pct_pass1}%)")
    else:
        print("[STAGE 1/5] Form enrichment unavailable — deep form signals will score 0")

    # ── STAGE 1b: OurHub Racing API enrichment ───────────────────────────────
    # Fetches confirmed going, trainer/jockey win rates, and win probabilities.
    # Only 3 API calls per day (well within 80/day free tier).
    if _OURHUB_AVAILABLE:
        _oh_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        print(f"\n[STAGE 1b] OurHub API enrichment for {_oh_date}...")
        try:
            _oh_data = fetch_ourhub_data(_oh_date)
            races = _ourhub_enrich(races, _oh_data)
        except Exception as e:
            print(f"  [OurHub] Enrichment failed (non-fatal): {e}")
    else:
        print("\n[STAGE 1b] OurHub enrichment unavailable — using defaults")

    print("\n" + "=" * 100)
    print("DAILY 3-PICK SELECTION ENGINE")
    print("=" * 100)
    print(f"  Races    : {len(races)}")
    print(f"  Strategy : Best horse per race -> top {TARGET_PICKS} cross-race bests (min score {MIN_CONFIDENCE})")
    print("=" * 100 + "\n")

    today        = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    avg_winner_odds = 3.80  # RECALIBRATED 2026-04-17: shifted from 4.65 to centre of best-performing 2-5 range

    # ── CHECK EXISTING UI PICKS (intraday accumulation guard) ─────────────────
    # Each refresh only fetches FUTURE races, so previous picks are never overwritten.
    # Without this guard, new picks are added per 2-hour refresh → too many picks/day.
    MAX_DAILY_UI_PICKS = 2  # data-driven reset: 2 high-quality picks beats 5 speculative
    from boto3.dynamodb.conditions import Key as _Key
    _existing_resp = table.query(KeyConditionExpression=_Key('bet_date').eq(today))
    _existing_items = _existing_resp.get('Items', [])
    while _existing_resp.get('LastEvaluatedKey'):
        _existing_resp = table.query(
            KeyConditionExpression=_Key('bet_date').eq(today),
            ExclusiveStartKey=_existing_resp['LastEvaluatedKey'])
        _existing_items.extend(_existing_resp.get('Items', []))
    _existing_ui = [i for i in _existing_items if i.get('show_in_ui') is True]
    _existing_ui_count = len(_existing_ui)
    now_utc = datetime.now(timezone.utc)
    cutoff  = now_utc + timedelta(minutes=15)

    # PICK LOCK: once the daily target is filled (2 picks), freeze for the rest of the day.
    # Also lock if it's past 12:00 UTC and any picks exist (belt-and-braces for partial days).
    # force_reanalyse bypasses both locks (used when scoring logic has changed mid-day).
    _target_filled = _existing_ui_count >= MAX_DAILY_UI_PICKS
    _time_lock     = now_utc.hour >= 12 and _existing_ui_count >= 1
    if (_target_filled or _time_lock) and not force_reanalyse:
        reason = "target filled" if _target_filled else "12:00 UTC time lock"
        print(f"  PICKS LOCKED ({reason}) at {now_utc.strftime('%H:%M')} UTC — "
              f"{_existing_ui_count}/{MAX_DAILY_UI_PICKS} picks set; skipping selection pass.")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'picks_locked': True,
                'picks_count': _existing_ui_count,
                'date': today,
                'message': f'Picks locked ({reason}). {_existing_ui_count} picks stand for today.'
            })
        }

    # Count UI picks whose races are PAST or within the 15-min cutoff as "locked".
    # These races won't appear in this analysis run, so their show_in_ui=True
    # records persist untouched.  Only races AFTER the cutoff are truly
    # re-analysable: this run's selection engine will overwrite them (promote or
    # demote) so they don't consume a permanent slot.
    _locked_ui = []
    for _eui in _existing_ui:
        _ert = _eui.get('race_time', '')
        try:
            _ert_dt = datetime.fromisoformat(_ert.replace('Z', '+00:00'))
            if _ert_dt.astimezone(timezone.utc) <= cutoff:
                _locked_ui.append(_eui)
        except Exception:
            _locked_ui.append(_eui)  # treat unparseable as past
    _locked_count = len(_locked_ui)
    _locked_ui_ids = {i['bet_id'] for i in _locked_ui}

    # Build set of race identifiers from the CURRENT scrape so we only re-analyse
    # picks whose race is actually in this scrape.  Picks from races not in the
    # current scrape (e.g. different venue set, afternoon-only vs morning) are
    # treated as locked — preserving them from accidental demotion/deletion.
    # FIX 2026-04-18: Without this, a manual refresh that scrapes a different set of
    # races than the morning run will demote/delete morning picks whose races aren't
    # in the new scrape, even though those races are still in the future.
    _current_scrape_races = set()
    for _race in races:
        _cs_course = (_race.get('course') or _race.get('venue') or '').lower().strip()
        _cs_time = (_race.get('start_time') or '')[:16]  # '2026-04-18T13:20' precision
        if _cs_course and _cs_time:
            _current_scrape_races.add((_cs_course, _cs_time))

    # Only track genuinely ranked picks (rank 1-5) as candidates for drop detection,
    # AND only if their race appears in the current scrape's race list.
    # Without the rank filter, every show_in_ui=True item (including previous drops)
    # counts, causing exponential inflation across refreshes.
    # Without the scrape-race filter, picks from a different scrape run get demoted
    # simply because their race isn't in this run's data.
    _reanalysable_ui_ids = set()
    _preserved_ui_ids = set()  # picks kept because their race isn't in this scrape
    for _eui in _existing_ui:
        if _eui['bet_id'] in _locked_ui_ids:
            continue
        if int(_eui.get('pick_rank', 0)) <= 0:
            continue
        # Check if this pick's race is in the current scrape
        _eui_course = (_eui.get('course') or _eui.get('venue') or '').lower().strip()
        _eui_time = str(_eui.get('race_time', ''))[:16]
        _race_in_scrape = (_eui_course, _eui_time) in _current_scrape_races
        if not _race_in_scrape:
            # Also try fuzzy match: course substring match at same time
            _race_in_scrape = any(
                _st == _eui_time and (_sc in _eui_course or _eui_course in _sc)
                for _sc, _st in _current_scrape_races
            )
        if _race_in_scrape:
            _reanalysable_ui_ids.add(_eui['bet_id'])
        else:
            _preserved_ui_ids.add(_eui['bet_id'])
            _locked_ui_ids.add(_eui['bet_id'])  # treat as locked for slot counting
            _locked_count += 1

    if _preserved_ui_ids:
        print(f"  Preserved {len(_preserved_ui_ids)} picks (race not in current scrape):")
        for _pid in _preserved_ui_ids:
            _pmatch = next((i for i in _existing_ui if i['bet_id'] == _pid), {})
            print(f"    - {_pmatch.get('horse', _pid)} ({_pmatch.get('course', '?')} "
                  f"{str(_pmatch.get('race_time', ''))[:16]})")

    _slots_remaining = max(0, MAX_DAILY_UI_PICKS - _locked_count)
    print(f"  Existing UI picks today: {_existing_ui_count} ({_locked_count} locked/past/preserved, "
          f"{len(_reanalysable_ui_ids)} re-analysable) / {MAX_DAILY_UI_PICKS} "
          f"({_slots_remaining} slots remaining)")
    if _slots_remaining == 0:
        print(f"  Daily pick cap reached — new horses will be saved as learning data only")
    # Use remaining slots instead of TARGET_PICKS for this run
    _effective_target = min(TARGET_PICKS, _slots_remaining)

    # ── STAGE 2: Horse history from DynamoDB ─────────────────────────────────
    print("[STAGE 2/5] Loading horse history from DynamoDB...")
    horse_history = load_horse_history()

    # ── PASS 1 ───────────────────────────────────────────────────────────────
    # Build a list of races, each containing scored runner items.
    # Also track the best-scoring horse in each race.
    all_races_data = []  # [{venue, race_time, market_id, runners:[{item, score}], best_idx}]

    for race in races:
        # FIX 2026-04-04: betfair_odds_fetcher writes 'course' (not 'venue'). Read 'course' first,
        # fall back to 'venue' for backward compat. Without this every pick gets course=Unknown
        # which both excludes it from cumulative-ROI and breaks the results matcher.
        venue      = race.get('course') or race.get('venue') or 'Unknown'
        race_time  = race.get('start_time', '')
        market_id  = race.get('market_id', race.get('marketId', ''))
        market_name = race.get('market_name', '')
        runners    = race.get('runners', [])

        # Skip Class 3-6 handicap races — handicappers design these to be unpredictable.
        # 2026-04-07: should_skip_race existed in comprehensive_pick_logic but was never
        # called here. Hooking it up now: Class 3-6 hcaps are structurally un-edgeable.
        _skip, _skip_reason = should_skip_race(race)
        if _skip:
            print(f"[SKIP — {_skip_reason}]  [{venue}  {race_time[:16]}]")
            continue

        # Skip races that have already started or are within 15 minutes
        try:
            race_dt = datetime.fromisoformat(race_time)
            # Make aware if naive (treat as UTC)
            if race_dt.tzinfo is None:
                race_dt = race_dt.replace(tzinfo=timezone.utc)
            if race_dt <= cutoff:
                print(f"[SKIP — already started/imminent]  [{venue}  {race_time[:16]}]")
                continue
        except (ValueError, TypeError):
            pass  # unparseable time — process anyway

        print(f"[{venue}  {race_time[:16]}]  {len(runners)} runners")

        # Find the race favourite (lowest decimal odds) — used as market signal
        valid_runners = [r for r in runners if float(r.get('odds', 0)) > 1.0]
        favourite_odds = min((float(r.get('odds', 99)) for r in valid_runners), default=99)

        # Collect weight_lbs for every runner in this race so scoring can do relative comparison
        field_weights = [int(r.get('weight_lbs', 0) or 0) for r in runners if int(r.get('weight_lbs', 0) or 0) > 0]

        # Parse distance in furlongs from market_name for debutant scorer
        # e.g. "5f Maiden", "1m2f Handicap", "7f Conditions Stakes"
        _dist_f = 0.0
        _dm = re.search(r'(\d+)m(\d+)f|(\d+)m|(\d+)f', str(market_name), re.IGNORECASE)
        if _dm:
            if _dm.group(1) and _dm.group(2):
                _dist_f = int(_dm.group(1)) * 8 + int(_dm.group(2))
            elif _dm.group(3):
                _dist_f = int(_dm.group(3)) * 8
            elif _dm.group(4):
                _dist_f = int(_dm.group(4))

        race_runners = []
        _race_fav_score = 0   # favourite's score after all bonuses (set in runner loop)
        _race_fav_horse = ''
        for runner in runners:
            horse_name = runner.get('name', 'Unknown')
            odds       = float(runner.get('odds', 0))

            # Inject race-level context into runner for sub-scorers
            if race.get('ourhub_going'):
                runner['_race_ourhub_going'] = race['ourhub_going']
            runner['distance_f'] = _dist_f
            runner['_race_type']  = _classify_race_type(market_name)

            score, breakdown, reasons = analyze_horse_comprehensive(
                runner,
                venue,
                avg_winner_odds=avg_winner_odds,
                course_winners_today=0,
                field_weights=field_weights,
                n_runners=len(runners),
            )

            # ── Database history bonus ───────────────────────────────────────
            # If we've seen this horse before and it has a meaningful win rate,
            # reward it.  A >40% DB win rate is genuinely exceptional.
            db_stats = horse_history.get(horse_name, {})
            if db_stats.get('runs', 0) >= 2:
                win_rate = db_stats.get('win_rate', 0.0)
                if win_rate >= 0.40:
                    db_bonus = 15
                elif win_rate >= 0.25:
                    db_bonus = 8
                elif win_rate >= 0.10:
                    db_bonus = 4
                else:
                    db_bonus = 0
                if db_bonus:
                    score += db_bonus
                    reasons.append(f"DB history: {int(win_rate*100)}% win rate ({db_stats['wins']}/{db_stats['runs']} runs): +{db_bonus}pts")
                    breakdown['db_history'] = db_bonus

            # ── Market-leader bonus ──────────────────────────────────────────
            # The race favourite aggregates all public information.
            # When our model agrees with the market (our top scorer is also the
            # market favourite), confidence increases significantly.
            # LESSON 2026-04-04: Comic Hero (odds=3, 3-5 losing band) scored 126 over
            # Strength of Spirit (odds=5) which WON at 4/1. The +16 market leader bonus
            # was stacking on top of a horse ALREADY in the historically losing 2/1-4/1
            # range. A favourite at 3 decimal gives no VALUE edge — the market is simply
            # over-using an odds-on short priced horse. Cap to +4 in losing band.
            _in_losing_band = 3.0 <= odds < 5.0
            market_leader_bonus = 0
            if odds > 1.0 and odds == favourite_odds:
                if _in_losing_band:
                    market_leader_bonus = 4   # REDUCED: fav in losing 3-5 range — market confidence here is unreliable
                    score += market_leader_bonus
                    reasons.append(f"Race favourite (3-5 losing band, reduced): +{market_leader_bonus}pts")
                else:
                    market_leader_bonus = 16   # Race favourite at value odds — market agrees, confidence signal valid
                    score += market_leader_bonus
                    reasons.append(f"Race market leader (lowest odds): +{market_leader_bonus}pts")
                breakdown['market_leader'] = market_leader_bonus
            elif odds > 1.0 and odds <= favourite_odds * 1.20:
                market_leader_bonus = 10   # Joint/co-favourite — INCREASED 4→10 (2026-03-30)
                score += market_leader_bonus
                reasons.append(f"Market co-favourite: +{market_leader_bonus}pts")
                breakdown['market_leader'] = market_leader_bonus
            elif odds > 1.0 and odds <= favourite_odds * 1.40:
                market_leader_bonus = 5    # Second choice within 40% of favourite — NEW tier (2026-03-30)
                score += market_leader_bonus
                reasons.append(f"Market second choice: +{market_leader_bonus}pts")
                breakdown['market_leader'] = market_leader_bonus

            # Market-leader floor: a short-priced favourite (≤1.80) that scores
            # below 50 has NO form data in our model but the market still backs it.
            # Floor to 50 so it surfaces in competitor analysis rather than being
            # buried at the noise floor. Lesson 2026-05-31: Stellarmasterpiece 6/4,
            # model score=30, won vs our 118-point pick Little Lady Lucy.
            if odds > 1.0 and odds == favourite_odds and odds <= 1.80 and score < 50:
                _floor_bump = 50 - score
                score += _floor_bump
                breakdown['market_leader_no_form'] = _floor_bump
                reasons.append(
                    f"Short-priced favourite ({odds:.2f}) — no model data, "
                    f"score floored to 50: +{_floor_bump}pts"
                )
            else:
                breakdown.setdefault('market_leader_no_form', 0)

            # ── Price steam / drift bonus (2026-03-30) ───────────────────────
            # Detected by betfair_odds_fetcher.py price_history comparison.
            # 'steaming' = price dropped ≥20% since last fetch (smart money in).
            # 'drifting'  = price rose ≥25% since last fetch (money going out).
            _pm = runner.get('price_movement', 'stable')
            _pm_pct = float(runner.get('price_move_pct', 0) or 0)
            if _pm == 'steaming' and _pm_pct >= 20:
                _steam_pts = min(15, int(_pm_pct * 0.5))   # e.g. 25% drop → +12 pts
                score += _steam_pts
                breakdown['price_steam'] = _steam_pts
                reasons.append(f"Market steaming: backed {_pm_pct:.0f}% shorter: +{_steam_pts}pts")
            elif _pm == 'drifting' and _pm_pct <= -25:
                _drift_pts = min(8, int(abs(_pm_pct) * 0.3))  # e.g. 30% rise → -9 → cap -8
                # PROFESSIONAL WORKFLOW LESSON (2026-04-07): Pro re-checks fundamentals when
                # Leopardstown drifts 5.0→5.5 and decides to KEEP the pick. Drift is a warning,
                # not a veto, when the underlying form case is sound.
                # If horse has strong form signals (deep_form >=16, trainer tier, going win),
                # cap drift penalty at half — don't let minor market noise override solid form.
                _strong_form = (
                    float(breakdown.get('deep_form', 0)) >= 16
                    or float(breakdown.get('trainer_reputation', 0)) >= 10
                    or float(breakdown.get('going_win_match', 0)) >= 10
                )
                if _strong_form and _drift_pts > 3:
                    _drift_pts = 3   # cap at -3 when fundamentals are sound
                    reasons.append(f"Market drifting {abs(_pm_pct):.0f}% — capped at -3pts (strong form fundamentals override drift signal)")
                else:
                    reasons.append(f"Market drifting: {abs(_pm_pct):.0f}% longer than last fetch: -{_drift_pts}pts")
                score -= _drift_pts
                breakdown['price_steam'] = -_drift_pts
            else:
                breakdown['price_steam'] = 0

            # ── FINAL SCORE CAP ──────────────────────────────────────────────────
            # comprehensive_pick_logic.py caps the function score at 108, but market_leader
            # (+16), db_history (+15), and price_steam (+15) are added here afterwards.
            # Without this cap, final scores reach 131-136 where ALL picks cluster at the
            # ceiling and the model can no longer differentiate between them.
            # Winner profile avg is 93pts — final cap of 120 keeps scores spread in the
            # realistic winner range (85-115) where the model has actual predictive power.
            _FINAL_SCORE_CAP = 120
            if score > _FINAL_SCORE_CAP:
                _fsc_reduction = score - _FINAL_SCORE_CAP
                score = _FINAL_SCORE_CAP
                breakdown['final_score_cap'] = -_fsc_reduction
                reasons.append(f"Final cap {_FINAL_SCORE_CAP}pts (post-enrichment was {score + _fsc_reduction:.0f}): -{_fsc_reduction:.0f}pts")

            # Track this race's market favourite so divergence check can run after selection
            if odds > 1.0 and odds == favourite_odds:
                _race_fav_score = score
                _race_fav_horse = horse_name

            confidence_level, confidence_grade, confidence_color = tier_from_score(score)

            bet_id = (f"{race_time}_{venue}_{horse_name}"
                      .replace(' ', '_').replace(':', '').replace('.', ''))

            item = {
                'bet_id':              bet_id,
                'bet_date':            today,
                'course':              venue,
                'race_course':         venue,
                'race_time':           race_time,
                'horse':               horse_name,
                'jockey':              runner.get('jockey', ''),
                'trainer':             runner.get('trainer', ''),
                'form':                runner.get('form', ''),
                'weight_lbs':          runner.get('weight_lbs', 0),
                'age':                 runner.get('age', ''),
                'official_rating':     runner.get('official_rating', ''),
                'draw':                runner.get('draw', ''),
                'odds':                Decimal(str(odds)) if odds else Decimal('0'),
                'decimal_odds':        Decimal(str(odds)) if odds else Decimal('0'),
                'combined_confidence': Decimal(str(score)),
                'comprehensive_score': Decimal(str(score)),
                'win_probability':      _win_prob_pct(score),
                'expected_value':       Decimal(str(_expected_value(_win_prob_pct(score), odds or 0))),
                'kelly_fraction':       Decimal(str(_kelly_fraction(_win_prob_pct(score), odds or 0))),
                'opening_price':        Decimal(str(odds)) if odds else Decimal('0'),
                'confidence_level':    confidence_level,
                'confidence_grade':    confidence_grade,
                'confidence_color':    confidence_color,
                'show_in_ui':          False,   # will be set in pass 2
                'recommended_bet':     False,   # will be set in pass 2
                'is_learning_pick':    True,    # will be set in pass 2
                'pick_rank':           0,       # 1-5 for top picks; 0 = learning
                'analysis_type':       'comprehensive_7factor',
                'score_breakdown':     breakdown,
                'selection_reasons':   reasons,
                'sport':               'horses',
                'race_type':           _classify_race_type(market_name),
                'outcome':             'pending',
                'market_id':           market_id,
                'market_name':         market_name,
                'selection_id':        runner.get('selectionId', 0),
                'race_coverage_pct':   Decimal(str(_final_form_pct)),
                'race_total_count':    len(runners),
                'form_enriched':       bool(runner.get('form_runs')),
                'created_at':          datetime.now(timezone.utc).isoformat(),
                'updated_at':          datetime.now(timezone.utc).isoformat(),
                # Horse history from DB
                'history_wins':        db_stats.get('wins', 0),
                'history_runs':        db_stats.get('runs', 0),
                'history_win_rate':    Decimal(str(round(db_stats.get('win_rate', 0.0), 4))),
            }

            race_runners.append({'item': item, 'score': score, 'horse': horse_name, 'odds': odds, 'history': db_stats})

        if not race_runners:
            continue

        # ── SAME-TRAINER DUAL ENTRY PENALTY ─────────────────────────────────
        # LESSON (2026-04-01): I'm Spartacus vs Clonmacash — same trainer (A McGuinness).
        # When a trainer runs 2+ horses in the same race, attention is split and the trainer
        # may favour one runner over another.  Penalise ALL horses from that trainer.
        _trainer_runs = {}  # trainer_lower -> [index]
        for _idx, _rr in enumerate(race_runners):
            _t = _rr['item'].get('trainer', '').strip().lower()
            if _t:
                _trainer_runs.setdefault(_t, []).append(_idx)
        for _t, _idxs in _trainer_runs.items():
            if len(_idxs) >= 2:
                _str_penalty = 10  # same_trainer_rival_penalty (matches DEFAULT_WEIGHTS)
                _trainer_display = race_runners[_idxs[0]]['item'].get('trainer', _t)
                for _idx in _idxs:
                    race_runners[_idx]['score'] -= _str_penalty
                    race_runners[_idx]['item']['comprehensive_score'] = Decimal(str(race_runners[_idx]['score']))
                    race_runners[_idx]['item']['score_breakdown']['same_trainer_rival'] = -_str_penalty
                    race_runners[_idx]['item']['selection_reasons'].append(
                        f"{_trainer_display} runs {len(_idxs)} horses in this race (split focus): -{_str_penalty}pts"
                    )
                print(f"  [SAME-TRAINER] {_trainer_display}: {len(_idxs)} runners "
                      f"— each penalised -{_str_penalty}pts")


        best = max(race_runners, key=lambda x: x['score'])
        sorted_by_score = sorted(race_runners, key=lambda x: x['score'], reverse=True)
        second_score = sorted_by_score[1]['score'] if len(sorted_by_score) > 1 else best['score']
        score_gap = max(0, best['score'] - second_score)
        best['item']['score_gap'] = Decimal(str(round(score_gap, 1)))

        # ── FIELD COMPLETENESS CHECK (Gate S8 prep) ────────────────────────
        # Cross-reference the SL racecard to get the true declared field size.
        # Betfair sometimes omits late declarations or non-runner substitutes.
        # Normalise the course name and match by time (UTC HH:MM from race_time).
        course_key = venue.lower().strip()
        time_key   = race_time[11:16] if len(race_time) >= 16 else ''
        sl_count   = sl_declared.get((course_key, time_key), 0)
        # Also try any SL key whose course contains or roughly matches our venue
        if not sl_count and time_key:
            for (ck, tk), cnt in sl_declared.items():
                if tk == time_key and (ck in course_key or course_key in ck):
                    sl_count = cnt
                    break
        analysed_count = len(race_runners)
        missing_runners = max(0, sl_count - analysed_count) if sl_count else 0

        _mkt_name = race.get('market_name', '')
        all_races_data.append({
            'venue':             venue,
            'race_time':         race_time,
            'market_name':       _mkt_name,
            'race_type':         _classify_race_type(_mkt_name),
            'runners':           race_runners,
            'raw_runners':       runners,
            'best':              best,
            'n_runners':         len(runners),
            'sl_declared_count': sl_count,
            'missing_runners':   missing_runners,
            'fav_horse':         _race_fav_horse,
            'fav_score':         _race_fav_score,
            'fav_odds':          favourite_odds,
        })

    # ── SELECT TOP 2 CROSS-RACE BESTS ────────────────────────────────────────
    # DATA-DRIVEN RESET 2026-06-16: 75 settled picks analysed.
    # Non-handicap + 2.0-3.5 odds = 66.7% WR / +96.5% ROI (12 picks).
    # Everything else: handicaps -59% ROI, 3.5-5.0 -26.9%, 8+ just 5.9% WR.
    # 3 rules replace 15 gates. Score ranks within the qualifying pool.

    # Rule 1 — race type. Handicaps and bumpers are structurally unedgeable.
    _NON_HCAP_TYPES = {
        'Maiden', 'Conditions Stakes', 'Listed Race', 'Group Race',
        'Novice Hurdle', 'Novice Chase', 'Hurdle', 'Chase', 'Flat',
    }
    # Rule 2 — odds window where we actually win (data: 66.7% WR in 2.0-3.5 band)
    _ODDS_MIN = 2.0
    _ODDS_MAX = 3.5
    # Rule 3 — signal count: at least 2 meaningful signals must fire
    _KEY_SIGNALS = ('market_leader', 'deep_form', 'going_suitability',
                    'price_steam', 'trainer_reputation', 'cd_bonus', 'jockey_quality')
    _MIN_SIGNALS = 2

    def _passes_quality_gates(r):
        """3-rule filter replacing 15 accumulated gates.
        Rule 1: Non-handicap race type only.
        Rule 2: Best horse odds 2.0–3.5 (data: 66.7% WR, +96.5% ROI in this band).
        Rule 3: At least 2 meaningful signals firing.
        Score >= 60 soft floor to exclude noise.
        """
        horse = r['best']['horse']
        score = r['best']['score']
        bd    = r['best']['item'].get('score_breakdown', {})

        # Rule 1 — race type must be non-handicap, non-bumper
        rt = r.get('race_type', _classify_race_type(r.get('market_name', '')))
        if rt not in _NON_HCAP_TYPES:
            print(f"  [SKIP] {horse}: {rt} (not in qualifying race types)")
            return False

        # Rule 2 — odds window 2.0–3.5 (data: 66.7% WR, +96.5% ROI)
        odds = float(r['best'].get('odds', 0) or 0)
        if odds < _ODDS_MIN:
            print(f"  [SKIP] {horse}: odds {odds:.2f} below {_ODDS_MIN} floor")
            return False
        if odds > _ODDS_MAX:
            print(f"  [SKIP] {horse}: odds {odds:.2f} above {_ODDS_MAX} ceiling")
            return False

        # Rule 3 — at least 2 meaningful signals firing
        n_signals = sum(1 for s in _KEY_SIGNALS if float(bd.get(s, 0) or 0) > 0)
        if n_signals < _MIN_SIGNALS:
            print(f"  [SKIP] {horse}: only {n_signals} signals (need {_MIN_SIGNALS})")
            return False

        # Soft score floor — catches complete scoring failures
        if score < MIN_CONFIDENCE:
            print(f"  [SKIP] {horse}: score {score:.0f} below floor {MIN_CONFIDENCE}")
            return False

        print(f"  [QUALIFY] {horse} @{odds:.2f} score={score:.0f} signals={n_signals} rt={rt}")
        return True

    # Build eligible list: races passing 3-rule filter, today only, with live odds
    eligible = [r for r in all_races_data
                if _passes_quality_gates(r)
                and r.get('race_time', '')[:10] == today
                and float(r['best'].get('odds', 0) or 0) > 0]
    # Rank by score; prefer shorter odds within the 2.0-3.5 window on ties
    eligible.sort(key=lambda r: (r['best']['score'],
                                  1 if float(r['best'].get('odds', 99)) < 2.5 else 0),
                  reverse=True)

    top_picks = eligible[:_effective_target]

    # ── FAVOURITE MISMATCH CHECK ──────────────────────────────────────────────
    # ── FAVOURITE MISMATCH + MARKET DISAGREEMENT CHECKS ─────────────────────
    # Two distinct cases:
    #   Case 1 (blind-spot): we're picking against an odds-on fav our model
    #     couldn't score — no form data at all.
    #   Case 2 (market disagreement): our pick is NOT the market favourite but
    #     the market favourite scored well (≥70) and is at shorter odds. The
    #     market knows something our model may not — remove pick from pool.
    #   Lesson 2026-06-05: Legacy Link 4.40 vs Amelia Earhart 3.85 (score 102).
    #     Old guard never fired (fav_score ≥ 50, fav_odds > 1.80). Need broader gate.
    _market_disagree_picks = []
    for _tp in top_picks:
        _fav_horse = _tp.get('fav_horse', '')
        _fav_score = float(_tp.get('fav_score', 0) or 0)
        _fav_odds  = float(_tp.get('fav_odds', 99) or 99)
        _our_odds  = float(_tp['best'].get('odds', 99) or 99)
        _our_horse = _tp['best']['horse']
        _our_score = float(_tp['best'].get('score', 0) or 0)

        # Case 1: blind-spot (original guard)
        if _our_horse != _fav_horse and _fav_score < 50 and _fav_odds <= 1.80:
            _mismatch_warn = (
                f"FAVOURITE_MISMATCH: {_fav_horse} is the {_fav_odds:.2f} market leader "
                f"but scored only {_fav_score:.0f} — our model has no form data on it. "
                f"Pick ({_our_horse}) beats an unscorable favourite: confidence reduced."
            )
            _tp['best']['item'].setdefault('warnings', []).append(_mismatch_warn)
            _tp['best']['item']['favourite_mismatch'] = True
            print(f"  [FAVOURITE_MISMATCH] {_tp['venue']} {_tp.get('race_time','')[:16]}: "
                  f"pick={_our_horse}, mkt fav={_fav_horse} ({_fav_odds:.2f}) "
                  f"scored only {_fav_score:.0f}")

        # Case 2: market disagreement — fav scored well but market prefers someone else
        # Only apply when our pick is at longer odds than the favourite AND the
        # favourite scored ≥ 70 (the market has real conviction about a well-performing horse).
        elif (_our_horse != _fav_horse
              and _fav_horse
              and _fav_score >= 70
              and _fav_odds < _our_odds):
            _score_lead = _our_score - _fav_score
            _odds_gap   = _our_odds - _fav_odds
            print(f"  [MARKET_DISAGREE] {_tp['venue']} {_tp.get('race_time','')[:16]}: "
                  f"pick={_our_horse} @{_our_odds:.2f} (score {_our_score:.0f}), "
                  f"mkt fav={_fav_horse} @{_fav_odds:.2f} (score {_fav_score:.0f}), "
                  f"score lead={_score_lead:+.0f}, odds gap={_odds_gap:+.2f}")
            # Only drop the pick if the score lead doesn't compensate the market disagreement.
            # Threshold: need ≥25 score points of lead to override a shorter-priced fav.
            if _score_lead < 25:
                print(f"    → Score lead {_score_lead:.0f} < 25pts threshold — "
                      f"dropping {_our_horse} (market disagreement, insufficient model edge)")
                _market_disagree_picks.append(_tp)
            else:
                print(f"    → Score lead {_score_lead:.0f} ≥ 25pts — keeping {_our_horse} "
                      f"(model edge outweighs market signal)")

    for _drop in _market_disagree_picks:
        top_picks.remove(_drop)

    # ── HOT PROSPECT BONUS SLOT ──────────────────────────────────────────────
    # Allow a 6th pick ONLY if a genuinely exceptional candidate exists beyond
    # the normal 5-pick cap. This pick appears only on the premium Top 5 page.
    # Threshold: score >= 130 AND odds < 5.0 (the 80%/42% WR bands from backtest).
    # Cap: max 6 total UI picks per day (5 normal + 1 hot prospect).
    HOT_PROSPECT_SCORE    = 130
    HOT_PROSPECT_MAX_ODDS = 5.0
    _total_ui_with_locked = _locked_count + len(top_picks)
    if _total_ui_with_locked >= MAX_DAILY_UI_PICKS and len(eligible) > _effective_target:
        _hot = eligible[_effective_target]
        _hot_score = _hot['best']['score']
        _hot_odds  = float(_hot['best'].get('odds', 99))
        if _hot_score >= HOT_PROSPECT_SCORE and _hot_odds < HOT_PROSPECT_MAX_ODDS:
            top_picks.append(_hot)
            print(f"  HOT PROSPECT added: {_hot['best']['horse']} "
                  f"score={_hot_score:.0f} @{_hot_odds:.2f} "
                  f"— exceptional pick, 6th slot activated")
        else:
            print(f"  No hot prospect: next eligible {_hot['best']['horse']} "
                  f"score={_hot_score:.0f} @{_hot_odds:.2f} "
                  f"— does not meet threshold (need score>=130, odds<5.0)")

    # Sort final picks: rank 1 = highest score (already sorted, but re-sort after hot prospect)
    top_picks.sort(key=lambda r: (r['best']['score'],
                                   1 if float(r['best'].get('odds', 99)) < 2.5 else 0),
                   reverse=True)

    def _pre_cap_score(r):
        bd   = r['best']['item'].get('score_breakdown', {})
        _ml  = float(bd.get('market_leader', 0) or 0)
        _cap = float(bd.get('score_cap', 0) or 0)
        return r['best']['score'] - _ml - _cap

    _selection_rank_scores = {
        r['best']['item']['bet_id']: _pre_cap_score(r)
        for r in top_picks
    }

    # Build a set of bet_ids for the top picks
    top_bet_ids = {r['best']['item']['bet_id']: rank
                   for rank, r in enumerate(top_picks, start=1)}
    # Track which bet_id is the hot prospect (rank 6 = the bonus slot)
    _hot_prospect_id = None
    if len(top_picks) > MAX_DAILY_UI_PICKS:
        _hot_prospect_id = top_picks[-1]['best']['item']['bet_id']

    print("\n" + "=" * 100)
    print(f"TOP {len(top_picks)} PICKS SELECTED")
    print("=" * 100)
    for rank, r in enumerate(top_picks, start=1):
        b = r['best']
        print(f"  #{rank}  {b['horse']:28}  @{b['odds']:5.2f}  Score: {b['score']:3.0f}  "
              f"[{r['venue']}  {r['race_time'][:16]}]")
    if not top_picks:
        print("  WARNING: No races met the minimum confidence threshold — no UI picks today")
    print("=" * 100 + "\n")

    # ── PASS 2 — SAVE ALL ITEMS ───────────────────────────────────────────────
    total_saved = 0
    ui_promoted = 0

    for race_data in all_races_data:
        race_total = len(race_data['runners'])
        _race_missing = race_data.get('missing_runners', 0)
        _sl_decl = race_data.get('sl_declared_count', 0)

        # Build all_horses list for UI field comparison — all scored runners in this race
        _sorted_runners = sorted(race_data['runners'], key=lambda x: x['score'], reverse=True)
        _all_horses_list = [
            {
                'horse':   h['item'].get('horse', ''),
                'jockey':  h['item'].get('jockey', ''),
                'trainer': h['item'].get('trainer', ''),
                'odds':    Decimal(str(round(float(h['item'].get('odds', 0) or 0), 2))),
                'score':   Decimal(str(round(float(h['score']), 0))),
            }
            for h in _sorted_runners
        ]

        for r in race_data['runners']:
            item  = r['item']
            bid   = item['bet_id']
            rank  = top_bet_ids.get(bid, 0)
            is_ui = rank > 0

            # Detect dropped picks — previously a ranked UI pick (1-5), now demoted
            _is_dropped = (not is_ui and bid in _reanalysable_ui_ids)
            item['show_in_ui']          = is_ui  # dropped picks are NOT show_in_ui
            item['recommended_bet']     = is_ui
            item['is_learning_pick']    = not is_ui and not _is_dropped
            item['pick_rank']           = rank
            item['is_hot_prospect']     = (bid == _hot_prospect_id) if _hot_prospect_id else False
            item['is_dropped']          = _is_dropped
            item['pick_type']           = 'dropped' if _is_dropped else ('morning' if is_ui else 'learning')
            item['race_analyzed_count'] = race_total
            if is_ui:
                # Kelly Criterion stake sizing (half-Kelly, 100-unit bankroll):
                # Stake = kelly_fraction × 100 units, bounded to 2–8 units.
                # Ranking is a tiebreaker: same Kelly → strongest pick gets most.
                # Overrides the fixed 5/3/2 allocation with mathematically optimal sizing.
                _kf = float(item.get('kelly_fraction', 0))
                _kelly_units = max(2, min(8, round(_kf * 100)))
                # Rank-based floor: ensure rank-1 ≥ rank-2 ≥ rank-3 stakes
                _rank_floor = {1: 4, 2: 3, 3: 2}.get(rank, 2)
                _stake_pts = max(_kelly_units, _rank_floor)
                item['stake']       = Decimal(str(_stake_pts))
                item['stake_pts']   = _stake_pts
                item['bet_type']    = 'Each Way'
                # Store the selection ranking score — differentiates picks that all hit
                # the score cap at the same value. UI uses this as the displayed confidence.
                _sel_rank = _selection_rank_scores.get(bid, float(r['score']))
                item['selection_rank_score'] = Decimal(str(round(float(_sel_rank), 0)))
            item['sl_declared_count']   = _sl_decl
            item['missing_runners']     = _race_missing
            item['all_horses']          = _all_horses_list  # full field for UI display

            try:
                table.put_item(Item=item)
                total_saved += 1
                if is_ui:
                    ui_promoted += 1
                    print(f"  >> PICK #{rank}: {item['horse']:28} @{float(item['odds']):5.2f}  "
                          f"Score:{r['score']:3.0f}  [{race_data['venue']}]")
                elif _is_dropped:
                    print(f"  ✗  DROPPED: {item['horse']:28} @{float(item['odds']):5.2f}  "
                          f"Score:{r['score']:3.0f}  (was UI pick, now demoted)")
                else:
                    print(f"  -  Learning: {item['horse']:28} @{float(item['odds']):5.2f}  "
                          f"Score:{r['score']:3.0f}")
            except Exception as e:
                print(f"  ERROR saving {item['horse']}: {e}")

    print(f"\nSaved {total_saved} horses | {ui_promoted} UI picks | "
          f"{total_saved - ui_promoted} learning records\n")

    # ── ZERO-PICKS ALERT ──────────────────────────────────────────────────────
    if ui_promoted == 0 and total_saved > 0:
        _zp_msg = (
            f"BetBudAI ALERT [{today}]: Analysis scored {total_saved} horses "
            f"but produced 0 UI picks. All races rejected by gates. "
            f"Form coverage: {_final_form_pct:.0f}%. Check gate thresholds and logs."
        )
        print(f"\n{'='*60}")
        print(f"[ZERO-PICKS ALERT] {_zp_msg}")
        print(f"{'='*60}\n")
        try:
            import boto3 as _b3
            _ses = _b3.client('ses', region_name='eu-west-1')
            _ses.send_email(
                Source='charles.mccarthy@gmail.com',
                Destination={'ToAddresses': ['charles.mccarthy@gmail.com']},
                Message={
                    'Subject': {'Data': f'🚨 BetBudAI: ZERO picks produced for {today}'},
                    'Body': {'Text': {'Data': _zp_msg}},
                }
            )
            print("[ZERO-PICKS ALERT] SES alert sent")
        except Exception as _zpe:
            print(f"[ZERO-PICKS ALERT] SES send failed (non-fatal): {_zpe}")

    # ── COVERAGE HEALTH CHECK ─────────────────────────────────────────────────
    # Verify every UI pick has a complete all_horses list matching the actual
    # Betfair runner count. Any mismatch means picks were built on a partial field
    # and must not be shown on the UI until reanalysed.
    _coverage_issues = []
    _field_coverages = []
    for rd in all_races_data:
        n_betfair = rd.get('n_runners', 0)
        for rr in rd['runners']:
            if top_bet_ids.get(rr['item']['bet_id'], 0) > 0:
                n_allh = len(rr['item'].get('all_horses', []))
                pct = round(100 * n_allh / n_betfair) if n_betfair else 0
                _field_coverages.append(pct)
                if n_allh != n_betfair:
                    _coverage_issues.append(
                        f"{rd['venue']} {rd['race_time'][11:16]} BST: "
                        f"scored {n_allh}/{n_betfair} runners"
                    )
                    print(f"  [HEALTH ⚠] {rd['venue']} "
                          f"{rd['race_time'][11:16]}: all_horses={n_allh} "
                          f"but Betfair returned {n_betfair} — pick flagged incomplete")
                else:
                    print(f"  [HEALTH ✓] {rd['venue']} "
                          f"{rd['race_time'][11:16]}: {n_allh}/{n_betfair} runners complete")

    _min_coverage = min(_field_coverages) if _field_coverages else 0
    _all_coverage_ok = len(_coverage_issues) == 0 and ui_promoted > 0
    if _coverage_issues:
        print(f"\n  ⚠ COVERAGE ISSUES — analysis_fully_complete = False")
        for issue in _coverage_issues:
            print(f"    - {issue}")
    else:
        print(f"\n  ✓ All UI picks have complete field data — analysis_fully_complete = True\n")

    # ── STAGE 5: Save analysis manifest ──────────────────────────────────────
    # Stores the pipeline completion status in DynamoDB so the UI can display
    # a real-time checklist showing which analysis stages fired today.
    try:
        _all_scored_items = [r['item'] for rd in all_races_data for r in rd['runners']]

        def _sig_pct(key):
            if not _all_scored_items: return 0
            n = sum(1 for i in _all_scored_items
                    if float((i.get('score_breakdown') or {}).get(key, 0)) != 0)
            return round(100 * n / len(_all_scored_items))

        from comprehensive_pick_logic import get_going_conditions as _gwc
        _going_ok = bool(_gwc())
        _form_pct = (round(100 * _form_enriched_count / _form_total_horses)
                     if _form_total_horses else 0)
        manifest = {
            'bet_id':   'SYSTEM_ANALYSIS_MANIFEST',
            'bet_date': 'STATUS',
            'run_time': datetime.now(timezone.utc).isoformat(),
            'today':    today,
            'picks_generated':        Decimal(str(ui_promoted)),
            'horses_scored':          Decimal(str(len(_all_scored_items))),
            'analysis_complete':      (ui_promoted > 0),
            'analysis_fully_complete': _all_coverage_ok,  # True only if every UI pick has full field
            'coverage_issues':        _coverage_issues,   # list of races with incomplete all_horses
            'min_field_coverage_pct': Decimal(str(_min_coverage)),
            'races_analyzed':         Decimal(str(len(all_races_data))),
            'runners_analyzed':       Decimal(str(len(_all_scored_items))),
            # Stage statuses
            'stage_betfair':          'ok',
            'stage_betfair_races':    Decimal(str(len(races))),
            'stage_betfair_horses':   Decimal(str(_form_total_horses)),
            'stage_history':          'ok',
            'stage_history_horses':   Decimal(str(len(horse_history))),
            'stage_going':            'ok' if _going_ok else 'missing',
            'stage_form_enricher':    'ok' if _form_enriched_count > 0 else 'not_run',
            'stage_form_enriched':    Decimal(str(_form_enriched_count)),
            'stage_form_total':       Decimal(str(_form_total_horses)),
            'stage_form_pct':         Decimal(str(_form_pct)),
            'stage_scoring':          'ok',
            'stage_picks':            'ok' if ui_promoted > 0 else 'no_picks',
            # Signal coverage (% of scored horses where each signal fired > 0)
            'sig_market_leader':      Decimal(str(_sig_pct('market_leader'))),
            'sig_deep_form':          Decimal(str(_sig_pct('deep_form'))),
            'sig_trainer':            Decimal(str(_sig_pct('trainer_reputation'))),
            'sig_going':              Decimal(str(_sig_pct('going_suitability'))),
            'sig_consistency':        Decimal(str(_sig_pct('consistency'))),
            'sig_cd_bonus':           Decimal(str(_sig_pct('cd_bonus'))),
            'sig_jockey':             Decimal(str(_sig_pct('jockey_quality'))),
            'sig_distance':           Decimal(str(_sig_pct('distance_suitability'))),
        }
        table.put_item(Item=manifest)
        print(f"[STAGE 5/5] Analysis manifest saved — pipeline "
              f"{'COMPLETE ✓' if ui_promoted > 0 and _form_enriched_count > 0 else 'PARTIAL ⚠'}")
    except Exception as _me:
        print(f"[STAGE 5/5] Warning: manifest save failed — {_me}")

    # ── WHATSAPP NOTIFICATIONS ────────────────────────────────────────────────
    if ui_promoted > 0:
        ui_pick_items = [
            r['item']
            for race_data in all_races_data
            for r in race_data['runners']
            if top_bet_ids.get(r['item']['bet_id'], 0) > 0
        ]
        # Sort by race_time so message is in chronological order
        ui_pick_items.sort(key=lambda x: str(x.get('race_time', '')))
        sent, err = send_pick_notifications(ui_pick_items)
        if sent:
            print(f'[WhatsApp] Notifications sent to {sent} recipient(s)')
        elif err:
            print(f'[WhatsApp] Skipped: {err}')

    return {'total': total_saved, 'ui_picks': ui_promoted, 'learning': total_saved - ui_promoted}


if __name__ == "__main__":
    stats = analyze_and_save_all()
    if stats:
        if stats['ui_picks']:
            print(f"OK {stats['ui_picks']} picks ready - run 'python show_todays_ui_picks.py' to review")
        else:
            print("WARNING: No high-confidence picks today -- check response_horses.json for race data")


