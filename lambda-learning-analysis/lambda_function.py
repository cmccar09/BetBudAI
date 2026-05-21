#!/usr/bin/env python3
"""
Lambda: Daily Training & Learning Analysis
Runs HOURLY to continuously analyze race results and improve strategy
TRAINS DAILY to progressively achieve GREEN status picks (75%+ confidence, 20%+ ROI)
Generates insights with detailed loss analysis and pattern recognition
Updates after every result batch for real-time learning
"""

import os
import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('SUREBET_DDB_TABLE', 'SureBetBets')
learning_table_name = os.environ.get('LEARNING_TABLE', 'BettingPerformance')

# GREEN STATUS THRESHOLDS (Progressive Goals)
GREEN_CONFIDENCE_MIN = 75.0  # High confidence
GREEN_ROI_MIN = 20.0  # Strong value
HIGH_CONFIDENCE_MIN = 60.0
MODERATE_CONFIDENCE_MIN = 45.0

def get_results_for_period(days=7):
    """Get all bets with results from last N days"""
    table = dynamodb.Table(table_name)
    
    all_results = []
    
    for days_ago in range(days):
        date = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        try:
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                FilterExpression='attribute_exists(actual_result) AND track_performance = :track',
                ExpressionAttributeValues={':date': date, ':track': True}
            )
            all_results.extend(response.get('Items', []))
        except Exception as e:
            print(f"Error querying {date}: {e}")
    
    print(f"Found {len(all_results)} bets with results from last {days} days")
    return all_results

def analyze_performance(results):
    """Analyze what's working and what's not"""
    
    analysis = {
        'overall': {
            'total_bets': len(results),
            'total_stake': 0,
            'total_pnl': 0,
            'wins': 0,
            'places': 0,
            'losses': 0,
            'win_rate': 0,
            'place_rate': 0,
            'roi': 0
        },
        'by_odds_range': defaultdict(lambda: {
            'count': 0, 'stake': 0, 'pnl': 0, 'wins': 0
        }),
        'by_course': defaultdict(lambda: {
            'count': 0, 'stake': 0, 'pnl': 0, 'wins': 0
        }),
        'by_bet_type': defaultdict(lambda: {
            'count': 0, 'stake': 0, 'pnl': 0, 'wins': 0
        }),
        'by_decision_rating': defaultdict(lambda: {
            'count': 0, 'stake': 0, 'pnl': 0, 'wins': 0
        }),
        'loss_analysis': {
            'total_losses': 0,
            'loss_amount': 0,
            'common_patterns': [],
            'favorites_lost': 0,  # Horses with odds < 3.0
            'longshots_lost': 0,  # Horses with odds > 8.0
            'high_confidence_losses': 0,  # Lost despite >70% confidence
            'do_it_losses': 0,  # Lost despite 'DO IT' rating
            'by_position': defaultdict(int),  # Track finishing positions
        },
        'favorite_analysis': {
            # Track favorite (odds <3.0) vs non-favorite performance separately
            'favorites_backed': 0,
            'favorites_won': 0,
            'favorites_win_rate': 0,
            'favorites_roi': 0,
            'favorites_total_stake': 0,
            'favorites_total_pnl': 0,
            'non_favorites_backed': 0,
            'non_favorites_won': 0,
            'non_favorites_win_rate': 0,
            'non_favorites_roi': 0,
            'non_favorites_total_stake': 0,
            'non_favorites_total_pnl': 0,
            # Value opportunities when favorite fails
            'favorite_failure_opportunities': 0,  # Times we backed non-fav and it won
            'favorite_failure_capture_rate': 0,  # % of non-fav wins we captured
        },
        'strategic_behavior': {
            # Detect trainers/jockeys "hiding form" in small races to boost odds for bigger events
            'trainer_patterns': defaultdict(lambda: {
                'small_race_performance': [],  # Track performance in low-value races
                'big_race_performance': [],    # Track performance in high-value races
                'elite_race_performance': [],  # Track performance in Group 1/2/3, major meetings
                'improvement_after_poor': 0,   # Count dramatic improvements
                'suspicious_patterns': 0       # Flag potential form hiding
            }),
            'class_drops_won': 0,      # Won after moving down in class
            'class_rises_won': 0,      # Won after moving up in class
            'prep_race_losses': 0,     # Lost in small races before big target
            'follow_up_wins': 0,       # Won big race after "prep" loss
            'hiding_form_flags': [],   # List of suspicious patterns detected
            'elite_races': {           # Group 1/2/3 and major meetings (everyone trying!)
                'total': 0,
                'won': 0,
                'win_rate': 0,
                'roi': 0,
                'total_stake': 0,
                'total_pnl': 0
            }
        }
    }
    
    for result in results:
        stake = float(result.get('stake', 0))
        pnl = float(result.get('pnl', 0))
        odds = float(result.get('odds', 0))
        is_winner = result.get('is_winner', False)
        is_placed = result.get('is_placed', False)
        course = result.get('course', 'Unknown')
        bet_type = result.get('bet_type', 'WIN')
        decision_rating = result.get('decision_rating', 'UNKNOWN')
        confidence = float(result.get('confidence', 0))
        actual_position = result.get('actual_position', 'Unknown')
        trainer = result.get('trainer', 'Unknown')
        jockey = result.get('jockey', 'Unknown')
        race_class = result.get('race_class', 'Unknown')
        prize_money = float(result.get('prize_money', 0))
        course = result.get('course', 'Unknown').upper()
        
        # Major meetings where EVERYONE tries hard (no form hiding)
        major_meetings = [
            'CHELTENHAM', 'ASCOT', 'AINTREE', 'GOODWOOD', 'EPSOM', 'YORK',
            'NEWMARKET', 'DONCASTER', 'CURRAGH', 'LEOPARDSTOWN', 'PUNCHESTOWN'
        ]
        is_major_meeting = any(meeting in course for meeting in major_meetings)
        
        # Classify race importance (3 tiers)
        # ELITE: Group 1/2/3, major meetings - EVERYONE trying to win!
        is_elite_race = (
            'GROUP 1' in race_class.upper() or 'GRADE 1' in race_class.upper() or
            'GROUP 2' in race_class.upper() or 'GRADE 2' in race_class.upper() or
            'GROUP 3' in race_class.upper() or 'GRADE 3' in race_class.upper() or
            is_major_meeting and prize_money > 30000
        )
        
        # SMALL: Prep races, form hiding likely
        is_small_race = prize_money < 5000 or 'SELLING' in race_class.upper() or 'CLAIMING' in race_class.upper()
        
        # BIG: Competitive but not elite
        is_big_race = not is_elite_race and (prize_money > 15000 or 'LISTED' in race_class.upper() or 'STAKES' in race_class.upper())
        
        # Overall stats
        analysis['overall']['total_stake'] += stake
        analysis['overall']['total_pnl'] += pnl
        if is_winner:
            analysis['overall']['wins'] += 1
        elif is_placed:
            analysis['overall']['places'] += 1
        else:
            analysis['overall']['losses'] += 1            
            # DETAILED LOSS ANALYSIS
            analysis['loss_analysis']['total_losses'] += 1
            analysis['loss_analysis']['loss_amount'] += abs(pnl)
            
            # Track finish position for losses
            if actual_position != 'Unknown':
                analysis['loss_analysis']['by_position'][str(actual_position)] += 1
            
            # Categorize types of losses
            if odds < 3.0:
                analysis['loss_analysis']['favorites_lost'] += 1
            elif odds > 8.0:
                analysis['loss_analysis']['longshots_lost'] += 1
            
            if confidence > 70:
                analysis['loss_analysis']['high_confidence_losses'] += 1
            
            if decision_rating == 'DO IT':
                analysis['loss_analysis']['do_it_losses'] += 1        
        
        # FAVORITE vs NON-FAVORITE TRACKING (Key profitability insight!)
        is_favorite = (odds < 3.0)  # Favorites typically have odds under 3.0
        
        if is_favorite:
            analysis['favorite_analysis']['favorites_backed'] += 1
            analysis['favorite_analysis']['favorites_total_stake'] += stake
            analysis['favorite_analysis']['favorites_total_pnl'] += pnl
            if is_winner:
                analysis['favorite_analysis']['favorites_won'] += 1
        else:
            analysis['favorite_analysis']['non_favorites_backed'] += 1
            analysis['favorite_analysis']['non_favorites_total_stake'] += stake
            analysis['favorite_analysis']['non_favorites_total_pnl'] += pnl
            if is_winner:
                analysis['favorite_analysis']['non_favorites_won'] += 1
                # VALUE CAPTURE: We backed a non-favorite and it won!
                analysis['favorite_analysis']['favorite_failure_opportunities'] += 1
        
        # STRATEGIC BEHAVIOR TRACKING (detect form hiding)
        strat = analysis['strategic_behavior']
        
        # Track ELITE races separately (Group 1/2/3, major meetings)
        if is_elite_race:
            strat['elite_races']['total'] += 1
            strat['elite_races']['total_stake'] += stake
            strat['elite_races']['total_pnl'] += pnl
            if is_winner:
                strat['elite_races']['won'] += 1
        
        # Track trainer performance across race tiers
        if trainer != 'Unknown':
            if is_elite_race:
                # ELITE races - everyone trying hard, trust the form!
                strat['trainer_patterns'][trainer]['elite_race_performance'].append({
                    'won': is_winner,
                    'odds': odds,
                    'position': actual_position,
                    'confidence': confidence,
                    'race_type': race_class
                })
            elif is_small_race:
                strat['trainer_patterns'][trainer]['small_race_performance'].append({
                    'won': is_winner,
                    'odds': odds,
                    'position': actual_position,
                    'confidence': confidence
                })
                if not is_winner and confidence > 50:
                    # High confidence but lost in small race - potential prep run
                    strat['prep_race_losses'] += 1
            elif is_big_race:
                strat['trainer_patterns'][trainer]['big_race_performance'].append({
                    'won': is_winner,
                    'odds': odds,
                    'position': actual_position,
                    'confidence': confidence
                })
                if is_winner:
                    # Check if previous race was a poor run (hiding form)
                    small_races = strat['trainer_patterns'][trainer]['small_race_performance']
                    if small_races and not small_races[-1].get('won', False):
                        # Won big race after losing small race - FLAG
                        strat['trainer_patterns'][trainer]['improvement_after_poor'] += 1
                        strat['follow_up_wins'] += 1
                        if odds > 4.0:  # Good odds after "poor" form
                            strat['trainer_patterns'][trainer]['suspicious_patterns'] += 1
                            strat['hiding_form_flags'].append({
                                'trainer': trainer,
                                'pattern': f"Won at {odds:.1f} after recent poor run - possible form hiding",
                                'horse': result.get('horse', 'Unknown'),
                                'date': result.get('bet_date', 'Unknown')
                            })
        
        # Track class movements
        prev_class = result.get('previous_class', None)
        if prev_class:
            if 'HIGHER' in prev_class.upper():
                if is_winner:
                    strat['class_rises_won'] += 1
            elif 'LOWER' in prev_class.upper():
                if is_winner:
                    strat['class_drops_won'] += 1
        
        # By odds range
        if odds <= 3.0:
            odds_range = 'favorite'
        elif odds <= 6.0:
            odds_range = 'medium'
        elif odds <= 10.0:
            odds_range = 'long_shot'
        else:
            odds_range = 'very_long'
        
        analysis['by_odds_range'][odds_range]['count'] += 1
        analysis['by_odds_range'][odds_range]['stake'] += stake
        analysis['by_odds_range'][odds_range]['pnl'] += pnl
        if is_winner:
            analysis['by_odds_range'][odds_range]['wins'] += 1
        
        # By course
        analysis['by_course'][course]['count'] += 1
        analysis['by_course'][course]['stake'] += stake
        analysis['by_course'][course]['pnl'] += pnl
        if is_winner:
            analysis['by_course'][course]['wins'] += 1
        
        # By bet type
        analysis['by_bet_type'][bet_type]['count'] += 1
        analysis['by_bet_type'][bet_type]['stake'] += stake
        analysis['by_bet_type'][bet_type]['pnl'] += pnl
        if is_winner:
            analysis['by_bet_type'][bet_type]['wins'] += 1
        
        # By decision rating
        analysis['by_decision_rating'][decision_rating]['count'] += 1
        analysis['by_decision_rating'][decision_rating]['stake'] += stake
        analysis['by_decision_rating'][decision_rating]['pnl'] += pnl
        if is_winner:
            analysis['by_decision_rating'][decision_rating]['wins'] += 1
    
    # Calculate rates
    total_bets = analysis['overall']['total_bets']
    if total_bets > 0:
        analysis['overall']['win_rate'] = analysis['overall']['wins'] / total_bets
        analysis['overall']['place_rate'] = (analysis['overall']['wins'] + analysis['overall']['places']) / total_bets
    
    total_stake = analysis['overall']['total_stake']
    if total_stake > 0:
        analysis['overall']['roi'] = (analysis['overall']['total_pnl'] / total_stake) * 100
    
    # Calculate favorite vs non-favorite rates
    fav_analysis = analysis['favorite_analysis']
    if fav_analysis['favorites_backed'] > 0:
        fav_analysis['favorites_win_rate'] = fav_analysis['favorites_won'] / fav_analysis['favorites_backed']
        if fav_analysis['favorites_total_stake'] > 0:
            fav_analysis['favorites_roi'] = (fav_analysis['favorites_total_pnl'] / fav_analysis['favorites_total_stake']) * 100
    
    if fav_analysis['non_favorites_backed'] > 0:
        fav_analysis['non_favorites_win_rate'] = fav_analysis['non_favorites_won'] / fav_analysis['non_favorites_backed']
        if fav_analysis['non_favorites_total_stake'] > 0:
            fav_analysis['non_favorites_roi'] = (fav_analysis['non_favorites_total_pnl'] / fav_analysis['non_favorites_total_stake']) * 100
        # Capture rate: How well are we picking the winners when favorites fail?
        # Ideal: If ~67% of races won by non-favorites, we want to capture as many as possible
        if fav_analysis['non_favorites_backed'] > 0:
            fav_analysis['favorite_failure_capture_rate'] = (fav_analysis['favorite_failure_opportunities'] / fav_analysis['non_favorites_backed']) * 100
    
    # Calculate ROI for each category
    for category in ['by_odds_range', 'by_course', 'by_bet_type', 'by_decision_rating']:
        for key, stats in analysis[category].items():
            if stats['stake'] > 0:
                stats['roi'] = (stats['pnl'] / stats['stake']) * 100
                stats['win_rate'] = stats['wins'] / stats['count'] if stats['count'] > 0 else 0
    
    return analysis

def generate_insights(analysis):
    """Generate actionable insights from analysis with detailed loss patterns"""
    
    insights = {
        'strengths': [],
        'weaknesses': [],
        'recommendations': [],
        'loss_patterns': []  # NEW: Specific reasons for losses
    }
    
    # ANALYZE LOSS PATTERNS FIRST (Critical for improvement)
    loss_data = analysis['loss_analysis']
    total_losses = loss_data['total_losses']
    
    if total_losses > 0:
        # Pattern 1: Losing on favorites
        if loss_data['favorites_lost'] > total_losses * 0.3:
            insights['loss_patterns'].append(
                f"Losing {loss_data['favorites_lost']}/{total_losses} on favorites (odds <3.0) - may be overestimating short-priced horses"
            )
            insights['recommendations'].append("CRITICAL: Reduce confidence on favorites by 15-20%, they're less value than expected")
        
        # Pattern 2: Losing on longshots
        if loss_data['longshots_lost'] > total_losses * 0.4:
            insights['loss_patterns'].append(
                f"Losing {loss_data['longshots_lost']}/{total_losses} on longshots (odds >8.0) - backing too many outsiders"
            )
            insights['recommendations'].append("AVOID: Significantly reduce longshot bets (>8.0 odds), they're not hitting often enough")
        
        # Pattern 3: High confidence failures
        if loss_data['high_confidence_losses'] > 3:
            insights['loss_patterns'].append(
                f"{loss_data['high_confidence_losses']} high-confidence bets (>70%) lost - overconfident"
            )
            insights['recommendations'].append("RECALIBRATE: Reduce ALL confidence scores by 10-15% - current model is overconfident")
        
        # Pattern 4: 'DO IT' rating failures
        if loss_data['do_it_losses'] > 2:
            do_it_total = analysis['by_decision_rating']['DO IT']['count']
            do_it_loss_rate = loss_data['do_it_losses'] / do_it_total if do_it_total > 0 else 0
            if do_it_loss_rate > 0.4:  # >40% failure rate on top picks
                insights['loss_patterns'].append(
                    f"{loss_data['do_it_losses']}/{do_it_total} 'DO IT' picks lost ({do_it_loss_rate*100:.0f}% failure rate)"
                )
                insights['recommendations'].append("URGENT: Tighten 'DO IT' criteria - require 20%+ ROI AND 80%+ confidence, current threshold too loose")
        
        # Pattern 5: Finishing positions
        if loss_data['by_position']:
            # Check if horses are finishing close (2nd-4th) or nowhere
            close_finishes = sum(loss_data['by_position'].get(str(pos), 0) for pos in [2, 3, 4])
            nowhere = sum(loss_data['by_position'].get(str(pos), 0) for pos in range(5, 20))
            
            if close_finishes > total_losses * 0.5:
                insights['loss_patterns'].append(
                    f"{close_finishes} losses finished 2nd-4th (close calls) - consider Each Way bets"
                )
                insights['recommendations'].append("STRATEGY: Switch high-confidence WIN bets (>65%) to Each Way for better place coverage")
            
            if nowhere > total_losses * 0.6:
                insights['loss_patterns'].append(
                    f"{nowhere} losses finished 5th or worse (not competitive) - poor selection"
                )
                insights['recommendations'].append("SELECTION: Review horse form analysis - too many uncompetitive picks, need stricter filters")
    
    # FAVORITE vs NON-FAVORITE ANALYSIS (67% rule exploitation!)
    fav_analysis = analysis['favorite_analysis']
    
    if fav_analysis['favorites_backed'] > 0 and fav_analysis['non_favorites_backed'] > 0:
        fav_win_rate = fav_analysis['favorites_win_rate'] * 100
        non_fav_win_rate = fav_analysis['non_favorites_win_rate'] * 100
        fav_roi = fav_analysis['favorites_roi']
        non_fav_roi = fav_analysis['non_favorites_roi']
        capture_rate = fav_analysis['favorite_failure_capture_rate']
        
        insights['strengths'].append(f"Favorite Strategy: {fav_analysis['favorites_backed']} backed, {fav_win_rate:.0f}% win rate, {fav_roi:.1f}% ROI")
        insights['strengths'].append(f"Non-Favorite Strategy: {fav_analysis['non_favorites_backed']} backed, {non_fav_win_rate:.0f}% win rate, {non_fav_roi:.1f}% ROI")
        
        # Key insight: Are we exploiting the 67% rule?
        if non_fav_roi > fav_roi:
            insights['strengths'].append(f"✅ EXCELLENT: Non-favorites ({non_fav_roi:.1f}% ROI) outperforming favorites ({fav_roi:.1f}% ROI) - exploiting 67% rule!")
            insights['recommendations'].append(f"DOUBLE DOWN: Increase stake on non-favorites with {capture_rate:.0f}% capture rate - this is where the value is")
        elif fav_roi > 10 and fav_win_rate > 40:
            insights['weaknesses'].append(f"⚠️ DANGER: Backing too many favorites ({fav_roi:.1f}% ROI at {fav_win_rate:.0f}% win) - low odds, low value")
            insights['recommendations'].append("SHIFT STRATEGY: Favorites win ~33% but at poor odds - focus on non-favorites (67% of winners) for better ROI")
        
        # Capture rate analysis
        if capture_rate < 20:
            insights['weaknesses'].append(f"⚠️ MISSING VALUE: Only capturing {capture_rate:.0f}% of non-favorite wins - missing 67% rule opportunities")
            insights['recommendations'].append("IMPROVE SELECTION: Need better non-favorite identification - study form, pace, track conditions to find the 67%")
        elif capture_rate > 35:
            insights['strengths'].append(f"🎯 VALUE CAPTURE: Excellent {capture_rate:.0f}% capture rate on non-favorite wins - finding value in the 67%!")
        
        # ROI-based recommendations
        if fav_roi < 0 and non_fav_roi > 5:
            insights['recommendations'].append("CRITICAL: STOP backing favorites (negative ROI) - ALL focus on non-favorites where value lies")
        elif fav_roi < 5:
            insights['recommendations'].append("TIGHTEN: Only back favorites when exceptional value (20%+ ROI, strong form, odds >2.5)")
    
    # STRATEGIC BEHAVIOR ANALYSIS (form hiding detection)
    strat = analysis['strategic_behavior']
    
    # ELITE RACE ANALYSIS (Group 1/2/3, major meetings - everyone trying!)
    elite_data = strat['elite_races']
    if elite_data['total'] > 0:
        elite_data['win_rate'] = elite_data['won'] / elite_data['total']
        elite_data['roi'] = (elite_data['total_pnl'] / elite_data['total_stake'] * 100) if elite_data['total_stake'] > 0 else 0
        
        insights['strengths'].append(
            f"🏆 ELITE RACES (Group 1/2/3, Major Meetings): {elite_data['total']} backed, "
            f"{elite_data['win_rate']*100:.1f}% win rate, {elite_data['roi']:.1f}% ROI - EVERYONE trying to win!"
        )
        
        if elite_data['roi'] > 10:
            insights['recommendations'].append(
                f"✨ ELITE RACE EDGE: {elite_data['roi']:.1f}% ROI on Group races - "
                "BOOST confidence by 20% on Group 1/2/3 and major meetings (no form hiding!)"
            )
        elif elite_data['roi'] < 0:
            insights['weaknesses'].append(
                f"⚠️ Elite race struggles: {elite_data['roi']:.1f}% ROI - competition is fierce, may be overestimating chances"
            )
            insights['recommendations'].append(
                "RECALIBRATE: Elite races have best horses - require 25%+ ROI and stronger form indicators"
            )
    
    if len(strat['hiding_form_flags']) > 0:
        insights['weaknesses'].append(f"🚨 FORM HIDING DETECTED: {len(strat['hiding_form_flags'])} suspicious patterns - trainers may be sandbagging small races")
        insights['recommendations'].append("CAUTION: Reduce confidence on horses in small/claiming races by 15% - trainers may not be trying hard")
        
        # List specific trainers with suspicious patterns
        for flag in strat['hiding_form_flags'][:3]:  # Show top 3
            insights['loss_patterns'].append(
                f"⚠️ {flag['trainer']}: {flag['pattern']} - {flag['horse']}"
            )
        
        insights['recommendations'].append("OPPORTUNITY: When these trainers step up to ELITE races (Group 1/2/3), BOOST confidence by 15% - no sandbagging at top level!")
    
    # Class movement analysis
    if strat['class_rises_won'] > 2:
        win_rate_up = strat['class_rises_won'] / max(1, analysis['overall']['total_bets']) * 100
        insights['strengths'].append(f"✅ Class Risers: {strat['class_rises_won']} wins when stepping up - horses are competitive at higher levels")
        if win_rate_up > 15:
            insights['recommendations'].append("BOOST: Increase confidence by 10% on horses stepping up in class - they're beating better horses")
    
    if strat['class_drops_won'] > strat['class_rises_won'] * 2:
        insights['weaknesses'].append(f"⚠️ Class Droppers: Winning more at lower class ({strat['class_drops_won']}) - may be overestimating quality")
        insights['recommendations'].append("RECALIBRATE: Don't overbet class droppers - they should win at lower levels, demand 18%+ ROI")
    
    # Prep race detection
    if strat['prep_race_losses'] > 3 and strat['follow_up_wins'] > 1:
        prep_to_win_ratio = strat['follow_up_wins'] / max(1, strat['prep_race_losses'])
        if prep_to_win_ratio > 0.3:  # >30% of prep losses led to follow-up wins
            insights['recommendations'].append(
                f"🎯 PATTERN DETECTED: {strat['follow_up_wins']}/{strat['prep_race_losses']} 'prep race' losses led to follow-up wins - "
                "track horses improving after recent runs in small races"
            )
    
    # Trainer-specific patterns
    suspicious_trainers = []
    for trainer, data in strat['trainer_patterns'].items():
        if data['suspicious_patterns'] > 1:
            suspicious_trainers.append(trainer)
    
    if suspicious_trainers:
        insights['recommendations'].append(
            f"🔍 WATCH LIST: {len(suspicious_trainers)} trainers with form-hiding patterns - "
            f"be CAUTIOUS in small races, AGGRESSIVE when they target big races"
        )
    
    # Analyze odds ranges
    best_odds_roi = -999
    best_odds_range = None
    worst_odds_roi = 999
    worst_odds_range = None
    
    for odds_range, stats in analysis['by_odds_range'].items():
        if stats['count'] < 3:  # Need minimum sample
            continue
        roi = stats.get('roi', 0)
        if roi > best_odds_roi:
            best_odds_roi = roi
            best_odds_range = odds_range
        if roi < worst_odds_roi:
            worst_odds_roi = roi
            worst_odds_range = odds_range
    
    if best_odds_range and best_odds_roi > 5:
        insights['strengths'].append(f"Strong performance on {best_odds_range} odds ({best_odds_roi:.1f}% ROI)")
        insights['recommendations'].append(f"Increase stake on {best_odds_range} selections")
    
    if worst_odds_range and worst_odds_roi < -10:
        insights['weaknesses'].append(f"Poor performance on {worst_odds_range} odds ({worst_odds_roi:.1f}% ROI)")
        insights['recommendations'].append(f"Reduce or avoid {worst_odds_range} selections")
    
    # Analyze decision ratings
    for rating in ['DO IT', 'RISKY', 'NOT GREAT']:
        stats = analysis['by_decision_rating'].get(rating, {})
        if stats.get('count', 0) >= 3:
            roi = stats.get('roi', 0)
            win_rate = stats.get('win_rate', 0)
            
            if rating == 'DO IT':
                if roi > 10:
                    insights['strengths'].append(f"'{rating}' picks performing well ({roi:.1f}% ROI, {win_rate*100:.1f}% win rate)")
                elif roi < 0:
                    insights['weaknesses'].append(f"'{rating}' picks underperforming ({roi:.1f}% ROI)")
                    insights['recommendations'].append("Review criteria for 'DO IT' rating - may be too optimistic")
            
            elif rating == 'RISKY':
                if roi > 5:
                    insights['strengths'].append(f"'{rating}' picks justified ({roi:.1f}% ROI)")
                elif roi < -5:
                    insights['weaknesses'].append(f"'{rating}' picks too risky ({roi:.1f}% ROI)")
                    insights['recommendations'].append("Reduce stakes or avoid 'RISKY' selections")
    
    # Best courses
    best_courses = sorted(
        [(course, stats) for course, stats in analysis['by_course'].items() if stats['count'] >= 3],
        key=lambda x: x[1].get('roi', 0),
        reverse=True
    )[:3]
    
    if best_courses and best_courses[0][1]['roi'] > 10:
        course, stats = best_courses[0]
        insights['strengths'].append(f"Excellent at {course} ({stats['roi']:.1f}% ROI, {stats['wins']}/{stats['count']} wins)")
    
    # Overall performance
    overall_roi = analysis['overall']['roi']
    if overall_roi > 5:
        insights['strengths'].append(f"Profitable overall: {overall_roi:.1f}% ROI")
    elif overall_roi < 0:
        insights['weaknesses'].append(f"Losing overall: {overall_roi:.1f}% ROI")
        insights['recommendations'].append("Consider reducing stakes or reviewing selection criteria")
    
    return insights

def calculate_quality_metrics(results):
    """Calculate quality distribution and progress toward GREEN status"""
    
    quality_distribution = {
        'green_count': 0,  # 75%+ confidence, 20%+ ROI, DO IT
        'high_count': 0,   # 60%+ confidence
        'moderate_count': 0,  # 45%+ confidence
        'low_count': 0,    # <45% confidence
        'top_pick_wins': 0,  # Track first pick success
        'daily_quality_score': 0,
        'improvement_needed': []
    }
    
    for bet in results:
        confidence = float(bet.get('combined_confidence', 0))
        expected_roi = float(bet.get('expected_roi', 0))
        decision_rating = bet.get('decision_rating', '')
        actual_result = bet.get('actual_result', '')
        
        # Calculate quality tiers
        is_green = (confidence >= GREEN_CONFIDENCE_MIN and 
                   expected_roi >= GREEN_ROI_MIN and 
                   decision_rating == "DO IT")
        
        if is_green:
            quality_distribution['green_count'] += 1
            # Validate if it actually won
            if actual_result in ['WON', 'PLACED']:
                quality_distribution['top_pick_wins'] += 1
        elif confidence >= HIGH_CONFIDENCE_MIN:
            quality_distribution['high_count'] += 1
        elif confidence >= MODERATE_CONFIDENCE_MIN:
            quality_distribution['moderate_count'] += 1
        else:
            quality_distribution['low_count'] += 1
    
    # Calculate daily quality score (0-100)
    total = len(results)
    if total > 0:
        green_pct = quality_distribution['green_count'] / total
        high_pct = quality_distribution['high_count'] / total
        moderate_pct = quality_distribution['moderate_count'] / total
        
        quality_distribution['daily_quality_score'] = (
            (green_pct * 50) +  # Green picks most important
            (high_pct * 30) +   # High quality significant
            (moderate_pct * 15) # Moderate quality baseline
        )
    
    # Determine improvement areas
    if quality_distribution['green_count'] == 0:
        quality_distribution['improvement_needed'].append("CRITICAL: Need to achieve first GREEN status pick (75%+ confidence, 20%+ ROI)")
    elif quality_distribution['green_count'] < 3:
        quality_distribution['improvement_needed'].append(f"GOAL: Increase GREEN picks from {quality_distribution['green_count']} to 3+ per day")
    
    if quality_distribution['high_count'] < 5:
        quality_distribution['improvement_needed'].append(f"GOAL: Increase HIGH confidence picks from {quality_distribution['high_count']} to 5+ per day")
    
    return quality_distribution

def calculate_training_adjustments(analysis, quality_metrics):
    """Calculate progressive training adjustments to reach GREEN status"""
    
    adjustments = {
        'confidence_calibration': 1.0,  # Multiply all confidence by this
        'roi_threshold_change': 0,    # Add this to ROI requirements
        'odds_range_focus': [],       # Which odds ranges to prioritize
        'course_mastery': {},         # Course-specific adjustments
        'pattern_boosts': {},         # Patterns to boost
        'pattern_penalties': {},      # Patterns to avoid
        'training_phase': 'foundation',  # Current training phase
        'days_to_green': 999         # Estimated days until first GREEN
    }
    
    overall_roi = analysis['overall']['roi']
    win_rate = analysis['overall']['win_rate']
    green_count = quality_metrics['green_count']
    
    # Determine training phase based on progress
    if green_count >= 3 and overall_roi >= 20:
        adjustments['training_phase'] = 'mastery'
        adjustments['days_to_green'] = 0  # Already achieved!
    elif green_count >= 1 or overall_roi >= 15:
        adjustments['training_phase'] = 'green_push'
        adjustments['days_to_green'] = 7
    elif win_rate >= 0.35 and overall_roi >= 10:
        adjustments['training_phase'] = 'quality_refinement'
        adjustments['days_to_green'] = 14
    else:
        adjustments['training_phase'] = 'foundation'
        adjustments['days_to_green'] = 21
    
    # Confidence calibration based on overconfidence
    loss_data = analysis['loss_analysis']
    if loss_data['high_confidence_losses'] > 3:
        # Too overconfident
        adjustments['confidence_calibration'] = 0.85  # Reduce 15%
    elif loss_data['high_confidence_losses'] > 1:
        adjustments['confidence_calibration'] = 0.90  # Reduce 10%
    else:
        adjustments['confidence_calibration'] = 1.0  # No change
    
    # ROI threshold adjustments
    if overall_roi < 10:
        adjustments['roi_threshold_change'] = +5  # Need stricter filters
    elif overall_roi > 25:
        adjustments['roi_threshold_change'] = -2  # Can be slightly looser
    
    # Find best odds ranges
    for odds_range, stats in analysis['by_odds_range'].items():
        if stats['count'] >= 3 and stats.get('roi', 0) >= 15:
            adjustments['odds_range_focus'].append({
                'range': odds_range,
                'roi': stats['roi'],
                'boost': +10  # Boost confidence by 10% in this range
            })
        elif stats['count'] >= 3 and stats.get('roi', 0) < -10:
            adjustments['pattern_penalties'][f'odds_{odds_range}'] = -15
    
    # Course mastery
    for course, stats in analysis['by_course'].items():
        if stats['count'] >= 3:
            roi = stats.get('roi', 0)
            if roi >= 20:
                adjustments['course_mastery'][course] = {'adjustment': +15, 'confidence': 'high'}
            elif roi <= -15:
                adjustments['course_mastery'][course] = {'adjustment': -20, 'confidence': 'avoid'}
    
    return adjustments

def store_learning_data(analysis, insights, quality_metrics, adjustments):
    """Store performance data and insights in DynamoDB with quality metrics"""
    try:
        learning_table = dynamodb.Table(learning_table_name)
    except:
        # Table doesn't exist, create it
        print(f"Creating {learning_table_name} table...")
        dynamodb.create_table(
            TableName=learning_table_name,
            KeySchema=[
                {'AttributeName': 'period', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'period', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Waiting for table creation...")
        dynamodb.meta.client.get_waiter('table_exists').wait(TableName=learning_table_name)
        learning_table = dynamodb.Table(learning_table_name)
    
    # Convert to JSON-serializable format
    def convert_to_json(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, defaultdict) or isinstance(obj, dict):
            return {k: convert_to_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json(v) for v in obj]
        return obj
    
    analysis_json = convert_to_json(analysis)
    quality_json = convert_to_json(quality_metrics)
    adjustments_json = convert_to_json(adjustments)
    
    # Store in DynamoDB with quality and training data
    item = {
        'period': 'last_7_days',
        'timestamp': datetime.utcnow().isoformat(),
        'analysis': json.dumps(analysis_json),
        'insights': json.dumps(insights),
        'quality_metrics': json.dumps(quality_json),  # NEW: Track quality distribution
        'training_adjustments': json.dumps(adjustments_json),  # NEW: Progressive training
        'overall_roi': Decimal(str(analysis['overall']['roi'])),
        'overall_win_rate': Decimal(str(analysis['overall']['win_rate'])),
        'total_bets': analysis['overall']['total_bets'],
        'total_pnl': Decimal(str(analysis['overall']['total_pnl'])),
        'green_count': quality_metrics['green_count'],  # NEW: Track GREEN picks
        'daily_quality_score': Decimal(str(quality_metrics['daily_quality_score'])),  # NEW: Quality score
        'training_phase': adjustments['training_phase']  # NEW: Current training phase
    }
    
    learning_table.put_item(Item=item)
    print(f"✓ Stored learning data in {learning_table_name}")

def lambda_handler(event, context):
    """Main Lambda handler - Daily Training System"""
    
    print("=== DAILY TRAINING & LEARNING ANALYSIS ===")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"🎯 GOAL: Achieve GREEN status picks (75%+ confidence, 20%+ ROI)")
    
    # Get results from last 7 days
    results = get_results_for_period(days=7)
    
    if len(results) < 5:
        print("Not enough results for analysis (need at least 5)")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Insufficient data', 'results_count': len(results)})
        }
    
    # Calculate quality metrics (path to GREEN)
    print("\n📊 Calculating quality distribution...")
    quality_metrics = calculate_quality_metrics(results)
    
    # Analyze performance
    print("\nAnalyzing performance patterns...")
    analysis = analyze_performance(results)
    
    # Generate insights
    print("\nGenerating insights...")
    insights = generate_insights(analysis)
    
    # Calculate training adjustments (progressive improvement)
    print("\n🎓 Calculating training adjustments...")
    adjustments = calculate_training_adjustments(analysis, quality_metrics)
    
    # Print summary
    print("\n=== PERFORMANCE SUMMARY ===")
    print(f"Total bets: {analysis['overall']['total_bets']}")
    print(f"Win rate: {analysis['overall']['win_rate']*100:.1f}%")
    print(f"ROI: {analysis['overall']['roi']:.1f}%")
    print(f"Total P&L: €{analysis['overall']['total_pnl']:.2f}")
    
    print("\n=== QUALITY DISTRIBUTION (Path to GREEN) ===")
    print(f"🟢 GREEN picks (75%+ conf, 20%+ ROI): {quality_metrics['green_count']}")
    print(f"🟡 HIGH picks (60%+ conf): {quality_metrics['high_count']}")
    print(f"🟠 MODERATE picks (45%+ conf): {quality_metrics['moderate_count']}")
    print(f"⚪ LOW picks (<45% conf): {quality_metrics['low_count']}")
    print(f"📈 Daily Quality Score: {quality_metrics['daily_quality_score']:.1f}/100")
    print(f"🏆 Top Pick Wins: {quality_metrics['top_pick_wins']}")
    
    print("\n=== TRAINING PROGRESS ===")
    print(f"Phase: {adjustments['training_phase'].upper()}")
    if adjustments['days_to_green'] == 0:
        print("🎉 ACHIEVEMENT UNLOCKED: GREEN STATUS REACHED!")
    else:
        print(f"Days to GREEN estimate: {adjustments['days_to_green']}")
    
    print("\n=== IMPROVEMENT AREAS ===")
    for improvement in quality_metrics['improvement_needed']:
        print(f"🎯 {improvement}")
    
    print("\n=== FAVORITE vs NON-FAVORITE ANALYSIS (67% Rule) ===")
    fav_analysis = analysis['favorite_analysis']
    if fav_analysis['favorites_backed'] > 0:
        print(f"Favorites backed: {fav_analysis['favorites_backed']}")
        print(f"  Win rate: {fav_analysis['favorites_win_rate']*100:.1f}% (typical: 33%)")
        print(f"  ROI: {fav_analysis['favorites_roi']:.1f}%")
    if fav_analysis['non_favorites_backed'] > 0:
        print(f"Non-favorites backed: {fav_analysis['non_favorites_backed']}")
        print(f"  Win rate: {fav_analysis['non_favorites_win_rate']*100:.1f}% (67% of races)")
        print(f"  ROI: {fav_analysis['non_favorites_roi']:.1f}%")
        print(f"  Value capture: {fav_analysis['favorite_failure_capture_rate']:.1f}% of non-fav wins")
        if fav_analysis['non_favorites_roi'] > fav_analysis['favorites_roi']:
            print(f"  ✅ NON-FAVORITES OUTPERFORMING - exploiting 67% rule!")
    
    print("\n=== TRAINING ADJUSTMENTS (Auto-applied) ===")
    if adjustments['confidence_calibration'] != 1.0:
        change_pct = (adjustments['confidence_calibration'] - 1.0) * 100
        print(f"⚙️ Confidence calibration: {change_pct:+.0f}%")
    
    if adjustments['roi_threshold_change'] != 0:
        print(f"⚙️ ROI threshold adjustment: {adjustments['roi_threshold_change']:+.0f}%")
    
    if adjustments['odds_range_focus']:
        print("⚙️ Focus on these odds ranges:")
        for focus in adjustments['odds_range_focus']:
            print(f"   {focus['range']}: ROI {focus['roi']:.1f}% → Boost confidence {focus['boost']:+d}%")
    
    if adjustments['course_mastery']:
        print("⚙️ Course-specific adjustments:")
        for course, data in list(adjustments['course_mastery'].items())[:5]:
            print(f"   {course}: {data['adjustment']:+d}% ({data['confidence']})")
    
    print("\n=== LOSS ANALYSIS ===")
    loss_data = analysis['loss_analysis']
    print(f"Total losses: {loss_data['total_losses']}")
    print(f"Favorites lost: {loss_data['favorites_lost']}")
    print(f"Longshots lost: {loss_data['longshots_lost']}")
    print(f"High confidence losses: {loss_data['high_confidence_losses']}")
    print(f"'DO IT' rating losses: {loss_data['do_it_losses']}")
    if loss_data['by_position']:
        print(f"Finish positions: {dict(loss_data['by_position'])}")
    
    print("\n=== STRATEGIC BEHAVIOR ANALYSIS (Form Hiding Detection) ===")
    strat = analysis['strategic_behavior']
    
    # ELITE RACES (Group 1/2/3, Major Meetings)
    elite_data = strat['elite_races']
    if elite_data['total'] > 0:
        print(f"🏆 ELITE RACES (Group 1/2/3, Major Meetings):")
        print(f"   Total backed: {elite_data['total']}")
        print(f"   Win rate: {elite_data['win_rate']*100:.1f}%")
        print(f"   ROI: {elite_data['roi']:.1f}%")
        print(f"   ✨ Everyone trying to win - NO form hiding at this level!")
        if elite_data['roi'] > 10:
            print(f"   ✅ EXCELLENT performance at elite level - keep targeting these!")
    
    if len(strat['hiding_form_flags']) > 0:
        print(f"🚨 SUSPICIOUS PATTERNS: {len(strat['hiding_form_flags'])} potential form-hiding detected")
        for flag in strat['hiding_form_flags'][:3]:
            print(f"   ⚠️  {flag['trainer']}: {flag['pattern']}")
    if strat['class_rises_won'] > 0:
        print(f"✅ Class rises won: {strat['class_rises_won']} (horses competitive at higher levels)")
    if strat['class_drops_won'] > 0:
        print(f"⚠️  Class drops won: {strat['class_drops_won']} (winning at easier levels)")
    if strat['prep_race_losses'] > 0 and strat['follow_up_wins'] > 0:
        print(f"🎯 Prep race pattern: {strat['follow_up_wins']}/{strat['prep_race_losses']} small race losses led to big race wins")
    
    print("\n=== INSIGHTS ===")
    for pattern in insights['loss_patterns']:
        print(f"📊 LOSS PATTERN: {pattern}")
    for strength in insights['strengths']:
        print(f"✓ {strength}")
    for weakness in insights['weaknesses']:
        print(f"⚠ {weakness}")
    
    print("\n=== RECOMMENDATIONS (Auto-applied to next run) ===")
    for rec in insights['recommendations']:
        print(f"→ {rec}")
    
    # Store learning data with quality and training metrics
    store_learning_data(analysis, insights, quality_metrics, adjustments)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Daily training analysis complete',
            'results_analyzed': len(results),
            'roi': float(analysis['overall']['roi']),
            'win_rate': float(analysis['overall']['win_rate']),
            'insights': insights
        })
    }
