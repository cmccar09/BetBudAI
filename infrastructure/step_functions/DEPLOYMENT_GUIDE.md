# Step Function Deployment Implementation Guide

## Overview
Three AWS Step Functions have been created to implement the three priority recommendations from the 2-week race review. These will automatically run on a schedule and can be manually triggered as needed.

## Files Created

### 1. Master Orchestration
**File:** `0_master_orchestration.json`
- Validates deployment prerequisites
- Runs all three step functions sequentially
- Includes rollback logic if any step fails
- Triggers: On-demand or scheduled (recommended: nightly after racing ends)

### 2. Nonrunner Tracking & Field Verification
**File:** `1_nonrunner_tracking_and_field_verification.json`
- Tracks nonrunners in real-time from BetFair
- Fetches current field status every 30 minutes (starting 2 hours before race)
- At T-5 minutes: fetches final field
- If field changed >15% or 2+ nonrunners: re-analyzes race with new field
- Updates DynamoDB tracking table with all changes
- **Expected Impact:** Fix 40 of 67 "winner missing from field" misses

### 3. Improver Scoring Boost
**File:** `2_improver_scoring_boost.json`
- Identifies horses flagged as potential improvers
- Boosts improver-flagged horse scores by +15 base points
- Adds +5 bonus for strong trip suitability
- Re-ranks all horses by boosted score
- Promotes top 3 improver-flagged picks to OFFICIAL picks (vs. learning/watchlist)
- Validates new picks meet minimum confidence (70) and win probability (15%)
- Stores metrics to track improver effectiveness
- **Expected Impact:** Fix 40 of 53 "improver flag noise" misses

### 4. Model Miss Deep Analysis
**File:** `3_model_miss_deep_analysis.json`
- Loads all 39 "other model miss" races from May 7-13
- Analyzes each race in parallel to find patterns
- Calculates field strength factor (average rating, field size, class)
- Analyzes pace dynamics (fast pace winners, close finishers, etc.)
- Identifies missing scoring factors with highest correlation to actual winners
- Validates new factors on test set
- Compiles recommendations for scoring changes
- Publishes detailed report to S3
- **Expected Impact:** Fix 15 of 39 "other model miss" misses

---

## Deployment Steps

### Prerequisites
Ensure these AWS resources exist:

#### DynamoDB Tables
1. **RaceNonrunnerTracking**
   - Primary Key: market_id (String), race_time (String)
   - Attributes: nonrunners, field_change_percent, final_field_count, timestamp
   - TTL: 30 days

2. **ImproverBoostMetrics**
   - Primary Key: market_id (String), race_time (String)
   - Attributes: improver_candidates_count, valid_picks_promoted, top_improver_horse, timestamp
   - TTL: 90 days

3. **ModelMissAnalysis**
   - Primary Key: analysis_id (String)
   - Attributes: races_analyzed, recommended_changes, expected_accuracy_improvement, timestamp
   - TTL: 365 days

#### Lambda Functions Required
See `lambda_functions_specification.md` for full specifications of all 20+ Lambda functions needed.

Key functions:
- `check-race-timing` - Calculates time until race start
- `betfair-fetch-current-field` - Pulls current runners from BetFair API
- `compare-race-fields` - Compares field changes
- `load-race-scoring-data` - Retrieves scoring data from DB
- `identify-improver-candidates` - Flags horses for improvement
- `calculate-improver-boost-scores` - Applies +15 point boost
- `load-model-miss-races` - Loads historical miss data
- `analyze-single-model-miss` - Analyzes individual race miss
- ... (see spec document for all 20+)

### Deployment Procedure

1. **Create DynamoDB Tables** (once)
   ```bash
   aws dynamodb create-table \
     --table-name RaceNonrunnerTracking \
     --attribute-definitions AttributeName=market_id,AttributeType=S AttributeName=race_time,AttributeType=S \
     --key-schema AttributeName=market_id,KeyType=HASH AttributeName=race_time,KeyType=RANGE \
     --billing-mode PAY_PER_REQUEST \
     --region eu-west-1
   
   # Repeat for ImproverBoostMetrics and ModelMissAnalysis
   ```

2. **Create/Update Lambda Functions**
   ```bash
   # See lambda_functions_specification.md for each function
   # Deploy using existing pipeline in _deploy_handlers.py
   python _deploy_handlers.py --deploy-all-step-functions
   ```

3. **Create Step Function State Machines**
   ```bash
   # Use AWS Console or CLI:
   aws stepfunctions create-state-machine \
     --name "nonrunner-tracking-verification" \
     --definition file://1_nonrunner_tracking_and_field_verification.json \
     --role-arn "arn:aws:iam::ACCOUNT_ID:role/StepFunctionsExecutionRole" \
     --region eu-west-1
   
   # Repeat for improver-scoring-boost and model-miss-deep-analysis
   # Then create master orchestration state machine
   ```

4. **Set Up Event Bridge Triggers** (optional - for automatic daily runs)
   ```json
   {
     "Name": "trigger-step-functions-nightly",
     "ScheduleExpression": "cron(21 18 * * ? *)",
     "Targets": [{
       "Arn": "arn:aws:stepfunctions:eu-west-1:ACCOUNT_ID:stateMachine:master-orchestration",
       "RoleArn": "arn:aws:iam::ACCOUNT_ID:role/EventBridgeExecutionRole"
     }]
   }
   ```

---

## Execution Flow

### On Demand (Manual Trigger)
```bash
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:eu-west-1:ACCOUNT_ID:stateMachine:master-orchestration" \
  --name "manual-run-20260514" \
  --region eu-west-1
```

### Scheduled (EventBridge)
- **Trigger:** Every night at 18:21 UTC (after racing ends at 18:00)
- **Duration:** ~45-60 minutes total
- **Output:** Results stored in DynamoDB + S3 report

### Execution Sequence
1. ✅ Validation (2 min)
   - Check all Lambda functions exist
   - Check all DynamoDB tables exist
   
2. 🏃 Step 1: Nonrunner Tracking (20 min)
   - Triggered at race time (or immediately if running post-race)
   - Tracks all nonrunners from T-120 to T-5
   - Re-analyzes if field changes significantly
   
3. 🎯 Step 2: Improver Boost (15 min)
   - After nonrunner tracking completes
   - Identifies all improver-flagged horses
   - Boosts scores and promotes top 3 to official picks
   - Stores metrics for measurement
   
4. 📊 Step 3: Model Miss Analysis (25 min)
   - After improver boost completes
   - Analyzes all 39 model misses in parallel
   - Generates detailed report with recommendations
   - Publishes to S3 and stores in DynamoDB

---

## Monitoring & Metrics

### CloudWatch Dashboards
All step functions log to CloudWatch. Create dashboard with these metrics:

**Step 1 Metrics:**
- Races tracked for nonrunners
- Nonrunner count per race
- Field re-analyses triggered
- Pick changes due to nonrunners

**Step 2 Metrics:**
- Improver candidates identified
- Improver-flagged horses boosted
- Official picks promoted from learning
- Average score boost applied

**Step 3 Metrics:**
- Model miss races analyzed
- New factors identified
- Field strength factor correlation
- Pace dynamics impact
- Projected accuracy improvement

### Key Performance Indicators (7-day tracking)

| Metric | Baseline | Target | Current |
|--------|----------|--------|---------|
| Hit Rate | 18.64% | 59-68% | TBD |
| Winners Missing from Field | 67 | 20-30 | TBD |
| Improver Flag Effectiveness | 53 misses | 10-15 | TBD |
| Model Miss Rate | 39 | 20-25 | TBD |
| Nonrunner Tracking Accuracy | N/A | >95% | TBD |

---

## Configuration

### Adjustable Parameters

**Nonrunner Tracking (1_nonrunner_tracking_and_field_verification.json)**
- `check_interval_minutes`: 30 (check for nonrunners every 30 min, change to 15 for more frequent)
- `field_change_percent`: 15 (trigger re-analysis if field changes >15%, lower = more sensitive)
- `nonrunner_count`: 2 (trigger re-analysis if 2+ nonrunners)

**Improver Scoring Boost (2_improver_scoring_boost.json)**
- `base_improver_boost`: 15 (boost all improver picks by 15 points)
- `trip_suitability_boost`: 5 (additional 5 points if trip strong)
- `max_boost_cap`: 35 (don't boost more than 35 total)
- `minimum_confidence_score`: 70 (picks must score 70+ to promote)
- `minimum_win_probability`: 0.15 (picks must have 15%+ win prob)

**Model Miss Analysis (3_model_miss_deep_analysis.json)**
- `min_correlation_threshold`: 0.15 (only include factors with 15%+ correlation)
- `top_n_factors`: 10 (recommend top 10 missing factors)
- `threshold_minimum_impact`: 5 (factor must improve 5+ races)

---

## Rollback Procedure

If any step fails:
1. Rollback automatically triggered
2. All changes reverted to pre-deployment state
3. Alert sent to team with error details
4. Manual investigation required before retry

To manual rollback:
```bash
# Step 1
aws lambda invoke \
  --function-name rollback-nonrunner-tracking \
  --payload '{"execution_id":"arn:aws:states:eu-west-1:ACCOUNT_ID:execution:id"}' \
  output.json

# Step 2
aws lambda invoke \
  --function-name rollback-improver-boost \
  --payload '{"execution_id":"arn:aws:states:eu-west-1:ACCOUNT_ID:execution:id"}' \
  output.json
```

---

## Testing

### Pre-Deployment Testing (Recommended)

1. **Test Step 1 (Nonrunner Tracking)**
   ```bash
   # Load a known race with historical nonrunners
   aws stepfunctions start-execution \
     --state-machine-arn "arn:aws:states:eu-west-1:ACCOUNT_ID:stateMachine:nonrunner-tracking-verification" \
     --input '{"market_id":"1.258017420","course":"Lingfield","race_time":"2026-05-12T19:20:00+00:00"}' \
     --region eu-west-1
   ```

2. **Test Step 2 (Improver Boost)**
   ```bash
   # Load a race with known improver-flagged winners
   aws stepfunctions start-execution \
     --state-machine-arn "arn:aws:states:eu-west-1:ACCOUNT_ID:stateMachine:improver-scoring-boost" \
     --input '{"market_id":"1.258066662","course":"Yarmouth","race_time":"2026-05-13T13:40:00+00:00"}' \
     --region eu-west-1
   ```

3. **Test Step 3 (Model Analysis)**
   ```bash
   # This will take 25+ minutes - run during off-peak
   aws stepfunctions start-execution \
     --state-machine-arn "arn:aws:states:eu-west-1:ACCOUNT_ID:stateMachine:model-miss-deep-analysis" \
     --region eu-west-1
   ```

4. **Verify Outputs**
   - Check DynamoDB tables for new records
   - Check S3 for generated reports
   - Review CloudWatch logs for errors
   - Validate pick changes vs. baseline

---

## Next Steps

1. ✅ Create Lambda functions (20+ functions specified in `lambda_functions_specification.md`)
2. ✅ Create DynamoDB tables
3. ✅ Deploy step function state machines
4. ✅ Configure EventBridge triggers
5. ✅ Run pre-deployment tests
6. ✅ Deploy to production
7. ✅ Monitor for 7 days
8. ✅ Evaluate impact and iterate

---

## Support & Troubleshooting

### Common Issues

**Issue:** "Lambda function not found"
- **Solution:** Deploy all lambda functions first using _deploy_handlers.py

**Issue:** "DynamoDB table doesn't exist"
- **Solution:** Create DynamoDB tables (see prerequisites section)

**Issue:** "Step function times out"
- **Solution:** Check individual Lambda function performance; may need to increase timeout values

**Issue:** "Improver picks not being promoted"
- **Solution:** Check validation scores in ImproverBoostMetrics table; may need to lower minimum_confidence_score threshold

---

**Deployment Date:** May 14, 2026  
**Expected Go-Live:** May 15-16, 2026  
**Monitoring Period:** 7 days (May 15-22, 2026)
