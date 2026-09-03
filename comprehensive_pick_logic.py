"""
COMPREHENSIVE PICK LOGIC - Always use this for all picks
Integrates ALL learnings:
1. Sweet spot (3-9 odds)
2. Optimal odds position (near average winner odds)
3. Form analysis (wins + consistency)
4. Course-specific performance
5. Horse history from database
6. Trainer analysis
7. Weather & going conditions
8. CHELTENHAM FESTIVAL SPECIFIC LOGIC (March 10-13, 2026)
"""

import json
import boto3
from decimal import Decimal
from datetime import datetime, timezone
from weather_going_inference import check_all_tracks_going

try:
    from track_daily_insights import get_track_insights
except ImportError:
    def get_track_insights(*a, **kw): return {}

# Deep form history signals (Racing Post / Sporting Life scraper)
try:
    from form_enricher import get_form_signals, _dist_to_furlongs
    FORM_ENRICHER_AVAILABLE = True
except ImportError:
    FORM_ENRICHER_AVAILABLE = False
    def get_form_signals(*a, **kw): return {}
    def _dist_to_furlongs(*a, **kw): return None

# Live 30-day trainer/jockey form stats from our own DynamoDB results
try:
    from trainer_form_stats import hot_form_bonus as _hot_form_bonus
    TRAINER_FORM_AVAILABLE = True
except ImportError:
    TRAINER_FORM_AVAILABLE = False
    def _hot_form_bonus(*a, **kw): return 0, {}, []

# Import Cheltenham analyzer when at Cheltenham
try:
    from cheltenham_analyzer import (
        TRAINER_STATS, 
        JOCKEY_STATS,
        analyze_form_string,
        analyze_trainer_jockey
    )
    CHELTENHAM_AVAILABLE = True
except ImportError:
    CHELTENHAM_AVAILABLE = False

# REBALANCED 2026-03-16: Tiered trainers/jockeys, reduced sweet_spot & trainer flat bonus,
#                         increased form/course/distance weights so actual horse evidence matters more.
# Key principle: FORM + COURSE/DISTANCE knowledge > raw trainer name > odds range
DEFAULT_WEIGHTS = {
    # 2026-09-03: pruned weight entries for factors removed as dead/noise —
    # see .claude/skills/vegas.md. Removed keys (no longer referenced
    # anywhere): recent_win, course_bonus, database_history, going_suitability,
    # track_pattern_bonus, novice_race_penalty, bounce_back_bonus,
    # short_form_improvement, aw_low_class_penalty, jockey_course_bonus,
    # meeting_focus_trainer/jockey/combo, new_trainer_debut, aw_evening_penalty,
    # unknown_trainer_penalty, large_field_penalty, same_trainer_rival_penalty,
    # irish_handicap_penalty. `cd_bonus` and `graded_race_cd_bonus` are KEPT —
    # the point AWARD was removed (noise) but the underlying C/D-win detection
    # (cd_pts) still feeds distance_suitability and deep_form as a signal.
    # `heavy_going_penalty` is KEPT — dead in this dataset's June-Sept window
    # but Heavy going essentially can't occur in a UK/Irish summer, so that's
    # seasonal absence, not a broken factor (see the code comment at its use
    # site for the full reasoning).
    'sweet_spot':           12,  # REDUCED 20->12: odds range is a useful filter, not a main signal
    'optimal_odds':         10,  # REDUCED 15->10: combined odds weighting should not dominate
    'total_wins':            8,  # INCREASED  5->8:  each form win carries more weight
    'consistency':           6,  # INCREASED  4->6:  places appear in 33% of losses (2026-03-30)
    'trainer_reputation':   15,  # restored: elite trainer tier 1
    'trainer_tier2':         8,  # unchanged: good trainers
    'trainer_tier3':         4,  # unchanged: decent trainers
    'favorite_correction':   7,  # unchanged: cap stacking on top of trainer bonus
    'jockey_quality':       12,  # restored: elite jockey tier 1
    'jockey_tier2':          6,  # restored: good/champion jockeys
    'weight_penalty':       10,  # unchanged
    'age_bonus':             7,  # REDUCED 10→7 (2026-04-01): 4yo flat bonus was inflating non-market-backed picks. Age matters less in handicaps than form/market signal.
    'distance_suitability': 18,  # INCREASED 12->18: proven distance/course match is very important
    'heavy_going_penalty':    12,  # NEW 2026-03-16: El Gavilan (score=100, 3/1 fav) 5th in Heavy; Heavy ground = unpredictable
    'cd_bonus':             18,  # detection kept (feeds distance_suitability/deep_form); point award removed 2026-09-03
    'graded_race_cd_bonus':  8,  # unchanged
    'official_rating_bonus': 8,  # NEW: high official rating = class horse
    'relative_weight_bonus': 8,  # NEW: carrying less weight than field average
    # Deep form signals (2026-03-20) — from Racing Post last-6-race history
    'form_exact_course_win':  20,  # Proven winner at THIS course
    'form_exact_distance_win':20,  # Proven winner at THIS distance (±0.5f)
    'form_going_win':         16,  # Won on same going type as today
    'form_going_place':        6,  # Placed (2nd/3rd) on same going — consistent
    'form_fresh_optimal':     10,  # Last run 14-35 days ago (peak freshness window)
    'form_close_2nd':         14,  # 2nd beaten < 4 lengths last time — unlucky loser
    'form_or_rising':         10,  # OR trajectory rising over last 3 runs
    'form_big_field_win':      8,  # Won in field of 10+ — proven in competitive race
    # Young improver signals (2026-03-25) — LESSON: Isabella Islay (4yo, form='93', 6.5→2/1 SP)
    # won Hereford 15:30 but scored only 33 (POOR) because she had 0 wins. Lightly-raced
    # young horses with improving form represent potential market movers that static analysis misses.
    'unexposed_bonus':        12,  # 2026-03-25: ≤5yo, ≤5 runs, 0 wins, 1+ place, odds 4-10
    # Class drop bonus (2026-04-01) — LESSON: Broomfields Cave won at Wincanton as a drop-in-grade
    # winner. The model missed it because we had no explicit signal for horses coming down from
    # a higher class. A horse that ran in Class 2/3 recently and drops to Class 4/5 today has
    # a proven quality ceiling above the current field.
    'class_drop_bonus':           12,  # Horse ran Class 2/3 in last 3 runs, today is Class 4/5+
}

# Cache for weights (reload every 5 minutes)
_weights_cache = {'weights': None, 'timestamp': None}

# Cache for going conditions (reload every hour)
_going_cache = {'going_data': None, 'timestamp': None}

def get_dynamic_weights():
    """Load current weights from DynamoDB (auto-adjusted by learning system)"""
    global _weights_cache
    
    # Check cache (5 minute TTL)
    if _weights_cache['weights'] and _weights_cache['timestamp']:
        age = (datetime.now() - _weights_cache['timestamp']).total_seconds()
        if age < 300:  # 5 minutes
            return _weights_cache['weights']
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')
        
        response = table.get_item(
            Key={
                'bet_id': 'SYSTEM_WEIGHTS',
                'bet_date': 'CONFIG'
            }
        )
        
        if 'Item' in response:
            weights = response['Item'].get('weights', {})
            # Convert Decimal to float
            weights_dict = {k: float(v) for k, v in weights.items()}
            
            # Update cache
            _weights_cache['weights'] = weights_dict
            _weights_cache['timestamp'] = datetime.now()
            
            return weights_dict
        else:
            return DEFAULT_WEIGHTS.copy()
    except Exception as e:
        print(f"Warning: Could not load dynamic weights, using defaults: {e}")
        return DEFAULT_WEIGHTS.copy()


def get_going_conditions():
    """Get current going conditions for all tracks (cached for 1 hour)"""
    global _going_cache
    
    # Check cache (1 hour TTL)
    if _going_cache['going_data'] and _going_cache['timestamp']:
        age = (datetime.now() - _going_cache['timestamp']).total_seconds()
        if age < 3600:  # 1 hour
            return _going_cache['going_data']
    
    try:
        # Get going data (prioritizes official declarations)
        going_data = check_all_tracks_going(use_official=True)
        
        # Update cache
        _going_cache['going_data'] = going_data
        _going_cache['timestamp'] = datetime.now()
        
        return going_data
    except Exception as e:
        print(f"Warning: Could not load going conditions: {e}")
        return {}


def is_cheltenham_festival(course, race_date=None):
    """
    Detect if this is a Cheltenham Festival race
    Festival dates: March 10-13, 2026
    """
    if not race_date:
        race_date = datetime.now()
    
    # Cheltenham venue check
    if 'cheltenham' not in course.lower():
        return False
    
    # Date range check (March 10-13, 2026)
    if isinstance(race_date, str):
        try:
            race_date = datetime.fromisoformat(race_date.replace('Z', '+00:00'))
        except:
            race_date = datetime.now()
    
    # Festival dates
    festival_start = datetime(2026, 3, 10)
    festival_end = datetime(2026, 3, 13, 23, 59)
    
    return festival_start <= race_date.replace(tzinfo=None) <= festival_end


def apply_cheltenham_scoring(horse_data, race_name=''):
    """
    Apply Cheltenham Festival specific scoring based on historical analysis
    Returns additional points to add to comprehensive score
    
    Historical patterns (2021-2025):
    - Willie Mullins: 32% Championship strike rate
    - Irish trained: 72.7% of winners
    - Previous Festival winners: 27.3% edge
    - Favorites win 40.9% of Championships
    - Form patterns '111' or '1111' critical
    """
    if not CHELTENHAM_AVAILABLE:
        return 0, []
    
    trainer = horse_data.get('trainer', '')
    jockey = horse_data.get('jockey', '')
    form = horse_data.get('form', '')
    odds = horse_data.get('odds', 99)
    
    bonus_points = 0
    cheltenham_reasons = []
    
    # 1. TRAINER BONUS (MOST CRITICAL)
    if trainer in TRAINER_STATS:
        stats = TRAINER_STATS[trainer]
        championship_wins = stats.get('championship_wins', 0)
        weight_multiplier = stats.get('weight_multiplier', 1.0)
        
        # Base trainer bonus
        trainer_bonus = int((weight_multiplier - 1.0) * 30)
        bonus_points += trainer_bonus
        
        if championship_wins >= 5:
            cheltenham_reasons.append(f"🏆 ELITE: {trainer} ({championship_wins} Championship wins) +{trainer_bonus}pts")
        elif championship_wins >= 3:
            cheltenham_reasons.append(f"⭐ {trainer} ({championship_wins} Championships) +{trainer_bonus}pts")
        elif championship_wins >= 1:
            cheltenham_reasons.append(f"✅ {trainer} (Championship winner) +{trainer_bonus}pts")
        
        # Irish trained bonus (72.7% of winners)
        if stats.get('irish_trained', False):
            irish_bonus = 15
            bonus_points += irish_bonus
            cheltenham_reasons.append(f"🇮🇪 Irish trained (73% of winners) +{irish_bonus}pts")
        
        # Race specialty match
        specialties = stats.get('specialties', [])
        if race_name and any(s.lower() in race_name.lower() for s in specialties):
            specialty_bonus = 20
            bonus_points += specialty_bonus
            cheltenham_reasons.append(f"🎯 Race specialist ({trainer}) +{specialty_bonus}pts")
    
    # 2. JOCKEY BONUS
    if jockey in JOCKEY_STATS:
        stats = JOCKEY_STATS[jockey]
        championship_wins = stats.get('championship_wins', 0)
        
        if championship_wins >= 5:
            jockey_bonus = 15
            bonus_points += jockey_bonus
            cheltenham_reasons.append(f"🏆 Elite jockey: {jockey} ({championship_wins} wins) +{jockey_bonus}pts")
        elif championship_wins >= 3:
            jockey_bonus = 10
            bonus_points += jockey_bonus
            cheltenham_reasons.append(f"⭐ {jockey} ({championship_wins} Championships) +{jockey_bonus}pts")
        elif championship_wins >= 1:
            jockey_bonus = 5
            bonus_points += jockey_bonus
            cheltenham_reasons.append(f"✅ {jockey} (Championship exp) +{jockey_bonus}pts")
        
        # Trainer-Jockey combo bonus
        pairs_with = stats.get('pairs_with', '')
        combo_bonus = stats.get('combo_bonus', 0)
        if pairs_with and pairs_with.lower() in trainer.lower() and combo_bonus > 0:
            bonus_points += combo_bonus
            cheltenham_reasons.append(f"🤝 PROVEN COMBO: {trainer}/{jockey} +{combo_bonus}pts")
    
    # 3. FORM PATTERN BONUS ('111' or '1111' critical)
    if '1111' in form:
        form_bonus = 20
        bonus_points += form_bonus
        cheltenham_reasons.append(f"📊 ELITE FORM '1111' (Championship pattern) +{form_bonus}pts")
    elif '111' in form:
        form_bonus = 15
        bonus_points += form_bonus
        cheltenham_reasons.append(f"📊 STRONG FORM '111' (Championship pattern) +{form_bonus}pts")
    elif '11' in form:
        form_bonus = 10
        bonus_points += form_bonus
        cheltenham_reasons.append(f"📊 Winning streak '11' +{form_bonus}pts")
    
    # 4. FAVORITE BONUS (40.9% win rate - but don't over-rely)
    if odds < 3.0:
        favorite_bonus = 7  # REDUCED from 10 - Ascot 13:15 lesson
        bonus_points += favorite_bonus
        cheltenham_reasons.append(f"💰 Favorite (41% Championship win rate) +{favorite_bonus}pts")
    
    return bonus_points, cheltenham_reasons


def analyze_horse_comprehensive(horse_data, course, avg_winner_odds=3.80, course_winners_today=0, field_weights=None, meeting_context=None, n_runners=0):
    """
    Comprehensive scoring system for horses
    Returns score and breakdown
    """
    name = horse_data.get('name')
    odds = horse_data.get('odds', 0)
    form = horse_data.get('form') or ''
    trainer = horse_data.get('trainer', '')
    
    # Load dynamic weights (auto-adjusted by learning system)
    weights = get_dynamic_weights()
    
    # Load going conditions
    going_data = get_going_conditions()
    
    # Load track insights from earlier races today
    track_insights = get_track_insights(course)
    
    score = 0
    breakdown = {}
    reasons = []

    # ── DEBUTANT BRANCH ───────────────────────────────────────────────────────
    # A first-time-out runner has no form — standard signals don't apply.
    # Use bloodstock signals instead: purchase price, sire tier, pedigree class,
    # analyst distance hint, amplified market signal.
    # The standard scoring continues below but most form-dependent signals will
    # return 0 naturally for a debutant (no form = no wins/places/streaks etc).
    _form_stripped = (form or '').replace('-', '').replace('/', '')
    _is_debutant = len(_form_stripped) == 0
    if _is_debutant:
        try:
            from debutant_scorer import score_debutant
            _race_dist = float(horse_data.get('distance_f', 0) or 0)
            _deb_delta, _deb_bd = score_debutant(horse_data, race_distance_f=_race_dist)
            score += _deb_delta
            breakdown.update(_deb_bd)
        except Exception as _e:
            print(f"  [debutant_scorer] import/call failed for {name}: {_e}")

    # 1. SWEET SPOT CHECK (Graduated - give points based on odds)
    # LESSON 2026-04-03: Historical data shows 3.0–4.9 decimal (2/1–4/1) is a LOSING RANGE
    # (-£11.95 P&L). The PROVEN winning range is 5.0–8.0 decimal (4/1–7/1, +£25.20 P&L).
    # Giving full sweet_spot points to 3.0–4.9 was actively rewarding known-losing odds bands.
    # Fix: 3.0–4.9 now scores 0pts (neutral), 5.0–8.0 gets full pts, 8.0–9.0 partial.
    sweet_spot_pts = 0
    # REBALANCED 2026-04-17: 7-day actuals show 2-3 odds = 50% SR (best),
    # 3-5 = 36% (solid), 5-8 = 11% (worst!). Previous weighting was inverted.
    # Flatten curve: reward shorter odds more, reduce 5-8 bonus.
    if 2.0 <= odds < 3.0:
        # BEST performing range: 50% SR in last 7 days
        sweet_spot_pts = int(weights['sweet_spot'] * 0.85)
        reasons.append(f"Strong odds range (2-3, highest SR): {sweet_spot_pts}pts")
    elif 3.0 <= odds < 5.0:
        # SOLID range: 36% SR in last 7 days — was wrongly flagged as losing band
        sweet_spot_pts = int(weights['sweet_spot'] * 0.5)
        reasons.append(f"Mid-range odds (3-5): {sweet_spot_pts}pts")
    elif 5.0 <= odds <= 8.0:
        # VALUE range: 11% SR but higher payouts — reduced from full bonus
        sweet_spot_pts = int(weights['sweet_spot'] * 0.65)
        reasons.append(f"Value odds range (5-8): {sweet_spot_pts}pts")
    elif 8.0 < odds <= 9.0:
        # Broad value tail
        sweet_spot_pts = int(weights['sweet_spot'] * 0.5)
        reasons.append(f"Good odds range (8-9): {sweet_spot_pts}pts")
    elif 1.5 <= odds < 2.0:
        # Lower points for very short odds
        sweet_spot_pts = int(weights['sweet_spot'] * 0.4)
        reasons.append(f"Very short odds (1.5-2): {sweet_spot_pts}pts")
    elif odds < 1.5:
        # Minimal points for heavy favorites
        sweet_spot_pts = int(weights['sweet_spot'] * 0.2)
        reasons.append(f"Heavy favorite (<1.5): {sweet_spot_pts}pts")
    elif 9.0 < odds <= 15.0:
        # Partial points for medium outsiders
        sweet_spot_pts = int(weights['sweet_spot'] * 0.5)
        reasons.append(f"Medium outsider (9-15): {sweet_spot_pts}pts")
    elif 15.0 < odds <= 20.0:
        # Small points for larger outsiders
        sweet_spot_pts = int(weights['sweet_spot'] * 0.2)
        reasons.append(f"Long shot (15-20): {sweet_spot_pts}pts")
    elif odds > 20.0:
        # Hard penalty: market strongly disagrees — flag as high-risk
        # LESSON 2026-03-20: Spit Spot 60/1 scored 92pts (same as Light Fandango 4/1 which WON)
        # The market price contains information our model lacks. Heavily penalise extreme outsiders.
        longshot_penalty = int(weights['sweet_spot'] * 2)   # = ~24pts deducted
        sweet_spot_pts = -longshot_penalty
        reasons.append(f"Extreme outsider (>{odds:.0f}/1) — market disagrees: -{longshot_penalty}pts")
    
    score += sweet_spot_pts
    breakdown['sweet_spot'] = sweet_spot_pts
    
    # 2. OPTIMAL ODDS POSITION
    # WIDENED 2026-03-30: Winners in optimal range (3/1-4/1) were being under-rewarded
    # because tight bands excluded them. Widen to 1.5/3.0/4.5 to reward near-optimal market prices.
    odds_distance = abs(odds - avg_winner_odds)
    if odds_distance < 1.5:
        optimal_pts = int(weights['optimal_odds'])
        score += optimal_pts
        breakdown['optimal_odds'] = optimal_pts
        reasons.append(f"Near optimal odds ({avg_winner_odds}): {optimal_pts}pts")
    elif odds_distance < 3.0:
        optimal_pts = int(weights['optimal_odds'] / 2)
        score += optimal_pts
        breakdown['optimal_odds'] = optimal_pts
        reasons.append(f"Good odds position: {optimal_pts}pts")
    elif odds_distance < 4.5:
        optimal_pts = max(1, int(weights['optimal_odds'] / 4))
        score += optimal_pts
        breakdown['optimal_odds'] = optimal_pts
        reasons.append(f"Reasonable odds range: {optimal_pts}pts")
    else:
        breakdown['optimal_odds'] = 0
    
    # 3. FORM ANALYSIS
    wins = form.count('1')
    places = form.count('2') + form.count('3')
    recent_win = form.split('-')[-1] == '1' if '-' in form else False

    # Surface-aware win counts (Bug fix 2026-03-22: AW wins ≠ soft turf wins)
    # LESSON: Quatre Bras (6 AW wins, 0 turf wins) and Flanker Jet (6 AW runs, 0 turf wins)
    # both scored going_suitability=20 because old code only checked total wins.
    # Now we split wins by surface using prev_results.going field.
    _AW_GOING_KEYWORDS = {'standard', 'fibresand', 'polytrack', 'slow'}  # SL going for AW
    _prev_results = horse_data.get('prev_results', [])
    turf_wins = 0           # wins on any turf ground
    turf_soft_wins = 0      # wins specifically on soft/yielding/heavy turf
    aw_wins = 0             # wins on all-weather surfaces
    for _pr in _prev_results:
        _pos = str(_pr.get('position', '')).strip()
        _going = str(_pr.get('going', '')).lower()
        _is_aw = any(kw in _going for kw in _AW_GOING_KEYWORDS)
        _is_soft = any(kw in _going for kw in ['soft', 'heavy', 'yielding', 'sloppy'])
        if _pos == '1':
            if _is_aw:
                aw_wins += 1
            else:
                turf_wins += 1
                if _is_soft:
                    turf_soft_wins += 1
    # Fallback: if no prev_results available, assume all wins are turf (can't verify)
    if not _prev_results:
        turf_wins = wins
        turf_soft_wins = wins
    
    # Recent win bonus REMOVED 2026-09-03 — NOISE (sign-flipped across CV
    # folds; only a 1.0% fire rate on the rebuilt dataset, since recent_win
    # is only True when the last-race digit is exactly '1' AND wins==0 was
    # already excluded upstream in most winning-form horses' other bonuses —
    # see .claude/skills/vegas.md). The `recent_win` boolean itself is kept:
    # distance_suitability below still uses it as a signal.

    # Total wins — CAPPED at 4 wins worth (32pts max)
    # LESSON 2026-04-17: Marty McFly got 40pts (5×8) from total_wins alone, came 9th/9.
    # Past wins in different conditions shouldn't dominate the score.
    win_pts_each = int(weights['total_wins'])
    win_points = min(wins * win_pts_each, win_pts_each * 4)  # Cap at 4 wins
    score += win_points
    breakdown['total_wins'] = win_points
    if wins > 0:
        reasons.append(f"{wins} total wins: {win_points}pts")
    
    # Consistency (places) — capped at 3 places worth
    # LESSON 2026-05-29: El Nay scored 36pts from 6 places but had 0 career wins.
    # Placing is not winning. Cap at 3 places to prevent place-form dominating the score.
    place_pts_each = int(weights['consistency'])
    place_points = min(places * place_pts_each, place_pts_each * 3)
    score += place_points
    breakdown['consistency'] = place_points
    if places > 0:
        reasons.append(f"{places} places (2nd/3rd): {place_points}pts")

    # Gate S18 (winless_penalty) REMOVED 2026-09-03 — NOISE (sign-flipped
    # across CV folds in the 2026-09-01 feature-level fit, confirmed on the
    # rebuilt 2026-06-01->09-02 dataset). See .claude/skills/vegas.md.
    # `_s18_runs` is kept — Gate S19 below (maiden_fav_penalty, a SIGNAL
    # factor) reuses this same run count.
    _s18_runs = len(form.replace('-', '')) if form else 0

    # Gate S19 — EXPOSED MAIDEN FAVOURITE TRAP
    # LESSON 2026-05-29: Food For Thought (1.9, 5★TF, Beckett) — hammered favourite in a
    # 5-runner maiden, had 2 runs (6th, 2nd), 0 wins. Gate S18 doesn't fire (needs 3+ runs).
    # But in a maiden race, a short-priced horse with multiple runs and no win is the most
    # common lay scenario. Trainer/Timeform reputation lifts the score; the fact it's been
    # beaten in a maiden already should counteract that. Penalty grows with runs: 2 runs = -10,
    # and applies regardless of Timeform stars (unlike S18's exception — if it can't win a maiden
    # with 5-star TF, the Timeform rating may simply be inflated by breeding, not racecourse form).
    _s19_race_type = horse_data.get('_race_type', '')
    _s19_is_maiden = 'maiden' in _s19_race_type.lower() or _s19_race_type == 'Maiden'
    _s19_runs = _s18_runs  # reuse run count from above
    if _s19_is_maiden and wins == 0 and _s19_runs >= 2:
        _odds_val = float(odds) if odds else 99.0
        if _odds_val < 3.5:
            # Short-priced maiden horse with 2+ runs and no win — exposed favourite
            _mfp = -15
            score += _mfp
            breakdown['maiden_fav_penalty'] = _mfp
            reasons.append(f"⚠ Exposed maiden favourite: {_s19_runs} runs, 0 wins, {_odds_val:.1f} odds: {_mfp}pts")
        else:
            # Longer-priced but still penalise — not expected to win and hasn't yet
            _mfp = -8
            score += _mfp
            breakdown['maiden_fav_penalty'] = _mfp
            reasons.append(f"⚠ Exposed in maiden: {_s19_runs} runs, 0 wins: {_mfp}pts")
    else:
        breakdown['maiden_fav_penalty'] = 0

    # Beaten Favourite penalty — in a maiden context specifically this is a red flag.
    # A horse that was backed to win, failed, and is now back in a maiden again = structural lay.
    # past_results_flags from Racing API: 'BF' = was beaten favourite.
    _ra_flags = str((horse_data.get('ra_data') or {}).get('past_results_flags') or '').upper()
    if 'BF' in _ra_flags:
        _bf_penalty = -10 if _s19_is_maiden else -5
        score += _bf_penalty
        breakdown['beaten_fav_penalty'] = _bf_penalty
        reasons.append(f"⚠ Beaten favourite in previous run: {_bf_penalty}pts")
    else:
        breakdown['beaten_fav_penalty'] = 0

    # 4. COURSE BONUS — REMOVED 2026-09-03 (see .claude/skills/vegas.md).
    # Dead factor (0/33,552 nonzero): `course_winners_today` is hardcoded to 0
    # at every call site (complete_daily_analysis.py always passes
    # course_winners_today=0), so this branch could structurally never fire.
    #
    # 4.5. CLAIMING JOCKEY BONUS — REMOVED 2026-09-03 (see .claude/skills/vegas.md).
    # Dead factor (0/33,552 nonzero): the bracket-allowance jockey-name format
    # this parses for (e.g. "Name(5)") never appears in the jockey field as
    # populated by this pipeline.
    #
    # 4b. GRADED RACE DETECTION
    # Grade 1/2/3 and Listed races are hand-selected elite fields.
    # Form-based going penalties are unreliable here: horses in Graded races are
    # specifically aimed at these races and have their trainers' confidence behind them.
    # Small sample form (e.g. 55-1632) does NOT reliably predict unreadiness for conditions.
    _race_name_raw = str(horse_data.get('race_name',
        horse_data.get('market_name',
        horse_data.get('race_type', '')))).lower()
    is_graded_race = any(kw in _race_name_raw for kw in [
        'grd1', 'grd2', 'grd3', 'grd 1', 'grd 2', 'grd 3',
        'grade 1', 'grade 2', 'grade 3',
        'g1 ', 'g2 ', 'g3 ', '(g1)', '(g2)', '(g3)',
        'grade one', 'grade two', 'grade three',
        'listed', 'group 1', 'group 2', 'group 3',
    ])

    # 5. GOING CONDITIONS
    # `_going_uncertain` is still needed by heavy_going_penalty below (kept as
    # a seasonal exception — see its own note). The going_suitability *scoring*
    # that used to live in this section was removed 2026-09-03 (see below).
    _going_uncertain = False   # default: assume official going unless overridden below

    # ── OurHub going override: if race has confirmed going from OurHub API, inject it
    #    into going_data so the downstream logic treats it as official (no halving).
    _ourhub_going = horse_data.get('_race_ourhub_going', '')
    if _ourhub_going and course not in going_data:
        # Only override if we have NO going data for this course at all
        going_data[course] = {
            'going': _ourhub_going,
            'adjustment': 0,
            'source': 'ourhub_official',
            'surface': 'all-weather' if 'Standard' in _ourhub_going else 'turf',
        }
        reasons.append(f"📡 Going from OurHub API: {_ourhub_going}")
    elif _ourhub_going and course in going_data:
        # We have going data but it's estimated — upgrade to official if OurHub confirms
        _existing_source = going_data[course].get('source', 'official')
        if _existing_source in ('weather_api', 'unavailable'):
            going_data[course]['going'] = _ourhub_going
            going_data[course]['source'] = 'ourhub_official'
            reasons.append(f"📡 Going upgraded via OurHub: {_ourhub_going} (was estimated)")

    # going_suitability scoring REMOVED 2026-09-03 — NOISE (sign-flipped
    # across CV folds in the 2026-09-01 feature-level fit, confirmed on the
    # rebuilt 2026-06-01->09-02 dataset, 44.3% fire rate). See
    # .claude/skills/vegas.md. `_going_uncertain` is kept — heavy_going_penalty
    # below (kept as a seasonal exception, see its own note) still needs to
    # know whether the going is an official declaration or an inferred
    # estimate.
    if course in going_data:
        going_info = going_data[course]
        _going_source = going_info.get('source', 'official')
        _going_uncertain = _going_source in ('weather_api', 'unavailable')

    # 5a. HEAVY GOING SPECIFIC PENALTY (Lesson: 2026-03-16 El Gavilan 5th at 3/1 fav, Class 4 Heavy Ffos Las)
    # Heavy is fundamentally different from Soft — extreme ground that very few horses handle.
    # Jack's Jury (9/1) won over Henderson's Jukebox Fury and 3/1 fav El Gavilan.
    # Apply a flat penalty to ALL horses when going is Heavy — unpredictability surcharge.
    _going_info_heavy = going_data.get(course, {})
    _is_heavy_going = str(_going_info_heavy.get('going', '')).startswith('Heavy')
    if _is_heavy_going:
        heavy_penalty = int(weights.get('heavy_going_penalty', 12))
        if _going_uncertain:
            heavy_penalty = heavy_penalty // 2   # inferred heavy going — uncertainty halves the surcharge
        score -= heavy_penalty
        breakdown['heavy_going_penalty'] = -heavy_penalty
        reasons.append(f"Heavy going (unpredictable, field evens out): -{heavy_penalty}pts")
    else:
        breakdown['heavy_going_penalty'] = 0

    # 5a-i. WATCHLIST IMPROVER SIGNAL — REMOVED 2026-09-03 (see .claude/skills/vegas.md).
    # Dead factor (0/33,552 nonzero, 2026-06-01->09-02): watchlist.py IS bundled
    # into the Lambda, so this isn't an import-availability problem like
    # trainer_hot_form/jockey_hot_form below — check_watchlist() is genuinely
    # never matching. Worth its own investigation if watchlist behaviour
    # matters, but out of scope for this pass.
    #
    # 5a-ii. BLOODSTOCK SIRE GOING SIGNAL — REMOVED 2026-09-03 (see .claude/skills/vegas.md).
    # Dead factor (0/33,552 nonzero): reads `horse_data.get('sire')`, but the
    # racecard pipeline never populates a top-level `sire` field — sire data
    # only exists (for debutants) at `horse_data['ra_data']['sire']`, which
    # this block never checked. Matches the known data-availability gap
    # documented in vegas.md's improvement idea #11 ("BetBudAI's own racecard
    # data has no sire/dam field at all right now"). Fixable in principle
    # (read ra_data.sire instead) but that's a new signal to validate, not a
    # dead-code removal — left for a future, properly backtested pass.

    # 5b. GRADED RACE GOING PENALTY CORRECTION — REMOVED 2026-09-03. This only
    # ever undid a going_suitability penalty, which no longer exists (see
    # above) — kept as dead code it would just never fire again.

    # 5c. C/D MARKER BONUS — cd_bonus scoring REMOVED 2026-09-03 — NOISE
    # (sign-flipped across CV folds, and extremely thin: 11/33,552 nonzero on
    # the rebuilt dataset — under 0.1% fire rate). See .claude/skills/vegas.md.
    # The detection logic (cd_marker / prev_results / form_runs scanning) is
    # kept and `cd_pts` still computed — distance_suitability and deep_form
    # below both branch on whether a C/D win was detected, so the detection
    # itself stays; only the standalone point award is removed.
    # C = course winner, D = distance winner, CD = both.
    # These are proven performance markers that our form string doesn't capture.
    # We look for them in horse_data['cd_marker'] (if the API provides it)
    # or fall back to trailing annotations in the form string.
    cd_marker = str(horse_data.get('cd_marker', horse_data.get('form_flags', ''))).upper()
    # Fallback: some racing feeds embed CD annotations at end of form string
    if not cd_marker and form:
        raw_form = str(horse_data.get('raw_form', form))
        trailing = raw_form.lstrip('0123456789-').upper()
        if trailing in ('C', 'D', 'CD'):
            cd_marker = trailing
    cd_pts = 0
    base_cd = int(weights.get('cd_bonus', 12))
    extra_cd = int(weights.get('graded_race_cd_bonus', 8)) if is_graded_race else 0
    if 'CD' in cd_marker:
        cd_pts = base_cd + extra_cd
    elif 'C' in cd_marker:
        cd_pts = (base_cd // 2) + extra_cd
    elif 'D' in cd_marker:
        cd_pts = (base_cd // 2) + extra_cd
    else:
        # LESSON 2026-03-22: Hello Judge won Carlisle 2m3f (exact C&D) but cd_bonus=0
        # because cd_marker/form annotation wasn't set. Fallback: scan prev_results directly.
        if not cd_pts and _prev_results and course:
            _race_dist = str(horse_data.get('distance', horse_data.get('race_distance', ''))).strip().lower()
            _c_win = False
            _cd_win = False
            for _pr in _prev_results:
                if str(_pr.get('position', '')).strip() == '1':
                    _pr_course = str(_pr.get('course', '')).strip()
                    _pr_dist = str(_pr.get('distance', '')).strip().lower()
                    _course_match = _pr_course.lower() == course.lower()
                    _dist_match = _pr_dist == _race_dist if _race_dist else False
                    if _course_match and _dist_match:
                        _cd_win = True; break
                    elif _course_match:
                        _c_win = True
            if _cd_win:
                cd_pts = base_cd + extra_cd
            elif _c_win:
                cd_pts = base_cd // 2 + extra_cd
            else:
                    pass  # continue to SL form_runs fallback below
            # Fallback: SL form_runs C/D detection — furlongs-based distance matching
            # 2026-03-30: form_runs from form_enricher give per-run course + distance_f;
            # use ±0.5f tolerance to reliably match C/D wins even when string distances differ.
            if not cd_pts and horse_data.get('form_runs') and course:
                _today_dist_f_cd = horse_data.get('race_distance_f')
                _c3 = False; _cd3 = False
                for _fr in horse_data['form_runs']:
                    if _fr.get('position') == 1:
                        _fr_course = str(_fr.get('course', '')).strip()
                        _fr_dist_f = _fr.get('distance_f')
                        _cm3 = _fr_course.lower() == course.lower()
                        _dm3 = (abs(_fr_dist_f - _today_dist_f_cd) <= 0.5
                                if _fr_dist_f is not None and _today_dist_f_cd else False)
                        if _cm3 and _dm3:
                            _cd3 = True; break
                        elif _cm3:
                            _c3 = True
                if _cd3:
                    cd_pts = base_cd + extra_cd
                elif _c3:
                    cd_pts = base_cd // 2 + extra_cd

    # 6. DATABASE HISTORY — REMOVED 2026-09-03 (see .claude/skills/vegas.md).
    # Dead factor: 6/33,552 nonzero across the 2026-06-01->09-02 rebuild dataset
    # (0.02%) — AND it ran a full DynamoDB `table.scan()` (FilterExpression on
    # `horse`) for every single horse in every single race, every day. Scan
    # cost scales with total table size (96K+ items), not matches, so this was
    # a full-table-scan-per-runner sitting in the hot scoring path for no real
    # signal in return. complete_daily_analysis.py's separate `db_history`
    # bonus (preloaded `horse_history` dict, not a per-horse scan) is the
    # actual functioning version of this signal and is untouched.

    # 7. TRACK PATTERN BONUS — REMOVED 2026-09-03 (see .claude/skills/vegas.md).
    # Dead factor (0/33,552 nonzero): track_daily_insights.py (the source of
    # `track_insights`) is not in scripts/build_analysis_lambda.ps1's bundled
    # file list, so get_track_insights() always falls back to its `{}` stub
    # in production and `track_insights.get('has_data')` is always falsy —
    # same root cause as trainer_hot_form/jockey_hot_form below.
    #
    # 8. TRAINER REPUTATION BONUS (Comprehensive UK + Irish trainers)
    # Elite jockeys for jockey quality analysis (added below)
    elite_jockeys_t1 = [
        # Truly elite (Champion level, multiple titles)
        'Paul Townend', 'P Townend', 'P. Townend',
        'Jack Kennedy', 'J Kennedy', 'J. Kennedy',
        'Rachael Blackmore', 'R Blackmore', 'R. Blackmore',
        'Mark Walsh', 'M Walsh', 'M. Walsh',
        'Ryan Moore', 'R Moore', 'R. Moore',
        'William Buick', 'W Buick', 'W. Buick',
        'Frankie Dettori', 'F Dettori', 'F. Dettori',
        'Oisin Murphy', 'O Murphy', 'O. Murphy',
    ]
    elite_jockeys_t2 = [
        # Very good / regular champion
        'Davy Russell', 'D Russell', 'D. Russell',
        'Patrick Mullins', 'P Mullins', 'Mr P. Mullins', 'Mr P Mullins',
        'Danny Mullins', 'D Mullins', 'D. Mullins',
        'Harry Cobden', 'H Cobden', 'H. Cobden',
        'Nico de Boinville', 'N de Boinville', 'N. de Boinville',
        'Harry Skelton', 'H Skelton', 'H. Skelton',
        'Sam Twiston-Davies', 'S Twiston-Davies', 'S. Twiston-Davies',
        'Bryony Frost', 'B Frost', 'B. Frost',
        'Tom Scudamore', 'T Scudamore', 'T. Scudamore',
        'Aidan Coleman', 'A Coleman', 'A. Coleman',
        'Jim Crowley', 'J Crowley', 'J. Crowley',
        'Tom Marquand', 'T Marquand', 'T. Marquand',
        'Hollie Doyle', 'H Doyle', 'H. Doyle',
    ]

    # Tiered trainer lists — ELITE (top strike-rate champions) vs GOOD vs DECENT
    # Tier 1: Truly elite — highest win rates at championship level
    elite_trainers_t1 = [
        # NH champions (Ireland & UK)
        'W P Mullins', 'W. P. Mullins', 'Willie Mullins', 'W Mullins',
        'Gordon Elliott', 'G Elliott', 'G. Elliott',
        'Henry De Bromhead', 'H De Bromhead', 'H. De Bromhead',
        'Nicky Henderson', 'N Henderson',
        'Paul Nicholls', 'P Nicholls',
        # Elite FLAT trainers (2026-04-01: all were marked 'unknown' causing -8pts wrong penalty)
        'W J Haggas', 'William Haggas', 'W. J. Haggas', 'W Haggas',
        'John & Thady Gosden', 'J & T Gosden', 'J Gosden', 'John Gosden', 'Thady Gosden', 'T Gosden',
        'Charlie Appleby', 'C Appleby',
        'Aidan O Brien', "Aidan O'Brien", 'A OBrien', "A O'Brien", 'A P OBrien', "A P O'Brien",
        'Roger Varian', 'R Varian',
        'Ralph Beckett', 'R Beckett', 'R M Beckett',  # R M Beckett = Ralph Beckett (middle initial variant)
        'Roger Charlton', 'R Charlton',
        # Top Irish flat trainers
        'Joseph OBrien', "Joseph O'Brien", 'J OBrien', "J O'Brien",
        'Dermot Weld', 'D Weld', 'D K Weld',
        'Ger Lyons', 'G M Lyons', 'G Lyons',
    ]
    # Tier 2: Good — solid strike rates, regular winners
    elite_trainers_t2 = [
        'Dan Skelton', 'D Skelton',
        'Donald McCain', 'D McCain', 'Donald Mccain',
        'Harry Fry', 'H Fry',
        'Emma Lavelle', 'E Lavelle',
        'Alan King', 'A King',
        'Kim Bailey', 'K Bailey',
        'Venetia Williams', 'V Williams',
        'Philip Hobbs', 'P Hobbs',
        'Jonjo O Neill', 'J O Neill', 'Jonjo Oneill', "Jonjo O'Neill", "A.J. O'Neill", "AJ O'Neill",
        "Fergal O'Brien", 'Fergal O Brien', 'F O Brien', 'Fergal Obrien',
        'Olly Murphy', 'O Murphy',
        'Gavin Cromwell', 'G Cromwell', 'Gavin Patrick Cromwell',
        'Warren Greatrex', 'W Greatrex',
        # Promoted 2026-04-01: Neil Mulholland — proven NH specialist (Wincanton, south-west tracks).
        # Broomfields Cave won Golan Loop race at 3/1; Mulholland was unmatched due to middle-initial
        # variants ("N P Mulholland") not matching "N Mulholland" substring check.
        'Neil Mulholland', 'N Mulholland', 'N P Mulholland', 'Neil P Mulholland', 'N. P. Mulholland',
        'N. Mulholland',
        # Good FLAT trainers (2026-04-01: missing, causing -8pts wrong penalty)
        'A M Balding', 'Andrew Balding', 'A. M. Balding',
        'H Palmer', 'Hugo Palmer', 'H. Palmer',
        'Clive Cox', 'C Cox', 'C. Cox',
        'Mark Johnston', 'M Johnston', 'C Johnston', 'Charlie Johnston',
        'Kevin Ryan', 'K Ryan', 'K. Ryan',
        'Eve Johnson Houghton', 'E Johnson Houghton', 'E J Houghton',
        'Richard Hannon', 'R Hannon', 'R. Hannon',
        'William Muir', 'W Muir', 'William Muir & Chris Grassick',
        'Tom Dascombe', 'T Dascombe',
        # ADDED 2026-04-04: K R Burke (Karl Burke) — well-known UK flat trainer, trained Group 1
        # winners (Laurens, The Gurkha). Strength of Spirit WON at 4/1 but scored only 73 because
        # Burke was penalised -8pts as 'unknown'. He is clearly a solid Tier 2 trainer.
        'K R Burke', 'Karl Burke', 'K. R. Burke',
        # Good Irish flat trainers
        'Donnacha OBrien', "Donnacha O'Brien",
        'Michael Halford', 'M Halford',
        'John Oxx', 'J Oxx',
        'Luke Comer', 'L Comer',
        'Kieran Cotter', 'K Cotter',
        'Daniel Murphy', 'D Murphy',
        # ADDED 2026-05-25: Key flat/2yo specialists missing from all tiers
        # causing them to be penalised -8pts as "unknown trainer" despite being
        # well-established at the top of the game.
        'Simon Crisford', 'S Crisford',                   # Godolphin-connected, T2 flat
        'James Tate', 'J Tate',                           # Strong UK flat, multiple stakes winners
        'Richard Fahey', 'R Fahey',                       # High-volume 2yo/3yo, consistent strike rate
        'Ed Walker', 'E Walker',                           # Quality flat trainer, Ascot specialist
        'Saeed bin Suroor', 'S bin Suroor', 'Saeed Bin Suroor',  # Godolphin T2, flat
        'Owen Burrows', 'O Burrows',                      # Shadwell stable, progressive horses
        'George Boughey', 'G Boughey',                    # Rising flat trainer, 2yo specialist
        'Ismail Mohammed', 'I Mohammed',                  # AW/flat specialist
        'Adrian Keatley', 'A Keatley',                    # Irish flat, solid strike rate
        'Joseph Patrick OBrien', "Joseph Patrick O'Brien",
    ]
    # Tier 3: Decent — know their horses, worth modest bonus
    elite_trainers_t3 = [
        'David Pipe', 'D Pipe',
        'Lucy Wadham', 'L Wadham',
        'Neil King', 'N King',
        'Charlie Longsdon', 'C Longsdon',
        'Colin Tizzard', 'C Tizzard',
        'Tim Easterby', 'T Easterby',
        'Michael Dods', 'M Dods',
        'Tony Carroll', 'T Carroll', 'A W Carroll',
        'David Barron', 'T D Barron', 'T. D. Barron',
        'J P Dempsey', 'J. P. Dempsey',
        'Don Browne', 'D Browne',
        # Added 2026-03-16 after Ffos Las Class 5 result:
        'Kerry Lee', 'K Lee',
        'Sam Thomas', 'S Thomas',
        'Nick Gifford', 'N Gifford',
        'Jamie Snowden', 'J Snowden',
        'Joe Tizzard', 'J Tizzard',
        'Ian Williams', 'I Williams',
        'George Scott', 'G Scott',
        'Richard Phillips', 'R Phillips',
        'Chris Gordon', 'C Gordon',
        'Gary Moore', 'G L Moore',
        'John Flint', 'J Flint',
        'Peter Bowen', 'P Bowen',
        'Rebecca Curtis', 'R Curtis',
        # ADDED 2026-05-25: 2yo/flat specialists missing from all tiers
        'Mick Channon', 'M Channon',                     # 2yo specialist, regular winner
        'Jamie Osborne', 'J Osborne',                    # solid flat/2yo
        'Brian Meehan', 'B Meehan',                      # flat/AW consistent
        'Roger Fell', 'R Fell',                          # Northern flat specialist
        'David Loughnane', 'D Loughnane',                # 2yo sprint specialist
        'Michael Bell', 'M Bell',                        # flat, solid Newmarket yard
        'Stuart Williams', 'S Williams',                  # AW/flat, consistent
        'Simon Dow', 'S Dow',                            # solid flat yard
        'William Knight', 'W Knight',                    # progressive flat yard
        'Jonathan Portman', 'J Portman',                 # southern flat specialist
    ]
    
    trainer_bonus = 0
    trainer_tier = 0
    if trainer:
        trainer_str = str(trainer)
        tstr_lower  = trainer_str.lower()
        if any(e.lower() in tstr_lower for e in elite_trainers_t1):
            trainer_tier   = 1
            trainer_bonus  = int(weights.get('trainer_reputation', 15))
        elif any(e.lower() in tstr_lower for e in elite_trainers_t2):
            trainer_tier   = 2
            trainer_bonus  = int(weights.get('trainer_tier2', 8))
        elif any(e.lower() in tstr_lower for e in elite_trainers_t3):
            trainer_tier   = 3
            trainer_bonus  = int(weights.get('trainer_tier3', 4))

        if trainer_bonus:
            tier_label = ['', 'Elite', 'Good', 'Decent'][trainer_tier]

            # David Pipe penalty in Heavy/Soft (Feb 20 lesson)
            if any(x in trainer_str for x in ['David Pipe', 'D Pipe', 'D. Pipe']):
                going_desc = going_data.get(course, {}).get('going', '')
                if 'Heavy' in going_desc or 'Soft' in going_desc:
                    penalty = trainer_bonus // 2
                    trainer_bonus = max(2, trainer_bonus - penalty)
                    reasons.append(f"David Pipe Heavy/Soft record: -{penalty}pts penalty")

            score += trainer_bonus
            breakdown['trainer_reputation'] = trainer_bonus
            reasons.append(f"{tier_label} trainer ({trainer}): +{trainer_bonus}pts")

    # 8b. RACING API LIVE TRAINER FORM — replaces/augments static tier list
    # trainer_14d_pct is from theracingapi.com Pro racecard: actual win% over last 14 days.
    # This is dynamic and far more reliable than a static name-based tier list.
    _ra = horse_data.get('ra_data', {})
    if _ra:
        _t14_pct  = int(_ra.get('trainer_14d_pct', 0) or 0)
        _t14_runs = int(_ra.get('trainer_14d_runs', 0) or 0)
        _ra_trainer_bonus = 0
        if _t14_runs >= 5:  # need at least 5 runs for meaningful sample
            if _t14_pct >= 35:
                _ra_trainer_bonus = 14
                reasons.append(f"Trainer on fire last 14 days ({_t14_pct}% from {_t14_runs} runs): +{_ra_trainer_bonus}pts")
            elif _t14_pct >= 25:
                _ra_trainer_bonus = 8
                reasons.append(f"Trainer in strong 14-day form ({_t14_pct}% from {_t14_runs} runs): +{_ra_trainer_bonus}pts")
            elif _t14_pct >= 18:
                _ra_trainer_bonus = 4
                reasons.append(f"Trainer in good 14-day form ({_t14_pct}% from {_t14_runs} runs): +{_ra_trainer_bonus}pts")
            elif _t14_runs >= 10 and _t14_pct < 5:
                _ra_trainer_bonus = -6
                reasons.append(f"Trainer out of form last 14 days ({_t14_pct}% from {_t14_runs} runs): {_ra_trainer_bonus}pts")

        if _ra_trainer_bonus:
            # Prevent double-counting: if static tier already fired, only add the difference
            _static_bonus = breakdown.get('trainer_reputation', 0)
            if _static_bonus > 0 and _ra_trainer_bonus > 0:
                # Static tier bonus already applied — add any extra from live form
                _extra = max(0, _ra_trainer_bonus - _static_bonus)
                if _extra > 0:
                    score += _extra
                    breakdown['trainer_live_form'] = _extra
            else:
                score += _ra_trainer_bonus
                breakdown['trainer_live_form'] = _ra_trainer_bonus

        # RPR (Racing Post Rating) — quality signal relative to career peak
        # High RPR = proven high-class performer. Low RPR in a competitive field = outclassed.
        _rpr = _ra.get('rpr')
        if _rpr and isinstance(_rpr, int):
            if _rpr >= 120:
                _rpr_pts = 10
                score += _rpr_pts
                breakdown['rpr_class'] = _rpr_pts
                reasons.append(f"High Racing Post Rating ({_rpr} RPR — class performer): +{_rpr_pts}pts")
            elif _rpr >= 100:
                _rpr_pts = 5
                score += _rpr_pts
                breakdown['rpr_class'] = _rpr_pts
                reasons.append(f"Good Racing Post Rating ({_rpr} RPR): +{_rpr_pts}pts")
            elif _rpr > 0 and _rpr < 60:
                _rpr_pts = -5
                score += _rpr_pts
                breakdown['rpr_class'] = _rpr_pts
                reasons.append(f"Low Racing Post Rating ({_rpr} RPR — may be outclassed): {_rpr_pts}pts")
            else:
                breakdown['rpr_class'] = 0
        else:
            breakdown['rpr_class'] = 0

    # 9. FAVORITE CORRECTION — capped, doesn't stack heavily on trainer
    # Only applies when trainer_tier=1 (truly elite) to avoid inflating mediocre picks
    favorite_bonus = 0
    if trainer_bonus > 0:
        max_fav = int(weights.get('favorite_correction', 7))
        if odds < 2.0 and trainer_tier == 1:
            favorite_bonus = max_fav
            reasons.append(f"Heavy favorite + elite trainer: +{favorite_bonus}pts")
        elif odds < 4.0 and trainer_tier == 1:
            favorite_bonus = max_fav // 2
            reasons.append(f"Short odds + elite trainer: +{favorite_bonus}pts")
        elif odds < 4.0 and trainer_tier == 2:
            favorite_bonus = max_fav // 3
            if favorite_bonus > 0:
                reasons.append(f"Short odds + good trainer: +{favorite_bonus}pts")
        if favorite_bonus:
            score += favorite_bonus
            breakdown['favorite_correction'] = favorite_bonus
    else:
        breakdown['favorite_correction'] = 0
    
    # 10. JOCKEY QUALITY — tiered by actual calibre
    jockey_name = horse_data.get('jockey', '')
    is_elite_jockey = False

    if jockey_name:
        jl = jockey_name.lower()
        if any(e.lower() in jl for e in elite_jockeys_t1):
            jq_pts = int(weights.get('jockey_quality', 12))
            score += jq_pts
            breakdown['jockey_quality'] = jq_pts
            reasons.append(f"Elite jockey ({jockey_name}): +{jq_pts}pts")
            is_elite_jockey = True
        elif any(e.lower() in jl for e in elite_jockeys_t2):
            jq_pts = int(weights.get('jockey_tier2', 6))
            score += jq_pts
            breakdown['jockey_quality'] = jq_pts
            reasons.append(f"Champion jockey ({jockey_name}): +{jq_pts}pts")
            is_elite_jockey = True

    if not is_elite_jockey:
        # 2026-04-13: OurHub integration — use real jockey win rate for unlisted jockeys
        _oh_jwr = horse_data.get('ourhub_jockey_win_rate', 0)
        _oh_jruns = horse_data.get('ourhub_jockey_runs', 0)
        if _oh_jwr and _oh_jruns >= 10 and jockey_name:
            if _oh_jwr >= 18:
                jq_pts = int(weights.get('jockey_tier2', 6))
                score += jq_pts
                breakdown['jockey_quality'] = jq_pts
                reasons.append(f"📡 OurHub: {jockey_name} {_oh_jwr:.0f}% win rate ({_oh_jruns} runs): +{jq_pts}pts")
            elif _oh_jwr >= 10:
                jq_pts = int(weights.get('jockey_tier2', 6)) // 2
                if jq_pts > 0:
                    score += jq_pts
                    breakdown['jockey_quality'] = jq_pts
                    reasons.append(f"📡 OurHub: {jockey_name} {_oh_jwr:.0f}% win rate ({_oh_jruns} runs): +{jq_pts}pts")
                else:
                    breakdown['jockey_quality'] = 0
            else:
                breakdown['jockey_quality'] = 0
        else:
            breakdown['jockey_quality'] = 0
    
    # Sections 11 (novice_penalty), 11b (aw_low_class_penalty), 11c
    # (aw_evening_penalty) and 11e (irish_handicap_penalty) REMOVED 2026-09-03
    # — all dead (0/33,552 nonzero, 2026-06-01->09-02 rebuild dataset; not
    # seasonal like cheltenham_festival/heavy_going_penalty below — these
    # conditions occur year-round, so the most likely cause is a field-name
    # or text-matching mismatch between what this code checks for and what
    # the pipeline actually populates. Not re-diagnosed here — see
    # .claude/skills/vegas.md).
    #
    # 11d (unknown_trainer_penalty), 12 (bounce_back) and 13
    # (short_form_improvement) also REMOVED 2026-09-03 — unknown_trainer_penalty
    # and short_form_improvement were NOISE (sign-flipped across CV folds in
    # the 2026-09-01 feature-level fit, confirmed on the rebuilt dataset);
    # bounce_back was DEAD (0/33,552 nonzero — non-seasonal, likely a form-
    # string pattern that's too strict to ever match real data). See
    # .claude/skills/vegas.md. NOTE: unknown_trainer_penalty fired on 71.7% of
    # observations — the single most common factor removed in this pass —
    # so live score distributions will shift upward by roughly that much on
    # average; watch gate thresholds (MIN_CONFIDENCE, score>=80 gates) over
    # the following few days of real picks.
    #
    # `is_low_class` itself is still needed below (the separate CLASS5_CAP
    # hard-ceiling logic), so it's kept — only the aw_low_class_penalty
    # score adjustment that used to sit alongside it was removed.
    race_name = race_data.get('market_name', '') if 'race_data' in locals() else horse_data.get('race_type', '')
    aw_marker = horse_data.get('race_class', horse_data.get('class', ''))
    aw_name_check = str(horse_data.get('race_name', horse_data.get('market_name', race_name))).lower()
    is_low_class = (
        str(aw_marker) in ['5', '6', 'Class 5', 'Class 6'] or
        'class 5' in aw_name_check or 'class 6' in aw_name_check or
        'class5' in aw_name_check or 'class6' in aw_name_check
    )

    # 14. WEIGHT ANALYSIS — relative within field + absolute heavy-weight penalty
    weight_penalty_pts   = int(weights.get('weight_penalty', 10))
    relative_weight_pts  = int(weights.get('relative_weight_bonus', 8))

    # Prefer weight_lbs (already converted by fetcher), fall back to parsing 'weight' field
    horse_weight_lbs = int(horse_data.get('weight_lbs', 0) or 0)
    if horse_weight_lbs == 0:
        weight_raw = horse_data.get('weight', horse_data.get('weight_raw', ''))
        if weight_raw:
            try:
                w_str = str(weight_raw)
                if '-' in w_str:
                    p = w_str.split('-')
                    horse_weight_lbs = int(p[0]) * 14 + int(p[1])
                else:
                    horse_weight_lbs = int(float(w_str))
            except Exception:
                horse_weight_lbs = 0

    weight_net = 0
    if horse_weight_lbs > 0:
        # Absolute heavy-weight penalty (top weight handicap burden)
        if horse_weight_lbs > 158:  # over 11st 4lb — top weight territory
            abs_penalty = min(weight_penalty_pts, (horse_weight_lbs - 158) // 2)
            weight_net -= abs_penalty
            reasons.append(f"Top weight burden ({horse_weight_lbs}lbs): -{abs_penalty}pts")

        # Relative weight within field (key competitive edge)
        valid_fw = [w for w in (field_weights or []) if isinstance(w, (int, float)) and w > 0]
        if len(valid_fw) >= 2:
            avg_fw = sum(valid_fw) / len(valid_fw)
            diff = avg_fw - horse_weight_lbs  # positive = carrying LESS than average
            if diff >= 10:          # 10+ lbs below average — significant weight advantage
                bonus = min(relative_weight_pts, int(diff / 3))
                weight_net += bonus
                reasons.append(f"Light weight advantage ({horse_weight_lbs}lbs vs {avg_fw:.0f}avg): +{bonus}pts")
            elif diff >= 5:         # 5-9 lbs below — modest advantage
                bonus = relative_weight_pts // 3
                weight_net += bonus
                reasons.append(f"Slightly lighter ({horse_weight_lbs}lbs vs {avg_fw:.0f}avg): +{bonus}pts")
            elif diff <= -10:        # 10+ lbs above average — significant burden
                penalty = min(weight_penalty_pts, int(abs(diff) / 3))
                weight_net -= penalty
                reasons.append(f"Weight burden ({horse_weight_lbs}lbs vs {avg_fw:.0f}avg): -{penalty}pts")

    score += weight_net
    breakdown['weight_penalty'] = weight_net

    # 14b. OFFICIAL RATING BONUS — class horse indicator
    or_bonus_pts = int(weights.get('official_rating_bonus', 8))
    official_rating = horse_data.get('official_rating', '')
    if official_rating:
        try:
            or_val = int(str(official_rating).strip())
            if or_val >= 155:       # Championship / Grade1 class
                or_net = or_bonus_pts
                score += or_net
                breakdown['official_rating_bonus'] = or_net
                reasons.append(f"High official rating ({or_val}): +{or_net}pts")
            elif or_val >= 140:     # Listed / Grade2-3 class
                or_net = or_bonus_pts // 2
                score += or_net
                breakdown['official_rating_bonus'] = or_net
                reasons.append(f"Good official rating ({or_val}): +{or_net}pts")
            else:
                breakdown['official_rating_bonus'] = 0
        except Exception:
            breakdown['official_rating_bonus'] = 0
    else:
        breakdown['official_rating_bonus'] = 0

    # 14c (jockey_course_bonus) and 14d (meeting_focus) REMOVED 2026-09-03 —
    # both dead (0/33,552 nonzero). jockey_course_bonus did its own per-horse
    # DynamoDB get_item() (cheap single-key read, not a scan — unlike the
    # database_history removal above — but still wasted work for a factor
    # that never returned points). meeting_focus depends on `meeting_context`
    # being pre-built by the caller; whatever's populating it, the trainer/
    # jockey single-meeting condition never matched in this dataset. Neither
    # is seasonal. See .claude/skills/vegas.md.

    # 15. AGE BONUS (peak age varies by race type)
    age_bonus_pts = int(weights.get('age_bonus', 10))
    horse_age = horse_data.get('age', None)
    
    if horse_age:
        try:
            age = int(horse_age)
            # National Hunt: peak 6-9 years, Flat: peak 3-5 years
            race_type = str(race_data.get('type', 'flat') if 'race_data' in locals() else 'flat').lower()
            
            if 'hurdle' in race_type or 'chase' in race_type or 'nh' in race_type:
                # National Hunt: peak 6-9
                if 6 <= age <= 9:
                    score += age_bonus_pts
                    breakdown['age_bonus'] = age_bonus_pts
                    reasons.append(f"Peak NH age ({age}yo): +{age_bonus_pts}pts")
                elif age < 5 or age > 11:
                    penalty = age_bonus_pts // 2
                    score -= penalty
                    breakdown['age_bonus'] = -penalty
                    reasons.append(f"Unproven age ({age}yo): -{penalty}pts")
                else:
                    breakdown['age_bonus'] = 0
            else:
                # Flat racing: peak 3-5
                if 3 <= age <= 5:
                    score += age_bonus_pts
                    breakdown['age_bonus'] = age_bonus_pts
                    reasons.append(f"Peak flat age ({age}yo): +{age_bonus_pts}pts")
                elif age > 7:
                    penalty = age_bonus_pts // 2
                    score -= penalty
                    breakdown['age_bonus'] = -penalty
                    reasons.append(f"Veteran ({age}yo): -{penalty}pts")
                else:
                    breakdown['age_bonus'] = 0
        except:
            breakdown['age_bonus'] = 0
    else:
        breakdown['age_bonus'] = 0
    
    # UNEXPOSED IMPROVER BONUS (2026-03-25)
    # LESSON: Isabella Islay (4yo, form='93', odds=6.5) won Hereford 15:30 at SP 2/1
    # but scored POOR because she had 0 wins. Lightly-raced young horses at fair-value
    # odds that have at least one placing are potential market movers.
    _uex_pts  = int(weights.get('unexposed_bonus', 12))
    _uex_runs = len(form.replace('-', '')) if form else 0
    _uex_age  = None
    try:
        _uex_age = int(horse_data.get('age', 0) or 0)
    except (TypeError, ValueError):
        pass
    # Tightened 2026-05-29: "unexposed" means ≤2 outings — genuinely lightly raced.
    # A horse with 3+ runs and no win has had enough chances and is covered by Gate S18.
    if (_uex_age and _uex_age <= 5 and _uex_runs <= 2
            and wins == 0 and places >= 1 and 4.0 <= odds <= 10.0):
        score += _uex_pts
        breakdown['unexposed_bonus'] = _uex_pts
        reasons.append(f"Unexposed {_uex_age}yo improver ({_uex_runs} runs, {places} place(s)): +{_uex_pts}pts")
    else:
        breakdown['unexposed_bonus'] = 0

    # 13. DISTANCE SUITABILITY — actual distance matching using CD marker + form evidence
    distance_pts = int(weights.get('distance_suitability', 18))
    # Priority 1: CD marker proves this horse has won at this course/distance
    if cd_pts > 0:
        # Already rewarded via cd_bonus - give a smaller additional confirming bonus
        dist_bonus = distance_pts // 3
        score += dist_bonus
        breakdown['distance_suitability'] = dist_bonus
        reasons.append(f"Confirmed distance evidence (C/D): +{dist_bonus}pts")
    elif recent_win and wins >= 2:
        # Won last time + multiple form wins = proven at the trip
        score += distance_pts
        breakdown['distance_suitability'] = distance_pts
        reasons.append(f"Proven distance performer (recent win + {wins} wins): +{distance_pts}pts")
    elif wins >= 3:
        # Multiple wins suggests versatile/settled at a distance
        bonus = distance_pts * 2 // 3
        score += bonus
        breakdown['distance_suitability'] = bonus
        reasons.append(f"Versatile/proven performer ({wins} form wins): +{bonus}pts")
    elif wins >= 1 and places >= 2:
        # Won once, placed twice — consistent, probably distance suited
        bonus = distance_pts // 3
        score += bonus
        breakdown['distance_suitability'] = bonus
        reasons.append(f"Consistent at distance (1W {places}P): +{bonus}pts")
    else:
        breakdown['distance_suitability'] = 0
    
    # 16. DEEP FORM SIGNALS (2026-03-20) — from Racing Post last-6-race history
    # These use the detailed per-run table (course, distance, going, pos, OR) scraped by
    # form_enricher.py.  If no form_runs data is present, all signals score 0 gracefully.
    if FORM_ENRICHER_AVAILABLE and horse_data.get('form_runs'):
        today_going_str = going_data.get(course, {}).get('going', '')
        today_dist_f = horse_data.get('race_distance_f')   # injected by get_comprehensive_pick
        fs = get_form_signals(horse_data, course, today_dist_f, today_going_str)

        form_detail_pts = 0

        # Override/augment the CD marker bonus with hard evidence from run history
        if fs.get('exact_course_win') and breakdown.get('cd_bonus', 0) == 0:
            pts = int(weights.get('form_exact_course_win', 20))
            form_detail_pts += pts
            reasons.append(f"Proven course winner at {course} (from run history): +{pts}pts")

        if fs.get('exact_distance_win') and breakdown.get('cd_bonus', 0) == 0:
            pts = int(weights.get('form_exact_distance_win', 20))
            form_detail_pts += pts
            reasons.append(f"Proven distance winner (from run history): +{pts}pts")

        # Going match — replaces/augments the inference-based going_suitability
        # Skip AW/Standard going: every AW race has identical going so "won on AW" is not
        # selective evidence. Also skip if going_suitability already awarded points (deduplicate).
        _going_is_aw = today_going_str.lower() in ('standard', 'aw', 'all weather', 'fast', 'slow')
        _going_already_scored = breakdown.get('going_suitability', 0) > 0
        if fs.get('going_win_match') and not _going_is_aw and not _going_already_scored:
            gw = fs['going_win_count']
            pts = int(weights.get('form_going_win', 16)) * min(gw, 2)  # up to 2× for multiple wins
            pts = min(pts, int(weights.get('form_going_win', 16)) * 2)  # cap at 2×
            form_detail_pts += pts
            reasons.append(f"Won {gw}× on {today_going_str} ground (proven going suitability): +{pts}pts")
        elif fs.get('going_place_match') and not _going_is_aw and not _going_already_scored:
            pts = int(weights.get('form_going_place', 6))
            form_detail_pts += pts
            reasons.append(f"Placed on {today_going_str} ground (consistent going form): +{pts}pts")

        # Freshness window
        days = fs.get('days_since_last_run')
        if fs.get('fresh_days_optimal'):
            pts = int(weights.get('form_fresh_optimal', 10))
            form_detail_pts += pts
            reasons.append(f"Optimal freshness ({days} days since last run): +{pts}pts")
        elif days is not None and days > 60:
            reasons.append(f"Long time off ({days} days) — fitness unknown")

        # Close 2nd last time — unlucky loser
        if fs.get('close_2nd_last_time'):
            pts = int(weights.get('form_close_2nd', 14))
            form_detail_pts += pts
            reasons.append(f"Beaten by < 4 lengths last run (close unlucky 2nd): +{pts}pts")

        # OR trajectory — only meaningful if the horse has raced recently (not a long layoff return)
        days_off = fs.get('days_since_last_run')
        if fs.get('or_trajectory_up') and (days_off is None or days_off <= 90):
            pts = int(weights.get('form_or_rising', 10))
            form_detail_pts += pts
            reasons.append(f"Rising OR trajectory (improving horse): +{pts}pts")

        # Big field winner
        if fs.get('big_field_win'):
            pts = int(weights.get('form_big_field_win', 8))
            form_detail_pts += pts
            reasons.append(f"Won in competitive field (10+ runners): +{pts}pts")

        # Class drop bonus — ran in higher class recently, drops down today
        if fs.get('class_drop'):
            pts = int(weights.get('class_drop_bonus', 12))
            form_detail_pts += pts
            reasons.append(f"Drop in grade (was class 1-3, today class 4+): +{pts}pts")

        if form_detail_pts > 0:
            # Cap: deep form cannot exceed 15% of the pre-deep-form base score.
            # LOWERED 2026-06-02: Was 25%. At base=90, 25% cap = 22pts deep_form allowed.
            # At 90pt base that was Rickety Bridge scoring 50pts deep_form (pre-fix).
            # Winner profile (93pts avg) requires deep form to be proportionate, not dominant.
            # 15% of 90 = 13pts; 12pt minimum always allowed (one solid C&D or going-win signal).
            _score_before_df = score
            _deep_form_cap = max(12, int(_score_before_df * 0.15))
            if form_detail_pts > _deep_form_cap:
                reasons.append(
                    f"Deep Form capped ({form_detail_pts}→{_deep_form_cap}pts: "
                    f"exceeds 15% of {_score_before_df}pt base score)"
                )
                form_detail_pts = _deep_form_cap
            score += form_detail_pts
            breakdown['deep_form'] = form_detail_pts
        else:
            breakdown['deep_form'] = 0

        # ── CURRENT FORM QUALITY (from form_runs) ───────────────────────────
        # These signal whether the horse is IN form RIGHT NOW, not just historically.
        # Separate from deep_form so they appear distinctly in score_breakdown.

        # won_last_2_runs bonus REMOVED 2026-09-03 — NOISE (sign-flipped
        # across CV folds; see .claude/skills/vegas.md).

        # Runs since last win — long losing streak is a red flag
        _rslw = fs.get('runs_since_last_win')
        if _rslw is not None:
            if _rslw >= 12:
                _lstreak_pen = 12
                score -= _lstreak_pen
                breakdown['losing_streak_penalty'] = -_lstreak_pen
                reasons.append(f"Extended losing run ({_rslw} runs without a win): -{_lstreak_pen}pts")
            elif _rslw >= 8:
                _lstreak_pen = 7
                score -= _lstreak_pen
                breakdown['losing_streak_penalty'] = -_lstreak_pen
                reasons.append(f"Losing run ({_rslw} runs without a win): -{_lstreak_pen}pts")
            else:
                breakdown['losing_streak_penalty'] = 0
        else:
            breakdown['losing_streak_penalty'] = 0

        # form_trend REMOVED 2026-09-03 — NOISE (sign-flipped across CV
        # folds; see .claude/skills/vegas.md).

    else:
        breakdown['deep_form'] = 0
        breakdown['losing_streak_penalty'] = 0

    # ── TIMEFORM STARS (from Sporting Life scrape) ──────────────────────────
    # Timeform rates every horse 1-5 stars based on current class, fitness, and form.
    # This is a pre-race assessment by professional analysts — a 5-star rating in a
    # field of 3-star horses is the strongest single class indicator we can get.
    # Stars are collected in form_enricher.py but were previously unused here.
    # 30-day winner data shows winners avg score 93 with clean 2-3 signal profiles.
    # Timeform stars give us a QUALITY signal independent of form-stacking.
    _tf_stars = horse_data.get('timeform_stars')
    if _tf_stars and isinstance(_tf_stars, (int, float)):
        _tf_stars = int(_tf_stars)
        if _tf_stars == 5:
            _tf_pts = 14
            score += _tf_pts
            breakdown['timeform_stars'] = _tf_pts
            reasons.append(f"Timeform 5-star rating (elite form/class): +{_tf_pts}pts")
        elif _tf_stars == 4:
            _tf_pts = 8
            score += _tf_pts
            breakdown['timeform_stars'] = _tf_pts
            reasons.append(f"Timeform 4-star rating (strong form): +{_tf_pts}pts")
        elif _tf_stars == 2:
            _tf_pts = -5
            score += _tf_pts
            breakdown['timeform_stars'] = _tf_pts
            reasons.append(f"Timeform 2-star rating (below par form): {_tf_pts}pts")
        elif _tf_stars == 1:
            _tf_pts = -10
            score += _tf_pts
            breakdown['timeform_stars'] = _tf_pts
            reasons.append(f"Timeform 1-star rating (poor form): {_tf_pts}pts")
        else:
            breakdown['timeform_stars'] = 0  # 3 stars = average, no adjustment
    else:
        breakdown['timeform_stars'] = 0

    # 14. CHELTENHAM FESTIVAL BONUS (CRITICAL FOR SYSTEM SURVIVAL)
    # Apply Championship-specific scoring if at Cheltenham Festival (March 10-13, 2026)
    if is_cheltenham_festival(course):
        race_name = horse_data.get('race_name', '')
        cheltenham_bonus, cheltenham_reasons = apply_cheltenham_scoring(horse_data, race_name)
        
        if cheltenham_bonus > 0:
            score += cheltenham_bonus
            breakdown['cheltenham_festival'] = cheltenham_bonus
            reasons.append(f"\n🏆 CHELTENHAM FESTIVAL BONUS: +{cheltenham_bonus}pts")
            reasons.extend(cheltenham_reasons)
            print(f"\n🏆 CHELTENHAM DETECTED - Applied {cheltenham_bonus} bonus points")
            print("   " + "\n   ".join(cheltenham_reasons))
        else:
            breakdown['cheltenham_festival'] = 0
            reasons.append("⚠️ CHELTENHAM: No elite connections - HIGH RISK")
    else:
        breakdown['cheltenham_festival'] = 0

    # ── FINAL CAP: Class 5/6 races — hard ceiling of 80pts (v4.4 lesson)
    # Lesson: El Gavilan 100pts → 5th (Heavy), Beauzon 91pts → 6th (AW Class5),
    # Queen Of Steel 99pts → 3rd, El Rojo Grande 98pts → 2nd.
    # No Class 5/6 horse should be presented as a 90-100pt certainty.
    # A cap of 80 still allows strong picks to be flagged, but prevents
    # form-streak inflation from overwhelming the class/unpredictability signals.
    CLASS5_CAP = 80
    if is_low_class and score > CLASS5_CAP:
        cap_reduction = score - CLASS5_CAP
        score = CLASS5_CAP
        breakdown['class5_cap'] = -cap_reduction
        reasons.append(f"Class 5/6 score capped at {CLASS5_CAP}pts (was {score + cap_reduction:.0f}): -{cap_reduction:.0f}pts")

    # large_field_penalty and small_field_bonus REMOVED 2026-09-03 — NOISE
    # (sign-flipped across CV folds; 20.8% and 26.8% fire rates respectively
    # on the rebuilt dataset, so this is a meaningful score-distribution
    # shift, not a rare edge case). draw_bias also REMOVED — NOISE (4.2% fire
    # rate). track_handedness and pace_profile REMOVED — DEAD (0/33,552
    # nonzero, non-seasonal). trainer_hot_form/jockey_hot_form REMOVED —
    # DEAD: trainer_form_stats.py (the source of `_hot_form_bonus`) is not in
    # scripts/build_analysis_lambda.ps1's bundled file list, so
    # TRAINER_FORM_AVAILABLE is always False in production and this always
    # fell through to its zero-fallback — same root cause as track_pattern_bonus
    # above. race_type_adj REMOVED — DEAD (0/33,552 nonzero; 'HCAP'/'GRP'/'LIST'
    # exclusions plus the exact NOV+HRD/CHS or MDN substring match apparently
    # never lines up with real market_name text in this pipeline). See
    # .claude/skills/vegas.md for all of the above.

    # ── GENERAL SCORE CAP: 108pts ────────────────────────────────────────────
    # LESSON 2026-04-17: Marty McFly scored 145 (9th of 9), Solar Pass 142 (5th of 6).
    # UPDATED 2026-04-18: Backtest shows score 110-120 has 60% WR vs 120+ at 28.6%.
    # LOWERED 2026-06-02: Winner profile (30-day analysis) averages 93pts. Complete_daily_analysis
    # adds market_leader (+16), db_history (+15), steam (+15) on top of this cap, pushing final
    # scores to 131-136 where all picks cluster at ceiling with NO differentiation.
    # Cap lowered 120→108 so post-function additions land in the 108-120 winner range.
    GENERAL_CAP = 108
    if score > GENERAL_CAP:
        cap_reduction = score - GENERAL_CAP
        score = GENERAL_CAP
        breakdown['score_cap'] = -cap_reduction
        reasons.append(f"Score capped at {GENERAL_CAP}pts (was {score + cap_reduction:.0f}): -{cap_reduction:.0f}pts")

    # ── Signal count audit ────────────────────────────────────────────────────
    # Count positive scoring signals (exclude penalties and meta fields).
    # Pruned 2026-09-03 to match the dead/noise factor removal above — several
    # of these keys no longer exist in breakdown at all (harmless either way,
    # since `v > 0` already excludes negative penalty values on its own; this
    # set only matters for the few penalties whose "off" state could read as
    # 0 rather than negative). See .claude/skills/vegas.md.
    _PENALTY_KEYS = {
        'score_cap', 'maiden_fav_penalty', 'beaten_fav_penalty',
        'heavy_going_penalty', 'losing_streak_penalty', 'weight_penalty',
        'signals_fired',
    }
    _signals_fired = sum(
        1 for k, v in breakdown.items()
        if k not in _PENALTY_KEYS and isinstance(v, (int, float)) and v > 0
    )
    breakdown['signals_fired'] = _signals_fired
    if _signals_fired < 3:
        print(f"  [LOW-SIGNAL] {name}: only {_signals_fired} positive signal(s) fired — "
              f"pick may be odds-driven rather than evidence-driven")

    return score, breakdown, reasons


# ---------------------------------------------------------------------------
# RACE SKIP FILTER
# Lesson: 2026-03-01 Huntingdon 14:45 - Reallyntruthfully (form 1111, 3/1) PU
# Class 3/4/5/6 handicaps are designed by handicappers to produce open results.
# Our trainer/jockey weights are calibrated for Grade 1 / Listed races.
# When both our pick AND the market favourite fail it is Class 3-6 chaos.
# Class 2 is the cut-off: Chester Cup / Royal Hunt Cup level are still viable.
# ---------------------------------------------------------------------------
SKIP_HANDICAP_CLASSES = {'3', '4', '5', '6', 'class 3', 'class 4', 'class 5', 'class 6'}

def should_skip_race(race_data):
    """
    Returns (True, reason_str) if this race should be skipped ENTIRELY.
    Skips Class 3 / 4 / 5 / 6 handicap races on any surface.
    Class 2 and above (Graded / Listed / Class 1-2) are still analysed.
    """
    import re
    market_name = str(race_data.get('market_name',
                       race_data.get('race_name',
                       race_data.get('race_type', '')))).lower()
    race_class  = str(race_data.get('race_class',
                       race_data.get('class', ''))).lower().strip()

    # Detect handicap from name keywords
    is_handicap = (
        'handicap' in market_name or
        ' hcap'    in market_name or
        market_name.endswith('hcap') or
        ' h '      in market_name        # abbreviated NH hurdle handicap
    )

    # Extract numeric class from name if not already in race_class field
    # e.g. "Class 3 Handicap Hurdle" or "Class3 Hcap Chase"
    if not race_class or race_class not in SKIP_HANDICAP_CLASSES:
        m = re.search(r'class\s*([3-6])', market_name)
        if m:
            race_class = m.group(1)

    if is_handicap and race_class in SKIP_HANDICAP_CLASSES:
        return True, f"Class {race_class.upper().replace('CLASS ', '')} handicap - skipped (unpredictable by design)"
    return False, None


def get_comprehensive_pick(race_data, course_stats=None, meeting_context=None):
    """
    Get best pick from race using comprehensive analysis
    SKIP RACE if multiple horses score 85+ (too close to call)
    
    course_stats: {'avg_winner_odds': 3.80, 'winners_today': 4}
    Returns: best_pick dict or None if race should be skipped
    """
    if course_stats is None:
        course_stats = {'avg_winner_odds': 3.80, 'winners_today': 0}
    
    course = race_data.get('venue') or race_data.get('course')
    runners = race_data.get('runners', [])

    # Parse today's race distance from market_name (e.g. "2m4f Nov Hrd" -> 20.0f)
    # Injected into each runner so analyze_horse_comprehensive can use it for form signals
    _market_name = str(race_data.get('market_name', race_data.get('race_name', '')))
    _today_dist_f = _dist_to_furlongs(_market_name)

    analyzed_horses = []
    
    # Calculate coverage: % of runners with form data
    total_runners = len(runners)
    runners_with_data = 0
    
    for runner in runners:
        form = runner.get('form', '')
        odds = runner.get('odds', 0)
        
        # Count as having data if has form and odds
        if form and form not in ['N/A', '', None] and odds and float(odds) > 0:
            runners_with_data += 1

        # Inject today's race distance so form_enricher signals can use it
        if _today_dist_f:
            runner['race_distance_f'] = _today_dist_f

        score, breakdown, reasons = analyze_horse_comprehensive(
            runner, 
            course,
            avg_winner_odds=course_stats.get('avg_winner_odds', 3.80),
            course_winners_today=course_stats.get('winners_today', 0),
            meeting_context=meeting_context
        )
        
        if score > 0:  # Only include horses in sweet spot
            analyzed_horses.append({
                'horse': runner,
                'score': score,
                'breakdown': breakdown,
                'reasons': reasons
            })
    
    if not analyzed_horses:
        return None
    
    # Calculate coverage percentage
    coverage = (runners_with_data / total_runners * 100) if total_runners > 0 else 0
    
    # Sort by score
    analyzed_horses.sort(key=lambda x: x['score'], reverse=True)
    
    # CHECK: If 2+ horses score 90+, apply tiered logic:
    # - Exactly 2 qualifying: back the TOP scorer (evidence: 14:55 Kelso 28-Feb-26 - top scorer won 14/1)
    # - 3+ qualifying: skip (too unpredictable - 14:30 Doncaster 28-Feb-26 lowest scorer won 5/1)
    # LESSON 2026-04-03: Raised from 85→90 to match new show_in_ui threshold (85-89 is a losing band).
    recommended_horses = [h for h in analyzed_horses if h['score'] >= 90]
    if len(recommended_horses) >= 3:
        # 3+ qualifiers - too close to call, skip
        print(f"  ⚠️  RACE SKIPPED: {len(recommended_horses)} horses scored 90+ (too close to call)")
        for h in recommended_horses:
            horse_name = h['horse'].get('name', 'Unknown')
            print(f"     - {horse_name}: {h['score']}/100")
        return None
    elif len(recommended_horses) == 2:
        # Exactly 2 qualifiers - back the top scorer, log the competition
        top = recommended_horses[0]
        second = recommended_horses[1]
        top_name = top['horse'].get('name', 'Unknown')
        second_name = second['horse'].get('name', 'Unknown')
        print(f"  2 horses scored 85+: backing top scorer {top_name} ({top['score']}) over {second_name} ({second['score']})")
        # Override analyzed_horses so best_pick below picks the top qualifier
        analyzed_horses = recommended_horses
    
    # Add coverage to the best pick
    best_pick = analyzed_horses[0]
    best_pick['coverage'] = round(coverage, 1)
    best_pick['total_runners'] = total_runners
    best_pick['analyzed_runners'] = runners_with_data

    # Summarise ALL runners for race card display (name, jockey, trainer, odds, score)
    best_pick['all_horses'] = [
        {
            'horse':   h['horse'].get('name', '') if isinstance(h['horse'], dict) else str(h['horse']),
            'jockey':  h['horse'].get('jockey', '') if isinstance(h['horse'], dict) else '',
            'trainer': h['horse'].get('trainer', '') if isinstance(h['horse'], dict) else '',
            'odds':    float(h['horse'].get('odds', 0) or 0) if isinstance(h['horse'], dict) else 0,
            'score':   round(float(h['score']), 0),
        }
        for h in analyzed_horses
    ]

    return best_pick


def format_pick_for_database(pick_data, race_data):
    """Format comprehensive pick for DynamoDB"""
    horse = pick_data['horse']
    race_time = race_data.get('start_time', '')
    course = race_data.get('venue') or race_data.get('course')
    score = pick_data['score']
    
    # Determine confidence level based on score
    if score >= 90:
        confidence_level = "VERY_HIGH"
    elif score >= 75:
        confidence_level = "HIGH"
    elif score >= 60:
        confidence_level = "MEDIUM"
    else:
        confidence_level = "LOW"
    
    # Show only recommended picks on UI
    # LEARNING 2026-02-26: 90-100 = +33% ROI, 80-84 = +8% ROI, 85-89 = -21.8% ROI
    # LESSON 2026-04-03: Raised threshold from 85→90 because 85-89 is a LOSING band.
    # 2026-02-28: AW Class 5/6 penalty applied - pushed below threshold automatically
    # LESSON 2026-03-20: Kalista Love (9/1, 2/11 field scored) & Spit Spot (60/1) both lost.
    #   Added: extreme odds gate + field coverage gate.
    # LESSON 2026-04-03: 3.0-4.9 decimal odds (2/1-4/1) is a historically LOSING range.
    #   Block show_in_ui for picks in that range unless score is 95+ (truly exceptional case).
    aw_penalised      = float(best_pick.get('breakdown', {}).get('aw_low_class_penalty', 0)) < 0
    extreme_odds      = float(horse.get('odds', 0)) > 30.0   # 30/1+: never recommend regardless of score
    low_coverage      = pick_data.get('coverage', 100) < 40   # <40% field scored = blind spot too large
    _pick_odds        = float(horse.get('odds', 0))
    losing_odds_band  = 3.0 <= _pick_odds < 5.0               # historically -£11.95 P&L range
    show_on_ui        = (score >= 90) and not aw_penalised and not extreme_odds and not low_coverage and not (losing_odds_band and score < 95)
    recommended_bet = show_on_ui
    # Add gates to pick metadata so UI can show why something was filtered
    if extreme_odds:   pick_data['reasons'].append('FILTERED: Odds >30/1 (market confidence too low)')
    if low_coverage:   pick_data['reasons'].append(f"FILTERED: Only {pick_data.get('coverage',0):.0f}% of field scored (<40% threshold)")
    if aw_penalised:   pick_data['reasons'].append('FILTERED: AW Class 5/6 penalty applied')
    if losing_odds_band and score < 95:
        pick_data['reasons'].append(f'FILTERED: Odds {_pick_odds:.1f} (3-5 range is historically -£11.95 P&L losing band; need 95+ score to show)')
    
    # Create bet_id
    bet_id = f"{race_time}_" + course + "_" + horse.get('name', '').replace(' ', '_')
    
    return {
        'bet_id': bet_id,
        'bet_date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'course': course,
        'horse': horse.get('name'),
        'odds': Decimal(str(horse.get('odds', 0))),
        'race_time': race_time,
        'sport': 'Horse Racing',
        'race_type': race_data.get('market_name', 'Unknown'),
        'confidence': Decimal(str(score)),
        'confidence_level': confidence_level,
        'show_in_ui': show_on_ui,
        'recommended_bet': recommended_bet,
        
        # Comprehensive analysis
        'analysis_method': 'COMPREHENSIVE',
        'analysis_score': Decimal(str(score)),
        'comprehensive_score': Decimal(str(score)),
        'form': horse.get('form', ''),
        'trainer': horse.get('trainer', ''),
        'selection_id': str(horse.get('selectionId', '')),
        
        'reasoning': f"Comprehensive analysis ({score}pts - {confidence_level}): " + ", ".join(pick_data['reasons'][:3]),
        'why_selected': pick_data['reasons'],
        'analysis_breakdown': {k: int(v) for k, v in pick_data['breakdown'].items()},
        
        'tags': ['comprehensive_analysis', 'sweet_spot', confidence_level.lower()],
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'comprehensive_learnings'
    }


if __name__ == "__main__":
    # Test with Wolverhampton 19:00
    with open('response_horses.json', 'r') as f:
        data = json.load(f)
    
    wolv_19 = None
    for race in data['races']:
        if race.get('venue') == 'Wolverhampton' and '19:00' in race.get('start_time', ''):
            wolv_19 = race
            break
    
    if wolv_19:
        # Wolverhampton stats from today
        wolverhampton_stats = {
            'avg_winner_odds': 3.80,  # Average of 10 winners today
            'winners_today': 4  # 4/4 Wolverhampton today
        }
        
        best_pick = get_comprehensive_pick(wolv_19, wolverhampton_stats)
        
        if best_pick:
            print("\n" + "="*80)
            print("COMPREHENSIVE PICK LOGIC - TEST")
            print("="*80)
            print(f"\nBEST PICK: {best_pick['horse']['name']} @ {best_pick['horse']['odds']}")
            print(f"Score: {best_pick['score']}")
            print(f"Form: {best_pick['horse']['form']}")
            print(f"Trainer: {best_pick['horse']['trainer']}")
            print(f"\nScoring Breakdown:")
            for key, value in best_pick['breakdown'].items():
                print(f"  {key}: {value}pts")
            print(f"\nReasons:")
            for reason in best_pick['reasons']:
                print(f"  ✓ {reason}")
            print("="*80)
