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

TARGET_PICKS   = 5      # 2026-04-17: Max 5 picks per day total (free users see top 2, paid see all 5).
                        # Intraday picks are added via /api/picks/intraday with pick_type='intraday'.
MIN_CONFIDENCE        = 78    # Global floor (fallback only — race-type thresholds below take precedence)
MIN_CONFIDENCE_HCAP   = 85   # 2026-04-06: Handicaps need higher conviction — handicapper designs
                              # these races to be competitive and hard to predict. A score of 78-84
                              # in a handicap provides insufficient model edge vs field variance.
MIN_CONFIDENCE_NORACE = 75   # Conditions / novice / maiden races: smaller fields, less weight chaos,
                              # form signals more reliable → lower threshold is appropriate.


def load_horse_history():
    """
    Scan DynamoDB for all previous results (analysis_type=comprehensive_7factor)
    where result_won is set.  Returns a dict: horse_name -> {wins, runs, win_rate}.
    Used to enrich scoring context with database knowledge of each horse.
    """
    print("Loading horse history from DynamoDB...")
    history = {}  # horse -> {'wins': int, 'runs': int}
    kwargs = {'FilterExpression': Attr('analysis_type').eq('comprehensive_7factor') & Attr('result_won').exists()}
    while True:
        resp = table.scan(**kwargs)
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
    # Compute win rate
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


def analyze_and_save_all():
    """
    Two-pass algorithm:
      Pass 1 — Score every horse, collect per-race bests.
      Select top-5 cross-race bests.
      Pass 2 — Save everything with correct show_in_ui flag.
    """
    races = load_races()
    if not races:
        print("No races found — run betfair_odds_fetcher.py first")
        return

    # Load SL declared field sizes for S8 completeness gate
    sl_declared = load_sl_declared_field_sizes()

    # ── STAGE 1: Deep form enrichment ────────────────────────────────────────
    # Fetches last-6-race run history from Racing Post / Sporting Life for every
    # runner and injects it as 'form_runs'. The scoring engine reads this to fire
    # exact_course_win (+20), exact_distance_win (+20), going_win_match (+32),
    # close_2nd_last_time (+14), fresh_days_optimal (+10), or_trajectory (+10).
    # Without this step all deep_form signals score 0 for every horse.
    _form_total_horses = sum(len(r.get('runners', [])) for r in races)
    _form_enriched_count = 0
    if _FORM_ENRICHER_AVAILABLE:
        print(f"\n[STAGE 1/5] Deep form enrichment — {_form_total_horses} horses from Racing Post/SL...")
        races = _form_enrich(races, verbose=True)
        _form_enriched_count = sum(
            1 for race in races for runner in race.get('runners', [])
            if runner.get('form_runs')
        )
        print(f"  ✓ Form enriched {_form_enriched_count}/{_form_total_horses} horses "
              f"({round(100*_form_enriched_count/_form_total_horses) if _form_total_horses else 0}%)")
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
    # Without this guard, 3 new picks are added per 2-hour refresh → 9+ picks/day.
    # Weekends have more racing cards → allow 8 picks; weekdays capped at 5.
    _dow = datetime.now(timezone.utc).weekday()  # 0=Mon … 6=Sun
    MAX_DAILY_UI_PICKS = 5   # 2026-04-17: Hard cap — 5 picks/day every day (free see 2, paid see 5)
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

        race_runners = []
        for runner in runners:
            horse_name = runner.get('name', 'Unknown')
            odds       = float(runner.get('odds', 0))

            # Inject race-level OurHub going into runner so scoring can access it
            if race.get('ourhub_going'):
                runner['_race_ourhub_going'] = race['ourhub_going']

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
                'outcome':             'pending',
                'market_id':           market_id,
                'market_name':         market_name,
                'selection_id':        runner.get('selectionId', 0),
                'race_coverage_pct':   Decimal('100'),
                'race_total_count':    len(runners),
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

        all_races_data.append({
            'venue':             venue,
            'race_time':         race_time,
            'market_name':       race.get('market_name', ''),
            'runners':           race_runners,
            'raw_runners':       runners,
            'best':              best,
            'n_runners':         len(runners),
            'sl_declared_count': sl_count,           # from SL racecard (0 if unavailable)
            'missing_runners':   missing_runners,    # runners in SL not in Betfair
        })

    # ── SELECT TOP 5 CROSS-RACE BESTS ────────────────────────────────────────
    import re as _re_s12  # for sprint distance detection in S12
    def _passes_quality_gates(r):
        """Quality gate filters applied at pick-selection time.
        S1: Non-market-backed picks need score >= 85 (or 80 if tr/cd anchor present; unexposed >= 50).
        S2: Must have at least one contextual anchor: market_leader, trainer, cd_bonus, OR unexposed_bonus.
            Override: score >= 88 AND gap >= 20 passes without anchor (clear model conviction).
        S3: Age-propped picks (age_bonus >= 10, no market/trainer) need score >= 92 (unexposed >= 50).
        S4: Score gap must be >= 8 (too-close races are coin-flips). Elite (>= 88) bypass.
        S5: Saturday gate — data shows only 9.3pt winner/loser gap on Saturdays vs 21.5pt on Sundays.
            Saturday races: score_gap must be >= 15, AND market_leader signal required for 16+ fields.
        S6: Large field (16+ runners) without market backing: require score_gap >= 12.
        S7: Novice/debut-heavy race — ≥60% runners with ≤1 career run in a named novice/conditions
            stakes, or ≥80% debut runners in any race → skip (model has no rivals form to compare).
            Override: our pick has ≥3 runs AND score >= 88 (we have form, others don't).
        2026-03-27: Relaxed S1 threshold (90→85/80) and added S2 override + S4 elite bypass.
        2026-03-29: Added S5 Saturday tightening + S6 large-field market requirement.
        2026-03-30: Added S7 novice/debut-heavy race gate.
        LESSON: Over-correcting on 2026-03-25 (85 threshold + halved ml bonus) → 0 picks for 2 days.
        LESSON: Saturday analysis — losers averaged 94.2pts (hardly below winners at 103.5); Sunday
                 losers averaged 74.7pts (clearly below winners at 96.2). Saturdays need harder gates.
        LESSON: 2026-03-30 Kempton 14:10 — picked Barefoot Beach (85pts, CD win) but 4/5 runners
                 had only 1 career run → Sizzling Seixas won at 9/1 → novice races are ungradeable.
        """
        score      = r['best']['score']
        bd         = r['best']['item'].get('score_breakdown', {})
        ml         = float(bd.get('market_leader', 0))
        tr         = float(bd.get('trainer_reputation', 0))
        cd         = float(bd.get('cd_bonus', 0))
        age        = float(bd.get('age_bonus', 0))
        unexposed  = float(bd.get('unexposed_bonus', 0))
        deep_form  = float(bd.get('deep_form', 0))   # SL form signals (course/distance/going wins)
        score_gap  = float(r['best']['item'].get('score_gap', 0))
        n_runners  = r.get('n_runners', 0)

        # Detect day of week from race_time
        is_saturday = False
        try:
            _rt = r.get('race_time', '')
            if _rt:
                _d = datetime.fromisoformat(_rt[:19])
                is_saturday = (_d.weekday() == 5)  # 5 = Saturday
        except Exception:
            pass

        # S5 — Saturday-specific tightening
        # Data: Saturday model discrimination gap is only 9.3pts (winner 103.5 vs loser 94.2).
        # Require a larger gap between our pick and the next-best horse in the race.
        if is_saturday:
            sat_gap_req = 15
            if score < 88 and score_gap < sat_gap_req:
                print(f"  [GATE-S5 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"SATURDAY gate — score_gap={score_gap:.1f} < {sat_gap_req} required "
                      f"(Saturday model discrimination historically weak — 9.3pt winner/loser gap)")
                return False
            # For 16+ runner races on Saturday, must have market backing — too chaotic otherwise
            if n_runners >= 16 and ml == 0:
                print(f"  [GATE-S5 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"SATURDAY large field ({n_runners} runners) — market leader signal required")
                return False

        # S6 — Large field without market backing
        # 16+ runner fields have pace/draw/traffic variance the model cannot see.
        # Without market agreement, our pick is essentially a coin-flip.
        if n_runners >= 16 and ml == 0 and score < 92:
            if score_gap < 12:
                print(f"  [GATE-S6 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"large field ({n_runners} runners), no market signal, gap={score_gap:.1f} < 12")
                return False

        # S2 — hard gate: at least one contextual anchor required
        # Anchors: market_leader, trainer, cd_bonus, unexposed_bonus, OR strong deep_form (≥16pts)
        # deep_form ≥ 16 = horse won on this going/course/distance → legitimate evidence
        # Override: high-conviction picks (88+ score, 20+ point gap) bypass anchor check
        if ml == 0 and tr == 0 and cd == 0 and unexposed == 0 and deep_form < 16:
            if score >= 88 and score_gap >= 20:
                print(f"  [GATE-S2 OVERRIDE] {r['best']['horse']} score={score:.0f} gap={score_gap:.0f}: "
                      f"high-conviction override — no anchor but clear model advantage")
            else:
                print(f"  [GATE-S2 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"no market_leader/trainer_rep/cd_bonus/unexposed signal")
                return False

        # S1 — non-market-backed picks need good score
        # If horse has another anchor (trainer or cd), threshold is 85; otherwise 88
        # RAISED 2026-04-01: was 80/85. Analysis of 47 races shows non-market picks with only
        # trainer/cd anchors lose at ~55% rate. Higher bar filters out more marginal picks.
        if ml == 0:
            if unexposed >= 10:
                min_s1 = 50
            elif tr > 0 or cd > 0:
                min_s1 = 85   # Was 80: raised after April 1 analysis — trainer/cd alone not enough
            else:
                min_s1 = 88   # Was 85: no market AND no strong anchor = very risky
            if score < min_s1:
                print(f"  [GATE-S1 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"not market-backed, needs >= {min_s1}")
                return False

        # S3 — age-padded with no market or trainer support needs >= 92; unexposed ≤5yo >= 50
        if age >= 10 and ml == 0 and tr == 0:
            min_s3 = 50 if unexposed >= 10 else 92
            if score < min_s3:
                print(f"  [GATE-S3 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"age_bonus={age:.0f} dominant, needs >= {min_s3}")
                return False

        # S4 — Score gap gate: require the race-best to outscore 2nd-best by at least 8 points.
        # ELITE bypass: scores >= 88 already indicate strong model conviction.
        if score < 88 and score_gap < 8:
            print(f"  [GATE-S4 REJECTED] {r['best']['horse']} score={score:.0f}: "
                  f"score_gap={score_gap:.1f} < 8 (too tight, race is a coin-flip)")
            return False

        # S7 — Novice/debut-heavy race gate (2026-03-30)
        # LESSON: 14:10 Kempton — 4/5 runners had 1 career run; won by a 9/1 shot.
        #   Barefoot Beach scored 85 (CD win, co-fav) but form data was nearly non-existent
        #   for most rivals → model has nothing to compare against → effectively a coin-flip.
        # Rule: if ≥ 60% of runners are on debut or have a single career run, SKIP unless:
        #   (a) our pick is the ONLY runner with real form (>= 3 runs), AND score >= 88, OR
        #   (b) race_name explicitly isn't a novice/conditions stakes
        _all_runners = r.get('raw_runners', [])
        if _all_runners:
            _debut_count = 0
            for _ru in _all_runners:
                _form = str(_ru.get('form', '') or '').strip()
                # Betfair FORM field: '-' = no runs, single char = 1 run, '1-' = debut win, etc.
                _run_chars = _form.replace('-', '').replace('/', '').replace('P', '') \
                                  .replace('F', '').replace('U', '').replace('0', '')
                _is_debut_or_one_run = len(_form) == 0 or _form == '-' or len(_run_chars) <= 1
                if _is_debut_or_one_run:
                    _debut_count += 1
            _debut_ratio = _debut_count / len(_all_runners)
            if _debut_ratio >= 0.60:
                _our_form = str(r['best']['item'].get('form', '') or '').strip()
                _our_runs = len(_our_form.replace('-', '').replace('/', ''))
                _market_name = r.get('market_name', '').lower()
                _is_novice_name = any(kw in _market_name for kw in
                                      ['nov', 'novice', 'mdn', 'maiden', 'cond', 'nstks', 'nst'])
                if _debut_ratio >= 0.80 and not (_our_runs >= 3 and score >= 88):
                    print(f"  [GATE-S7 REJECTED] {r['best']['horse']} score={score:.0f}: "
                          f"debut-heavy field — {_debut_count}/{len(_all_runners)} runners "
                          f"({_debut_ratio:.0%} ≤1 run) → model has no rivals form to compare")
                    return False
                if _is_novice_name and not (_our_runs >= 3 and score >= 88):
                    print(f"  [GATE-S7 REJECTED] {r['best']['horse']} score={score:.0f}: "
                          f"novice stakes ('{r.get('market_name','')}') — "
                          f"{_debut_count}/{len(_all_runners)} runners ≤1 run → skip")
                    return False

        # S8 — Incomplete field gate (2026-04-01)
        # LESSON: Kingcormac (Wincanton 15:20, Class 5) — Betfair returned 5 runners but the
        # SL racecard declared 6.  The winner (Starlucky) was never in our analysis.
        # We picked the best of an incomplete field — a guaranteed blind spot.
        # Rule: if the SL racecard declares N runners and we only scored M < N, we're missing
        # at least N-M horses. This almost always means a late entry / non-runner substitute
        # was omitted by Betfair — exactly the runner that can win at big odds and wreck the bet.
        #
        # Thresholds:
        #   - Missing 2+ runners: BLOCK unconditionally (too many unknowns)
        #   - Missing 1 runner:   BLOCK unless our pick is the market favourite (ml > 0)
        #     Rationale: if we back the market leader in a small incomplete field, the
        #     missing horse is unlikely to beat the public's top selection.
        #   - Missing 0 or sl_count==0 (racecard unavailable): allow through
        _missing = r.get('missing_runners', 0)
        _sl_decl = r.get('sl_declared_count', 0)
        if _missing >= 2:
            print(f"  [GATE-S8 REJECTED] {r['best']['horse']} score={score:.0f}: "
                  f"incomplete field \u2014 only {r['n_runners']}/{_sl_decl} declared runners analysed "
                  f"({_missing} missing). Cannot rank a field we haven\u2019t fully seen.")
            return False
        if _missing == 1 and ml == 0:
            print(f"  [GATE-S8 REJECTED] {r['best']['horse']} score={score:.0f}: "
                  f"incomplete field \u2014 {r['n_runners']}/{_sl_decl} runners analysed, 1 missing "
                  f"and pick is NOT market leader. Missing runner could be the winner.")
            return False
        if _missing == 1 and ml > 0:
            print(f"  [GATE-S8 WARNING] {r['best']['horse']} score={score:.0f}: "
                  f"1 undeclared runner missing but pick is market leader \u2014 allowing through.")

        # S9 — Minimum odds gate (2026-04-06, refined 2026-04-07, relaxed 2026-04-17)
        # LESSON 2026-04-17: Gold Star Hero (1.72, score 102) WON but was blocked by 2.0 floor.
        # Galaxy Wonder (2.44, score 124) blocked by EV check (non-monotonic win_prob made EV<0).
        # Fix: lower absolute floor to 1.5, allow 1.5-2.5 for score>=90 (no EV gate — our
        # EV calculation is not reliable enough at short prices to be a hard gate).
        _min_odds = 2.5
        _best_odds = float(r['best'].get('odds', 99))
        # Absolute floor: nothing below 1.5 regardless of score
        if _best_odds < 1.5:
            print(f"  [GATE-S9 REJECTED] {r['best']['horse']} score={score:.0f}: "
                  f"odds {_best_odds:.2f} below absolute floor (1.5) — unbeatable for any system")
            return False
        # 1.5-2.5: allow high-scoring picks (score >= 90)
        if _best_odds < _min_odds:
            if score >= 90:
                print(f"  [GATE-S9 ELITE] {r['best']['horse']} score={score:.0f}: "
                      f"odds {_best_odds:.2f} below 2.5 but high score — allowing")
            else:
                print(f"  [GATE-S9 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"odds {_best_odds:.2f} < {_min_odds:.2f} (needs score>=90 to waive)")
                return False

        # S10 — Irish NHF bumper short-priced favourite gate (2026-04-06)
        # LESSON: Boundfornowhere (Cork 16:45, score=104 ELITE, 7/4 fav) — lost to 80/1 shot.
        # Pattern: Irish NH Flat bumpers are inherently unpredictable. Form is shallow (≤3 runs each),
        # point-to-point form is unquantifiable, and heavy/soft ground randomises the result.
        # When our pick is the SHORT-PRICED FAVOURITE in an Irish bumper, the market_leader bonus
        # (+16pts) inflates the score without adding genuine predictive edge. The 68/1 range of
        # outcomes (2nd-placed Kill Vanhowe at 13/2, winner at 80/1) shows the market itself
        # has no reliable information — being the favourite is NOT an edge.
        # Gate: Irish venue + bumper/NHF race type + market leader at ≤4.0 odds → require score ≥ 110,
        # OR require 3+ recent bumper wins in form. Most horses won't pass — and that's the point.
        _race_mkt = str(r.get('market_name', r.get('race_name', ''))).upper()
        _is_nhf_bumper = 'NHF' in _race_mkt or 'BUMPER' in _race_mkt or 'N.H. FLAT' in _race_mkt
        _IRISH_BUMPER_VENUES = {
            'curragh', 'dundalk', 'navan', 'naas', 'leopardstown', 'cork',
            'galway', 'tipperary', 'punchestown', 'killarney', 'gowran',
            'bellewstown', 'roscommon', 'tramore', 'ballinrobe', 'sligo',
            'fairyhouse', 'listowel', 'down royal', 'downroyal',
        }
        _is_irish_bumper_venue = r.get('course', '').lower().strip() in _IRISH_BUMPER_VENUES
        if _is_nhf_bumper and _is_irish_bumper_venue and ml > 0 and _best_odds <= 4.0:
            # Count recent bumper wins from form — form like 'P-1' or '11' suggests bumper ability
            _bumper_form = str(r['best']['item'].get('form', '') or '')
            _bumper_recent_wins = _bumper_form.replace('-', '').replace('/', '').count('1')
            if _bumper_recent_wins < 2 and score < 110:
                print(f"  [GATE-S10 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"Irish NHF bumper short-priced favourite ({_best_odds}). "
                      f"Market leader bonus inflates score but bumper form is shallow — "
                      f"need score>=110 OR >=2 bumper wins. Lesson: Boundfornowhere 2026-04-06 (104→lost 80/1)")
                return False

        # S11 — Expected Value gate (2026-04-07)
        # Core principle from value betting theory: EV = p×d - 1.
        # If EV < -0.15, the model says we're giving away more than 15 cents per £1 staked.
        # Even with calibration uncertainty in win_probability, EV < -0.15 is a clear signal
        # that odds are too short for our estimated probability of winning.
        # Scores >= 95 (ELITE) bypass: at ELITE confidence our probability estimate likely
        # understates true chance (50%+ calibrated, may genuinely be 55-60%).
        # Source: "Efficiency of Racetrack Betting Markets", Kelly (1956), Sharp Sports Betting.
        _wp = _win_prob_pct(score)
        _ev = _expected_value(_wp, _best_odds)
        if _ev < -0.15 and score < 95:
            print(f"  [GATE-S11 REJECTED] {r['best']['horse']} score={score:.0f}: "
                  f"EV={_ev:+.3f} (win_prob={_wp}%, odds={_best_odds:.2f}) — "
                  f"negative expected value > 15% loss per unit staked")
            return False
        if _ev < 0:
            print(f"  [GATE-S11 WARNING] {r['best']['horse']} score={score:.0f}: "
                  f"EV={_ev:+.3f} (marginally negative) — allowing through (calibration margin)")

        # S12 — Sprint handicap with 12+ runners (2026-04-07)
        # PROFESSIONAL WORKFLOW LESSON: Pro skips "Redcar 2:25 Sprint Handicap, messy pace,
        # 12 runners" immediately. Sprint handicaps (≤7f) with large fields have extremely
        # unpredictable pace dynamics — draw, barrier, early speed all dominate form.
        # This is the single race type where well-handicapped horses lose most unexpectedly.
        # We already block 16+ with S6. Here we extend: sprint handicaps block at 12+.
        _mkt_s12 = str(r.get('market_name', '')).lower()
        _dist_s12 = _re_s12.search(r'(\d+)f', _mkt_s12)
        _dist_f_s12 = int(_dist_s12.group(1)) if _dist_s12 else 99
        _is_sprint_hcap = (
            ('hcap' in _mkt_s12 or 'handicap' in _mkt_s12 or ' h ' in _mkt_s12)
            and _dist_f_s12 <= 7
        )
        if _is_sprint_hcap and n_runners >= 12:
            if score < 92 and ml == 0:
                print(f"  [GATE-S12 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"sprint handicap ({n_runners} runners) — messy pace dynamics, "
                      f"no market backing. Pro workflow: skip this race type at 12+")
                return False

        # S13 — Odds ceiling gate (2026-04-18, backtest-driven)
        # EVIDENCE: 144 horses Mar 22-Apr 17 backtest:
        #   odds 2-3: 80% WR (+97.8% ROI)  |  odds 3-4: 42.1% (+40.2%)
        #   odds 4-5: 30.8% (+34.9%)        |  odds 5-6: 20.8% (+9.3%)
        #   odds 6-8: 0% WR (-100% ROI)     |  odds 10+: 0% WR
        # Horses at 6+ odds have near-zero hit rate. Allow only if score >= 100
        # AND market leader (captures rare legitimate longshot picks like Royal Velvet 9.2).
        if _best_odds >= 6.0:
            if score < 100 or ml == 0:
                print(f"  [GATE-S13 REJECTED] {r['best']['horse']} score={score:.0f}: "
                      f"odds {_best_odds:.2f} >= 6.0 — backtest shows 0% WR in 6-8 band. "
                      f"Needs score>=100 AND market leader to override.")
                return False
            else:
                print(f"  [GATE-S13 WARNING] {r['best']['horse']} score={score:.0f}: "
                      f"odds {_best_odds:.2f} >= 6.0 but elite score + ML — allowing")

        # S14 — Excessive score gap gate (2026-04-18, backtest-driven)
        # EVIDENCE: score_gap 50+ has only 11.1% WR (1W of 9 picks).
        # When the model scores one horse 50+ pts above the field, it's stacking
        # bonuses (form+trainer+jockey+distance) that each add noise — false dominance.
        # Gap 0-10: 50% WR, gap 30-50: 50% WR, gap 50+: 11.1% — clear red flag.
        if score_gap >= 50 and score < 100:
            print(f"  [GATE-S14 REJECTED] {r['best']['horse']} score={score:.0f}: "
                  f"score_gap={score_gap:.0f} >= 50 — backtest shows 11% WR for huge gaps. "
                  f"Score inflation indicator (stacked bonuses ≠ real edge).")
            return False

        return True

    def _race_min_confidence(r):
        """Return the minimum score required for this race type to qualify as a UI pick.
        Handicaps are harder to predict (field deliberately levelled by weights) so require
        a higher model conviction. Conditions/novice/maiden races have simpler fields.
        2026-04-06: replaces the single MIN_CONFIDENCE=78 with race-type-specific thresholds.
        """
        market_name = r.get('market_name', '').lower()
        is_handicap = (
            'hcap' in market_name or
            'handicap' in market_name or
            market_name.endswith(' h') or
            ' h ' in market_name
        )
        if is_handicap:
            return MIN_CONFIDENCE_HCAP    # 85
        return MIN_CONFIDENCE_NORACE      # 75

    eligible = [r for r in all_races_data
                if r['best']['score'] >= _race_min_confidence(r)
                and _passes_quality_gates(r)
                and r.get('race_time', '')[:10] == today]  # exclude tomorrow's races
    eligible.sort(key=lambda r: r['best']['score'], reverse=True)

    # ── PICK SELECTION (2026-04-18 backtest-driven) ────────────────────────────
    # EVIDENCE from 104 UI picks Mar 22-Apr 17:
    #   odds 2-3: 80% WR  |  3-4: 42%  |  4-5: 31%  |  5-6: 21%  |  6+: 0%
    #   Simulation "top score + odds < 4.0" → 61.9% WR, +116.7% ROI
    # Strategy: sort by COMPOSITE score = raw_score + odds_preference_bonus.
    # This shifts selection toward shorter-priced horses when scores are close,
    # without ignoring a genuinely high-scoring longer-odds pick.
    def _odds_preference_bonus(odds):
        """Backtest-calibrated bonus: shorter prices win far more often."""
        if odds < 3.0:  return 8   # 80% WR band — strongly prefer
        if odds < 4.0:  return 4   # 42% WR band — moderately prefer
        if odds < 5.0:  return 0   # 31% WR band — neutral
        return -4                  # 21% WR and below — penalise

    def _selection_score(r):
        raw = r['best']['score']
        odds = float(r['best'].get('odds', 99))
        return raw + _odds_preference_bonus(odds)

    eligible.sort(key=lambda r: _selection_score(r), reverse=True)

    top_picks = eligible[:_effective_target]

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

    # Sort final picks: rank 1 = highest composite selection score
    top_picks.sort(key=lambda r: _selection_score(r), reverse=True)

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


