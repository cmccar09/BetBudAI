# BetBudAI Fanout Optimization - Quick Start Guide

**Created**: 2026-05-20  
**Deploy Time**: ~30 minutes for Phase 1

---

## What This Does

Optimizes BetBudAI job scheduling and adds parallel execution:

✅ **Faster Results**: Results arrive 33% faster (20 min vs 30 min)  
✅ **Better Coverage**: Optimized refresh times (14:30, 17:30 instead of 14:00, 18:00)  
✅ **Cost Savings**: 40% fewer daily invocations (~12 less per day)  
✅ **Faster Pipelines**: 25-28% faster execution with parallel tasks  

---

## Before You Start

**Prerequisites**:
1. AWS CLI configured (`aws configure`)
2. Correct region set: `export AWS_REGION=eu-west-1`
3. Python 3.9+ installed
4. Boto3 installed: `pip install boto3`

**Backup**:
```bash
# Backup current EventBridge rules
aws events list-rules --region eu-west-1 > backup-eventbridge-rules-$(date +%Y%m%d).json

# Backup Step Functions
aws stepfunctions list-state-machines --region eu-west-1 > backup-stepfunctions-$(date +%Y%m%d).json
```

---

## Phase 1: Schedule Optimization (Deploy Today)

**Time**: 10 minutes  
**Risk**: Low  
**Impact**: Immediate cost savings + better coverage

### Step 1: Dry Run (Verify)

```bash
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI

# Preview changes (no actual deployment)
python scripts/deploy_fanout_tasks.py --phase 1 --dry-run
```

**Expected Output**:
```
======================================================================
PHASE 1: SCHEDULE OPTIMIZATION
======================================================================

[1/4] Removing deprecated schedule rules...
  [DRY RUN] Would remove: betbudai-refresh-14-trigger
  [DRY RUN] Would remove: betbudai-refresh-18-trigger

[2/4] Creating/updating main schedule rules...
  [DRY RUN] Would create: betbudai-morning-trigger (08:30 UTC)
  [DRY RUN] Would create: betbudai-refresh-14-30-trigger (14:30 UTC)
  [DRY RUN] Would create: betbudai-refresh-17-30-trigger (17:30 UTC)
  ...

[3/4] Creating optimized results polling schedule...
  [DRY RUN] Would create 27 poll times (every 20 min, 13:00-21:00 UTC)

[4/4] Deployment summary
  - Removed: 2 old rules
  - Created/Updated: 8 main schedules
  - Created: 27 polling schedules
  - New polling frequency: Every 20 minutes (13:00-21:00 UTC)
  - Daily invocation reduction: ~12 invocations/day (~40%)

⚠ DRY RUN - No changes made
```

### Step 2: Deploy (For Real)

```bash
# Deploy schedule changes
python scripts/deploy_fanout_tasks.py --phase 1

# Wait ~30 seconds for AWS to propagate changes

# Verify deployment
aws events list-rules --region eu-west-1 | grep betbudai | wc -l
# Should show ~35 rules (8 main + 27 polling)
```

### Step 3: Verify New Schedule

```bash
# Check specific rules
aws events describe-rule --name betbudai-refresh-14-30-trigger --region eu-west-1
aws events describe-rule --name betbudai-refresh-17-30-trigger --region eu-west-1

# Verify old rules removed
aws events describe-rule --name betbudai-refresh-14-trigger --region eu-west-1
# Should return: ResourceNotFoundException
```

### Step 4: Monitor First Runs

**Watch CloudWatch Logs**:
```bash
# Tomorrow morning at 08:30 UTC
aws logs tail /aws/lambda/betbudai-morning --follow --region eu-west-1

# Tomorrow afternoon at 14:30 UTC
aws logs tail /aws/lambda/betbudai-refresh --follow --region eu-west-1
```

**Success Indicators**:
- ✅ Morning pipeline runs at 08:30 UTC
- ✅ Refresh runs at 12:00, 13:30, 14:30, 16:00, 17:30 UTC
- ✅ Results polls every 20 min (13:00-21:00 only)
- ✅ Evening pipeline runs at 20:00 UTC
- ✅ No errors in logs

---

## Phase 2: Parallel Execution (Deploy Next Week)

**Time**: 20 minutes  
**Risk**: Low (has fallback)  
**Impact**: 25-28% faster pipelines

### Prerequisites

✅ Phase 1 deployed successfully  
✅ 3+ days of stable operation  
✅ No increased error rates

### Deploy Fanout Step Functions

```bash
# Dry run
python scripts/deploy_fanout_tasks.py --phase 2 --dry-run

# Deploy
python scripts/deploy_fanout_tasks.py --phase 2

# Verify Step Functions created
aws stepfunctions list-state-machines --region eu-west-1 | grep fanout
```

**Expected Step Functions**:
- `betbudai-morning-fanout`: Parallel morning pipeline
- `betbudai-evening-fanout`: Parallel evening pipeline

### Monitor Performance

**Check Execution Times**:
```bash
# Morning pipeline (target: <2.75 min)
aws stepfunctions describe-execution \
  --execution-arn <arn> \
  --region eu-west-1 | jq '.startDate, .stopDate'

# Evening pipeline (target: <3.7 min)
aws stepfunctions describe-execution \
  --execution-arn <arn> \
  --region eu-west-1 | jq '.startDate, .stopDate'
```

---

## Rollback (If Issues)

### Phase 1 Rollback
```bash
# Restore old schedule from backup
aws events put-rule \
  --name betbudai-refresh-14-trigger \
  --schedule-expression "cron(0 14 * * ? *)" \
  --state ENABLED \
  --region eu-west-1

aws events put-rule \
  --name betbudai-refresh-18-trigger \
  --schedule-expression "cron(0 18 * * ? *)" \
  --state ENABLED \
  --region eu-west-1

# Remove new rules
aws events delete-rule --name betbudai-refresh-14-30-trigger --region eu-west-1
aws events delete-rule --name betbudai-refresh-17-30-trigger --region eu-west-1
```

### Phase 2 Rollback
```bash
# Disable Step Functions
aws stepfunctions update-state-machine \
  --state-machine-arn <arn> \
  --role-arn arn:aws:iam::813281204422:role/StepFunctionsExecutionRole-DISABLED \
  --region eu-west-1
```

---

## New Schedule Reference

### Main Pipelines

| Time (UTC) | Job | Purpose |
|------------|-----|---------|
| 08:30 | Morning | Initial odds fetch + analysis |
| 12:00 | Refresh | Pre-racing update |
| 13:30 | Featured Lock | **CRITICAL** - Lock featured picks |
| 14:30 | Refresh | Mid-afternoon (NEW) |
| 16:00 | Refresh | Afternoon update |
| 17:30 | Refresh | Evening update (NEW) |
| 20:00 | Evening | Settle races + P&L + learning |
| 22:00 | Learning Deep | Deep analysis (NEW) |

### Results Polling

**Active Hours**: 13:00-21:00 UTC  
**Frequency**: Every 20 minutes  
**Times**: :00, :20, :40 each hour

**Quiet Hours**: 21:00-13:00 UTC  
**Status**: Disabled (no racing)

---

## Troubleshooting

### Issue: EventBridge rule not triggering

**Check**:
```bash
# Verify rule state
aws events describe-rule --name <rule-name> --region eu-west-1

# Check Lambda permissions
aws lambda get-policy --function-name <function-name> --region eu-west-1
```

**Fix**:
```bash
# Re-add permission
aws lambda add-permission \
  --function-name <function-name> \
  --statement-id <rule-name>-permission \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:eu-west-1:813281204422:rule/<rule-name> \
  --region eu-west-1
```

### Issue: Step Function fails

**Check logs**:
```bash
# Get execution details
aws stepfunctions describe-execution \
  --execution-arn <arn> \
  --region eu-west-1

# Check individual Lambda logs
aws logs tail /aws/lambda/<function-name> --follow --region eu-west-1
```

**Common causes**:
- IAM role missing permissions
- Lambda function not found
- DynamoDB throttling

### Issue: Results not updating

**Check**:
```bash
# Verify results poll is running
aws events describe-rule --name betbudai-results-poll-14-00 --region eu-west-1

# Check if active hours are correct
# (Should only run 13:00-21:00 UTC)
```

---

## Performance Monitoring

### Key Metrics Dashboard

**Create CloudWatch Dashboard**:
```bash
# Deploy monitoring dashboard
aws cloudwatch put-dashboard \
  --dashboard-name BetBudAI-Performance \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "metrics": [
            ["AWS/Lambda", "Duration", {"stat": "Average"}]
          ],
          "period": 300,
          "stat": "Average",
          "region": "eu-west-1",
          "title": "Pipeline Duration"
        }
      }
    ]
  }' \
  --region eu-west-1
```

**View Dashboard**:
https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#dashboards:name=BetBudAI-Performance

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Morning duration | 3.8 min | 2.75 min | 28% faster |
| Evening duration | 6.5 min | 4.9 min | 25% faster |
| Results latency | 30 min | 20 min | 33% faster |
| Daily invocations | 85 | 73 | 14% fewer |
| Quiet-hour invocations | 16 | 0 | 100% reduction |

---

## Success Checklist

### Phase 1 (Week 1)
- [ ] Dry run successful
- [ ] Deployment completed
- [ ] Old rules removed
- [ ] New rules created
- [ ] First morning run successful (08:30)
- [ ] First refresh run successful (12:00)
- [ ] Featured lock working (13:30)
- [ ] New refresh times working (14:30, 17:30)
- [ ] Results polling every 20 min
- [ ] Evening run successful (20:00)
- [ ] No errors in CloudWatch Logs
- [ ] Invocation count reduced

### Phase 2 (Week 2)
- [ ] Phase 1 stable for 3+ days
- [ ] Step Functions deployed
- [ ] Morning fanout working
- [ ] Evening fanout working
- [ ] Execution times improved
- [ ] No DynamoDB conflicts
- [ ] No increase in errors

---

## Support

**Issues**: Report to engineering team  
**Documentation**: 
- Full analysis: [OPTIMIZED_JOB_SCHEDULE_ANALYSIS.md](OPTIMIZED_JOB_SCHEDULE_ANALYSIS.md)
- Deployment plan: [FANOUT_DEPLOYMENT_PLAN.md](FANOUT_DEPLOYMENT_PLAN.md)

**Emergency Rollback**: Contact on-call engineer

---

**Last Updated**: 2026-05-20  
**Version**: 1.0
