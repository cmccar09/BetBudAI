# Enhanced Learning System - Code Implementation Examples
**Version**: 1.0  
**Created**: May 20, 2026  
**Purpose**: Quick reference for implementing enhanced learning system

---

## Example 1: Deep Loss Analysis Function

Add to `backend/core/miss_analyzer.py`:

```python
def analyze_loss_deeply(
    top_pick: Dict[str, Any],
    actual_winner: Dict[str, Any],
    all_runners: List[Dict[str, Any]],
    race_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep dive analysis extracting structured learning insights.
    
    Args:
        top_pick: Our #1 pick that lost
        actual_winner: The actual winning horse
        all_runners: All horses in the race
        race_data: Complete race context (course, going, field_size, etc.)
    
    Returns:
        Complete LOSS_ANALYSIS_SCHEMA record
    """
    
    # Extract what made us pick this horse
    top_factors = _get_top_contributing_factors(top_pick)
    
    # Identify what winner had that we missed
    winner_advantages = _identify_winner_advantages(actual_winner, top_pick)
    
    # Pricing analysis
    pricing = _analyze_pricing_vs_performance(top_pick, actual_winner)
    
    # Form trends comparison
    form_analysis = _compare_form_trajectories(top_pick, actual_winner)
    
    # Jockey/trainer dynamics
    jt_analysis = _analyze_jockey_trainer_performance(top_pick, actual_winner)
    
    # Going/conditions suitability
    conditions = _analyze_conditions_suitability(top_pick, actual_winner, race_data)
    
    # Field composition changes
    field_analysis = _analyze_field_changes(race_data)
    
    # Categorize severity and fixability
    categorization = _categorize_miss_with_fix_estimate(
        top_pick, actual_winner, winner_advantages
    )
    
    return {
        'market_id': race_data.get('market_id'),
        'bet_date': race_data.get('bet_date'),
        'race_time': race_data.get('race_time'),
        'our_pick': {
            'horse_name': top_pick.get('horse_name'),
            'horse_id': top_pick.get('horse_id'),
            'score': top_pick.get('score'),
            'rank': 1,
            'odds_at_start': top_pick.get('odds_at_start'),
            'actual_finish': top_pick.get('finish_position', 0),
        },
        'actual_winner': {
            'horse_name': actual_winner.get('horse_name'),
            'horse_id': actual_winner.get('horse_id'),
            'score': actual_winner.get('score', 0),
            'rank': actual_winner.get('rank', 99),
            'odds_at_win': actual_winner.get('odds_at_win'),
        },
        'why_we_picked_this_horse': top_factors,
        'why_winner_beat_us': winner_advantages,
        'pricing_analysis': pricing,
        'form_vs_history': form_analysis,
        'jockey_trainer_dynamics': jt_analysis,
        'going_and_conditions': conditions,
        'field_and_market': field_analysis,
        'categorization': categorization,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


def _get_top_contributing_factors(pick: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the top 3 factors that made us pick this horse."""
    
    # Get breakdown of score components (if available)
    score_breakdown = pick.get('score_breakdown', {})
    
    # Sort by contribution
    sorted_factors = sorted(
        score_breakdown.items(),
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    return {
        'top_3_factors': [f[0] for f in sorted_factors],
        'top_3_weights': [f[1] for f in sorted_factors],
        'was_improver_flagged': pick.get('potential_improver_flag', False),
        'had_trip_suitability_edge': pick.get('trip_suitability_score', 0) > 70,
        'market_position': _categorize_market_position(pick.get('odds_at_start', 0)),
    }


def _identify_winner_advantages(winner: Dict[str, Any], our_pick: Dict[str, Any]) -> Dict[str, Any]:
    """Identify what the winner had that our pick didn't."""
    
    # Compare signal presence
    factors_winner_had = []
    
    # Form velocity
    if winner.get('form_velocity', 0) > 0 and our_pick.get('form_velocity', 0) <= 0:
        factors_winner_had.append('form_velocity_bonus')
    
    # Class drop
    if winner.get('class_drop', False) and not our_pick.get('class_drop', False):
        factors_winner_had.append('class_drop_bonus')
    
    # Jockey upgrade
    if winner.get('jockey_upgrade', False) and not our_pick.get('jockey_upgrade', False):
        factors_winner_had.append('jockey_upgrade')
    
    # Trip suitability
    if winner.get('trip_suitability_score', 0) > our_pick.get('trip_suitability_score', 0) + 20:
        factors_winner_had.append('trip_suitability')
    
    # Course wins
    if winner.get('course_wins', 0) > our_pick.get('course_wins', 0):
        factors_winner_had.append('course_bonus')
    
    # Trainer hot form
    if winner.get('trainer_hot_form', False) and not our_pick.get('trainer_hot_form', False):
        factors_winner_had.append('trainer_form_bonus')
    
    # Determine critical signal (most important one we missed)
    critical_signal = factors_winner_had[0] if factors_winner_had else 'unknown'
    
    # Score comparison
    score_gap = winner.get('score', 0) - our_pick.get('score', 0)
    rank_gap = winner.get('rank', 99) - 1
    
    # Odds comparison
    winner_odds = winner.get('odds_at_start', 0)
    our_pick_odds = our_pick.get('odds_at_start', 0)
    winner_was_market_fav = winner_odds < 4.0
    market_disagreed = abs(winner_odds - our_pick_odds) > 2.0
    
    return {
        'factors_winner_had_we_missed': factors_winner_had,
        'score_gap': score_gap,
        'rank_gap': rank_gap,
        'odds_comparison': {
            'winner_odds': winner_odds,
            'our_pick_odds': our_pick_odds,
            'winner_was_market_favorite': winner_was_market_fav,
            'market_disagreed_with_us': market_disagreed,
        },
        'critical_signal_we_underweighted': critical_signal,
    }


def _categorize_market_position(odds: float) -> str:
    """Categorize horse's market position based on odds."""
    if odds < 3.5:
        return 'favorite'
    elif odds < 6.0:
        return 'second_fav'
    elif odds < 10.0:
        return 'mid_market'
    else:
        return 'outsider'


def _analyze_pricing_vs_performance(pick: Dict[str, Any], winner: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze if our pick was overpriced/underpriced relative to performance."""
    
    pick_odds = pick.get('odds_at_start', 0)
    pick_score = pick.get('score', 0)
    winner_odds = winner.get('odds_at_start', 0)
    
    # Simple heuristic: if score > 85 but odds > 8, possibly overpriced by market
    pick_overpriced = pick_score > 85 and pick_odds > 8.0
    
    # If score < 70 but odds < 5, possibly underpriced (market backed more than our model)
    pick_underpriced = pick_score < 70 and pick_odds < 5.0
    
    # Winner value category
    if winner_odds > 10.0:
        winner_value = 'value_bet'
    elif winner_odds >= 4.0:
        winner_value = 'fair_price'
    else:
        winner_value = 'short'
    
    return {
        'our_pick_overpriced': pick_overpriced,
        'our_pick_underpriced': pick_underpriced,
        'winner_value': winner_value,
    }


def _compare_form_trajectories(pick: Dict[str, Any], winner: Dict[str, Any]) -> Dict[str, Any]:
    """Compare form trends between our pick and winner."""
    
    pick_form_trend = pick.get('form_trend', 'stable')
    winner_form_trend = winner.get('form_trend', 'stable')
    
    # Check if recent form contradicted historical patterns
    recent_contradicted_historical = (
        pick_form_trend == 'declining' and pick.get('historical_win_rate', 0) > 0.20
    )
    
    winner_improving = winner_form_trend == 'improving'
    pick_declining = pick_form_trend == 'declining'
    
    return {
        'recent_form_contradicted_historical': recent_contradicted_historical,
        'winner_had_improving_form_trend': winner_improving,
        'our_pick_had_declining_form': pick_declining,
    }


def _analyze_jockey_trainer_performance(pick: Dict[str, Any], winner: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze jockey/trainer dynamics."""
    
    # Jockey/trainer combo strength
    winner_combo_strong = (
        winner.get('trainer_tier') in [1, 2] and 
        winner.get('jockey_tier') in [1, 2]
    )
    
    pick_jockey_downgrade = pick.get('jockey_downgrade', False)
    winner_jockey_upgrade = winner.get('jockey_upgrade', False)
    
    # Trainer hot form (3+ wins in last 14 days)
    trainer_hot_form = winner.get('trainer_hot_form', False)
    
    return {
        'jockey_trainer_combo_outperformed': winner_combo_strong,
        'our_pick_had_jockey_downgrade': pick_jockey_downgrade,
        'winner_had_jockey_upgrade': winner_jockey_upgrade,
        'trainer_hot_form_signal': trainer_hot_form,
    }


def _analyze_conditions_suitability(
    pick: Dict[str, Any],
    winner: Dict[str, Any],
    race_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze going and conditions suitability."""
    
    going = race_data.get('going', 'unknown')
    distance = race_data.get('distance', 0)
    class_level = race_data.get('class', 0)
    
    # Check if going was different from optimal
    pick_optimal_going = pick.get('optimal_going', 'good')
    going_different = going.lower() != pick_optimal_going.lower()
    
    # Check if distance was different from optimal
    pick_optimal_distance = pick.get('optimal_distance', 0)
    distance_different = abs(distance - pick_optimal_distance) > 200  # >1f difference
    
    # Class level comparison
    pick_historical_class = pick.get('average_class', 0)
    if class_level < pick_historical_class:
        class_comparison = 'class_drop'
    elif class_level > pick_historical_class:
        class_comparison = 'class_rise'
    else:
        class_comparison = 'same_class'
    
    return {
        'going_type': going,
        'going_different_than_optimal': going_different,
        'distance_different_than_optimal': distance_different,
        'class_level_vs_history': class_comparison,
    }


def _analyze_field_changes(race_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze if field composition changed after analysis."""
    
    field_size = race_data.get('field_size', 0)
    nonrunners = race_data.get('nonrunners', [])
    late_declarations = race_data.get('late_declarations', [])
    
    field_changed = len(nonrunners) >= 2 or len(late_declarations) >= 1
    
    return {
        'field_size': field_size,
        'field_changed_after_analysis': field_changed,
        'winner_late_declaration': False,  # Would need to check if winner in late_declarations
        'nonrunners_affected_outcome': len(nonrunners) > 0,
    }


def _categorize_miss_with_fix_estimate(
    pick: Dict[str, Any],
    winner: Dict[str, Any],
    winner_advantages: Dict[str, Any]
) -> Dict[str, Any]:
    """Categorize the miss and estimate how to fix it."""
    
    score_gap = winner_advantages['score_gap']
    critical_signal = winner_advantages['critical_signal_we_underweighted']
    
    # Determine primary reason
    if winner_advantages['rank_gap'] > 10:
        primary_reason = 'winner_not_in_top_picks'
        severity = 'high'
        is_fixable = True
        estimated_adjustment = int(abs(score_gap)) + 10
    elif winner_advantages.get('factors_winner_had_we_missed'):
        primary_reason = 'model_underweighted_signal'
        severity = 'high'
        is_fixable = True
        estimated_adjustment = int(abs(score_gap)) + 5
    elif score_gap < -10:
        primary_reason = 'winner_scored_much_lower'
        severity = 'medium'
        is_fixable = False  # Our model saw winner as weak
        estimated_adjustment = 0
    else:
        primary_reason = 'close_call'
        severity = 'low'
        is_fixable = True
        estimated_adjustment = int(abs(score_gap))
    
    return {
        'primary_miss_reason': primary_reason,
        'severity': severity,
        'is_fixable': is_fixable,
        'estimated_point_adjustment': estimated_adjustment,
    }
```

---

## Example 2: Automated Weight Adjustment

Add to `backend/pipeline/learning/auto_adjustment_rules.py`:

```python
"""
Automated Weight Adjustment Rules

Rules are applied weekly (Sunday 23:00 UTC) after pattern analysis.
Each rule has safety limits to prevent over-adjustment.
"""

from typing import Dict, List, Any, Tuple
import logging
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


AUTO_ADJUSTMENT_RULES = {
    'decrease_weight_when_factor_in_10_losses': {
        'enabled': True,
        'threshold': 10,
        'adjustment': -2,
        'max_decrease_per_week': -10,
        'applies_to': 'all_weights',
    },
    'increase_weight_when_factor_in_10_wins': {
        'enabled': True,
        'threshold': 10,
        'adjustment': +3,
        'max_increase_per_week': +15,
        'applies_to': 'all_weights',
    },
    'boost_improver_signal_when_underperforming': {
        'enabled': True,
        'condition': 'improver_demoted > 30% of weekly misses',
        'adjustment': +10,
        'max_boost': 50,
        'affects': ['form_velocity_bonus', 'bounce_back_bonus', 'short_form_improvement'],
    },
    'reduce_market_dependence_when_market_wrong': {
        'enabled': True,
        'condition': 'market_favorite_won < 40% when we picked different',
        'adjustment': -2,
        'affects': ['favorite_correction', 'sweet_spot', 'optimal_odds'],
    },
}


def apply_automated_adjustments(
    weekly_analysis: Dict[str, Any],
    current_weights: Dict[str, float],
    rules: Dict[str, Any] = AUTO_ADJUSTMENT_RULES
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """
    Apply automated weight adjustments based on learning rules.
    
    Args:
        weekly_analysis: Output from weekly pattern analysis
        current_weights: Current weight values from DynamoDB
        rules: Adjustment rules to apply
    
    Returns:
        (updated_weights, changes_log)
    """
    
    updated_weights = current_weights.copy()
    changes_log = []
    
    logger.info("Applying automated weight adjustments...")
    
    # Rule 1: Decrease weight for factors in consecutive losses
    if rules['decrease_weight_when_factor_in_10_losses']['enabled']:
        factors_in_losses = _identify_factors_in_consecutive_losses(
            weekly_analysis,
            threshold=rules['decrease_weight_when_factor_in_10_losses']['threshold']
        )
        
        for factor, count in factors_in_losses.items():
            adjustment = rules['decrease_weight_when_factor_in_10_losses']['adjustment']
            old_value = updated_weights.get(factor, 0)
            new_value = max(0, old_value + adjustment)
            
            # Apply max decrease limit
            max_decrease = rules['decrease_weight_when_factor_in_10_losses']['max_decrease_per_week']
            if new_value < old_value + max_decrease:
                new_value = old_value + max_decrease
            
            updated_weights[factor] = new_value
            changes_log.append({
                'weight': factor,
                'rule': 'decrease_weight_when_factor_in_10_losses',
                'old_value': old_value,
                'new_value': new_value,
                'adjustment': new_value - old_value,
                'reason': f'Factor present in {count} consecutive losses',
            })
            logger.info(f"Decreased {factor}: {old_value} → {new_value} (in {count} losses)")
    
    # Rule 2: Increase weight for factors in consecutive wins
    if rules['increase_weight_when_factor_in_10_wins']['enabled']:
        factors_in_wins = _identify_factors_in_consecutive_wins(
            weekly_analysis,
            threshold=rules['increase_weight_when_factor_in_10_wins']['threshold']
        )
        
        for factor, count in factors_in_wins.items():
            adjustment = rules['increase_weight_when_factor_in_10_wins']['adjustment']
            old_value = updated_weights.get(factor, 0)
            new_value = old_value + adjustment
            
            # Apply max increase limit
            max_increase = rules['increase_weight_when_factor_in_10_wins']['max_increase_per_week']
            if new_value > old_value + max_increase:
                new_value = old_value + max_increase
            
            updated_weights[factor] = new_value
            changes_log.append({
                'weight': factor,
                'rule': 'increase_weight_when_factor_in_10_wins',
                'old_value': old_value,
                'new_value': new_value,
                'adjustment': new_value - old_value,
                'reason': f'Factor present in {count} consecutive wins',
            })
            logger.info(f"Increased {factor}: {old_value} → {new_value} (in {count} wins)")
    
    # Rule 3: Boost improver signal if underperforming
    if rules['boost_improver_signal_when_underperforming']['enabled']:
        improver_miss_count = weekly_analysis.get('patterns', {}).get('category_distribution', {}).get('improver_demoted', 0)
        total_misses = weekly_analysis.get('summary', {}).get('model_misses', 1)
        improver_miss_rate = improver_miss_count / total_misses if total_misses > 0 else 0
        
        if improver_miss_rate > 0.30:
            improver_weights = rules['boost_improver_signal_when_underperforming']['affects']
            adjustment = rules['boost_improver_signal_when_underperforming']['adjustment']
            max_boost = rules['boost_improver_signal_when_underperforming']['max_boost']
            
            for weight in improver_weights:
                old_value = updated_weights.get(weight, 0)
                new_value = min(old_value + adjustment, max_boost)
                updated_weights[weight] = new_value
                changes_log.append({
                    'weight': weight,
                    'rule': 'boost_improver_signal_when_underperforming',
                    'old_value': old_value,
                    'new_value': new_value,
                    'adjustment': new_value - old_value,
                    'reason': f'Improver miss rate {improver_miss_rate:.1%} > 30% threshold',
                })
                logger.info(f"Boosted improver weight {weight}: {old_value} → {new_value}")
    
    # Rule 4: Reduce market dependence when market wrong
    if rules['reduce_market_dependence_when_market_wrong']['enabled']:
        # Need to calculate market favorite win rate from weekly analysis
        market_fav_wins = 0
        market_divergence_cases = 0
        
        # This would come from divergence analysis (Phase 2)
        # For now, use a placeholder
        market_fav_win_rate = weekly_analysis.get('market_analysis', {}).get('market_favorite_win_rate', 0.50)
        
        if market_fav_win_rate < 0.40:
            market_weights = rules['reduce_market_dependence_when_market_wrong']['affects']
            adjustment = rules['reduce_market_dependence_when_market_wrong']['adjustment']
            
            for weight in market_weights:
                old_value = updated_weights.get(weight, 0)
                new_value = max(0, old_value + adjustment)
                updated_weights[weight] = new_value
                changes_log.append({
                    'weight': weight,
                    'rule': 'reduce_market_dependence_when_market_wrong',
                    'old_value': old_value,
                    'new_value': new_value,
                    'adjustment': new_value - old_value,
                    'reason': f'Market favorite win rate {market_fav_win_rate:.1%} < 40%',
                })
                logger.info(f"Reduced market weight {weight}: {old_value} → {new_value}")
    
    logger.info(f"Applied {len(changes_log)} weight adjustments")
    return updated_weights, changes_log


def _identify_factors_in_consecutive_losses(
    weekly_analysis: Dict[str, Any],
    threshold: int = 10
) -> Dict[str, int]:
    """
    Identify factors that appear in consecutive losses.
    
    Args:
        weekly_analysis: Weekly pattern analysis
        threshold: Minimum consecutive appearances
    
    Returns:
        Dict of {factor_name: count}
    """
    
    # Get detailed loss analyses
    loss_analyses = weekly_analysis.get('detailed_analyses', [])
    
    # Count factor appearances in losses
    factor_counts = Counter()
    
    for loss in loss_analyses:
        factors = loss.get('why_we_picked_this_horse', {}).get('top_3_factors', [])
        for factor in factors:
            factor_counts[factor] += 1
    
    # Filter to those above threshold
    consecutive_losses = {
        factor: count
        for factor, count in factor_counts.items()
        if count >= threshold
    }
    
    return consecutive_losses


def _identify_factors_in_consecutive_wins(
    weekly_analysis: Dict[str, Any],
    threshold: int = 10
) -> Dict[str, int]:
    """
    Identify factors that appear in consecutive wins.
    
    Similar to losses but for wins.
    """
    
    # This would analyze WIN_ANALYSIS records (Phase 2)
    # For now, return empty dict
    
    # Placeholder logic:
    # win_analyses = fetch_wins_from_weekly_analysis(weekly_analysis)
    # factor_counts = Counter()
    # for win in win_analyses:
    #     factors = win.get('success_factors', {}).get('top_3_signals_that_worked', [])
    #     for factor in factors:
    #         factor_counts[factor] += 1
    
    return {}
```

---

## Example 3: Manual Review Alert System

Add to `backend/pipeline/learning/handler.py`:

```python
import boto3

sns_client = boto3.client('sns', region_name='eu-west-1')
SNS_TOPIC_ARN = 'arn:aws:sns:eu-west-1:ACCOUNT_ID:betbudai-learning-alerts'


MANUAL_REVIEW_TRIGGERS = {
    'critical_performance_drop': {
        'condition': 'strike_rate < 0.40 for 3 consecutive days',
        'severity': 'critical',
        'channels': ['email', 'sms'],
    },
    'new_signal_opportunity': {
        'condition': 'consistent_winner_pattern detected > 5/week',
        'severity': 'medium',
        'channels': ['email'],
    },
    'weight_divergence': {
        'condition': 'weight adjusted > 20 points in single week',
        'severity': 'high',
        'channels': ['email'],
    },
    'field_composition_failure': {
        'condition': 'winner_not_in_field > 40% for 2 consecutive days',
        'severity': 'critical',
        'channels': ['email', 'sms'],
    },
}


def check_manual_review_triggers(
    daily_metrics: Dict[str, Any],
    weekly_analysis: Dict[str, Any],
    changes_log: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Check if any conditions require manual human review.
    
    Returns list of alerts to send.
    """
    
    alerts = []
    
    # Critical performance drop
    rolling_7day_sr = daily_metrics.get('rolling_7day', {}).get('strike_rate', 1.0)
    if rolling_7day_sr < 0.40:
        consecutive_days = _count_consecutive_low_strike_days(daily_metrics)
        if consecutive_days >= 3:
            alerts.append({
                'trigger': 'critical_performance_drop',
                'severity': 'critical',
                'message': (
                    f"CRITICAL ALERT: Strike rate dropped to {rolling_7day_sr:.1%} "
                    f"for {consecutive_days} consecutive days. Immediate review required."
                ),
                'notification_channels': ['email', 'sms'],
                'data': {
                    'strike_rate': rolling_7day_sr,
                    'consecutive_days': consecutive_days,
                    'target': 0.60,
                    'gap': rolling_7day_sr - 0.60,
                }
            })
    
    # New signal opportunity
    new_signals = weekly_analysis.get('missing_signals', {}).get('consistent_winner_patterns_not_captured', [])
    for signal in new_signals:
        if signal.get('frequency', 0) >= 5:
            alerts.append({
                'trigger': 'new_signal_opportunity',
                'severity': 'medium',
                'message': (
                    f"OPPORTUNITY: New pattern detected - {signal['pattern_description']}. "
                    f"Appeared {signal['frequency']} times this week. Consider adding signal."
                ),
                'notification_channels': ['email'],
                'data': signal,
            })
    
    # Weight divergence
    for change in changes_log:
        adjustment = abs(change.get('new_value', 0) - change.get('old_value', 0))
        if adjustment > 20:
            alerts.append({
                'trigger': 'weight_divergence',
                'severity': 'high',
                'message': (
                    f"WARNING: Weight {change['weight']} adjusted by {adjustment:.0f} points "
                    f"({change['old_value']:.0f} → {change['new_value']:.0f}). "
                    f"Reason: {change.get('reason', 'Unknown')}. Verify intended."
                ),
                'notification_channels': ['email'],
                'data': change,
            })
    
    # Field composition failure
    winner_not_in_field_count = 0
    total_misses = 0
    
    category_dist = weekly_analysis.get('patterns', {}).get('category_distribution', {})
    winner_not_in_field_count = category_dist.get('winner_not_in_field', 0)
    total_misses = sum(category_dist.values())
    
    if total_misses > 0:
        field_failure_rate = winner_not_in_field_count / total_misses
        if field_failure_rate > 0.40:
            alerts.append({
                'trigger': 'field_composition_failure',
                'severity': 'critical',
                'message': (
                    f"CRITICAL: {winner_not_in_field_count} winners not in analyzed field "
                    f"({field_failure_rate:.1%} of misses). Field verification system failing. "
                    f"Check Betfair API and field_change_detector deployment immediately."
                ),
                'notification_channels': ['email', 'sms'],
                'data': {
                    'winner_not_in_field_count': winner_not_in_field_count,
                    'total_misses': total_misses,
                    'failure_rate': field_failure_rate,
                }
            })
    
    return alerts


def send_alerts(alerts: List[Dict[str, Any]]):
    """Send alerts via SNS."""
    
    for alert in alerts:
        message = alert['message']
        subject = f"BetBudAI Alert: {alert['trigger']}"
        
        # Add data context
        if 'data' in alert:
            message += f"\n\nData:\n{json.dumps(alert['data'], indent=2)}"
        
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=message,
            )
            logger.info(f"Sent alert: {alert['trigger']}")
        except Exception as e:
            logger.error(f"Failed to send alert {alert['trigger']}: {e}")


def _count_consecutive_low_strike_days(daily_metrics: Dict[str, Any]) -> int:
    """Count consecutive days with strike rate < 40%."""
    
    # This would query historical daily_metrics from DynamoDB
    # For now, return placeholder
    
    return 3  # Placeholder
```

---

## Example 4: Integration with Evening Handler

Update `backend/pipeline/evening/miss_analysis_handler.py`:

```python
from backend.core.miss_analyzer import analyze_loss_deeply
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
insights_table = dynamodb.Table('BetBudAI_LearningInsights')


def lambda_handler(event, context):
    """Evening miss analysis handler with deep insights."""
    
    try:
        target_date = event.get('target_date')
        if not target_date:
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            target_date = yesterday.strftime('%Y-%m-%d')
        
        logger.info(f"Starting enhanced miss analysis for {target_date}")
        
        # Fetch yesterday's races
        race_items = _fetch_yesterday_races(target_date)
        if not race_items:
            return {'statusCode': 200, 'body': json.dumps({'message': 'No races'})}
        
        # Extract race data
        races = _extract_race_data(race_items)
        
        # Analyze each miss with DEEP analysis
        miss_analyses = []
        hits = []
        
        for race_key, race_data in races.items():
            picks = race_data.get('picks', [])
            winner = race_data.get('actual_winner')
            
            if not picks or not winner:
                continue
            
            top_pick_id = picks[0].get('horse_id')
            winner_id = winner.get('horse_id')
            
            if top_pick_id == winner_id:
                # Hit - store for win analysis (Phase 2)
                hits.append({
                    'race': race_key,
                    'pick': picks[0].get('horse_name'),
                    'odds': picks[0].get('odds_at_start')
                })
            else:
                # Miss - DEEP ANALYSIS
                all_runners = race_data.get('all_runners', [])
                
                deep_analysis = analyze_loss_deeply(
                    top_pick=picks[0],
                    actual_winner=winner,
                    all_runners=all_runners,
                    race_data=race_data
                )
                
                miss_analyses.append(deep_analysis)
                
                # Store in DynamoDB
                _store_loss_insight(target_date, race_key, deep_analysis)
        
        # Aggregate patterns (existing logic)
        categories = [m.get('categorization', {}).get('primary_miss_reason') for m in miss_analyses]
        category_counts = Counter(categories)
        
        total_races = len(hits) + len(miss_analyses)
        hit_rate = len(hits) / total_races if total_races > 0 else 0
        
        response_data = {
            'target_date': target_date,
            'total_races': total_races,
            'hits': len(hits),
            'misses': len(miss_analyses),
            'hit_rate': f"{hit_rate:.1%}",
            'category_distribution': dict(category_counts),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(
            f"Enhanced miss analysis complete: {len(hits)} hits, {len(miss_analyses)} misses "
            f"({hit_rate:.1%} hit rate)"
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(response_data, default=str)
        }
    
    except Exception as e:
        logger.error(f"Evening miss analysis failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def _store_loss_insight(analysis_date: str, race_key: str, analysis: Dict[str, Any]):
    """Store deep loss analysis in DynamoDB."""
    
    try:
        # Convert floats to Decimal for DynamoDB
        analysis_decimal = json.loads(
            json.dumps(analysis),
            parse_float=Decimal
        )
        
        insights_table.put_item(
            Item={
                'analysis_date': analysis_date,
                'analysis_type': f'daily_loss#{race_key}',
                'analysis_data': analysis_decimal,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ttl_timestamp': int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp()),
            }
        )
        logger.info(f"Stored loss insight for {race_key}")
    except Exception as e:
        logger.error(f"Failed to store loss insight: {e}")
```

---

## Quick Deploy Script

Create `scripts/deploy_enhanced_learning.sh`:

```bash
#!/bin/bash
set -e

echo "=========================================="
echo "Deploying Enhanced Learning System - Phase 1"
echo "=========================================="

# Step 1: Create DynamoDB tables
echo "[1/6] Creating DynamoDB tables..."
aws dynamodb create-table \
  --table-name BetBudAI_LearningInsights \
  --attribute-definitions \
    AttributeName=analysis_date,AttributeType=S \
    AttributeName=analysis_type,AttributeType=S \
  --key-schema \
    AttributeName=analysis_date,KeyType=HASH \
    AttributeName=analysis_type,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1 || echo "Table already exists"

aws dynamodb create-table \
  --table-name BetBudAI_WeightChangelog \
  --attribute-definitions \
    AttributeName=change_date,AttributeType=S \
    AttributeName=change_timestamp,AttributeType=S \
  --key-schema \
    AttributeName=change_date,KeyType=HASH \
    AttributeName=change_timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1 || echo "Table already exists"

echo "[2/6] Updating Lambda layers..."
cd backend
pip install -r requirements.txt -t ./python
zip -r core-layer.zip python/
aws lambda publish-layer-version \
  --layer-name surebet-core \
  --zip-file fileb://core-layer.zip \
  --compatible-runtimes python3.11 \
  --region eu-west-1

echo "[3/6] Deploying evening-miss-analysis Lambda..."
cd pipeline/evening
zip -r miss_analysis.zip handler.py
aws lambda update-function-code \
  --function-name surebet-evening-miss-analysis \
  --zip-file fileb://miss_analysis.zip \
  --region eu-west-1

echo "[4/6] Deploying learning Lambda..."
cd ../learning
zip -r learning.zip handler.py auto_adjustment_rules.py
aws lambda update-function-code \
  --function-name surebet-learning \
  --zip-file fileb://learning.zip \
  --region eu-west-1

echo "[5/6] Creating SNS topic for alerts..."
SNS_ARN=$(aws sns create-topic --name betbudai-learning-alerts --region eu-west-1 --query 'TopicArn' --output text)
echo "SNS Topic ARN: $SNS_ARN"

echo "[6/6] Testing deployment..."
aws lambda invoke \
  --function-name surebet-evening-miss-analysis \
  --payload '{"target_date": "2026-05-19"}' \
  --region eu-west-1 \
  test-output.json
cat test-output.json

echo ""
echo "=========================================="
echo "Phase 1 Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Subscribe to SNS topic: $SNS_ARN"
echo "2. Monitor CloudWatch logs for errors"
echo "3. Review first day's learning insights in DynamoDB"
echo "4. Check weight adjustments in changelog table"
echo ""
```

Make executable:
```bash
chmod +x scripts/deploy_enhanced_learning.sh
```

---

**Implementation Notes**:
1. Start with Phase 1 examples above
2. Test each function independently before integration
3. Monitor CloudWatch logs closely for first 48 hours
4. Review first week's weight changes manually before trusting automation
5. Adjust thresholds in `AUTO_ADJUSTMENT_RULES` based on observed patterns

**Files to Create/Modify**:
- `backend/core/miss_analyzer.py` - Add deep analysis functions
- `backend/pipeline/learning/auto_adjustment_rules.py` - New file
- `backend/pipeline/learning/handler.py` - Add automation logic
- `backend/pipeline/evening/miss_analysis_handler.py` - Integrate deep analysis
- `scripts/deploy_enhanced_learning.sh` - Deployment script
