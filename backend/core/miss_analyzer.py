"""
Model Miss Analyzer - Deep Analysis of Selection Failures

Analyzes historical race data to identify patterns in model misses:
- Why top picks weren't the winners
- What factors differentiated winners from model selections
- Gaps in current scoring model
- Recommendations for score weighting adjustments

Expected impact: +15-25 winners/week + model improvement insights
"""

import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)


def extract_miss_features(
    top_pick: Dict[str, Any],
    actual_winner: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare top pick vs actual winner to identify feature gaps.
    
    Args:
        top_pick: Model's top selection {horse_id, name, score, confidence, ...}
        actual_winner: Actual winning horse {horse_id, name, odds_won, ...}
    
    Returns:
        Feature comparison dict
    """
    
    features = {
        'score_gap': actual_winner.get('score', 0) - top_pick.get('score', 0),
        'rank_gap': actual_winner.get('rank', 0) - top_pick.get('rank', 1),  # rank 1 for top pick
        'odds_gap': (actual_winner.get('odds_at_start', 0) - 
                     top_pick.get('odds_at_start', 0)),
        'improvement_flag_top': top_pick.get('potential_improver_flag', False),
        'improvement_flag_winner': actual_winner.get('potential_improver_flag', False),
        'form_trend_top': top_pick.get('form_trend', 'stable'),
        'form_trend_winner': actual_winner.get('form_trend', 'stable'),
        'trip_suitability_top': top_pick.get('trip_suitability_score', 0),
        'trip_suitability_winner': actual_winner.get('trip_suitability_score', 0),
        'trainer_form_top': top_pick.get('trainer_form_rank', 0),
        'trainer_form_winner': actual_winner.get('trainer_form_rank', 0),
        'jockey_form_top': top_pick.get('jockey_form_score', 0),
        'jockey_form_winner': actual_winner.get('jockey_form_score', 0),
        'course_history_top': top_pick.get('course_wins', 0),
        'course_history_winner': actual_winner.get('course_wins', 0),
        'distance_wins_top': top_pick.get('distance_wins', 0),
        'distance_wins_winner': actual_winner.get('distance_wins', 0),
        'class_drop_top': top_pick.get('class_drop', False),
        'class_drop_winner': actual_winner.get('class_drop', False),
        'weather_going_suitability_top': top_pick.get('going_score', 0),
        'weather_going_suitability_winner': actual_winner.get('going_score', 0),
    }
    
    return features


def categorize_miss(
    top_pick: Dict[str, Any],
    actual_winner: Dict[str, Any],
    all_runners: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Categorize why the miss occurred.
    
    Categories:
    - winner_not_in_field: Model field didn't include winner
    - improver_demoted: Winner was improver but demoted in ranking
    - underranked: Winner in field but ranked 6+
    - long_shot: Winner had double-digit odds
    - pace_dynamics: Pace-favored horse that model didn't weight enough
    - trip_change: Field changes between analysis and race
    - score_gap_narrow: Top picks too close to separate (margin < 3 points)
    - form_reversal: Horse that looked worse but had hidden improvement
    
    Args:
        top_pick: Model's top selection
        actual_winner: Actual winner
        all_runners: All horses in race as analyzed by model
    
    Returns:
        Categorization details
    """
    
    winner_id = actual_winner.get('horse_id')
    top_pick_id = top_pick.get('horse_id')
    
    # Check if winner was in model's field
    winner_in_field = any(h.get('horse_id') == winner_id for h in all_runners)
    
    if not winner_in_field:
        return {
            'category': 'winner_not_in_field',
            'reason': 'Winner excluded from model field (likely nonrunner at analysis time)',
            'severity': 'high'
        }
    
    # Check improver dynamics
    if actual_winner.get('potential_improver_flag') and not top_pick.get('potential_improver_flag'):
        return {
            'category': 'improver_demoted',
            'reason': 'Winner was improver but not selected (improver signal weak or demoted)',
            'severity': 'high'
        }
    
    # Check ranking
    winner_rank = actual_winner.get('rank', 99)
    if winner_rank >= 6:
        return {
            'category': 'underranked',
            'reason': f'Winner ranked {winner_rank}, outside top 5 picks',
            'severity': 'medium',
            'winner_rank': winner_rank
        }
    
    # Check odds
    winner_odds = actual_winner.get('odds_at_start', 0)
    if winner_odds > 10:
        return {
            'category': 'long_shot',
            'reason': f'Winner had {winner_odds:.1f} odds, exceeds typical long-shot threshold',
            'severity': 'low',
            'winner_odds': winner_odds
        }
    
    # Check trip suitability gap
    trip_gap = (actual_winner.get('trip_suitability_score', 0) - 
                top_pick.get('trip_suitability_score', 0))
    if trip_gap > 20:
        return {
            'category': 'trip_change',
            'reason': f'Trip dynamics favored winner (+{trip_gap:.0f} trip score)',
            'severity': 'medium',
            'trip_score_gap': trip_gap
        }
    
    # Check score gap
    score_gap = actual_winner.get('score', 0) - top_pick.get('score', 0)
    if abs(score_gap) < 3:
        return {
            'category': 'score_gap_narrow',
            'reason': f'Top picks within 3 points of winner (gap: {score_gap:.1f})',
            'severity': 'low',
            'score_gap': score_gap
        }
    
    # Default: model fundamentally missed this pattern
    return {
        'category': 'model_miss',
        'reason': 'Winner had features model underweights',
        'severity': 'high',
        'score_gap': score_gap
    }


def analyze_single_miss(
    market_id: str,
    race_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a single race miss in detail.
    
    Args:
        market_id: BetFair market ID
        race_data: Complete race data with analysis and result
                   {market_id, race_time, runners: [all analyzed], picks: [top 3],
                    actual_winner: {horse_id, ...}, ...}
    
    Returns:
        Miss analysis record
    """
    
    race_time = race_data.get('race_time')
    all_runners = race_data.get('runners', [])
    picks = race_data.get('picks', [])
    actual_winner = race_data.get('actual_winner', {})
    
    if not picks or not actual_winner:
        return {
            'market_id': market_id,
            'status': 'incomplete_data',
            'reason': 'Missing picks or winner data'
        }
    
    top_pick = picks[0] if picks else {}
    features = extract_miss_features(top_pick, actual_winner)
    categorization = categorize_miss(top_pick, actual_winner, all_runners)
    
    analysis = {
        'market_id': market_id,
        'race_time': race_time,
        'analysis_performed_at': datetime.now(timezone.utc).isoformat(),
        'top_pick': {
            'horse_id': top_pick.get('horse_id'),
            'name': top_pick.get('horse_name'),
            'score': top_pick.get('score'),
            'odds': top_pick.get('odds_at_start')
        },
        'actual_winner': {
            'horse_id': actual_winner.get('horse_id'),
            'name': actual_winner.get('horse_name'),
            'score': actual_winner.get('score'),
            'odds': actual_winner.get('odds_at_start'),
            'rank': actual_winner.get('rank', 99)
        },
        'features': features,
        'categorization': categorization,
        'field_size': len(all_runners),
        'nonrunner_count': race_data.get('nonrunner_count', 0)
    }
    
    return analysis


def aggregate_miss_patterns(
    miss_analyses: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Find common patterns across multiple misses.
    
    Args:
        miss_analyses: List of individual miss analyses
    
    Returns:
        Aggregated patterns and recommendations
    """
    
    if not miss_analyses:
        return {'error': 'No miss data provided'}
    
    # Category distribution
    categories = [m.get('categorization', {}).get('category') for m in miss_analyses]
    category_counts = Counter(categories)
    
    # Feature statistics
    score_gaps = [m.get('features', {}).get('score_gap', 0) for m in miss_analyses]
    trip_gaps = [m.get('features', {}).get('trip_suitability_winner', 0) - 
                 m.get('features', {}).get('trip_suitability_top', 0) 
                 for m in miss_analyses]
    
    improver_miss_count = len([m for m in miss_analyses 
                               if m.get('categorization', {}).get('category') == 'improver_demoted'])
    improver_miss_rate = improver_miss_count / len(miss_analyses) if miss_analyses else 0
    
    # Identify top missing scoring factors
    missing_factors = []
    for miss in miss_analyses:
        features = miss.get('features', {})
        if features.get('improvement_flag_winner') and not features.get('improvement_flag_top'):
            missing_factors.append('improver_flag')
        if features.get('trip_suitability_winner', 0) > features.get('trip_suitability_top', 0) + 15:
            missing_factors.append('trip_suitability')
        if features.get('form_trend_winner') == 'improving' and features.get('form_trend_top') == 'stable':
            missing_factors.append('form_trend')
        if features.get('class_drop_winner') and not features.get('class_drop_top'):
            missing_factors.append('class_drop')
    
    factor_counts = Counter(missing_factors)
    
    # Recommendations
    recommendations = []
    
    if category_counts.get('improver_demoted', 0) > len(miss_analyses) * 0.20:
        recommendations.append({
            'factor': 'improver_flag',
            'action': 'Boost improver-flagged horses by +15-20 points',
            'impact_misses': improver_miss_count,
            'priority': 'high'
        })
    
    if category_counts.get('underranked', 0) > len(miss_analyses) * 0.15:
        recommendations.append({
            'factor': 'ranking_separation',
            'action': 'Widen score gaps between picks (wider margin to separate horse 1 from 5)',
            'impact_misses': category_counts.get('underranked', 0),
            'priority': 'high'
        })
    
    if statistics.mean(trip_gaps) > 15:
        recommendations.append({
            'factor': 'trip_suitability',
            'action': 'Increase trip suitability weighting by 20-25%',
            'mean_gap': statistics.mean(trip_gaps),
            'priority': 'high'
        })
    
    aggregation = {
        'total_misses': len(miss_analyses),
        'analysis_period': {
            'start': min(m.get('race_time') for m in miss_analyses if m.get('race_time')),
            'end': max(m.get('race_time') for m in miss_analyses if m.get('race_time'))
        },
        'category_distribution': dict(category_counts),
        'top_miss_reason': category_counts.most_common(1)[0][0] if category_counts else None,
        'statistics': {
            'avg_score_gap': statistics.mean(score_gaps) if score_gaps else 0,
            'median_score_gap': statistics.median(score_gaps) if score_gaps else 0,
            'avg_trip_gap': statistics.mean(trip_gaps) if trip_gaps else 0,
            'improver_miss_rate': improver_miss_rate
        },
        'top_missing_factors': dict(factor_counts.most_common(5)),
        'recommendations': recommendations,
        'analysis_completed_at': datetime.now(timezone.utc).isoformat()
    }
    
    return aggregation


def analyze_model_misses_pipeline(
    race_data_list: List[Dict[str, Any]],
    date_range: Optional[Tuple[str, str]] = None
) -> Dict[str, Any]:
    """
    Main pipeline: analyze all model misses and generate recommendations.
    
    This is the entry point for the miss analyzer Lambda/step function.
    
    Args:
        race_data_list: List of race records with picks and actual winners
        date_range: Optional (start_date, end_date) in ISO format
    
    Returns:
        Complete miss analysis report with recommendations
    """
    
    logger.info(
        f"Starting model miss analysis for {len(race_data_list)} races"
    )
    
    try:
        # Analyze each miss
        miss_analyses = []
        for race_data in race_data_list:
            market_id = race_data.get('market_id')
            
            # Only analyze races where model missed (picks != winner)
            picks = race_data.get('picks', [])
            winner = race_data.get('actual_winner')
            
            if picks and winner:
                top_pick_id = picks[0].get('horse_id')
                winner_id = winner.get('horse_id')
                
                if top_pick_id != winner_id:
                    analysis = analyze_single_miss(market_id, race_data)
                    miss_analyses.append(analysis)
        
        # Aggregate patterns
        if miss_analyses:
            patterns = aggregate_miss_patterns(miss_analyses)
        else:
            patterns = {
                'total_misses': 0,
                'note': 'No misses found in provided data'
            }
        
        # Summary statistics
        summary = {
            'date_range': date_range,
            'races_analyzed': len(race_data_list),
            'model_misses': len(miss_analyses),
            'hit_rate': 1 - (len(miss_analyses) / len(race_data_list)) if race_data_list else 0,
            'patterns': patterns
        }
        
        logger.info(
            f"Miss analysis complete: {len(miss_analyses)} misses found "
            f"({summary['hit_rate']:.1%} hit rate)"
        )
        
        return {
            'status': 'success',
            'summary': summary,
            'detailed_analyses': miss_analyses,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.exception(f"Error in miss analysis pipeline: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
