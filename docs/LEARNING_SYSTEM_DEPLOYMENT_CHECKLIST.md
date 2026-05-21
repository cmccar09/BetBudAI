# Enhanced Learning System - Deployment Checklist
**Start Date**: May 20, 2026  
**Target Completion**: Phase 1 by May 27, 2026  
**Owner**: Development Team

---

## Phase 1: Quick Wins (Deploy This Week)

### Task 1A: Enhanced Daily Loss Analysis (Priority: CRITICAL)
**Estimated Time**: 2-3 days  
**Expected Impact**: +20-30 winners/week

#### Step 1: Extend `backend/core/miss_analyzer.py`
- [ ] Add `LOSS_ANALYSIS_SCHEMA` constant
- [ ] Implement `analyze_loss_deeply()` function
  - [ ] `_get_top_contributing_factors()`
  - [ ] `_identify_winner_advantages()`
  - [ ] `_analyze_pricing_vs_performance()`
  - [ ] `_compare_form_trajectories()`
  - [ ] `_analyze_pace_dynamics()`
  - [ ] `_analyze_jockey_trainer_performance()`
  - [ ] `_analyze_conditions_suitability()`
  - [ ] `_analyze_field_changes()`
  - [ ] `_categorize_miss_with_fix_estimate()`
- [ ] Add unit tests for new functions
- [ ] Deploy to Lambda layer

#### Step 2: Update `backend/pipeline/evening/miss_analysis_handler.py`
- [ ] Replace `_inline_analyze_miss()` call with `analyze_loss_deeply()`
- [ ] Add DynamoDB writes to `BetBudAI_LearningInsights` table
- [ ] Add error handling for analysis failures
- [ ] Test with recent race data
- [ ] Deploy Lambda function

#### Step 3: Create DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name BetBudAI_LearningInsights \
  --attribute-definitions \
    AttributeName=analysis_date,AttributeType=S \
    AttributeName=analysis_type,AttributeType=S \
  --key-schema \
    AttributeName=analysis_date,KeyType=HASH \
    AttributeName=analysis_type,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```
- [ ] Create table in AWS
- [ ] Configure TTL (90 days) on `ttl_timestamp` attribute
- [ ] Test write/read access from Lambda
- [ ] Grant IAM permissions to evening-miss-analysis Lambda

#### Step 4: Validation
- [ ] Run evening analysis on yesterday's races
- [ ] Verify records written to DynamoDB
- [ ] Check CloudWatch logs for errors
- [ ] Review first 5 detailed loss analyses manually
- [ ] Confirm insights are actionable

---

### Task 1B: Automated Weight Adjustments (Priority: HIGH)
**Estimated Time**: 2-3 days  
**Expected Impact**: +15-25 winners/week

#### Step 1: Create `backend/pipeline/learning/auto_adjustment_rules.py`
- [ ] Define `AUTO_ADJUSTMENT_RULES` constant
- [ ] Implement rule: decrease_weight_when_factor_in_10_losses
- [ ] Implement rule: increase_weight_when_factor_in_10_wins
- [ ] Implement rule: boost_improver_signal_when_underperforming
- [ ] Implement rule: reduce_market_dependence_when_market_wrong
- [ ] Add safety limits (max adjustment per week)
- [ ] Add unit tests

#### Step 2: Extend `backend/pipeline/learning/handler.py`
- [ ] Add `apply_automated_adjustments()` function
- [ ] Add `_identify_factors_in_consecutive_losses()` helper
- [ ] Add `_identify_factors_in_consecutive_wins()` helper
- [ ] Add `_detect_new_trainer_jockey_patterns()` helper
- [ ] Integrate with existing `lambda_handler()`
- [ ] Call `apply_automated_adjustments()` after analysis
- [ ] Write changes to `BetBudAI_WeightChangelog` table
- [ ] Update weights in `SureBetBets` table (SYSTEM_WEIGHTS record)
- [ ] Test with mock data

#### Step 3: Create `BetBudAI_WeightChangelog` Table
```bash
aws dynamodb create-table \
  --table-name BetBudAI_WeightChangelog \
  --attribute-definitions \
    AttributeName=change_date,AttributeType=S \
    AttributeName=change_timestamp,AttributeType=S \
  --key-schema \
    AttributeName=change_date,KeyType=HASH \
    AttributeName=change_timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```
- [ ] Create table in AWS
- [ ] Grant IAM permissions to learning Lambda
- [ ] Test write access

#### Step 4: Deploy and Monitor
- [ ] Deploy learning Lambda with new code
- [ ] Manually trigger learning pipeline for last 7 days
- [ ] Review weight changes proposed
- [ ] Verify changes written to changelog
- [ ] Verify weights updated in SYSTEM_WEIGHTS
- [ ] Monitor next day's picks for impact

---

### Task 1C: Manual Review Alerts (Priority: HIGH)
**Estimated Time**: 1-2 days  
**Expected Impact**: Prevent catastrophic failures

#### Step 1: Set up SNS Topic
```bash
aws sns create-topic \
  --name betbudai-learning-alerts \
  --region eu-west-1

aws sns subscribe \
  --topic-arn arn:aws:sns:eu-west-1:ACCOUNT_ID:betbudai-learning-alerts \
  --protocol email \
  --notification-endpoint your-email@domain.com

aws sns subscribe \
  --topic-arn arn:aws:sns:eu-west-1:ACCOUNT_ID:betbudai-learning-alerts \
  --protocol sms \
  --notification-endpoint +44XXXXXXXXXX
```
- [ ] Create SNS topic
- [ ] Subscribe email address
- [ ] Subscribe phone number for SMS
- [ ] Confirm subscriptions
- [ ] Test send message

#### Step 2: Add Alert Logic to Learning Pipeline
- [ ] Add `MANUAL_REVIEW_TRIGGERS` constant to handler.py
- [ ] Implement `check_manual_review_triggers()` function
- [ ] Add `_count_consecutive_low_strike_days()` helper
- [ ] Add `_count_consecutive_negative_roi_days()` helper
- [ ] Integrate SNS publishing for alerts
- [ ] Test with mock alert conditions

#### Step 3: Deploy and Validate
- [ ] Deploy updated learning Lambda
- [ ] Manually trigger with test data that should alert
- [ ] Verify email received
- [ ] Verify SMS received (if applicable)
- [ ] Check CloudWatch logs for alert records

---

## Phase 2: Medium-Term (Weeks 2-4)

### Task 2A: Win Analysis System
**Estimated Time**: 3-4 days  
**Expected Impact**: +10-15 winners/week

- [ ] Add `WIN_ANALYSIS_SCHEMA` to miss_analyzer.py
- [ ] Implement `analyze_win_deeply()` function
- [ ] Update evening handler to analyze wins
- [ ] Store win insights in DynamoDB
- [ ] Build win pattern replication logic
- [ ] Deploy and monitor

### Task 2B: Market Divergence Tracking
**Estimated Time**: 3-4 days  
**Expected Impact**: +15-20 winners/week

- [ ] Add `DIVERGENCE_ANALYSIS_SCHEMA`
- [ ] Implement `analyze_market_divergence()` function
- [ ] Identify market favorite for each race
- [ ] Compare our pick vs market favorite
- [ ] Track outcome (who was right)
- [ ] Detect systematic market biases
- [ ] Store divergence insights
- [ ] Deploy and monitor

### Task 2C: Weekly Pattern Recognition
**Estimated Time**: 4-5 days  
**Expected Impact**: +20-30 winners/week

- [ ] Add `WEEKLY_PATTERN_ANALYSIS` schema
- [ ] Implement `weekly_learning_analysis()` function
- [ ] Build trainer performance analyzer
- [ ] Build course performance analyzer
- [ ] Build form pattern analyzer
- [ ] Build weight effectiveness analyzer
- [ ] Build missing signals detector
- [ ] Build weight interaction analyzer
- [ ] Schedule weekly execution (Sunday 23:00 UTC)
- [ ] Deploy and monitor

---

## Phase 3: Long-Term (Months 2-3)

### Task 3A: Continuous Improvement Dashboard
**Estimated Time**: 1-2 weeks  
**Expected Impact**: Better visibility, faster intervention

- [ ] Create `BetBudAI_LearningMetrics` table
- [ ] Implement daily metrics calculation
- [ ] Implement rolling 7-day metrics
- [ ] Implement rolling 30-day metrics
- [ ] Build dashboard UI (React component)
- [ ] Add real-time metric updates
- [ ] Visualize weight evolution over time
- [ ] Deploy dashboard to production

### Task 3B: Advanced Pattern Detection
**Estimated Time**: 2-3 weeks  
**Expected Impact**: +30-50 winners/week

- [ ] Implement ML-based pattern discovery
- [ ] Build anomaly detection for unusual winners
- [ ] Create predictive modeling for weight adjustments
- [ ] A/B testing framework
- [ ] Deploy and monitor

---

## Pre-Deployment Checklist (Before Each Phase)

### Code Quality
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Code reviewed by peer
- [ ] No hardcoded credentials or secrets
- [ ] Error handling comprehensive
- [ ] Logging added at key points

### Infrastructure
- [ ] DynamoDB tables created
- [ ] IAM permissions granted
- [ ] Lambda memory/timeout configured appropriately
- [ ] SNS topics configured (if needed)
- [ ] EventBridge schedules created (if needed)
- [ ] CloudWatch alarms set up

### Testing
- [ ] Tested with real race data
- [ ] Tested with edge cases (empty data, missing fields)
- [ ] Tested failure scenarios
- [ ] Verified DynamoDB writes
- [ ] Verified notifications work
- [ ] Manual smoke test successful

### Documentation
- [ ] Code comments added
- [ ] README updated (if needed)
- [ ] Architecture diagram updated (if needed)
- [ ] Deployment notes documented
- [ ] Rollback plan documented

---

## Post-Deployment Monitoring (First 48 Hours)

### Immediate Checks (Hour 1)
- [ ] Lambda executed successfully
- [ ] No errors in CloudWatch logs
- [ ] DynamoDB records created
- [ ] Data quality looks correct
- [ ] No unexpected costs

### Daily Checks (Days 1-7)
- [ ] Review weight changes applied
- [ ] Check strike rate impact
- [ ] Monitor alert frequency
- [ ] Review learning insights
- [ ] Verify data pipeline health

### Weekly Review (Week 1)
- [ ] Strike rate improved?
- [ ] ROI positive?
- [ ] Weight adjustments sensible?
- [ ] Alerts actionable?
- [ ] Any issues to fix?

---

## Success Criteria

### Phase 1 Success (End of Week 1)
- [ ] Enhanced loss analysis running daily
- [ ] Automated weight adjustments applying
- [ ] Alerts functional
- [ ] Strike rate: 35-40% (target)
- [ ] No critical errors in 7 days
- [ ] Team confident in system

### Phase 2 Success (End of Week 4)
- [ ] Win analysis operational
- [ ] Market divergence tracking live
- [ ] Weekly pattern recognition running
- [ ] Strike rate: 50-55% (target)
- [ ] ROI: +10% (target)
- [ ] 5-10 weight adjustments/week

### Phase 3 Success (End of Week 12)
- [ ] Full dashboard operational
- [ ] Advanced pattern detection live
- [ ] Strike rate: 60-70% (target)
- [ ] ROI: +20% (target)
- [ ] Model stabilized (3-5 adjustments/week)
- [ ] Learning velocity positive

---

## Rollback Plan

### If Strike Rate Drops Below 30%
1. Immediately disable automated weight adjustments
2. Restore previous weights from changelog
3. Review last 3 days of changes
4. Identify problematic adjustment
5. Fix rule logic
6. Re-enable with monitoring

### If Critical Errors in Production
1. Disable failing Lambda
2. Check CloudWatch logs for root cause
3. Fix bug in development
4. Test thoroughly
5. Re-deploy with monitoring

### If Data Quality Issues
1. Pause learning pipeline
2. Investigate data source
3. Fix data extraction/transformation
4. Backfill corrected data
5. Resume pipeline

---

## Contact & Escalation

### Development Team
- Primary: [Your Name] - [Email] - [Phone]
- Backup: [Backup Name] - [Email] - [Phone]

### Critical Alerts
- Strike rate < 30%: Escalate immediately
- Negative ROI 5+ days: Escalate within 4 hours
- System errors: Escalate within 1 hour
- Data quality issues: Escalate within 2 hours

---

## Notes & Lessons Learned

### Week 1 Notes
_Add notes here after first week_

### Week 2 Notes
_Add notes here after second week_

### Week 4 Notes
_Add notes here after Phase 2 complete_

### Week 12 Notes
_Add notes here after Phase 3 complete_

---

**Last Updated**: May 20, 2026  
**Version**: 1.0  
**Status**: Ready for Phase 1 deployment
