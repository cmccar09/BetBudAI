# Lambda Functions Specification for Step Function Pipelines

## Overview
This document specifies all Lambda functions required to support the three step function pipelines. Total: 25 Lambda functions across 3 domains.

---

## Domain 1: Nonrunner Tracking (6 functions)

### 1. check-race-timing
**Purpose:** Calculate time until race start and determine check interval
**Trigger:** Step function (check-race-timing state)
**Input:**
```json
{
  "race_time": "2026-05-12T19:20:00+00:00",
  "check_interval_minutes": 30
}
```
**Output:**
```json
{
  "minutes_to_race": 45,
  "seconds_until_race": 2700,
  "status": "scheduled"
}
```
**Runtime:** Python 3.9
**Dependencies:** datetime
**Memory:** 256 MB
**Timeout:** 10 seconds

### 2. betfair-fetch-current-field
**Purpose:** Fetch current runner list from BetFair API
**Trigger:** Step function (fetch-current-betfair-field state)
**Input:**
```json
{
  "market_id": "1.258017420",
  "course": "Lingfield",
  "race_time": "2026-05-12T19:20:00+00:00",
  "fetch_type": "current_runners"
}
```
**Output:**
```json
{
  "market_id": "1.258017420",
  "runners": [
    {"selection_id": 12345, "horse": "Twilight Moon", "status": "active"},
    {"selection_id": 12346, "horse": "Arths Gold", "status": "active"}
  ],
  "timestamp": "2026-05-12T18:50:00+00:00"
}
```
**Runtime:** Python 3.9
**Dependencies:** betfairlightweight, requests
**Memory:** 512 MB
**Timeout:** 30 seconds
**Environment Variables:**
- BETFAIR_USERNAME
- BETFAIR_PASSWORD
- BETFAIR_APP_KEY

### 3. compare-race-fields
**Purpose:** Compare BetFair current field to our model field
**Trigger:** Step function (compare-fields state)
**Input:**
```json
{
  "market_id": "1.258017420",
  "course": "Lingfield",
  "race_time": "2026-05-12T19:20:00+00:00",
  "current_betfair_field": [...],
  "model_field": [...]
}
```
**Output:**
```json
{
  "field_change_percent": 12.5,
  "nonrunner_count": 1,
  "nonrunners": ["Yaa Min"],
  "new_runners": [],
  "final_field_count": 8,
  "original_field_count": 9
}
```
**Runtime:** Python 3.9
**Dependencies:** None (standard lib)
**Memory:** 256 MB
**Timeout:** 10 seconds

### 4. update-race-picks
**Purpose:** Update picks in database when field changes
**Trigger:** Step function (update-picks state)
**Input:**
```json
{
  "market_id": "1.258017420",
  "old_picks": [...],
  "new_picks": [...],
  "reason": "Post-nonrunner field verification"
}
```
**Output:**
```json
{
  "status": "updated",
  "picks_changed": 2,
  "old_pick_1": "Twilight Moon",
  "new_pick_1": "Arths Gold"
}
```
**Runtime:** Python 3.9
**Dependencies:** boto3
**Memory:** 256 MB
**Timeout:** 15 seconds
**Environment Variables:**
- DYNAMO_TABLE_NAME

### 5. surebet-analysis (reuse existing)
**Purpose:** Re-analyze race with new field composition
**Note:** This is an existing function; reuse as-is
**Expected modifications:** Add `reanalysis_reason` and `force_reanalysis` parameters

### 6. store-nonrunner-tracking (DynamoDB task)
**Purpose:** Store nonrunner data for tracking
**Note:** Built into step function as DynamoDB putItem task
**Table:** RaceNonrunnerTracking

---

## Domain 2: Improver Scoring Boost (10 functions)

### 7. load-race-scoring-data
**Purpose:** Load complete scoring breakdown for all horses in a race
**Trigger:** Step function (load-race-data state)
**Input:**
```json
{
  "market_id": "1.258017420",
  "course": "Lingfield",
  "race_time": "2026-05-12T19:20:00+00:00"
}
```
**Output:**
```json
{
  "market_id": "1.258017420",
  "all_horses": [
    {
      "horse": "Twilight Moon",
      "score": 101,
      "score_breakdown": {...},
      "potential_improver_flag": false,
      "form": "1144241-1"
    }
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** boto3
**Memory:** 512 MB
**Timeout:** 20 seconds
**Environment Variables:**
- DYNAMO_TABLE_PICKS

### 8. identify-improver-candidates
**Purpose:** Identify horses flagged as potential improvers
**Trigger:** Step function (identify-improver state)
**Input:**
```json
{
  "all_horses": [...],
  "trip_suitability_threshold": 15,
  "trainer_improvement_threshold": 5
}
```
**Output:**
```json
{
  "horses": [
    {
      "horse": "Sea The Storm",
      "trip_suitability_score": 16,
      "trainer_hot_form_pct": 35,
      "distance_pattern": "improving",
      "improver_confidence": 0.85
    }
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** numpy
**Memory:** 512 MB
**Timeout:** 15 seconds

### 9. evaluate-improver-strength
**Purpose:** Deep evaluation of improver candidates
**Trigger:** Step function (evaluate-improvers state)
**Input:**
```json
{
  "candidates": [...],
  "evaluation_factors": [...]
}
```
**Output:**
```json
{
  "ranked_improvers": [
    {
      "horse": "Sea The Storm",
      "evaluation_score": 8.5,
      "factors": {...},
      "promotion_confidence": 0.95
    }
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy
**Memory:** 512 MB
**Timeout:** 20 seconds

### 10. calculate-improver-boost-scores
**Purpose:** Apply +15 score boost and calculate new rankings
**Trigger:** Step function (calculate-boost state)
**Input:**
```json
{
  "all_horses": [...],
  "improver_candidates": [...],
  "base_improver_boost": 15,
  "trip_suitability_boost": 5,
  "max_boost_cap": 35
}
```
**Output:**
```json
{
  "all_horses": [
    {
      "horse": "Sea The Storm",
      "original_score": 110,
      "boost_applied": 15,
      "new_score": 125,
      "boost_reason": "improver_flag"
    }
  ],
  "average_boost_applied": 15,
  "improver_boosted_scores": [...]
}
```
**Runtime:** Python 3.9
**Dependencies:** None
**Memory:** 256 MB
**Timeout:** 10 seconds

### 11. rank-horses-by-score
**Purpose:** Re-rank horses by new boosted scores
**Trigger:** Step function (rank-horses state)
**Input:**
```json
{
  "horses_with_scores": [...],
  "sort_order": "descending"
}
```
**Output:**
```json
{
  "rankings": [
    {"rank": 1, "horse": "Sea The Storm", "score": 125},
    {"rank": 2, "horse": "Legacy Link", "score": 78}
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** None
**Memory:** 256 MB
**Timeout:** 10 seconds

### 12. extract-improver-picks
**Purpose:** Extract top 3 improver-flagged picks from rankings
**Trigger:** Step function (extract-picks state)
**Input:**
```json
{
  "ranked_horses": [...],
  "improver_candidates": [...],
  "top_n": 3
}
```
**Output:**
```json
{
  "Payload": {
    "improver_picks": [
      {
        "rank": 1,
        "horse": "Sea The Storm",
        "boosted_score": 125,
        "improver_flag_confidence": 0.95
      }
    ]
  }
}
```
**Runtime:** Python 3.9
**Dependencies:** None
**Memory:** 256 MB
**Timeout:** 10 seconds

### 13. validate-improver-picks
**Purpose:** Validate improver picks meet quality thresholds
**Trigger:** Step function (validate-picks state)
**Input:**
```json
{
  "improver_picks": [...],
  "market_id": "1.258017420",
  "minimum_confidence_score": 70,
  "minimum_win_probability": 0.15
}
```
**Output:**
```json
{
  "valid_picks": [
    {
      "horse": "Sea The Storm",
      "boosted_score": 125,
      "confidence_grade": "ELITE",
      "win_probability": 0.35
    }
  ],
  "valid_picks_count": 1
}
```
**Runtime:** Python 3.9
**Dependencies:** boto3
**Memory:** 256 MB
**Timeout:** 15 seconds

### 14. promote-improver-picks
**Purpose:** Promote validated improver picks to official status
**Trigger:** Step function (promote-picks state)
**Input:**
```json
{
  "market_id": "1.258017420",
  "course": "Lingfield",
  "race_time": "2026-05-12T19:20:00+00:00",
  "valid_picks": [...],
  "original_pick_type": "learning",
  "new_pick_type": "official",
  "promotion_reason": "Improver-flagged horse with strong trip suitability"
}
```
**Output:**
```json
{
  "promoted_picks": 1,
  "updated_picks": [...]
}
```
**Runtime:** Python 3.9
**Dependencies:** boto3
**Memory:** 256 MB
**Timeout:** 15 seconds
**Environment Variables:**
- DYNAMO_TABLE_PICKS

### 15. store-improver-metrics (DynamoDB task)
**Purpose:** Store improver boost metrics for measurement
**Note:** Built into step function as DynamoDB putItem task
**Table:** ImproverBoostMetrics

---

## Domain 3: Model Miss Analysis (9 functions)

### 16. load-model-miss-races
**Purpose:** Load all model miss races from period
**Trigger:** Step function (load-misses state)
**Input:**
```json
{
  "date_from": "2026-05-07",
  "date_to": "2026-05-13",
  "miss_type": "other_model_miss"
}
```
**Output:**
```json
{
  "races": [
    {
      "market_id": "1.258066790",
      "course": "York",
      "race_time": "2026-05-13T13:20:00+00:00",
      "top_pick": "Plage De Havre",
      "top_score": 85,
      "winner": "Klassleader",
      "winner_score": 81,
      "winner_rank": 3,
      "winner_odds": 3.3
    }
  ],
  "total_races": 39
}
```
**Runtime:** Python 3.9
**Dependencies:** boto3, pandas
**Memory:** 512 MB
**Timeout:** 30 seconds
**Environment Variables:**
- DYNAMODB_HISTORICAL_PICKS_TABLE

### 17. analyze-single-model-miss
**Purpose:** Analyze individual model miss race
**Trigger:** Map state in step function
**Input:**
```json
{
  "market_id": "1.258066790",
  "course": "York",
  "race_time": "2026-05-13T13:20:00+00:00",
  "top_pick_horse": "Plage De Havre",
  "top_pick_score": 85,
  "actual_winner": "Klassleader",
  "winner_score": 81,
  "winner_rank": 3,
  "winner_odds": 3.3
}
```
**Output:**
```json
{
  "market_id": "1.258066790",
  "analysis": {
    "gap_to_winner_score": 4,
    "winner_characteristics": {
      "form_pattern": "improving",
      "jockey_form": "hot",
      "odds_vs_rating": "underrated"
    },
    "scoring_factors_missed": ["jockey_hot_form", "market_position"],
    "factors_overweighted": ["distance_suitability"]
  }
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy
**Memory:** 512 MB
**Timeout:** 20 seconds
**Environment Variables:**
- DYNAMODB_RACE_DATA_TABLE

### 18. aggregate-miss-analysis
**Purpose:** Aggregate findings from all 39 races
**Trigger:** Step function (aggregate state)
**Input:**
```json
{
  "analyses": [...]
}
```
**Output:**
```json
{
  "total_races_analyzed": 39,
  "average_gap_to_winner": 15.2,
  "most_common_missed_factors": [
    {"factor": "jockey_hot_form", "frequency": 18},
    {"factor": "market_position", "frequency": 14}
  ],
  "most_common_overweighted_factors": [
    {"factor": "distance_suitability", "frequency": 12}
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy
**Memory:** 512 MB
**Timeout:** 20 seconds

### 19. calculate-field-strength
**Purpose:** Calculate field strength as factor in missing winners
**Trigger:** Step function (field-strength state)
**Input:**
```json
{
  "races": [...],
  "field_metrics": [...]
}
```
**Output:**
```json
{
  "races_analyzed": 39,
  "average_official_rating": 78.5,
  "average_field_size": 10.2,
  "field_strength_impact_rating": "moderate",
  "weak_field_miss_rate": 0.42,
  "strong_field_miss_rate": 0.18,
  "average_impact": 12.5
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy
**Memory:** 512 MB
**Timeout:** 20 seconds

### 20. analyze-pace-dynamics
**Purpose:** Analyze pace profile and its effect on winners
**Trigger:** Step function (pace-analysis state)
**Input:**
```json
{
  "races": [...],
  "pace_factors": [...]
}
```
**Output:**
```json
{
  "races_analyzed": 39,
  "frontrunner_win_rate": 0.35,
  "closer_win_rate": 0.45,
  "mid_field_win_rate": 0.20,
  "fast_pace_races": 18,
  "fast_pace_miss_rate": 0.52,
  "slow_pace_miss_rate": 0.21,
  "average_impact": 18.7
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy
**Memory:** 512 MB
**Timeout:** 20 seconds

### 21. identify-missing-scoring-factors
**Purpose:** Identify scoring factors we're missing
**Trigger:** Step function (identify-factors state)
**Input:**
```json
{
  "aggregated_analysis": {...},
  "field_strength_analysis": {...},
  "pace_analysis": {...},
  "min_correlation_threshold": 0.15
}
```
**Output:**
```json
{
  "new_factors": [
    {
      "name": "market_position_vs_rating",
      "description": "Horse quoted lower than official rating suggests",
      "correlation": 0.32,
      "affected_races": 15
    },
    {
      "name": "pace_suitability_rating",
      "description": "How well horse profile suits predicted pace",
      "correlation": 0.28,
      "affected_races": 12
    }
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy, scipy
**Memory:** 512 MB
**Timeout:** 25 seconds

### 22. rank-missing-factors
**Purpose:** Rank new factors by impact
**Trigger:** Step function (rank-factors state)
**Input:**
```json
{
  "factors": [...],
  "rank_by": "correlation_to_actual_winners",
  "top_n": 10
}
```
**Output:**
```json
{
  "top_factors": [
    {
      "rank": 1,
      "name": "market_position_vs_rating",
      "correlation": 0.32
    },
    {
      "rank": 2,
      "name": "pace_suitability_rating",
      "correlation": 0.28
    }
  ]
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas
**Memory:** 256 MB
**Timeout:** 15 seconds

### 23. validate-factor-correlation
**Purpose:** Validate each factor correlation on test set
**Trigger:** Map state in step function
**Input:**
```json
{
  "factor_name": "market_position_vs_rating",
  "correlation_score": 0.32,
  "affected_races": [...],
  "validation_races": [...]
}
```
**Output:**
```json
{
  "factor_name": "market_position_vs_rating",
  "original_correlation": 0.32,
  "validation_correlation": 0.29,
  "valid": true,
  "confidence": 0.95
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas, numpy, scipy
**Memory:** 512 MB
**Timeout:** 30 seconds

### 24. compile-model-recommendations
**Purpose:** Compile recommendations for model improvements
**Trigger:** Step function (compile-recommendations state)
**Input:**
```json
{
  "aggregated_analysis": {...},
  "field_strength_analysis": {...},
  "pace_analysis": {...},
  "validated_factors": [...],
  "threshold_minimum_impact": 5
}
```
**Output:**
```json
{
  "scoring_changes_summary": "Add 2 new factors, adjust field strength weighting, increase pace dynamics",
  "recommended_changes": [
    {
      "change": "Add market_position_vs_rating factor",
      "impact": "Fix ~8 additional winners",
      "implementation": "New scoring component"
    }
  ],
  "projected_improvement_percent": 15.5
}
```
**Runtime:** Python 3.9
**Dependencies:** pandas
**Memory:** 512 MB
**Timeout:** 20 seconds

### 25. generate-model-miss-report
**Purpose:** Generate detailed report of findings
**Trigger:** Step function (generate-report state)
**Input:**
```json
{
  "market_id_list": [...],
  "total_races": 39,
  "analyses": [...],
  "aggregated_findings": {...},
  "field_strength_findings": {...},
  "pace_findings": {...},
  "recommended_changes": {...}
}
```
**Output:**
```json
{
  "s3_location": "s3://betbudai-reports/model-analysis/miss_analysis_2026_05_07_to_05_13.json",
  "report": {
    "title": "Model Miss Analysis: May 7-13, 2026",
    "races_analyzed": 39,
    "findings": [...],
    "recommendations": [...]
  }
}
```
**Runtime:** Python 3.9
**Dependencies:** boto3, json
**Memory:** 512 MB
**Timeout:** 30 seconds
**Environment Variables:**
- S3_REPORTS_BUCKET
- S3_REPORTS_PREFIX

---

## Supporting Functions

### 26. finalize-deployment
**Purpose:** Mark deployment complete, summary
**Trigger:** Step function (finalize state)
**Runtime:** Python 3.9
**Memory:** 256 MB
**Timeout:** 15 seconds

### 27. handle-deployment-failure
**Purpose:** Handle failures during deployment
**Trigger:** Step function (error handling)
**Runtime:** Python 3.9
**Memory:** 256 MB
**Timeout:** 10 seconds

### 28. validate-deployment-config
**Purpose:** Validate all prerequisites before deployment
**Trigger:** Step function (validate state)
**Runtime:** Python 3.9
**Memory:** 256 MB
**Timeout:** 30 seconds

---

## Deployment Notes

- All functions should use IAM role: `SureBetLambdaExecutionRole`
- All functions should log to CloudWatch with prefix: `/aws/lambda/surebetai/`
- Set up SNS alerts for function errors
- Enable X-Ray tracing for all functions for performance debugging
- Use reserved concurrency for critical functions (betfair-fetch, improver-boost): 10
- Set up Lambda layers for shared dependencies (boto3, pandas, numpy)

---

**Total Lambda Functions:** 25  
**Total Lines of Code:** ~5,000-7,000  
**Estimated Development Time:** 40-60 hours  
**Testing Time:** 20-30 hours
