# Enhanced Learning System Design - BetBudAI
**Version**: 2.0  
**Created**: May 20, 2026  
**Target**: Transform 18.64% strike rate to 60-70% through systematic daily learning  
**Expected Impact**: +150-200 winners/week through continuous improvement

---

## Executive Summary

BetBudAI's current learning system (`backend/pipeline/learning/handler.py` + `backend/core/miss_analyzer.py`) performs basic miss categorization but lacks the depth needed to extract actionable insights from each race. This design adds:

1. **Daily Learning Questions** - Comprehensive post-race analysis checklist
2. **Weekly Pattern Recognition** - Aggregate analysis to identify systematic biases
3. **Automated Weight Adjustments** - Rules-based learning that improves model daily
4. **Manual Review Triggers** - Alert system for critical issues requiring human intervention
5. **Continuous Improvement Metrics** - Track learning velocity and model evolution

---

## Section 1: Daily Learning Questions (After Each Race Result)

### Current State
- Basic categorization: `improver_demoted`, `underranked`, `long_shot`, `winner_not_in_field`, `model_miss`
- Simple feature comparison: score_gap, trip_gap, trainer_form, jockey_form
- No structured question framework for extracting insights

### Enhanced Framework

#### 1.1 For EACH LOSS (Top Pick Did Not Win)

**Core Questions to Store in DynamoDB:**

```python
LOSS_ANALYSIS_SCHEMA = {
    'market_id': str,
    'bet_date': str,
    'race_time': str,
    'our_pick': {
        'horse_name': str,
        'horse_id': str,
        'score': float,
        'rank': int,
        'odds_at_start': float,
        'actual_finish': int,  # 1st, 2nd, 3rd, unplaced
    },
    'actual_winner': {
        'horse_name': str,
        'horse_id': str,
        'score': float,  # our score for this horse
        'rank': int,     # our ranking for this horse
        'odds_at_win': float,
    },
    
    # CRITICAL LEARNING QUESTIONS
    'why_we_picked_this_horse': {
        'top_3_factors': [str],  # e.g., ['recent_win', 'trainer_reputation', 'course_bonus']
        'top_3_weights': [float],  # corresponding weight contributions
        'was_improver_flagged': bool,
        'had_trip_suitability_edge': bool,
        'market_position': str,  # 'favorite', 'second_fav', 'mid_market', 'outsider'
    },
    
    'why_winner_beat_us': {
        'factors_winner_had_we_missed': [str],  # e.g., ['form_velocity', 'class_drop', 'jockey_upgrade']
        'score_gap': float,  # winner_score - our_pick_score (negative if winner scored lower)
        'rank_gap': int,     # winner_rank - 1 (how far down our list was winner)
        'odds_comparison': {
            'winner_odds': float,
            'our_pick_odds': float,
            'winner_was_market_favorite': bool,
            'market_disagreed_with_us': bool,  # True if winner was market fav but we picked different
        },
        'critical_signal_we_underweighted': str,  # single most important missed signal
    },
    
    'pricing_analysis': {
        'our_pick_overpriced': bool,  # odds > fair value based on score
        'our_pick_underpriced': bool,  # odds < fair value (market backed more than us)
        'winner_value': str,  # 'value_bet' (>10/1), 'fair_price' (4-10), 'short' (<4/1)
    },
    
    'form_vs_history': {
        'recent_form_contradicted_historical': bool,
        'winner_had_improving_form_trend': bool,  # form_velocity positive
        'our_pick_had_declining_form': bool,
    },
    
    'pace_and_trip': {
        'pace_scenario': str,  # 'fast_pace', 'steady_pace', 'slow_pace'
        'winner_suited_pace': bool,
        'our_pick_suited_pace': bool,
        'trip_bias_existed': bool,  # e.g., front-runners dominated, closers won
        'we_missed_trip_bias': bool,
    },
    
    'jockey_trainer_dynamics': {
        'jockey_trainer_combo_outperformed': bool,  # winner had strong combo we underweighted
        'our_pick_had_jockey_downgrade': bool,
        'winner_had_jockey_upgrade': bool,
        'trainer_hot_form_signal': bool,  # trainer on 3+ win streak
    },
    
    'going_and_conditions': {
        'going_type': str,  # 'good', 'good_to_soft', 'heavy', etc.
        'going_different_than_optimal': bool,  # race going != horse's optimal going
        'distance_different_than_optimal': bool,
        'class_level_vs_history': str,  # 'class_drop', 'class_rise', 'same_class'
    },
    
    'field_and_market': {
        'field_size': int,
        'field_changed_after_analysis': bool,  # late withdrawals/declarations
        'winner_late_declaration': bool,  # winner wasn't in morning field
        'nonrunners_affected_outcome': bool,
    },
    
    'categorization': {
        'primary_miss_reason': str,  # from existing categories + new ones
        'severity': str,  # 'critical', 'high', 'medium', 'low'
        'is_fixable': bool,  # can we adjust weights or need new data?
        'estimated_point_adjustment': int,  # how many points would have moved winner to #1
    },
    
    'timestamp': str,
}
```

**Implementation in `backend/core/miss_analyzer.py`:**

Add new function:
```python
def analyze_loss_deeply(
    top_pick: Dict[str, Any],
    actual_winner: Dict[str, Any],
    all_runners: List[Dict[str, Any]],
    race_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep dive analysis extracting structured learning insights.
    
    Returns complete LOSS_ANALYSIS_SCHEMA record for storage.
    """
    
    # Extract what factors made us pick this horse
    top_factors = _get_top_contributing_factors(top_pick)
    
    # Identify what winner had that we missed
    winner_advantages = _identify_winner_advantages(actual_winner, top_pick)
    
    # Pricing analysis
    pricing = _analyze_pricing_vs_performance(top_pick, actual_winner)
    
    # Form trends
    form_analysis = _compare_form_trajectories(top_pick, actual_winner)
    
    # Pace/trip (requires race pace data - may need to scrape)
    pace_analysis = _analyze_pace_dynamics(race_data, all_runners)
    
    # Jockey/trainer
    jt_analysis = _analyze_jockey_trainer_performance(top_pick, actual_winner)
    
    # Going/conditions
    conditions = _analyze_conditions_suitability(top_pick, actual_winner, race_data)
    
    # Field composition
    field_analysis = _analyze_field_changes(race_data)
    
    # Categorize severity and fixability
    categorization = _categorize_miss_with_fix_estimate(
        top_pick, actual_winner, winner_advantages
    )
    
    return {
        'our_pick': _extract_pick_summary(top_pick),
        'actual_winner': _extract_winner_summary(actual_winner),
        'why_we_picked_this_horse': top_factors,
        'why_winner_beat_us': winner_advantages,
        'pricing_analysis': pricing,
        'form_vs_history': form_analysis,
        'pace_and_trip': pace_analysis,
        'jockey_trainer_dynamics': jt_analysis,
        'going_and_conditions': conditions,
        'field_and_market': field_analysis,
        'categorization': categorization,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
```

#### 1.2 For EACH WIN (Top Pick Won)

**Win Analysis Schema:**

```python
WIN_ANALYSIS_SCHEMA = {
    'market_id': str,
    'bet_date': str,
    'race_time': str,
    'our_winning_pick': {
        'horse_name': str,
        'horse_id': str,
        'score': float,
        'odds_at_start': float,
        'odds_at_settlement': float,
    },
    
    'success_factors': {
        'top_3_signals_that_worked': [str],  # e.g., ['form_velocity_bonus', 'class_drop_bonus', 'trainer_course_bonus']
        'signal_weights_that_contributed': [float],
        'was_improver_flagged': bool,
        'improver_boost_applied': bool,
        'trip_suitability_score': float,
    },
    
    'confidence_validation': {
        'score_vs_field_average': float,  # how much better than field
        'score_vs_second_pick': float,    # separation from our #2 pick
        'market_confidence': str,  # 'favorite', 'second_fav', 'value_winner'
        'odds_category': str,  # 'short' (<4/1), 'mid' (4-8/1), 'value' (8-15/1), 'longshot' (>15/1)
    },
    
    'what_made_this_different_from_losses': {
        'unique_signal_present': str,  # signal present here but missing in recent losses
        'signal_strength_vs_avg': float,  # how strong was winning signal vs average
        'avoided_common_trap': str,  # e.g., 'avoided_heavy_going', 'avoided_large_field'
    },
    
    'pattern_identification': {
        'course_type': str,  # 'flat', 'NH', 'AW'
        'venue': str,
        'distance_category': str,  # 'sprint', 'middle', 'staying'
        'going': str,
        'class_level': str,
        'field_size': int,
        'time_of_day': str,  # 'morning', 'afternoon', 'evening'
        'is_replicable_pattern': bool,  # can we find similar races?
    },
    
    'roi_impact': {
        'stake': float,
        'return': float,
        'profit': float,
        'roi_percent': float,
        'contribution_to_daily_pnl': float,
    },
    
    'timestamp': str,
}
```

**Implementation:**

Add to `backend/core/miss_analyzer.py`:
```python
def analyze_win_deeply(
    winning_pick: Dict[str, Any],
    all_runners: List[Dict[str, Any]],
    race_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze successful pick to reinforce what worked.
    
    Returns WIN_ANALYSIS_SCHEMA record.
    """
    
    # What signals contributed most
    success_factors = _extract_winning_signals(winning_pick)
    
    # Confidence validation (was it deserved or lucky?)
    confidence = _validate_win_confidence(winning_pick, all_runners)
    
    # What made this different from recent losses
    differentiators = _identify_winning_differentiators(winning_pick)
    
    # Pattern for replication
    pattern = _extract_replicable_pattern(race_data, winning_pick)
    
    # ROI contribution
    roi = _calculate_win_roi_impact(winning_pick)
    
    return {
        'our_winning_pick': _extract_pick_summary(winning_pick),
        'success_factors': success_factors,
        'confidence_validation': confidence,
        'what_made_this_different_from_losses': differentiators,
        'pattern_identification': pattern,
        'roi_impact': roi,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
```

#### 1.3 For MARKET DIVERGENCE (Our Pick vs Market Favorite)

**Divergence Analysis Schema:**

```python
DIVERGENCE_ANALYSIS_SCHEMA = {
    'market_id': str,
    'bet_date': str,
    'race_time': str,
    
    'our_pick': {
        'horse_name': str,
        'score': float,
        'odds': float,
        'market_rank': int,  # market's ranking (1=fav, 2=2nd fav, etc)
    },
    
    'market_favorite': {
        'horse_name': str,
        'our_score_for_this_horse': float,  # what we scored the market fav
        'our_rank_for_this_horse': int,
        'odds': float,
    },
    
    'actual_winner': {
        'horse_name': str,
        'was_our_pick': bool,
        'was_market_fav': bool,
        'odds': float,
    },
    
    'divergence_analysis': {
        'divergence_category': str,  # 'we_backed_longshot', 'we_backed_fav', 'we_backed_mid_market'
        'outcome': str,  # 'we_won', 'market_won', 'neither_won'
        
        # When our pick was NOT market favorite
        'why_we_disagreed_with_market': {
            'signals_we_valued_market_didnt': [str],
            'market_possibly_missing': str,  # 'form_trend', 'trip_suitability', etc.
            'our_edge_hypothesis': str,
        },
        
        # When market favorite won and we missed it
        'why_market_was_right': {
            'signals_market_saw_we_missed': [str],
            'our_model_weakness': str,
            'should_increase_weight_on': [str],
        },
        
        # When our longshot won
        'what_edge_did_we_have': {
            'unique_signal': str,
            'market_inefficiency_exploited': str,
            'replicable_edge': bool,
        },
        
        # Systematic market bias detection
        'market_bias_detected': {
            'type': str,  # 'overvalues_recent_wins', 'undervalues_class_drops', etc.
            'exploitable': bool,
            'frequency': str,  # how often does this bias appear
        },
    },
    
    'timestamp': str,
}
```

**Implementation:**

```python
def analyze_market_divergence(
    our_pick: Dict[str, Any],
    market_favorite: Dict[str, Any],
    actual_winner: Dict[str, Any],
    all_runners: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze divergence between our model and market to detect edges.
    """
    
    # Categorize divergence type
    divergence_cat = _categorize_divergence(our_pick, market_favorite)
    
    # Determine outcome
    outcome = _determine_divergence_outcome(our_pick, market_favorite, actual_winner)
    
    # Analyze why we disagreed
    if our_pick['horse_id'] != market_favorite['horse_id']:
        disagreement = _analyze_disagreement_reasons(our_pick, market_favorite)
    
    # If market won, why?
    if actual_winner['horse_id'] == market_favorite['horse_id'] and actual_winner['horse_id'] != our_pick['horse_id']:
        market_right = _analyze_why_market_was_right(market_favorite, our_pick)
    
    # If we won with longshot, what edge?
    if actual_winner['horse_id'] == our_pick['horse_id'] and our_pick['odds'] > market_favorite['odds']:
        our_edge = _identify_our_edge(our_pick, market_favorite)
    
    # Detect systematic biases
    bias = _detect_market_bias(our_pick, market_favorite, actual_winner, all_runners)
    
    return {
        'our_pick': _extract_pick_summary(our_pick),
        'market_favorite': _extract_market_fav_summary(market_favorite),
        'actual_winner': _extract_winner_summary(actual_winner),
        'divergence_analysis': {
            'divergence_category': divergence_cat,
            'outcome': outcome,
            'why_we_disagreed_with_market': disagreement if 'disagreement' in locals() else {},
            'why_market_was_right': market_right if 'market_right' in locals() else {},
            'what_edge_did_we_have': our_edge if 'our_edge' in locals() else {},
            'market_bias_detected': bias,
        },
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
```

---

## Section 2: Weekly Learning Questions (Aggregate Analysis)

### Current State
- Basic category counts: `category_distribution`
- Simple statistics: `avg_score_gap`, `median_score_gap`
- Top missing factors (limited to 5)
- Recommendations generated but not automatically applied

### Enhanced Weekly Framework

**Run every Sunday at 23:00 UTC via `backend/pipeline/learning/handler.py`**

#### 2.1 Pattern Recognition Queries

```python
WEEKLY_PATTERN_ANALYSIS = {
    'analysis_period': {
        'start_date': str,
        'end_date': str,
        'total_races': int,
        'total_picks': int,
    },
    
    'trainer_performance': {
        'trainers_outperforming_expectations': [
            {
                'trainer_name': str,
                'expected_wins': int,  # based on our model scores
                'actual_wins': int,
                'outperformance': float,  # (actual - expected) / expected
                'recommended_weight_increase': int,
            }
        ],
        'trainers_underperforming_expectations': [
            {
                'trainer_name': str,
                'expected_wins': int,
                'actual_wins': int,
                'underperformance': float,
                'recommended_weight_decrease': int,
            }
        ],
    },
    
    'course_performance': {
        'courses_with_different_patterns': [
            {
                'course_name': str,
                'our_strike_rate': float,
                'expected_strike_rate': float,
                'pattern_difference': str,  # e.g., 'favors_front_runners', 'class_drops_dominate'
                'sample_size': int,
                'pattern_reliability': str,  # 'high', 'medium', 'low' based on sample size
            }
        ],
    },
    
    'form_pattern_analysis': {
        'winning_form_combinations': [
            {
                'form_pattern': str,  # e.g., '121', '211', '311', '142'
                'wins': int,
                'appearances': int,
                'strike_rate': float,
                'currently_weighted': bool,
                'should_add_signal': bool,
            }
        ],
    },
    
    'weight_effectiveness': {
        'weights_predicting_winners': [
            {
                'weight_name': str,
                'appears_in_winners': int,
                'appears_in_losers': int,
                'win_rate_when_present': float,
                'current_weight_value': float,
                'recommended_adjustment': str,  # '+5', '-3', 'no change'
            }
        ],
        'weights_predicting_losers': [
            {
                'weight_name': str,
                'appears_in_winners': int,
                'appears_in_losers': int,
                'loss_rate_when_present': float,
                'current_weight_value': float,
                'recommended_adjustment': str,
            }
        ],
    },
    
    'missing_signals': {
        'consistent_winner_patterns_not_captured': [
            {
                'pattern_description': str,  # e.g., 'Trainer+Jockey combo at specific venue'
                'frequency': int,  # how many winners had this
                'current_signal_exists': bool,
                'estimated_impact': str,  # '+10-15 winners/week'
                'implementation_priority': str,  # 'critical', 'high', 'medium', 'low'
            }
        ],
    },
    
    'weight_interactions': {
        'synergistic_combinations': [
            {
                'weight_1': str,
                'weight_2': str,
                'combined_win_rate': float,  # win rate when BOTH present
                'individual_win_rates': [float, float],
                'synergy_bonus_recommended': int,
            }
        ],
    },
    
    'timestamp': str,
}
```

#### 2.2 Performance Analysis Queries

```python
WEEKLY_PERFORMANCE_METRICS = {
    'overall_metrics': {
        'total_picks': int,
        'winners': int,
        'losers': int,
        'strike_rate': float,
        'roi_percent': float,
        'profit_loss': float,
        'average_winning_odds': float,
        'average_losing_odds': float,
    },
    
    'strike_rate_by_odds_range': {
        '2_to_4': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        '4_to_6': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        '6_to_8': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        '8_to_10': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        '10_plus': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
    },
    
    'strike_rate_by_race_type': {
        'flat_turf': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        'flat_aw': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        'jumps_chase': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
        'jumps_hurdle': {'picks': int, 'wins': int, 'strike_rate': float, 'roi': float},
    },
    
    'strike_rate_by_time_of_day': {
        'morning_0800_1200': {'picks': int, 'wins': int, 'strike_rate': float},
        'afternoon_1200_1700': {'picks': int, 'wins': int, 'strike_rate': float},
        'evening_1700_2200': {'picks': int, 'wins': int, 'strike_rate': float},
    },
    
    'strike_rate_by_field_size': {
        '4_to_7_runners': {'picks': int, 'wins': int, 'strike_rate': float},
        '8_to_12_runners': {'picks': int, 'wins': int, 'strike_rate': float},
        '13_to_16_runners': {'picks': int, 'wins': int, 'strike_rate': float},
        '17_plus_runners': {'picks': int, 'wins': int, 'strike_rate': float},
    },
    
    'strike_rate_by_signal_activation': {
        'phase1_signals_on': {'picks': int, 'wins': int, 'strike_rate': float},
        'phase1_signals_off': {'picks': int, 'wins': int, 'strike_rate': float},
        'comparison_note': str,  # 'Phase 1 signals improve strike rate by X%'
    },
    
    'roi_by_pick_rank': {
        'pick_1': {'picks': int, 'wins': int, 'roi': float},
        'pick_2_to_3': {'picks': int, 'wins': int, 'roi': float},
        'pick_4_to_5': {'picks': int, 'wins': int, 'roi': float},
        'watchlist': {'picks': int, 'wins': int, 'roi': float},
    },
    
    'improvement_trajectory': {
        'week_1_strike_rate': float,
        'week_2_strike_rate': float,
        'week_3_strike_rate': float,
        'week_4_strike_rate': float,
        'trend': str,  # 'improving', 'declining', 'stable'
        'velocity': float,  # rate of change per week
    },
    
    'timestamp': str,
}
```

**Implementation:**

Add to `backend/pipeline/learning/handler.py`:
```python
def weekly_learning_analysis(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Comprehensive weekly analysis generating actionable insights.
    
    Args:
        start_date: Start of analysis window (ISO format)
        end_date: End of analysis window (ISO format)
    
    Returns:
        Combined pattern + performance analysis with recommendations
    """
    
    # Fetch all race data for the week
    race_data = _fetch_weekly_race_data(start_date, end_date)
    
    # Pattern recognition
    patterns = _analyze_weekly_patterns(race_data)
    
    # Performance metrics
    performance = _calculate_weekly_performance(race_data)
    
    # Generate recommendations
    recommendations = _generate_weekly_recommendations(patterns, performance)
    
    return {
        'analysis_period': {'start_date': start_date, 'end_date': end_date},
        'pattern_analysis': patterns,
        'performance_metrics': performance,
        'recommendations': recommendations,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
```

---

## Section 3: Continuous Improvement Metrics

### Dashboard Metrics to Track Daily

Store in DynamoDB table: `BetBudAI_LearningMetrics`

**Primary Key**: `metric_date` (YYYY-MM-DD)  
**Sort Key**: `metric_type` (e.g., 'daily_summary', 'rolling_7day', 'rolling_30day')

```python
DAILY_METRICS_RECORD = {
    'metric_date': str,
    'metric_type': 'daily_summary',
    
    'core_metrics': {
        'total_picks': int,
        'winners': int,
        'losers': int,
        'strike_rate': float,
        'roi_percent': float,
        'profit_loss': float,
    },
    
    'rolling_7day': {
        'strike_rate': float,
        'roi_percent': float,
        'target_strike_rate': 0.60,  # 60% target
        'gap_to_target': float,  # negative if below, positive if above
        'trend': str,  # 'improving', 'declining', 'stable'
    },
    
    'rolling_30day': {
        'strike_rate': float,
        'roi_percent': float,
        'target_roi': 20.0,  # 20% ROI target
        'gap_to_target': float,
    },
    
    'signal_comparison': {
        'phase1_signals_active': bool,
        'strike_rate_with_phase1': float,
        'strike_rate_without_phase1': float,
        'improvement_from_phase1': float,  # percentage points
    },
    
    'learning_velocity': {
        'weight_adjustments_this_week': int,
        'new_patterns_detected': int,
        'strike_rate_change_vs_last_week': float,
        'is_model_improving': bool,
    },
    
    'alert_triggers': [
        {
            'alert_type': str,  # 'strike_rate_drop', 'roi_below_threshold', etc.
            'severity': str,  # 'critical', 'high', 'medium'
            'message': str,
            'triggered_at': str,
        }
    ],
    
    'timestamp': str,
}
```

**Alert Rules:**

```python
ALERT_RULES = {
    'strike_rate_drop': {
        'condition': 'rolling_7day_strike_rate < 0.50 for 3 consecutive days',
        'severity': 'critical',
        'action': 'Trigger emergency weight review',
    },
    'roi_negative': {
        'condition': 'rolling_7day_roi < 0 for 2 consecutive days',
        'severity': 'high',
        'action': 'Review high-confidence picks only, pause watchlist',
    },
    'field_composition_errors': {
        'condition': 'winner_not_in_field > 30% of daily misses',
        'severity': 'critical',
        'action': 'Field verification system failing, check deployment',
    },
    'improver_signal_failure': {
        'condition': 'improver_demoted_category > 40% of misses',
        'severity': 'high',
        'action': 'Increase improver boost weights immediately',
    },
    'model_stagnation': {
        'condition': 'strike_rate_change_vs_last_week == 0 for 2 weeks',
        'severity': 'medium',
        'action': 'Model not learning, review weight update logic',
    },
}
```

---

## Section 4: Automated Learning Actions

### Current State
- Manual weight adjustments via `backend/config/weights.py`
- Learning pipeline calls `surebet-learning` function but doesn't auto-apply changes
- Recommendations generated but require human approval

### Enhanced Automated System

#### 4.1 Auto-Adjustment Rules

**Store rules in**: `backend/pipeline/learning/auto_adjustment_rules.py`

```python
AUTO_ADJUSTMENT_RULES = {
    'decrease_weight_when_factor_in_10_losses': {
        'enabled': True,
        'threshold': 10,  # consecutive losses with factor present
        'adjustment': -2,  # decrease weight by 2 points
        'max_decrease_per_week': -10,  # safety limit
        'applies_to': 'all_weights',
    },
    
    'increase_weight_when_factor_in_10_wins': {
        'enabled': True,
        'threshold': 10,  # consecutive wins with factor present
        'adjustment': +3,  # increase weight by 3 points
        'max_increase_per_week': +15,  # safety limit
        'applies_to': 'all_weights',
    },
    
    'flag_new_pattern_trainer_jockey': {
        'enabled': True,
        'threshold': 5,  # trainer/jockey combo wins 5+ times in 30 days
        'expected_wins': 2,  # when model expected ≤2
        'action': 'create_new_signal',
        'suggested_weight': 12,
    },
    
    'alert_strike_rate_drop': {
        'enabled': True,
        'threshold': 0.40,  # 40% strike rate for 7 days
        'target': 0.60,
        'action': 'send_alert_and_pause_low_confidence_picks',
    },
    
    'boost_improver_signal_when_underperforming': {
        'enabled': True,
        'condition': 'improver_demoted > 30% of weekly misses',
        'adjustment': +10,  # add 10 points to improver_boost
        'max_boost': 50,  # cap at +50 total
    },
    
    'reduce_market_dependence_when_market_wrong': {
        'enabled': True,
        'condition': 'market_favorite_won < 40% when we picked different',
        'adjustment': -2,  # reduce market-related weights
        'affects': ['favorite_correction', 'sweet_spot', 'optimal_odds'],
    },
}
```

**Implementation:**

Add to `backend/pipeline/learning/handler.py`:
```python
def apply_automated_adjustments(
    weekly_analysis: Dict[str, Any],
    current_weights: Dict[str, float],
    rules: Dict[str, Any] = AUTO_ADJUSTMENT_RULES
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    """
    Apply automated weight adjustments based on rules.
    
    Args:
        weekly_analysis: Output from weekly_learning_analysis
        current_weights: Current weight values from DynamoDB
        rules: Auto-adjustment rules
    
    Returns:
        (updated_weights, changes_log)
    """
    
    updated_weights = current_weights.copy()
    changes_log = []
    
    # Rule 1: Decrease weight for factors in 10 consecutive losses
    if rules['decrease_weight_when_factor_in_10_losses']['enabled']:
        factors_in_losses = _identify_factors_in_consecutive_losses(weekly_analysis, threshold=10)
        for factor in factors_in_losses:
            adjustment = rules['decrease_weight_when_factor_in_10_losses']['adjustment']
            old_value = updated_weights.get(factor, 0)
            new_value = max(0, old_value + adjustment)  # don't go negative
            updated_weights[factor] = new_value
            changes_log.append({
                'weight': factor,
                'rule': 'decrease_weight_when_factor_in_10_losses',
                'old_value': old_value,
                'new_value': new_value,
                'reason': f'Factor present in {len(factors_in_losses)} consecutive losses',
            })
    
    # Rule 2: Increase weight for factors in 10 consecutive wins
    if rules['increase_weight_when_factor_in_10_wins']['enabled']:
        factors_in_wins = _identify_factors_in_consecutive_wins(weekly_analysis, threshold=10)
        for factor in factors_in_wins:
            adjustment = rules['increase_weight_when_factor_in_10_wins']['adjustment']
            old_value = updated_weights.get(factor, 0)
            new_value = old_value + adjustment
            updated_weights[factor] = new_value
            changes_log.append({
                'weight': factor,
                'rule': 'increase_weight_when_factor_in_10_wins',
                'old_value': old_value,
                'new_value': new_value,
                'reason': f'Factor present in {len(factors_in_wins)} consecutive wins',
            })
    
    # Rule 3: Flag new trainer/jockey combo patterns
    if rules['flag_new_pattern_trainer_jockey']['enabled']:
        new_patterns = _detect_new_trainer_jockey_patterns(
            weekly_analysis,
            threshold=rules['flag_new_pattern_trainer_jockey']['threshold']
        )
        for pattern in new_patterns:
            changes_log.append({
                'pattern': pattern['combo'],
                'rule': 'flag_new_pattern_trainer_jockey',
                'action': 'manual_review_required',
                'wins': pattern['wins'],
                'expected': pattern['expected'],
                'suggested_weight': rules['flag_new_pattern_trainer_jockey']['suggested_weight'],
            })
    
    # Rule 4: Boost improver signal if underperforming
    if rules['boost_improver_signal_when_underperforming']['enabled']:
        improver_miss_rate = weekly_analysis['patterns']['category_distribution'].get('improver_demoted', 0) / weekly_analysis['summary']['model_misses']
        if improver_miss_rate > 0.30:
            # Increase improver-related weights
            improver_weights = ['form_velocity_bonus', 'bounce_back_bonus', 'short_form_improvement']
            for weight in improver_weights:
                adjustment = rules['boost_improver_signal_when_underperforming']['adjustment']
                old_value = updated_weights.get(weight, 0)
                new_value = min(old_value + adjustment, rules['boost_improver_signal_when_underperforming']['max_boost'])
                updated_weights[weight] = new_value
                changes_log.append({
                    'weight': weight,
                    'rule': 'boost_improver_signal_when_underperforming',
                    'old_value': old_value,
                    'new_value': new_value,
                    'reason': f'Improver miss rate {improver_miss_rate:.1%} > 30% threshold',
                })
    
    # Rule 5: Reduce market dependence when market wrong
    if rules['reduce_market_dependence_when_market_wrong']['enabled']:
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
                    'reason': f'Market favorite win rate {market_fav_win_rate:.1%} < 40%',
                })
    
    return updated_weights, changes_log
```

#### 4.2 Manual Review Triggers

**When to Alert for Human Review:**

```python
MANUAL_REVIEW_TRIGGERS = {
    'critical_performance_drop': {
        'condition': 'strike_rate < 0.40 for 3 consecutive days',
        'alert': 'CRITICAL: Strike rate dropped to {rate}%. Review weight changes and model logic immediately.',
        'notification': ['email', 'sms', 'slack'],
    },
    
    'new_signal_opportunity': {
        'condition': 'consistent_winner_pattern_detected with frequency > 5/week',
        'alert': 'OPPORTUNITY: New winning pattern detected: {pattern_description}. Consider adding signal.',
        'notification': ['email'],
    },
    
    'weight_divergence': {
        'condition': 'weight_adjusted > 20 points in single week',
        'alert': 'WARNING: Weight {weight_name} adjusted by {adjustment} points. Verify intended.',
        'notification': ['email'],
    },
    
    'field_composition_systematic_failure': {
        'condition': 'winner_not_in_field > 40% for 2 consecutive days',
        'alert': 'CRITICAL: Field verification failing. Check Betfair API, field_change_detector deployment.',
        'notification': ['email', 'sms', 'slack'],
    },
    
    'roi_negative_streak': {
        'condition': 'roi < 0 for 5 consecutive days',
        'alert': 'CRITICAL: Negative ROI for 5 days ({roi}%). Pause picks and review strategy.',
        'notification': ['email', 'sms'],
    },
}
```

**Implementation:**

Add to `backend/pipeline/learning/handler.py`:
```python
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
    if daily_metrics['rolling_7day']['strike_rate'] < 0.40:
        consecutive_days = _count_consecutive_low_strike_days(daily_metrics)
        if consecutive_days >= 3:
            alerts.append({
                'trigger': 'critical_performance_drop',
                'severity': 'critical',
                'message': f"CRITICAL: Strike rate dropped to {daily_metrics['rolling_7day']['strike_rate']:.1%}%. Review immediately.",
                'notification_channels': ['email', 'sms', 'slack'],
            })
    
    # New signal opportunity
    new_signals = weekly_analysis.get('missing_signals', {}).get('consistent_winner_patterns_not_captured', [])
    for signal in new_signals:
        if signal['frequency'] >= 5:
            alerts.append({
                'trigger': 'new_signal_opportunity',
                'severity': 'medium',
                'message': f"OPPORTUNITY: {signal['pattern_description']} detected {signal['frequency']}x. Consider adding signal.",
                'notification_channels': ['email'],
            })
    
    # Weight divergence
    for change in changes_log:
        if abs(change.get('new_value', 0) - change.get('old_value', 0)) > 20:
            alerts.append({
                'trigger': 'weight_divergence',
                'severity': 'high',
                'message': f"WARNING: Weight {change['weight']} adjusted by {change['new_value'] - change['old_value']} points.",
                'notification_channels': ['email'],
            })
    
    # Field composition failure
    winner_not_in_field_rate = weekly_analysis.get('patterns', {}).get('category_distribution', {}).get('winner_not_in_field', 0)
    total_misses = weekly_analysis.get('summary', {}).get('model_misses', 1)
    if winner_not_in_field_rate / total_misses > 0.40:
        alerts.append({
            'trigger': 'field_composition_systematic_failure',
            'severity': 'critical',
            'message': f"CRITICAL: {winner_not_in_field_rate} winners not in analyzed field ({winner_not_in_field_rate/total_misses:.1%}). Check field verification.",
            'notification_channels': ['email', 'sms', 'slack'],
        })
    
    # Negative ROI streak
    if daily_metrics['rolling_7day']['roi_percent'] < 0:
        consecutive_days = _count_consecutive_negative_roi_days(daily_metrics)
        if consecutive_days >= 5:
            alerts.append({
                'trigger': 'roi_negative_streak',
                'severity': 'critical',
                'message': f"CRITICAL: Negative ROI for {consecutive_days} days ({daily_metrics['rolling_7day']['roi_percent']:.1%}). Pause picks.",
                'notification_channels': ['email', 'sms'],
            })
    
    return alerts
```

---

## Section 5: Implementation Priorities

### Phase 1: Quick Wins (Deploy This Week)

**Priority 1A: Enhanced Daily Loss Analysis** (2-3 days)
- Extend `backend/core/miss_analyzer.py` with deep loss analysis functions
- Implement `LOSS_ANALYSIS_SCHEMA` storage to DynamoDB
- Update `backend/pipeline/evening/miss_analysis_handler.py` to use new analysis
- Expected impact: +20-30 winners/week from better insight extraction

**Priority 1B: Automated Weight Adjustments** (2-3 days)
- Add `auto_adjustment_rules.py` to learning pipeline
- Implement `apply_automated_adjustments` function
- Deploy rule: boost improver weights when `improver_demoted > 30%`
- Expected impact: +15-25 winners/week from responsive weight tuning

**Priority 1C: Manual Review Alerts** (1-2 days)
- Implement alert trigger checks
- Set up SNS notifications (email + SMS)
- Connect to Slack for real-time alerts
- Expected impact: Prevent catastrophic failures, catch issues within hours

### Phase 2: Medium-Term (2-4 Weeks)

**Priority 2A: Win Analysis System**
- Implement `WIN_ANALYSIS_SCHEMA` and storage
- Build win pattern replication logic
- Track what works and amplify it
- Expected impact: +10-15 winners/week from reinforcement learning

**Priority 2B: Market Divergence Tracking**
- Implement `DIVERGENCE_ANALYSIS_SCHEMA`
- Build market bias detection
- Identify systematic market inefficiencies
- Expected impact: +15-20 winners/week from edge detection

**Priority 2C: Weekly Pattern Recognition**
- Full implementation of weekly aggregation queries
- Trainer/course/form pattern detection
- Weight interaction analysis
- Expected impact: +20-30 winners/week from systematic pattern exploitation

### Phase 3: Long-Term (1-3 Months)

**Priority 3A: Continuous Improvement Dashboard**
- Build real-time dashboard showing learning velocity
- Track rolling metrics vs targets
- Visualize weight evolution over time
- Expected impact: Better visibility, faster intervention

**Priority 3B: Advanced Pattern Detection**
- Machine learning for pattern discovery (beyond rules)
- Anomaly detection for unusual winners
- Predictive modeling for weight adjustments
- Expected impact: +30-50 winners/week from ML-enhanced learning

**Priority 3C: A/B Testing Framework**
- Split picks into test/control groups
- Test weight changes on subset before full deployment
- Measure lift from each change
- Expected impact: Reduce risk of bad weight changes

---

## Section 6: Success Metrics

### Key Performance Indicators (Track Daily)

| Metric | Current | Target (4 weeks) | Target (12 weeks) |
|--------|---------|------------------|-------------------|
| **Strike Rate** | 18.64% | 50-55% | 60-70% |
| **7-Day ROI** | Unknown | +10% | +20% |
| **30-Day ROI** | Unknown | +8% | +18% |
| **Winners/Week** | ~30 | 90-100 | 120-140 |
| **Improver Miss Rate** | 30% | 15% | <10% |
| **Field Composition Errors** | 37% | 10% | <5% |
| **Model Miss Rate** | 22% | 15% | <10% |
| **Learning Velocity** | 0 adjustments/week | 5-10 adjustments/week | 3-5 adjustments/week |

### Leading Indicators (Early Warning System)

1. **Weight Adjustment Frequency**: Should see 5-10 weight changes/week initially, declining to 3-5 as model stabilizes
2. **Pattern Detection Rate**: New patterns discovered weekly initially, declining as model matures
3. **Alert Frequency**: Critical alerts should decrease over time (if increasing, model regressing)
4. **ROI Volatility**: Should decrease as model becomes more consistent

---

## Section 7: Monitoring & Maintenance

### Daily Checks (Automated)
- Run evening miss analysis after all results settled
- Calculate daily metrics and store in DynamoDB
- Check alert triggers and send notifications
- Apply automated weight adjustments if rules triggered

### Weekly Reviews (Automated + Manual)
- Sunday 23:00 UTC: Run weekly aggregation analysis
- Generate pattern recognition report
- Apply weekly automated adjustments
- Email comprehensive report to team
- Manual review of flagged patterns/signals

### Monthly Reviews (Manual)
- Deep dive into model evolution
- Review all weight changes made in month
- Validate improvement trajectory
- Adjust targets if needed
- Document key learnings

---

## Section 8: Data Storage Architecture

### New DynamoDB Tables Required

**Table 1: `BetBudAI_LearningInsights`**
- Primary Key: `analysis_date` (YYYY-MM-DD)
- Sort Key: `analysis_type` (`daily_loss` | `daily_win` | `daily_divergence` | `weekly_pattern` | `weekly_performance`)
- Attributes: JSON blobs following schemas above
- TTL: 90 days (keep 3 months of detailed analysis)

**Table 2: `BetBudAI_LearningMetrics`**
- Primary Key: `metric_date` (YYYY-MM-DD)
- Sort Key: `metric_type` (`daily_summary` | `rolling_7day` | `rolling_30day`)
- Attributes: Continuous improvement metrics
- TTL: 365 days (keep 1 year of metrics)

**Table 3: `BetBudAI_WeightChangelog`**
- Primary Key: `change_date` (YYYY-MM-DD)
- Sort Key: `change_timestamp` (ISO timestamp)
- Attributes: `weight_name`, `old_value`, `new_value`, `rule_applied`, `reason`, `applied_by` (system|human)
- TTL: No TTL (permanent record)

### Integration with Existing Tables

**Extend `SureBetBets` Table:**
- Add attributes to race records: `loss_analysis_id`, `win_analysis_id`, `divergence_analysis_id`
- Link picks to detailed learning insights
- Enable historical pattern queries

---

## Appendix A: Code Integration Points

### File: `backend/pipeline/learning/handler.py`
**Add**:
- `weekly_learning_analysis()` function
- `apply_automated_adjustments()` function
- `check_manual_review_triggers()` function

### File: `backend/core/miss_analyzer.py`
**Extend**:
- `analyze_single_miss()` → `analyze_loss_deeply()`
- Add `analyze_win_deeply()` function
- Add `analyze_market_divergence()` function
- Add helper functions: `_get_top_contributing_factors()`, `_identify_winner_advantages()`, etc.

### File: `backend/pipeline/evening/miss_analysis_handler.py`
**Modify**:
- Call `analyze_loss_deeply()` instead of basic analysis
- Store results in `BetBudAI_LearningInsights` table
- Trigger automated adjustments if rules met

### File: `backend/config/weights.py`
**Add**:
- `save_weight_change_log()` function to record all changes
- Version tracking for weights
- Rollback capability if change degrades performance

---

## Appendix B: Sample Dashboard Queries

### Query 1: What factors are consistently in winners?
```python
# Aggregate across all WIN_ANALYSIS records from last 30 days
winning_factors = Counter()
for win_record in fetch_wins_last_30_days():
    for factor in win_record['success_factors']['top_3_signals_that_worked']:
        winning_factors[factor] += 1

# Output: form_velocity_bonus: 45, class_drop_bonus: 38, trainer_course_bonus: 32, ...
```

### Query 2: What factors are consistently in losers?
```python
# Aggregate across all LOSS_ANALYSIS records from last 30 days
losing_factors = Counter()
for loss_record in fetch_losses_last_30_days():
    for factor in loss_record['why_we_picked_this_horse']['top_3_factors']:
        losing_factors[factor] += 1

# Output: recent_win: 67, trainer_reputation: 54, sweet_spot: 48, ...
```

### Query 3: Strike rate by signal presence
```python
# For each signal, calculate win rate when present vs absent
for signal_name in ALL_SIGNALS:
    wins_with_signal = count_wins_with_signal(signal_name)
    total_with_signal = count_picks_with_signal(signal_name)
    strike_rate = wins_with_signal / total_with_signal
    
    print(f"{signal_name}: {strike_rate:.1%} strike rate when present")
```

---

## Conclusion

This enhanced learning system transforms BetBudAI from a static model into a continuously improving AI that learns from every race. The key differentiators:

1. **Structured Question Framework**: No more ad-hoc analysis - every race generates standardized insights
2. **Automated Response**: Model adjusts weights without human intervention when patterns clear
3. **Early Warning System**: Alerts catch performance degradation before it becomes catastrophic
4. **Pattern Mining**: Weekly aggregation discovers systematic edges humans might miss
5. **Continuous Metrics**: Track learning velocity to ensure model is actually improving

**Expected 12-Week Trajectory:**
- Week 1-2: Implement Phase 1 (daily analysis + auto-adjustments) → Strike rate 35-40%
- Week 3-4: Add win analysis + divergence tracking → Strike rate 45-50%
- Week 5-8: Weekly pattern recognition fully operational → Strike rate 55-60%
- Week 9-12: Model stabilizes with continuous refinement → Strike rate 60-70%

**Total Expected Impact**: +100-120 winners/week vs current baseline (30/week → 130-150/week)

Deploy Phase 1 immediately to start learning from today's results.
