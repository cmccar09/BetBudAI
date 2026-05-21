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
    'sweet_spot':           12,  # REDUCED 20->12: odds range is a useful filter, not a main signal
    'optimal_odds':         10,  # REDUCED 15->10: combined odds weighting should not dominate
    'recent_win':           16,  # REDUCED 22->16 (2026-03-25): last-race win still #1 signal but was dominating too heavily
    'total_wins':            8,  # INCREASED  5->8:  each form win carries more weight
    'consistency':           6,  # INCREASED  4->6:  places appear in 33% of losses (2026-03-30)
    'course_bonus':         12,  # INCREASED 10->12: course familiarity
    'database_history':     15,  # unchanged
    'going_suitability':    16,  # INCREASED 14->16: going is critical in UK NH
    'track_pattern_bonus':   8,  # REDUCED 10->8
    'trainer_reputation':   15,  # restored: elite trainer tier 1
    'trainer_tier2':         8,  # unchanged: good trainers
    'trainer_tier3':         4,  # unchanged: decent trainers
    'favorite_correction':   7,  # unchanged: cap stacking on top of trainer bonus
    'jockey_quality':       12,  # restored: elite jockey tier 1
    'jockey_tier2':          6,  # restored: good/champion jockeys
    'weight_penalty':       10,  # unchanged
    'age_bonus':             7,  # REDUCED 10→7 (2026-04-01): 4yo flat bonus was inflating non-market-backed picks. Age matters less in handicaps than form/market signal.
    'distance_suitability': 18,  # INCREASED 12->18: proven distance/course match is very important
    'novice_race_penalty':  15,  # unchanged
    'bounce_back_bonus':     8,  # REDUCED 12->8
    'short_form_improvement':8,  # REDUCED 10->8
    'aw_low_class_penalty': 50,  # RAISED 35→50 (2026-03-16): Beauzon 91pts finished 6th in AW Class 5; form streak overwhelmed -35 penalty
    'heavy_going_penalty':    12,  # NEW 2026-03-16: El Gavilan (score=100, 3/1 fav) 5th in Heavy; Heavy ground = unpredictable
    'cd_bonus':             18,  # restored: C/D winner strong evidence
    'graded_race_cd_bonus':  8,  # unchanged
    'official_rating_bonus': 8,  # NEW: high official rating = class horse
    'jockey_course_bonus':   8,  # NEW: jockey course familiarity from history
    'relative_weight_bonus': 8,  # NEW: carrying less weight than field average
    # Meeting-focus signals (2026-03-19)  — priority: jockey sole ride > trainer sole runner
    'meeting_focus_trainer':  10,  # Trainer sole runner at this meeting today
    'meeting_focus_jockey':   10,  # Jockey only rides at this meeting today
    'meeting_focus_combo':    10,  # unchanged: trainer+jockey both focused = strongest signal
    'new_trainer_debut':       5,  # Horse has no prior DB record with this trainer
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
    # AW evening racing penalty (2026-03-25) — LESSON: Wolverhampton 20:00/20:30 races all lost.
    # Evening AW races (after 17:30) have higher variance: small fields, market over-reacts to
    # morning form, last-minute gambles distort prices, track bias not visible until late cards.
    # Scores 81-92 marked STRONG but all unplaced — evening AW races need extra discount.
    'aw_evening_penalty':     12,  # 2026-03-25: AW venues after 17:30 — reduce confidence
    # Unknown/low-tier trainer penalty (2026-03-25) — LESSON: Brian Toomey (Burdett Estate),
    # D M Simcock (Mr Nugget), K Woollacott (Knock Off Soxs) all lost. No trainer in any tier
    # means the score was built entirely from form/odds — weaker evidence for daily picks.
    'unknown_trainer_penalty': 8,  # 2026-03-25: trainer not Tier1/2/3 — reduce confidence
    # Large-field handicap penalty (2026-03-29) — LESSON: Saturday analysis showed losers scored
    # 94.2 avg (only 9.3pts below winners) in 16+ runner fields. Model has no visibility of
    # pace/draw/traffic in big fields — their variance is fundamentally higher and our signals
    # do not discriminate reliably. Apply a per-runner discount so big fields need a much
    # clearer quality advantage before surviving the confidence gate.
    'large_field_penalty':        10,  # 16-19 runners: -10pts; 20+ runners: -18pts
    # Class drop bonus (2026-04-01) — LESSON: Broomfields Cave won at Wincanton as a drop-in-grade
    # winner. The model missed it because we had no explicit signal for horses coming down from
    # a higher class. A horse that ran in Class 2/3 recently and drops to Class 4/5 today has
    # a proven quality ceiling above the current field.
    'class_drop_bonus':           12,  # Horse ran Class 2/3 in last 3 runs, today is Class 4/5+
    # Same-trainer rival penalty (2026-04-01) — LESSON: I'm Spartacus vs Clonmacash, same trainer
    # A McGuinness. When a trainer enters 2+ horses in the same race, stable attention is split and
    # the trainer may prefer one runner over another — reducing confidence in either pick.
    'same_trainer_rival_penalty': 10,  # -10pts per horse when trainer has 2+ in same race
    # Irish competitive venue penalty (2026-04-01) — LESSON: Dmaniac (Curragh handicap sc=107) and
    # I'm Spartacus (Dundalk handicap sc=84) both lost. Irish handicaps at these tracks are
    # notoriously competitive with large fields, tight weights, and unpredictable pace scenarios.
    # Our form signals are just as good there, but the BETTING MARKET is much harder to read.
    'irish_handicap_penalty':    10,  # Handicap race at Irish track (Curragh/Dundalk/Navan/Naas/Leopardstown)
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


def analyze_horse_comprehensive(horse_data, course, avg_winner_odds=4.65, course_winners_today=0, field_weights=None, meeting_context=None, n_runners=0):
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
    
    # 1. SWEET SPOT CHECK (Graduated - give points based on odds)
    # LESSON 2026-04-03: Historical data shows 3.0–4.9 decimal (2/1–4/1) is a LOSING RANGE
    # (-£11.95 P&L). The PROVEN winning range is 5.0–8.0 decimal (4/1–7/1, +£25.20 P&L).
    # Giving full sweet_spot points to 3.0–4.9 was actively rewarding known-losing odds bands.
    # Fix: 3.0–4.9 now scores 0pts (neutral), 5.0–8.0 gets full pts, 8.0–9.0 partial.
    sweet_spot_pts = 0
    if 5.0 <= odds <= 8.0:
        # PROVEN BEST range: 4/1–7/1, +£25.20 P&L (Feb 2026 data) — full sweet spot
        sweet_spot_pts = int(weights['sweet_spot'])
        reasons.append(f"Sweet spot 5-8 (PROVEN best range): {sweet_spot_pts}pts")
    elif 8.0 < odds <= 9.0:
        # Broad sweet spot tail — slight reduction
        sweet_spot_pts = int(weights['sweet_spot'] * 0.75)
        reasons.append(f"Good odds range (8-9): {sweet_spot_pts}pts")
    elif 3.0 <= odds < 5.0:
        # KNOWN LOSING RANGE (2/1–4/1): -£11.95 P&L historical data — neutral, no bonus
        # No points added but no penalty either; other signals may still justify a pick.
        sweet_spot_pts = 0
        reasons.append(f"⚠️ Caution: 3-5 odds range (historically losing band, 2/1-4/1): 0pts")
    elif 2.0 <= odds < 3.0:
        # Partial points for short odds
        sweet_spot_pts = int(weights['sweet_spot'] * 0.6)
        reasons.append(f"Short odds (2-3): {sweet_spot_pts}pts")
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
    
    # Recent win bonus
    recent_win_pts = int(weights['recent_win'])
    if recent_win:
        score += recent_win_pts
        breakdown['recent_win'] = recent_win_pts
        reasons.append(f"Recent win (last race): {recent_win_pts}pts")
    else:
        breakdown['recent_win'] = 0
    
    # Total wins
    win_pts_each = int(weights['total_wins'])
    win_points = wins * win_pts_each
    score += win_points
    breakdown['total_wins'] = win_points
    if wins > 0:
        reasons.append(f"{wins} total wins: {win_points}pts")
    
    # Consistency (places)
    place_pts_each = int(weights['consistency'])
    place_points = places * place_pts_each
    score += place_points
    breakdown['consistency'] = place_points
    if places > 0:
        reasons.append(f"{places} places (2nd/3rd): {place_points}pts")
    
    # 4. COURSE BONUS
    course_bonus_pts = int(weights['course_bonus'])
    if course_winners_today > 0:
        score += course_bonus_pts
        breakdown['course_performance'] = course_bonus_pts
        reasons.append(f"{course} validated ({course_winners_today} today): {course_bonus_pts}pts")
    else:
        breakdown['course_performance'] = 0
    
    # 4.5. CLAIMING JOCKEY BONUS (NEW 2026-02-20)
    # Claiming jockeys (indicated by numbers in brackets like (5), (7)) get weight allowances
    # In Heavy/Soft going, reduced weight is a significant advantage
    jockey = horse_data.get('jockey', '')
    claiming_allowance = 0
    if '(' in jockey and ')' in jockey:
        try:
            # Extract claiming allowance: "Toby McCain-Mitchell(5)" -> 5
            claiming_str = jockey.split('(')[1].split(')')[0]
            claiming_allowance = int(claiming_str)
        except:
            claiming_allowance = 0
    
    if claiming_allowance > 0 and course in going_data:
        going_desc = going_data[course].get('going', 'Unknown')
        if 'Heavy' in going_desc or 'Soft' in going_desc:
            # In testing ground, weight allowance is crucial
            claiming_bonus = claiming_allowance * 2  # 5lb claim = 10pts bonus
            score += claiming_bonus
            breakdown['claiming_jockey'] = claiming_bonus
            reasons.append(f"Claiming {claiming_allowance}lb in {going_desc}: {claiming_bonus}pts")
        else:
            # Moderate bonus in normal conditions
            claiming_bonus = claiming_allowance
            score += claiming_bonus
            breakdown['claiming_jockey'] = claiming_bonus
            reasons.append(f"Claiming {claiming_allowance}lb allowance: {claiming_bonus}pts")
    else:
        breakdown['claiming_jockey'] = 0
    
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

    # 5. GOING CONDITIONS - Proper horse suitability assessment
    # February UK/Ireland: Soft/Heavy ground is the norm - this is a MAJOR differentiator
    # A horse that can't handle soft simply has little chance; proven soft-ground performers
    # get a significant edge over rivals who prefer quicker ground.
    base_going_pts = int(weights.get('going_suitability', 14))
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

    if course in going_data:
        going_info = going_data[course]
        going_adjustment = going_info.get('adjustment', 0)
        going_description = going_info.get('going', 'Unknown')
        is_soft_ground = 'Heavy' in going_description or 'Soft' in going_description
        is_extreme = abs(going_adjustment) >= 5  # Heavy/Soft or very firm
        is_all_weather = going_info.get('surface', '') == 'all-weather' or 'Standard' in going_description

        # GOING CONFIDENCE GATE (2026-04-06): When going is inferred from weather rather than
        # officially declared by the track, it is uncertain — halve all going-based bonuses and
        # penalties to reflect that the actual conditions may differ from the estimate.
        # source='official' → confirmed declaration → full weight
        # source='weather_api' → inferred, not official → halve (uncertain / awaiting inspection)
        # source='unavailable' → no data → halve (worst case — treat as uncertain)
        _going_source = going_info.get('source', 'official')
        _going_uncertain = _going_source in ('weather_api', 'unavailable')
        if _going_uncertain:
            # Halve base_going_pts so ALL downstream paths (bonus & every penalty) are reduced by 50%.
            # This single change propagates to going_suitability_pts, aw_penalty, and extreme penalties.
            base_going_pts = base_going_pts // 2
            reasons.append(f"⚠️ Going estimated (not official declaration) — going signals halved")
        
        # LESSON 2026-03-20: Kalista Love & Spit Spot had going_suitability=32pts (35% of total score).
        # Capped at 10pts max (reduced from 16, 2026-03-30): loss analysis shows winners consistently
        # had 0 or negative going scores yet still won — over-weighting going misleads selection.
        going_suitability_pts = min(base_going_pts * 2 if is_extreme else base_going_pts, 10)
        
        if is_all_weather:
            # All-weather: ground irrelevant, give neutral bonus for all runners
            going_suitability_pts = base_going_pts // 2
            score += going_suitability_pts
            breakdown['going_suitability'] = going_suitability_pts
            reasons.append(f"All-weather (going neutral): +{going_suitability_pts}pts")
        else:
            # Check horse going preference from data (explicit field if available)
            going_pref = str(horse_data.get('going_preference', horse_data.get('goes_on', ''))).lower()
            
            # Infer suitability from preference field or form
            suited = False
            if going_pref and going_pref not in ['', 'none', 'unknown', 'n/a']:
                # Explicit preference known
                if is_soft_ground and any(g in going_pref for g in ['soft', 'heavy', 'any', 'all']):
                    suited = True
                elif not is_soft_ground and any(g in going_pref for g in ['firm', 'good', 'fast', 'any', 'all']):
                    suited = True
            
            if not suited:
                # Form-based proxy — surface-aware (fix: 2026-03-22)
                # LESSON: AW wins do NOT prove soft turf suitability.
                # Use turf_wins/turf_soft_wins from prev_results surface detection.
                if is_soft_ground:
                    if turf_soft_wins >= 1:
                        suited = True   # Proven specifically on soft/heavy turf
                    elif turf_wins >= 2:
                        suited = True   # Multiple turf wins = handles varied going
                    elif turf_wins >= 1 and not is_extreme and 'Heavy' not in going_description:
                        suited = True   # 1 turf win in moderate soft = probably handles it
                    # NOTE: AW-only horses (turf_wins==0) deliberately NOT marked suited
                else:
                    # Good/Firm ground — AW wins count as speed/form proof
                    if wins >= 3:
                        suited = True
                    elif wins >= 2 and not is_extreme:
                        suited = True
                    elif wins >= 1:
                        suited = True
            
            # AW-specialist penalty on soft turf: no turf wins at all = unknown quantity
            # LESSON 2026-03-22: Quatre Bras & Flanker Jet had 0 turf wins. Previously got
            # going_suitability=+20. Now penalised to correctly rank them below turf horses.
            _aw_specialist_on_soft = (
                is_soft_ground and aw_wins >= 2 and turf_wins == 0 and not suited
            )

            if suited:
                score += going_suitability_pts
                breakdown['going_suitability'] = going_suitability_pts
                reasons.append(f"Proven/suited to {going_description}: +{going_suitability_pts}pts")
            elif _aw_specialist_on_soft:
                aw_penalty = base_going_pts
                score -= aw_penalty
                breakdown['going_suitability'] = -aw_penalty
                reasons.append(f"AW specialist ({aw_wins} AW wins, 0 turf) on soft ground: -{aw_penalty}pts")
            elif is_extreme and wins == 0:
                # No wins at all in extreme going = flag risk
                penalty = base_going_pts
                score -= penalty
                breakdown['going_suitability'] = -penalty
                reasons.append(f"No wins - unproven in {going_description}: -{penalty}pts")
            elif is_extreme and wins <= 1:
                # Limited form in extreme going = smaller risk flag
                penalty = base_going_pts // 2
                score -= penalty
                breakdown['going_suitability'] = -penalty
                reasons.append(f"Limited wins - questionable in {going_description}: -{penalty}pts")
            else:
                breakdown['going_suitability'] = 0
    else:
        # Track not in going data - use seasonal default (Feb = probably soft)
        current_month = datetime.now().month
        if current_month in [1, 2, 3, 11, 12]:  # Winter months
            # Soft is likely - only reward horses with multiple wins
            if wins >= 2:
                default_pts = base_going_pts // 2
                score += default_pts
                breakdown['going_suitability'] = default_pts
                reasons.append(f"Consistent form (going prob. soft in {datetime.now().strftime('%B')}): +{default_pts}pts")
            else:
                breakdown['going_suitability'] = 0
        else:
            breakdown['going_suitability'] = 0

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

    # 5b. GRADED RACE GOING PENALTY CORRECTION
    # If a going penalty was applied but the race is Graded (Grd1/2/3/Listed),
    # remove the penalty. Graded-class horses are prepared for all conditions;
    # penalising them based on limited form digits is a false negative.
    # Lesson: James Du Berlais (W. P. Mullins, Grd2 Navan, form 55-1632) won at
    # score 43 because we deducted 7pts going penalty from only 1 win in form.
    if is_graded_race and breakdown.get('going_suitability', 0) < 0:
        penalty_was = breakdown['going_suitability']
        score -= penalty_was   # undo the penalty (penalty_was is negative, so this adds back)
        breakdown['going_suitability'] = 0
        reasons = [r for r in reasons if 'questionable in' not in r and 'unproven in' not in r]
        reasons.append(f"Graded race - going penalty removed (elite field): 0pts")

    # 5c. C/D MARKER BONUS
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
        score += cd_pts
        breakdown['cd_bonus'] = cd_pts
        reasons.append(f"Course & Distance winner (CD): +{cd_pts}pts")
    elif 'C' in cd_marker:
        cd_pts = (base_cd // 2) + extra_cd
        score += cd_pts
        breakdown['cd_bonus'] = cd_pts
        reasons.append(f"Course winner (C): +{cd_pts}pts")
    elif 'D' in cd_marker:
        cd_pts = (base_cd // 2) + extra_cd
        score += cd_pts
        breakdown['cd_bonus'] = cd_pts
        reasons.append(f"Distance winner (D): +{cd_pts}pts")
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
                score += cd_pts
                breakdown['cd_bonus'] = cd_pts
                reasons.append(f"Course & Distance winner (from run history, C&D): +{cd_pts}pts")
            elif _c_win:
                cd_pts = base_cd // 2 + extra_cd
                score += cd_pts
                breakdown['cd_bonus'] = cd_pts
                reasons.append(f"Course winner (from run history, C): +{cd_pts}pts")
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
                    score += cd_pts
                    breakdown['cd_bonus'] = cd_pts
                    reasons.append(f"Course & Distance winner (SL run history, C&D): +{cd_pts}pts")
                elif _c3:
                    cd_pts = base_cd // 2 + extra_cd
                    score += cd_pts
                    breakdown['cd_bonus'] = cd_pts
                    reasons.append(f"Course winner (SL run history, C): +{cd_pts}pts")
                else:
                    breakdown['cd_bonus'] = 0
            elif not cd_pts:
                breakdown['cd_bonus'] = 0

    # 6. DATABASE HISTORY
    db = boto3.resource('dynamodb', region_name='eu-west-1')
    table = db.Table('SureBetBets')
    
    try:
        response = table.scan(
            FilterExpression='horse = :name',
            ExpressionAttributeValues={':name': name}
        )
        history = response.get('Items', [])
        history_wins = sum(1 for r in history if r.get('outcome') == 'win')
        history_losses = sum(1 for r in history if r.get('outcome') == 'loss')
        
        if history_wins > 0:
            score += 15
            breakdown['database_history'] = 15
            win_rate = (history_wins / (history_wins + history_losses) * 100) if (history_wins + history_losses) > 0 else 0
            reasons.append(f"Past wins in database ({history_wins}W-{history_losses}L = {win_rate:.0f}%): 15pts")
        else:
            breakdown['database_history'] = 0
    except:
        breakdown['database_history'] = 0
    
    # 7. TRACK PATTERN BONUS (Learning from today's earlier races at this track)
    if track_insights.get('has_data') and track_insights.get('suggested_boost'):
        pattern_bonus = 0
        
        for factor, boost_amount in track_insights['suggested_boost'].items():
            # Apply boost only if this horse scored in that factor
            if breakdown.get(factor, 0) > 0:
                pattern_bonus += boost_amount
        
        if pattern_bonus > 0:
            max_pattern_bonus = int(weights.get('track_pattern_bonus', 10))
            pattern_bonus = min(pattern_bonus, max_pattern_bonus)  # Cap at max
            score += pattern_bonus
            breakdown['track_pattern_bonus'] = pattern_bonus
            
            pattern_name = track_insights.get('dominant_pattern', 'pattern')
            races_analyzed = track_insights.get('races_analyzed', 0)
            reasons.append(f"Matches {pattern_name} (from {races_analyzed} races today): +{pattern_bonus}pts")
        else:
            breakdown['track_pattern_bonus'] = 0
    else:
        breakdown['track_pattern_bonus'] = 0
    
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
    
    # 11. NOVICE RACE PENALTY (NEW - Lesson from Ascot 13:15)
    novice_penalty = 0
    race_name = race_data.get('market_name', '') if 'race_data' in locals() else horse_data.get('race_type', '')
    if race_name and any(keyword in race_name.lower() for keyword in ['nov', 'novice', 'maiden']):
        novice_penalty = int(weights.get('novice_race_penalty', 15))
        score -= novice_penalty
        breakdown['novice_penalty'] = -novice_penalty
        reasons.append(f"⚠️ Novice race (less predictable): -{novice_penalty}pts")
    else:
        breakdown['novice_penalty'] = 0

    # 11b. LOW CLASS PENALTY (Lesson: 2026-02-28 Lingfield + 2026-03-16 Ffos Las 14:30)
    # Class 5/6 handicaps are designed by handicappers to produce unpredictable results.
    # AW Class 5/6: full penalty (going advantage = 0, form consistency unreliable).
    # Turf Class 5/6: reduced penalty — going still matters but fields are weaker/randomised.
    # Lesson: Queen Of Steel scored 99 but finished 3rd in Class 5 Soft, Hellfire Princess (67) won.
    aw_low_class_penalty = 0
    aw_marker = horse_data.get('race_class', horse_data.get('class', ''))
    aw_name_check = str(horse_data.get('race_name', horse_data.get('market_name', race_name))).lower()
    is_low_class = (
        str(aw_marker) in ['5', '6', 'Class 5', 'Class 6'] or
        'class 5' in aw_name_check or 'class 6' in aw_name_check or
        'class5' in aw_name_check or 'class6' in aw_name_check
    )
    _going_info_for_class = going_data.get(course, {})
    _is_aw_for_class = (
        _going_info_for_class.get('surface', '') == 'all-weather' or
        'Standard' in str(_going_info_for_class.get('going', ''))
    )
    if is_low_class:
        if _is_aw_for_class:
            # Full penalty on AW — no going edge AND handicapper-levelled field
            aw_low_class_penalty = int(weights.get('aw_low_class_penalty', 35))
            score -= aw_low_class_penalty
            breakdown['aw_low_class_penalty'] = -aw_low_class_penalty
            reasons.append(f"AW Class 5/6 (unpredictable handicap): -{aw_low_class_penalty}pts")
        else:
            # Reduced penalty on turf — going suitability still differentiates, but
            # Class 5 fields are weak and high scores are unreliable (Ffos Las 14:30 lesson)
            # RAISED 2026-04-01: Kingcormac (Class 5 turf) lost — turf Class 5 penalty was too lenient.
            # Now 70% of aw_low_class_penalty instead of 50%, making it 35pts (was 25pts).
            turf_class5_penalty = int(weights.get('aw_low_class_penalty', 50) * 7 // 10)
            score -= turf_class5_penalty
            breakdown['aw_low_class_penalty'] = -turf_class5_penalty
            reasons.append(f"Turf Class 5/6 (weaker field, results less predictable): -{turf_class5_penalty}pts")
    else:
        breakdown['aw_low_class_penalty'] = 0

    # 11c. AW EVENING RACING PENALTY (2026-03-25)
    # LESSON: Wolverhampton 20:00/20:30 — Burdett Estate (82/92) and Mr Nugget (87) all lost.
    # Evening AW races have inflated form signals: small fields, gambled-on horses, track bias
    # invisible at booking time.  Apply discount to any AW race starting after 17:30.
    _AW_EVENING_VENUES = {'wolverhampton', 'kempton', 'kempton park', 'chelmsford', 'chelmsford city',
                          'lingfield', 'lingfield park', 'southwell', 'windsor'}
    _race_time_str = str(horse_data.get('race_time', '')).strip()
    _is_aw_venue = course.lower() in _AW_EVENING_VENUES
    _is_evening = False
    if _race_time_str:
        try:
            from datetime import datetime as _dt_ev, timezone as _tz_ev, timedelta as _td_ev
            import calendar as _cal_ev, re as _re
            # Parse race_time as UTC-aware (race_time is always stored as UTC +00:00)
            # Convert to UK local time (GMT=UTC, BST=UTC+1) before applying the 17:30 threshold.
            # Bug fix: checking raw UTC hour vs 17:30 missed races at 16:30–17:30 UTC in BST.
            def _uk_evening_mins(rt_str):
                try:
                    d = _dt_ev.fromisoformat(rt_str.replace('Z', '+00:00'))
                    if d.tzinfo is None:
                        d = d.replace(tzinfo=_tz_ev.utc)
                    d_utc = d.astimezone(_tz_ev.utc)
                    # Compute BST start/end for this year (last Sunday of March/October at 01:00 UTC)
                    def _last_sun(y, m):
                        last = _cal_ev.monthrange(y, m)[1]
                        return next(day for day in range(last, last-7, -1)
                                    if _dt_ev(y, m, day).weekday() == 6)
                    bst_on  = _dt_ev(d_utc.year, 3,  _last_sun(d_utc.year, 3),  1, tzinfo=_tz_ev.utc)
                    bst_off = _dt_ev(d_utc.year, 10, _last_sun(d_utc.year, 10), 1, tzinfo=_tz_ev.utc)
                    uk_off  = 1 if bst_on <= d_utc < bst_off else 0
                    local   = d_utc + _td_ev(hours=uk_off)
                    return local.hour * 60 + local.minute
                except Exception:
                    # Fallback: raw HH:MM regex (legacy format)
                    m2 = _re.search(r'(\d{1,2}):(\d{2})', rt_str)
                    return int(m2.group(1)) * 60 + int(m2.group(2)) if m2 else 0
            _total_mins = _uk_evening_mins(_race_time_str)
            _is_evening = _total_mins >= 17 * 60 + 30   # 17:30 UK local time
        except Exception:
            pass
    _aw_evening_penalty = 0
    if _is_aw_venue and _is_evening:
        _aw_evening_penalty = int(weights.get('aw_evening_penalty', 12))
        score -= _aw_evening_penalty
        breakdown['aw_evening_penalty'] = -_aw_evening_penalty
        reasons.append(f"⚠️ AW evening racing ({course} {_race_time_str[:5]}): -{_aw_evening_penalty}pts")
    else:
        breakdown['aw_evening_penalty'] = 0

    # 11d. UNKNOWN TRAINER PENALTY (2026-03-25)
    # LESSON: Brian Toomey, D M Simcock, K Woollacott — not in any trainer tier.
    # Horses from unlisted trainers score via form/odds only; reliability is lower.
    # 2026-04-13: OurHub integration — if we have real trainer win-rate data, use it
    # instead of blindly penalising. >20% win rate = award T2-equivalent bonus,
    # >12% = no penalty, otherwise keep the penalty.
    if trainer and trainer_tier == 0 and trainer_bonus == 0:
        _oh_twr = horse_data.get('ourhub_trainer_win_rate', 0)
        _oh_truns = horse_data.get('ourhub_trainer_runs', 0)
        if _oh_twr and _oh_truns >= 10:
            # Enough data from OurHub to make a call
            if _oh_twr >= 20:
                # Strong trainer — give T2-equivalent bonus instead of penalty
                _oh_bonus = int(weights.get('trainer_tier2', 8))
                score += _oh_bonus
                breakdown['unknown_trainer_penalty'] = _oh_bonus
                reasons.append(f"📡 OurHub: {trainer} {_oh_twr:.0f}% win rate ({_oh_truns} runs): +{_oh_bonus}pts")
            elif _oh_twr >= 12:
                # Decent trainer — no penalty
                breakdown['unknown_trainer_penalty'] = 0
                reasons.append(f"📡 OurHub: {trainer} {_oh_twr:.0f}% win rate ({_oh_truns} runs) — penalty waived")
            else:
                # Low win rate — keep penalty
                _utp = int(weights.get('unknown_trainer_penalty', 8))
                score -= _utp
                breakdown['unknown_trainer_penalty'] = -_utp
                reasons.append(f"📡 OurHub: {trainer} {_oh_twr:.0f}% win rate ({_oh_truns} runs): -{_utp}pts")
        else:
            _utp = int(weights.get('unknown_trainer_penalty', 8))
            score -= _utp
            breakdown['unknown_trainer_penalty'] = -_utp
            reasons.append(f"Unknown trainer tier ({trainer}): -{_utp}pts")
    else:
        breakdown['unknown_trainer_penalty'] = 0

    # 11e. IRISH HANDICAP VENUE PENALTY (2026-04-01)
    # LESSON: Dmaniac (Curragh, sc=107, no market leader) and I'm Spartacus (Dundalk, sc=84)
    # both lost. Irish flat/NH handicaps at these venues are notoriously competitive with
    # very tight weights and large fields. Our form model works but top-score picks at Irish
    # handicap tracks without market backing are less reliable.
    _IRISH_HANDICAP_VENUES = {
        'curragh', 'dundalk', 'navan', 'naas', 'leopardstown', 'cork',
        'galway', 'tipperary', 'punchestown', 'killarney', 'gowran',
        'bellewstown', 'roscommon', 'tramore', 'ballinrobe', 'sligo',
        'fairyhouse', 'listowel', 'down royal', 'downroyal',
    }
    _race_name_for_hcap = str(horse_data.get('race_name', horse_data.get('market_name', ''))).lower()
    _is_handicap = (
        'handicap' in _race_name_for_hcap or ' hcap' in _race_name_for_hcap or
        _race_name_for_hcap.endswith('hcap') or ' h ' in _race_name_for_hcap
    )
    _is_irish_venue = course.lower().strip() in _IRISH_HANDICAP_VENUES
    _irish_hcap_penalty = 0
    if _is_irish_venue and _is_handicap:
        _irish_hcap_penalty = int(weights.get('irish_handicap_penalty', 10))
        score -= _irish_hcap_penalty
        breakdown['irish_handicap_penalty'] = -_irish_hcap_penalty
        reasons.append(f"⚠️ Irish handicap ({course}) — competitive field, reduced confidence: -{_irish_hcap_penalty}pts")
    else:
        breakdown['irish_handicap_penalty'] = 0

    # 12. BOUNCE-BACK PATTERN (NEW - Lesson from Ascot 13:15)
    # Detect patterns like 2-6-1 or 2-5-1 showing recovery after poor run
    bounce_back_pts = int(weights.get('bounce_back_bonus', 12))
    if form:
        form_parts = form.split('-')
        if len(form_parts) >= 3:
            try:
                # Check last 3 runs: [good]-[bad]-[better]
                last_3 = form_parts[-3:]
                if (last_3[0] in ['1', '2', '3'] and  # Started well
                    last_3[1] in ['5', '6', '7', '8', '9', '0'] and  # Poor run
                    last_3[2] in ['1', '2', '3']):  # Recovered
                    score += bounce_back_pts
                    breakdown['bounce_back'] = bounce_back_pts
                    reasons.append(f"📈 Bounce-back pattern ({'-'.join(last_3)}): +{bounce_back_pts}pts")
                else:
                    breakdown['bounce_back'] = 0
            except:
                breakdown['bounce_back'] = 0
        else:
            breakdown['bounce_back'] = 0
    else:
        breakdown['bounce_back'] = 0
    
    # 13. SHORT FORM IMPROVEMENT (Updated 2026-03-25)
    # LESSON: Isabella Islay (4yo, form='93') improved 9th→3rd but scored 0 here
    # because (a) the race wasn't flagged as novice, (b) old code required '2' in form.
    # Now ALSO fires for young horses (≤5yo) showing clear position improvement in short form.
    short_form_pts = int(weights.get('short_form_improvement', 10))
    if form:
        _sfi_chars = form.replace('-', '')
        _sfi_len   = len(_sfi_chars)
        _last_run  = _sfi_chars[-1] if _sfi_len >= 1 else ''
        _prev_run  = _sfi_chars[-2] if _sfi_len >= 2 else ''
        _sfi_age   = None
        try:
            _sfi_age = int(horse_data.get('age', 0) or 0)
        except (TypeError, ValueError):
            pass
        if novice_penalty < 0 and _sfi_len <= 3 and '2' in form:
            # Original: novice race with a 2nd-place in short form
            score += short_form_pts
            breakdown['short_form_improvement'] = short_form_pts
            reasons.append(f"🌟 Limited form in novice (improving?): +{short_form_pts}pts")
        elif (_sfi_age and _sfi_age <= 5 and _sfi_len <= 4 and
              _last_run in ('1', '2', '3') and _prev_run and _prev_run > _last_run):
            # NEW: Young horse showing clear improvement in last 2 runs (e.g. 9→3, 8→2, 5→1)
            score += short_form_pts
            breakdown['short_form_improvement'] = short_form_pts
            reasons.append(f"🌟 Young horse improving ({_prev_run}→{_last_run}, last 2 runs): +{short_form_pts}pts")
        else:
            breakdown['short_form_improvement'] = 0
    else:
        breakdown['short_form_improvement'] = 0
    
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

    # 14c. JOCKEY-COURSE FAMILIARITY — bonus if jockey has won here before
    jc_bonus_pts = int(weights.get('jockey_course_bonus', 8))
    jockey_for_course = str(horse_data.get('jockey', '')).strip()
    if jockey_for_course and course:
        try:
            jc_key = f"JOCKEY_COURSE_{jockey_for_course.replace(' ', '_')}_{course.replace(' ', '_')}"
            _db_jc = boto3.resource('dynamodb', region_name='eu-west-1')
            _tbl_jc = _db_jc.Table('SureBetBets')
            jc_resp = _tbl_jc.get_item(Key={'bet_id': jc_key, 'bet_date': 'HISTORY'})
            jc_item = jc_resp.get('Item', {})
            jc_wins = int(jc_item.get('course_wins', 0))
            jc_runs = int(jc_item.get('course_runs', 0))
            if jc_runs >= 2 and jc_wins >= 1:
                jc_win_rate = jc_wins / jc_runs
                if jc_win_rate >= 0.30:
                    jc_pts = jc_bonus_pts
                elif jc_win_rate >= 0.15:
                    jc_pts = jc_bonus_pts // 2
                else:
                    jc_pts = 0
                if jc_pts > 0:
                    score += jc_pts
                    breakdown['jockey_course_bonus'] = jc_pts
                    reasons.append(f"Jockey {jockey_for_course} {jc_wins}/{jc_runs} wins at {course}: +{jc_pts}pts")
                else:
                    breakdown['jockey_course_bonus'] = 0
            else:
                breakdown['jockey_course_bonus'] = 0
        except Exception:
            breakdown['jockey_course_bonus'] = 0
    else:
        breakdown['jockey_course_bonus'] = 0

    # 14d. MEETING FOCUS SIGNALS (2026-03-19)
    # Trainer or jockey appearing ONLY at this meeting today signals a targeted, focused effort.
    # If they're not spread across multiple meetings they likely fancy this horse.
    # meeting_context must be pre-built by the caller (workflow) before scoring begins.
    if meeting_context:
        t = str(horse_data.get('trainer', '')).strip()
        j = str(horse_data.get('jockey', '')).strip()
        focus_pts = 0
        focus_reasons = []

        # Signal 1: Trainer's only horse at this meeting today across ALL meetings
        trainer_meetings = meeting_context.get('trainer_meetings', {})  # trainer -> set of courses
        if t and t in trainer_meetings and len(trainer_meetings[t]) == 1:
            sig1_pts = int(weights.get('meeting_focus_trainer', 10))
            focus_pts += sig1_pts
            focus_reasons.append(f"Trainer sole at {course} today (focused effort): +{sig1_pts}pts")

        # Signal 2: Jockey only rides at this meeting today (not spread across multiple courses)
        jockey_meetings = meeting_context.get('jockey_meetings', {})  # jockey -> set of courses
        if j and j in jockey_meetings and len(jockey_meetings[j]) == 1:
            sig2_pts = int(weights.get('meeting_focus_jockey', 10))
            focus_pts += sig2_pts
            focus_reasons.append(f"Jockey committed to {course} only today: +{sig2_pts}pts")

        # Signal 3: Trainer+jockey combo only paired at this meeting today
        combo_meetings = meeting_context.get('combo_meetings', {})  # (trainer,jockey) -> set of courses
        combo_key = f"{t}|{j}"
        if t and j and combo_key in combo_meetings and len(combo_meetings[combo_key]) == 1:
            sig3_pts = int(weights.get('meeting_focus_combo', 10))
            focus_pts += sig3_pts
            focus_reasons.append(f"Trainer/jockey duo solely at {course} today: +{sig3_pts}pts")

        # Signal 4: New trainer debut — horse has no prior DB pick with this trainer
        new_trainer_horses = meeting_context.get('new_trainer_horses', set())
        horse_trainer_key = f"{name}|{t}"
        if horse_trainer_key in new_trainer_horses:
            sig4_pts = int(weights.get('new_trainer_debut', 5))
            focus_pts += sig4_pts
            focus_reasons.append(f"Debut run for new trainer {t}: +{sig4_pts}pts")

        # LESSON 2026-03-22: trainer+jockey+combo each fired separately = 30pts for small NH yards
        # where trainer/jockey always run exclusively at their local track. These three signals are
        # not independent — if trainer is sole at course AND jockey is sole at course, the combo is
        # definitionally true. Take MAX, not sum.
        if focus_pts > 0:
            # Cap: take value of whichest single signal fired rather than additive sum
            max_single = max(
                int(weights.get('meeting_focus_trainer', 10)) if any('sole at' in r for r in focus_reasons) else 0,
                int(weights.get('meeting_focus_jockey', 10)) if any('committed to' in r for r in focus_reasons) else 0,
                int(weights.get('meeting_focus_combo', 10)) if any('duo solely' in r for r in focus_reasons) else 0,
            )
            focus_pts = max_single
            score += focus_pts
            breakdown['meeting_focus'] = focus_pts
            reasons.append(focus_reasons[0])  # report only highest-priority signal
        else:
            breakdown['meeting_focus'] = 0
    else:
        breakdown['meeting_focus'] = 0

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
    if (_uex_age and _uex_age <= 5 and _uex_runs <= 5
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
            score += form_detail_pts
            breakdown['deep_form'] = form_detail_pts
        else:
            breakdown['deep_form'] = 0
    else:
        breakdown['deep_form'] = 0

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

    # LARGE-FIELD PENALTY (2026-03-29)
    # LESSON: Saturday analysis (21 settled picks) showed losers averaged 94.2pts —
    # only 9.3pts below winners. In 16+ runner fields pace/draw/traffic dominate form
    # signals and the model cannot discriminate reliably. Apply a structural discount.
    if n_runners >= 20:
        _lfp = int(weights.get('large_field_penalty', 10)) + 8  # -18 for 20+ runners
        score -= _lfp
        breakdown['large_field_penalty'] = -_lfp
        reasons.append(f"Large field ({n_runners} runners) — high variance, draw/pace unknown: -{_lfp}pts")
    elif n_runners >= 16:
        _lfp = int(weights.get('large_field_penalty', 10))       # -10 for 16-19 runners
        score -= _lfp
        breakdown['large_field_penalty'] = -_lfp
        reasons.append(f"Big field ({n_runners} runners) — above-average variance: -{_lfp}pts")
    else:
        breakdown['large_field_penalty'] = 0

    # SMALL FIELD TACTICAL BONUS (2026-04-07)
    # PROFESSIONAL WORKFLOW LESSON: Pro explicitly selects Ascot 3:45 (6 runners) BECAUSE
    # small fields have high predictability — fewer variables, form reads more reliably,
    # pace dynamics clearer, class/quality differences more decisive.
    # Source: Modern Pace Handicapping — "race shape determines winners more in large fields
    # than small ones; small fields reward handicapping accuracy."
    # 4-6 runners: highest predictability window — tactical races, class tells.
    # 7-8 runners: moderate boost — field still manageable.
    # Requires the pick NOT to be in a bumper/NHF (shallow form pool).
    _sf_market = str(horse_data.get('race_name', horse_data.get('market_name', ''))).lower()
    _is_nh_sf  = any(x in _sf_market for x in ['hurdle', 'chase', 'nhf', 'bumper', 'national hunt'])
    if not _is_nh_sf:
        if 4 <= n_runners <= 6:
            _sfb = 7
            score += _sfb
            breakdown['small_field_bonus'] = _sfb
            reasons.append(f"Small field ({n_runners} runners) — high tactical predictability: +{_sfb}pts")
        elif 7 <= n_runners <= 8:
            _sfb = 4
            score += _sfb
            breakdown['small_field_bonus'] = _sfb
            reasons.append(f"Manageable field ({n_runners} runners) — cleaner form read: +{_sfb}pts")
        else:
            breakdown['small_field_bonus'] = 0
    else:
        breakdown['small_field_bonus'] = 0

    # 15. DRAW BIAS — UK/Irish track-specific stall advantage/disadvantage
    # Source: well-documented published draw statistics for UK/Irish flat tracks.
    # Only applies to flat races where stall draw is meaningful.
    # NH racing (hurdles/chases/bumpers) has no meaningful draw bias.
    # Requires stall draw to be populated AND field size >= 6 runners.
    _draw_bias_pts = 0
    _draw_str = str(horse_data.get('draw', '') or '').strip()
    _market_for_draw = str(horse_data.get('race_name', horse_data.get('market_name', ''))).lower()
    _is_nh_draw = any(x in _market_for_draw for x in ['hurdle', 'chase', 'nhf', 'bumper', 'national hunt'])
    try:
        _draw_num = int(_draw_str)
    except (ValueError, TypeError):
        _draw_num = 0

    if _draw_num > 0 and n_runners >= 6 and not _is_nh_draw:
        # Relative draw position: 0.0 = stall 1 (widest inside), 1.0 = highest stall (widest outside)
        _draw_rel = (_draw_num - 1) / max(n_runners - 1, 1)
        _draw_low  = _draw_rel <= 0.30   # bottom 30% of stalls
        _draw_high = _draw_rel > 0.70    # top 30% of stalls
        _course_l  = course.lower().strip()

        # Determine race distance from market_name (e.g. "7f Hcap", "1m2f Chase")
        import re as _re_draw
        _dist_match = _re_draw.search(r'(\d+)f', _market_for_draw)
        _dist_f = int(_dist_match.group(1)) if _dist_match else 16
        _is_sprint_draw = _dist_f <= 7   # sprints most affected by draw

        # ── EXTREME low-draw bias (very tight tracks) ─────────────────────
        # Chester: hairpin bends, stall 1 worth multiple lengths. Zero disadvantage
        #          is acceptable up to stall 8; anything 9+ rapidly worse.
        # Pontefract: tight left-hand oval with uphill finish. Low draw critical.
        if _course_l in {'chester', 'pontefract'}:
            if _draw_low:
                _draw_bias_pts = 10
                reasons.append(f"Low draw advantage at {course} (stall {_draw_num}/{n_runners}): +{_draw_bias_pts}pts")
            elif _draw_high:
                _draw_bias_pts = -8
                reasons.append(f"High draw disadvantage at {course} (stall {_draw_num}/{n_runners}): {_draw_bias_pts}pts")

        # ── Standard LOW-draw bias ────────────────────────────────────────
        # AW round tracks: inside rail saves ground. Sprint distances especially.
        # Carlisle, York, Hamilton: low-draw advantage on sprint tracks.
        elif _course_l in {'wolverhampton', 'lingfield', 'lingfield park', 'kempton', 'kempton park',
                           'chelmsford', 'chelmsford city', 'southwell', 'york', 'carlisle',
                           'hamilton', 'thirsk', 'leicester', 'chepstow', 'naas', 'dundalk'}:
            if _draw_low and _is_sprint_draw:
                _draw_bias_pts = 6
                reasons.append(f"Low draw advantage at {course} sprint (stall {_draw_num}/{n_runners}): +{_draw_bias_pts}pts")
            elif _draw_high and n_runners >= 8 and _is_sprint_draw:
                _draw_bias_pts = -4
                reasons.append(f"High draw disadvantage at {course} sprint (stall {_draw_num}/{n_runners}): {_draw_bias_pts}pts")

        # ── HIGH-draw bias ────────────────────────────────────────────────
        # Ascot straight (5-6f): stands-side rail (high stalls) overwhelmingly favoured
        #   in fields of 12+. Rowley Mile Newmarket: stands side (high draw) in 6f+ races.
        # Beverley: high draw advantage on stiff uphill finish.
        elif _course_l in {'ascot', 'newmarket', 'beverley', 'curragh'}:
            if _draw_high:
                # More important in larger fields
                _hd_bonus = 8 if n_runners >= 12 else 5
                _draw_bias_pts = _hd_bonus
                reasons.append(f"High draw advantage at {course} (stall {_draw_num}/{n_runners}, stands side): +{_draw_bias_pts}pts")
            elif _draw_low and n_runners >= 12 and _is_sprint_draw:
                _draw_bias_pts = -5
                reasons.append(f"Low draw disadvantage at {course} (stall {_draw_num}/{n_runners}): {_draw_bias_pts}pts")

    if _draw_bias_pts != 0:
        score += _draw_bias_pts
        breakdown['draw_bias'] = _draw_bias_pts
    else:
        breakdown['draw_bias'] = 0

    # 16. TRACK HANDEDNESS PREFERENCE
    # Some horses consistently run better on left-handed tracks vs right-handed.
    # Detected from form_runs course history if available.
    # UK left-handed: Ascot, Cheltenham, Goodwood, Epsom, Lingfield, Kempton,
    #   Sandown, Windsor, Chepstow, Exeter, Hereford, Newbury, Nottingham
    # UK right-handed: Newmarket, York, Doncaster, Chester, Haydock, Pontefract,
    #   Carlisle, Hamilton, Beverley, Catterick, Newcastle, Ripon, Leeds
    _LEFT_HANDED  = {'ascot', 'cheltenham', 'goodwood', 'epsom', 'lingfield', 'lingfield park',
                     'kempton', 'kempton park', 'sandown', 'sandown park', 'windsor', 'chepstow',
                     'exeter', 'hereford', 'newbury', 'nottingham', 'leicester', 'brighton',
                     'plumpton', 'huntingdon', 'fakenham', 'market rasen', 'towcester',
                     'leopardstown', 'punchestown', 'cork', 'tipperary', 'killarney',
                     'gowran', 'gowran park', 'tramore', 'bellewstown', 'sligo'}
    _RIGHT_HANDED = {'newmarket', 'york', 'doncaster', 'chester', 'haydock', 'haydock park',
                     'pontefract', 'carlisle', 'hamilton', 'beverley', 'catterick', 'newcastle',
                     'ripon', 'thirsk', 'musselburgh', 'ayr', 'wolverhampton', 'southwell',
                     'chelmsford', 'chelmsford city', 'wincanton', 'taunton',
                     'curragh', 'dundalk', 'naas', 'navan', 'fairyhouse', 'galway',
                     'roscommon', 'listowel', 'ballinrobe', 'down royal', 'downroyal'}
    _today_handed = ('L' if course.lower().strip() in _LEFT_HANDED else
                     'R' if course.lower().strip() in _RIGHT_HANDED else None)
    _form_runs_h = horse_data.get('form_runs', [])
    if _today_handed and _form_runs_h and len(_form_runs_h) >= 3:
        _wins_same, _wins_opp, _runs_same, _runs_opp = 0, 0, 0, 0
        for _fr in _form_runs_h:
            _fr_course = str(_fr.get('course', '')).lower().strip()
            _fr_fin    = str(_fr.get('finish_position', '') or '').strip()
            _fr_won    = _fr_fin == '1'
            if _fr_course in _LEFT_HANDED:
                _fr_hand = 'L'
            elif _fr_course in _RIGHT_HANDED:
                _fr_hand = 'R'
            else:
                continue
            if _fr_hand == _today_handed:
                _runs_same += 1
                if _fr_won: _wins_same += 1
            else:
                _runs_opp += 1
                if _fr_won: _wins_opp += 1
        # Only reward if horse has meaningful history on both types
        if _runs_same >= 2 and _runs_opp >= 2:
            _sr_same = _wins_same / _runs_same
            _sr_opp  = _wins_opp  / _runs_opp
            if _sr_same >= 0.35 and _sr_same > (_sr_opp + 0.15):
                _hand_pts = 8
                score += _hand_pts
                breakdown['track_handedness'] = _hand_pts
                _hand_label = 'left' if _today_handed == 'L' else 'right'
                reasons.append(f"Proven on {_hand_label}-handed tracks ({_wins_same}/{_runs_same} wins "
                               f"vs {_wins_opp}/{_runs_opp} other direction): +{_hand_pts}pts")
            elif _sr_opp >= 0.35 and _sr_opp > (_sr_same + 0.15):
                _hand_pen = -6
                score += _hand_pen
                breakdown['track_handedness'] = _hand_pen
                _hand_label = 'left' if _today_handed == 'L' else 'right'
                reasons.append(f"⚠️ Poor record on {_hand_label}-handed tracks ({_wins_same}/{_runs_same} wins "
                               f"vs {_wins_opp}/{_runs_opp} better direction): {_hand_pen}pts")
            else:
                breakdown['track_handedness'] = 0
        else:
            breakdown['track_handedness'] = 0
    else:
        breakdown['track_handedness'] = 0

    # 17. PACE PROFILE — DISTANCE SPECIALISATION
    # Source: Modern Pace Handicapping — horses have metabolic specialisations for
    # distance ranges. Sprinters (≤7f) lack stamina for middle distances; stayers
    # (12f+) lack the pace for sprints. Out-of-range selections carry structural risk.
    # We proxy "running style" from career distance history: if a horse's proven winning
    # distance average diverges significantly from today's trip, apply a pace discount.
    # Data required: form_runs (position + distance_f per run).
    _pr_runs = horse_data.get('form_runs', [])
    _win_dists = []
    _all_dists  = []
    for _pr in _pr_runs:
        _d = _pr.get('distance_f')
        if _d:
            _all_dists.append(float(_d))
            if _pr.get('position') == 1:
                _win_dists.append(float(_d))

    # Re-parse today's distance (furlongs) from market_name — same source as section 15
    import re as _re_pace
    _pace_dist_match = _re_pace.search(
        r'(\d+(?:\.\d+)?)f',
        str(horse_data.get('race_name', horse_data.get('market_name', ''))).lower()
    )
    _today_dist_pace = float(_pace_dist_match.group(1)) if _pace_dist_match else None

    _pace_pts = 0
    if _today_dist_pace and _win_dists and len(_all_dists) >= 3:
        _avg_win_dist = sum(_win_dists) / len(_win_dists)
        _dist_gap = _today_dist_pace - _avg_win_dist

        # STAMINA CONCERN: stepping up 4+ furlongs beyond proven winning distance.
        # Example: sprinter that wins at 5-6f asks to stay 10f — metabolically wrong.
        if _dist_gap >= 4.0:
            _pace_pts = -6
            reasons.append(
                f"Stamina concern: avg win dist {_avg_win_dist:.1f}f, today {_today_dist_pace:.0f}f "
                f"(+{_dist_gap:.0f}f step-up beyond proven zone): {_pace_pts}pts"
            )
        # PACE CONCERN: dropping 4+ furlongs below proven winning distance.
        # Example: stayer that wins at 12-16f racing over 8f — pace demands are alien.
        elif _dist_gap <= -4.0:
            _pace_pts = -4
            reasons.append(
                f"Pace concern: avg win dist {_avg_win_dist:.1f}f, today {_today_dist_pace:.0f}f "
                f"({abs(_dist_gap):.0f}f below specialisation): {_pace_pts}pts"
            )
        # PROVEN ZONE: within 1f of average winning distance — horse knows this trip.
        # Small bonus for proven stamina at exactly today's distance range.
        elif abs(_dist_gap) <= 1.0:
            _pace_pts = 4
            reasons.append(
                f"In proven distance zone ({_today_dist_pace:.0f}f vs avg win {_avg_win_dist:.1f}f): "
                f"+{_pace_pts}pts"
            )

    if _pace_pts != 0:
        score += _pace_pts
    breakdown['pace_profile'] = _pace_pts

    # ── LIVE TRAINER / JOCKEY HOT FORM (2026-03-30) ─────────────────────────
    # Use rolling 30-day DynamoDB results to detect trainers/jockeys on a hot streak
    # (+8/+6 pts) or cold streak (-5/-3 pts).  Does NOT require a static tier list.
    if TRAINER_FORM_AVAILABLE:
        _hf_pts, _hf_bd, _hf_rsns = _hot_form_bonus(
            str(horse_data.get('trainer', '') or ''),
            str(horse_data.get('jockey', '')  or ''),
        )
        if _hf_pts != 0:
            score += _hf_pts
            breakdown.update(_hf_bd)
            reasons.extend(_hf_rsns)
        else:
            breakdown['trainer_hot_form'] = 0
            breakdown['jockey_hot_form']  = 0
    else:
        breakdown['trainer_hot_form'] = 0
        breakdown['jockey_hot_form']  = 0

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
    
    course_stats: {'avg_winner_odds': 4.65, 'winners_today': 4}
    Returns: best_pick dict or None if race should be skipped
    """
    if course_stats is None:
        course_stats = {'avg_winner_odds': 4.65, 'winners_today': 0}
    
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
            avg_winner_odds=course_stats.get('avg_winner_odds', 4.65),
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
            'avg_winner_odds': 4.65,  # Average of 10 winners today
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
