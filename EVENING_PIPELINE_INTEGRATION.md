# Evening Pipeline Learning Integration Guide

**Version**: 1.0  
**Last Updated**: May 20, 2026  
**Status**: Ready for Production Deployment

---

## Overview

This document describes the integration of the **Automated Learning System** into the existing **Evening Pipeline**.

### Current Evening Pipeline Flow

```
21:00 UTC → Fetch results from Sporting Life (surebet-sl-results)
21:02 UTC → Update fav/form stats (surebet-fav-results)
21:04 UTC → Fetch Betfair SP (surebet-results-fetch)
21:06 UTC → Generate P&L report (surebet-loss-report)
21:08 UTC → Cache ROI summary (surebet-cache-roi)
21:10 UTC → Optional: Miss analysis (evening-miss-analysis)
21:12 UTC → Send daily report email
```

### Enhanced Pipeline Flow (With Learning)

```
21:00 UTC → Fetch results from Sporting Life
21:02 UTC → Update fav/form stats
21:04 UTC → Fetch Betfair SP
21:06 UTC → Generate P&L report
21:08 UTC → Cache ROI summary
21:10 UTC → Optional: Miss analysis
21:15 UTC → ⚡ TRIGGER AUTOMATED LEARNING ⚡
           ├─ Learning orchestrator spawns
           ├─ Analyze today's races in parallel
           ├─ Detect patterns (2-3 seconds)
           ├─ Evaluate weight adjustments (1 second)
           ├─ Deploy high-confidence changes (1 second)
           └─ Generate learning insights (1 second)
21:20 UTC → Send enhanced daily report (with learning insights)
```

**Total Additional Time**: ~5-8 seconds  
**Expected Impact**: +20-30 winners/week

---

## Integration Architecture

### Components

1. **Learning Integrator** (`backend/pipeline/evening/learning_integration.py`)
   - Fetches settled races from DynamoDB
   - Analyzes misses and wins
   - Detects patterns
   - Evaluates weight adjustments
   - Deploys changes (if confidence > 80%)

2. **Lambda Orchestrator** (`backend/lambda/learning_orchestrator_handler.py`)
   - AWS Lambda wrapper
   - Handles invocation from evening pipeline
   - Manages timeout and error handling
   - Returns structured results

3. **DynamoDB Tables**
   - `BetBudAI_LearningInsights`: Stores analysis results
   - `BetBudAI_WeightChangelog`: Tracks weight changes
   - `SureBetBets`: Main data source (existing)

4. **CloudWatch Dashboard**
   - Real-time monitoring
   - Performance metrics
   - Pattern detection frequency
   - Lambda execution stats

---

## Modification to Evening Pipeline

### File: `backend/pipeline/evening/handler.py`

**Location**: After optional analysis steps (around line 97)

**Add This Code**:

```python
# Trigger automated learning (ADDED 2026-05-20)
if run_analysis:
    try:
        from backend.pipeline.evening.learning_integration import (
            invoke_learning_orchestrator,
            generate_enhanced_daily_report
        )

        logger.info("[evening-pipeline] Triggering automated learning...")
        learning_results = invoke_learning_orchestrator(target_date, event)

        if learning_results.get('status') == 'success':
            logger.info(
                f"[evening-pipeline] Learning complete: "
                f"Analyzed {learning_results.get('races_analyzed', 0)} races, "
                f"deployed {learning_results.get('adjustments_deployed', 0)} adjustments"
            )
            analysis_results['automated_learning'] = learning_results

            # Generate enhanced report
            enhanced_report = generate_enhanced_daily_report(
                base_report={'roi_data': analysis_results.get('daily_roi', {})},
                learning_results=learning_results,
                target_date=target_date
            )

            # Store enhanced report for email
            analysis_results['enhanced_report_text'] = enhanced_report

        else:
            logger.warning(
                f"[evening-pipeline] Learning skipped: "
                f"{learning_results.get('reason', learning_results.get('error', 'unknown'))}"
            )
            analysis_results['automated_learning'] = learning_results

    except Exception as e:
        logger.error(f"[evening-pipeline] Learning failed: {e}", exc_info=True)
        analysis_results['automated_learning'] = {'status': 'error', 'error': str(e)}
```

**Why This Location?**
- After results are settled and ROI calculated
- Before daily report email (so we can include learning insights)
- Non-blocking: If learning fails, pipeline continues

---

## Pattern Detection Rules

The learning system detects these patterns automatically:

### Miss Patterns (Why We Lost)

| Pattern | Trigger | Action | Confidence |
|---------|---------|--------|------------|
| **Consistent Placer Bias** | Winner was improver, we picked consistent placer | Decrease `consistency` (-33%), decrease `form_velocity_bonus` (-33%) | 85% |
| **Class Advantage Missed** | Winner had class drop, we didn't | Increase `class_drop_bonus` (+25%), increase `class_drop_rebound_bonus` (+25%) | 60% |
| **Course Form Underweight** | Winner had 2+ more course wins | Increase `course_bonus` (+20%), increase `cd_bonus` (+15%) | 70% |
| **Trainer Form Underweight** | Winner had better trainer rank | Increase `trainer_form_bonus` (+25%), increase `trainer_course_bonus` (+20%) | 65% |
| **Market Overreliance** | We picked favorite <4.0, it lost | Decrease `favorite_correction` (-40%), decrease `sweet_spot` (-25%) | 75% |

### Win Patterns (What We Did Right)

| Pattern | Trigger | Action | Confidence |
|---------|---------|--------|------------|
| **Improver Success** | Winner was flagged as improver | Increase `form_velocity_bonus` (+15%) | 80% |
| **Class Drop Success** | Winner had class drop | Increase `class_drop_bonus` (+10%) | 85% |
| **Course Specialist Success** | Winner had 2+ course wins | Increase `course_bonus` (+10%) | 80% |

### Deployment Threshold

**Adjustments are only deployed if**:
- Confidence ≥ 80% (configurable)
- Pattern appears in ≥20% of races
- Change is within safety limits (±50% max)

---

## Configuration Options

### Environment Variables (Lambda)

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | 0.80 | Minimum confidence to deploy adjustments |
| `ENABLE_AUTO_DEPLOY` | true | Enable automatic weight deployment |
| `DRY_RUN` | false | If true, only log adjustments (don't deploy) |
| `MAX_WORKERS` | 10 | Maximum parallel analysis workers |

### Event Parameters (Evening Pipeline)

You can override defaults by passing these in the event:

```json
{
  "target_date": "2026-05-20",
  "run_analysis": true,
  "learning_confidence_threshold": 0.80,
  "learning_auto_deploy": true,
  "learning_dry_run": false,
  "learning_max_races": 50
}
```

---

## Safety Features

### 1. Confidence Threshold
- Only deploy changes with ≥80% confidence
- Lower confidence changes are logged but not applied

### 2. Change Limits
- Maximum change per adjustment: ±50%
- Maximum total change per weight per day: ±50%

### 3. Rollback Mechanism
- All changes logged to `BetBudAI_WeightChangelog`
- Previous weights stored with timestamp
- Can rollback manually via DynamoDB

### 4. Dry Run Mode
- Test learning without deploying
- Set `DRY_RUN=true` in Lambda env vars
- Logs all proposed changes

### 5. Fail-Safe
- Learning failures don't block evening pipeline
- Email report still sent (without learning section)
- CloudWatch alerts for errors

---

## Monitoring & Alerts

### CloudWatch Dashboard

Deploy the dashboard to monitor:
- Daily races analyzed
- Patterns detected
- Adjustments deployed
- Strike rate trend (7-day rolling)
- Lambda execution time
- Error rate

**Deploy Command**:
```bash
aws cloudwatch put-dashboard \
  --dashboard-name BetBudAI-Learning \
  --dashboard-body file://cloudwatch_dashboard.json \
  --region eu-west-1
```

### CloudWatch Alarms

Set up alarms for:
1. **Learning Lambda Errors** (threshold: 1 error)
2. **High Execution Time** (threshold: 120 seconds)
3. **Strike Rate Drop** (threshold: <30% for 3 days)
4. **No Adjustments Deployed** (threshold: 0 for 7 days)

---

## Testing Before Production

### 1. Dry Run Test (Yesterday's Data)

```bash
# Test with yesterday's data without deploying
aws lambda invoke \
  --function-name betbudai-learning-orchestrator \
  --payload '{
    "target_date": "2026-05-19",
    "learning_confidence_threshold": 0.80,
    "learning_auto_deploy": false,
    "learning_dry_run": true,
    "learning_max_races": 10
  }' \
  --region eu-west-1 \
  /tmp/learning_test.json

# View results
cat /tmp/learning_test.json | jq .
```

### 2. Historical Analysis (Last 7 Days)

```bash
# Analyze patterns over last week
for i in {1..7}; do
  DATE=$(date -u -d "$i days ago" +%Y-%m-%d)
  echo "Analyzing $DATE..."

  aws lambda invoke \
    --function-name betbudai-learning-orchestrator \
    --payload "{\"target_date\": \"$DATE\", \"learning_dry_run\": true}" \
    --region eu-west-1 \
    /tmp/learning_$DATE.json
done

# Aggregate results
jq -s '[.[] | .body | fromjson] | 
  {
    total_races: ([.[].races_analyzed] | add),
    total_patterns: ([.[].patterns_detected] | add),
    total_adjustments: ([.[].adjustments_proposed] | add)
  }' /tmp/learning_*.json
```

### 3. Integration Test (Full Pipeline)

```bash
# Test full evening pipeline with learning
aws lambda invoke \
  --function-name surebet-evening-pipeline \
  --payload '{
    "stage": "evening",
    "target_date": "2026-05-19",
    "send_email": false,
    "run_analysis": true
  }' \
  --region eu-west-1 \
  /tmp/evening_test.json

# Check results
cat /tmp/evening_test.json | jq '.body | fromjson | .analysis_steps.automated_learning'
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Review deployment script: `scripts/deploy_learning_pipeline.sh`
- [ ] Update Lambda execution role ARN in script
- [ ] Verify AWS credentials configured
- [ ] Check DynamoDB table quotas (should be PAY_PER_REQUEST)
- [ ] Review weight adjustment rules
- [ ] Set confidence threshold (recommend 0.80 for first week)

### Deployment

```bash
# Run deployment script
cd /path/to/BetBudAI
chmod +x scripts/deploy_learning_pipeline.sh
./scripts/deploy_learning_pipeline.sh
```

**Script will**:
1. Create DynamoDB tables (if not exist)
2. Package Lambda function
3. Deploy/update Lambda
4. Set environment variables
5. Configure permissions
6. Run test invocation

### Post-Deployment

- [ ] Verify DynamoDB tables created
- [ ] Verify Lambda deployed successfully
- [ ] Test Lambda invocation (dry run)
- [ ] Update evening pipeline handler (add learning code)
- [ ] Deploy updated evening pipeline
- [ ] Deploy CloudWatch dashboard
- [ ] Set up CloudWatch alarms
- [ ] Configure SNS topic for alerts (optional)
- [ ] Send test email with enhanced report
- [ ] Monitor first production run (tonight 21:15 UTC)

---

## Expected Results

### First Week

- **Day 1-2**: Learning system calibrates, few adjustments
- **Day 3-5**: Pattern detection stabilizes, 2-4 adjustments/day
- **Day 6-7**: Strike rate improves by 5-10%

### First Month

- **Week 1**: Baseline establishment
- **Week 2**: Initial improvements (+5-10% strike rate)
- **Week 3**: Model stabilization
- **Week 4**: Target performance (+20-30 winners/week)

### Success Metrics

- ✅ Strike rate: 35-40% (Week 1), 50-55% (Week 4)
- ✅ ROI: +5% (Week 1), +10% (Week 4)
- ✅ Weight adjustments: 3-5/day (stable after Week 2)
- ✅ Learning execution time: <10 seconds
- ✅ Zero critical errors in 7 days

---

## Troubleshooting

### Issue: Learning Lambda Times Out

**Symptoms**: Lambda execution exceeds 600 seconds

**Solutions**:
1. Reduce `MAX_WORKERS` from 10 to 5
2. Reduce `learning_max_races` from 50 to 25
3. Increase Lambda timeout to 900 seconds
4. Optimize race analysis (parallelize more)

### Issue: No Adjustments Deployed

**Symptoms**: Learning runs but deploys 0 adjustments for 3+ days

**Possible Causes**:
1. Confidence threshold too high (>0.80)
2. Not enough data (need more races)
3. Patterns not reaching 20% frequency threshold

**Solutions**:
1. Lower confidence threshold to 0.70 temporarily
2. Wait for more data (give it 7-10 days)
3. Review pattern detection logic

### Issue: Strike Rate Decreases After Deployment

**Symptoms**: Strike rate drops 5%+ after learning enabled

**Immediate Actions**:
1. Enable dry run mode: Set `DRY_RUN=true` in Lambda env vars
2. Review last 3 days of weight changes in `BetBudAI_WeightChangelog`
3. Identify problematic adjustment
4. Manually rollback weights in DynamoDB `SureBetBets` table

**Rollback Steps**:
```bash
# 1. Query recent changes
aws dynamodb query \
  --table-name BetBudAI_WeightChangelog \
  --key-condition-expression "change_date = :date" \
  --expression-attribute-values '{":date": {"S": "2026-05-20"}}' \
  --region eu-west-1

# 2. Manually restore weights in SYSTEM_WEIGHTS record
# (Use AWS Console or CLI to update SureBetBets table)
```

### Issue: DynamoDB Write Throttling

**Symptoms**: Lambda logs show "ProvisionedThroughputExceededException"

**Solutions**:
1. Verify tables use PAY_PER_REQUEST billing mode
2. If on provisioned: Increase write capacity units
3. Add exponential backoff to write operations

---

## Emergency Contact

### Disable Learning System

**If something goes wrong and you need to stop learning immediately**:

```bash
# Option 1: Enable dry run (learning runs but doesn't deploy)
aws lambda update-function-configuration \
  --function-name betbudai-learning-orchestrator \
  --environment "Variables={
    CONFIDENCE_THRESHOLD=0.80,
    ENABLE_AUTO_DEPLOY=false,
    DRY_RUN=true,
    MAX_WORKERS=10
  }" \
  --region eu-west-1

# Option 2: Remove learning from evening pipeline
# Edit backend/pipeline/evening/handler.py
# Comment out or remove the learning integration code block
# Redeploy evening pipeline
```

### Rollback Weights to Emergency V3

```bash
# Restore known-good weights from Emergency V3 deployment
cd /path/to/BetBudAI
python scripts/deploy_emergency_v3.py
```

---

## Support & Documentation

- **Integration Code**: `backend/pipeline/evening/learning_integration.py`
- **Lambda Handler**: `backend/lambda/learning_orchestrator_handler.py`
- **Deployment Script**: `scripts/deploy_learning_pipeline.sh`
- **Monitoring**: CloudWatch Dashboard "BetBudAI-Learning"
- **Changelog**: `BetBudAI_WeightChangelog` DynamoDB table
- **Learning Insights**: `BetBudAI_LearningInsights` DynamoDB table

---

## Next Steps After Successful Deployment

1. **Week 1**: Monitor daily, review adjustments manually
2. **Week 2**: Enable more aggressive thresholds (0.75 confidence)
3. **Week 3**: Add win analysis (not just miss analysis)
4. **Week 4**: Implement weekly pattern recognition
5. **Month 2**: Add market divergence tracking
6. **Month 3**: Implement A/B testing framework

---

**Ready to deploy? Run**: `./scripts/deploy_learning_pipeline.sh`

**Questions?** Review deployment guide: `DEPLOYMENT_GUIDE.md`
