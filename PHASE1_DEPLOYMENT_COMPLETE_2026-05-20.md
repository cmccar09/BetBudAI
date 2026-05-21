# Phase 1 Deployment Complete - Schedule Optimization

**Deployment Date**: May 20, 2026  
**Deployment Time**: $(date +"%Y-%m-%d %H:%M:%S %Z")  
**Phase**: 1 - Schedule Optimization  
**Status**: ✅ **SUCCESSFULLY DEPLOYED**

---

## Deployment Summary

Phase 1 of the BetBudAI Fanout Optimization has been successfully deployed to production. The optimized schedule is now active and running.

### What Was Deployed

#### ✅ Successfully Created/Updated (8 main schedules)

1. **betbudai-morning-trigger** - `cron(30 8 * * ? *)` (08:30 UTC)
   - Status: ✅ Deployed
   - Target: `betbudai-morning`

2. **betbudai-refresh-12-trigger** - `cron(0 12 * * ? *)` (12:00 UTC)
   - Status: ✅ Deployed
   - Target: `betbudai-refresh`

3. **betbudai-featured-lock-trigger** - `cron(30 13 * * ? *)` (13:30 UTC) **CRITICAL**
   - Status: ✅ Deployed
   - Target: `betbudai-refresh`
   - **Note**: Featured meeting lock - DO NOT CHANGE

4. **betbudai-refresh-14-30-trigger** - `cron(30 14 * * ? *)` (14:30 UTC) **NEW**
   - Status: ✅ Deployed
   - Target: `betbudai-refresh`
   - **Note**: Replaced 14:00 refresh (better spacing after featured lock)

5. **betbudai-refresh-16-trigger** - `cron(0 16 * * ? *)` (16:00 UTC)
   - Status: ✅ Deployed
   - Target: `betbudai-refresh`

6. **betbudai-refresh-17-30-trigger** - `cron(30 17 * * ? *)` (17:30 UTC) **NEW**
   - Status: ✅ Deployed
   - Target: `betbudai-refresh`
   - **Note**: Replaced 18:00 refresh (better evening coverage)

7. **betbudai-evening-trigger** - `cron(0 20 * * ? *)` (20:00 UTC)
   - Status: ✅ Deployed
   - Target: `betbudai-evening`

8. **betbudai-learning-deep-trigger** - `cron(0 22 * * ? *)` (22:00 UTC) **NEW**
   - Status: ✅ Deployed (rule created)
   - Target: `betbudai-learning-orchestrator`
   - **Note**: Lambda function doesn't exist yet - will be created in future deployment

#### ✅ Successfully Created (27 polling schedules)

Results polling every 20 minutes from 13:00-21:00 UTC (active racing hours):
- 13:00, 13:20, 13:40
- 14:00, 14:20, 14:40
- 15:00, 15:20, 15:40
- 16:00, 16:20, 16:40
- 17:00, 17:20, 17:40
- 18:00, 18:20, 18:40
- 19:00, 19:20, 19:40
- 20:00, 20:20, 20:40
- 21:00, 21:20, 21:40

**Target**: `betbudai-results-poll` (Lambda function doesn't exist yet - rules will activate when function is deployed)

#### ❌ Successfully Removed (2 old rules)

1. **betbudai-refresh-14-trigger** (14:00 refresh)
   - Status: Already removed (was not found)
   
2. **betbudai-refresh-18-trigger** (18:00 refresh)
   - Status: ✅ Successfully deleted

---

## New Schedule (Active Now)

### Main Pipelines (UTC)

| Time | Job | Type | Status |
|------|-----|------|--------|
| 08:30 | Morning Pipeline | Critical | ✅ Active |
| 12:00 | Refresh | High Priority | ✅ Active |
| 13:30 | **Featured Lock** | **CRITICAL** | ✅ Active |
| 14:30 | Refresh | Medium Priority | ✅ Active (NEW) |
| 16:00 | Refresh | Medium Priority | ✅ Active |
| 17:30 | Refresh | Medium Priority | ✅ Active (NEW) |
| 20:00 | Evening Pipeline | Critical | ✅ Active |
| 22:00 | Learning Deep | Low Priority | ⏸️ Waiting for function |

### Results Polling (UTC)

**Active Hours**: 13:00-21:00 UTC  
**Frequency**: Every 20 minutes (:00, :20, :40)  
**Status**: ⏸️ Waiting for `betbudai-results-poll` function deployment

---

## Expected Impact (Once Fully Active)

### Performance Improvements

✅ **Results Latency**: 30 min → 20 min (33% faster)  
✅ **Better Coverage**: 14:30 and 17:30 replace 14:00 and 18:00  
✅ **No Wasteful Polling**: Disabled 21:00-13:00 UTC (quiet hours)

### Cost Savings

✅ **Daily Invocations**: Will reduce by ~12/day when polling function is deployed  
✅ **Monthly Savings**: Estimated $27/month  
✅ **Annual Savings**: Estimated $324/year

### Coverage Improvements

✅ **14:30 Refresh**: Better spacing (1 hour after featured lock)  
✅ **17:30 Refresh**: Better evening coverage (replaces 18:00)  
✅ **Active-Hours Polling**: No wasteful overnight invocations

---

## Known Issues & Next Steps

### ⚠️ Missing Lambda Functions

The following Lambda functions don't exist yet but have EventBridge rules ready:

1. **betbudai-learning-orchestrator** (for 22:00 learning deep dive)
   - Rule: `betbudai-learning-deep-trigger` (created, waiting)
   - Action Needed: Deploy learning orchestrator function

2. **betbudai-results-poll** (for 20-minute polling)
   - Rules: 27 polling schedules (created, waiting)
   - Action Needed: Deploy results polling function OR update rules to use existing function

### Next Deployment Steps

1. **Identify Existing Results Polling Function**
   - Current system uses Step Function: `surebet-results-poll-live`
   - Decision needed: Create new Lambda or update rules to use Step Function

2. **Deploy Learning Orchestrator** (if desired)
   - Create `betbudai-learning-orchestrator` Lambda
   - Or update `betbudai-learning-deep-trigger` to use existing `betbudai-learning` function

3. **Phase 2 Preparation** (Week 2)
   - Monitor Phase 1 for 3 days
   - Verify all schedules working correctly
   - Prepare fanout Step Functions

---

## Monitoring & Verification

### Immediate Verification (Next 24 Hours)

**Tomorrow Morning** (May 21, 2026):
- [ ] 08:30 UTC - Verify morning pipeline runs
- [ ] 12:00 UTC - Verify refresh runs
- [ ] 13:30 UTC - **CRITICAL** - Verify featured lock runs
- [ ] 14:30 UTC - Verify new refresh time works
- [ ] 16:00 UTC - Verify refresh runs
- [ ] 17:30 UTC - Verify new evening refresh works
- [ ] 20:00 UTC - Verify evening pipeline runs

### CloudWatch Monitoring

**Check Logs**:
```bash
# Morning pipeline
aws logs tail /aws/lambda/betbudai-morning --follow --region eu-west-1

# Refresh pipeline
aws logs tail /aws/lambda/betbudai-refresh --follow --region eu-west-1

# Evening pipeline
aws logs tail /aws/lambda/betbudai-evening --follow --region eu-west-1
```

**Check EventBridge Metrics**:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name TriggeredRules \
  --dimensions Name=RuleName,Value=betbudai-morning-trigger \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region eu-west-1
```

---

## Rollback Procedure (If Needed)

If issues are detected, rollback is simple:

### Quick Rollback Commands

```bash
# Restore 14:00 refresh
aws events put-rule \
  --name betbudai-refresh-14-trigger \
  --schedule-expression "cron(0 14 * * ? *)" \
  --state ENABLED \
  --region eu-west-1

# Restore 18:00 refresh
aws events put-rule \
  --name betbudai-refresh-18-trigger \
  --schedule-expression "cron(0 18 * * ? *)" \
  --state ENABLED \
  --region eu-west-1

# Remove new 14:30 refresh
aws events delete-rule \
  --name betbudai-refresh-14-30-trigger \
  --region eu-west-1

# Remove new 17:30 refresh
aws events delete-rule \
  --name betbudai-refresh-17-30-trigger \
  --region eu-west-1

# Disable 20-minute polling rules
for hour in {13..21}; do
  for min in 00 20 40; do
    aws events disable-rule \
      --name betbudai-results-poll-${hour}-${min} \
      --region eu-west-1
  done
done
```

**Rollback Time**: ~5 minutes  
**Risk**: Low (just EventBridge rules, no code changes)

---

## Backup Location

Full backup of EventBridge rules before deployment:
```
backup/eventbridge-rules-backup-YYYYMMDD-HHMMSS.json
```

---

## Success Criteria (3-Day Evaluation)

Phase 1 will be considered successful if:

- [ ] All main schedules trigger at correct times
- [ ] Featured lock continues working at 13:30 UTC (CRITICAL)
- [ ] No increase in error rates
- [ ] Morning pipeline runs successfully at 08:30
- [ ] New refresh times (14:30, 17:30) work correctly
- [ ] Evening pipeline runs successfully at 20:00
- [ ] No user complaints about timing changes

**Evaluation Date**: May 23, 2026  
**Phase 2 Deployment**: Pending Phase 1 success (Week of May 27, 2026)

---

## Communication

### Internal Team
- ✅ Engineering team notified of deployment
- ✅ Deployment summary shared
- ⏳ 3-day monitoring period begins

### Stakeholders
- ⏳ Daily status updates during monitoring period
- ⏳ Full Phase 1 report after 3 days

### Users
- No user-facing changes (backend optimization only)
- Results will arrive slightly faster once polling function is updated

---

## Phase 2 Preview

**Planned for Week 2** (May 27-31, 2026):
- Deploy fanout Step Functions for parallel execution
- Morning pipeline: 28% faster (3.8 min → 2.75 min)
- Evening pipeline: 25% faster (6.5 min → 4.9 min)
- Prerequisites: Phase 1 stable for 3+ days

---

## Contact & Support

**Deployment Lead**: BetBudAI Engineering Team  
**On-Call**: PagerDuty rotation  
**Issues**: Slack #betbudai-dev  
**Emergency Rollback**: Contact engineering lead

---

## Deployment Checklist

### Pre-Deployment
- [x] Backup current EventBridge rules
- [x] Test deployment script (dry-run)
- [x] Review deployment plan
- [x] Verify AWS credentials

### Deployment
- [x] Remove deprecated rules (14:00, 18:00)
- [x] Create new schedules (14:30, 17:30, 22:00)
- [x] Create polling schedules (27 rules)
- [x] Verify rules created successfully

### Post-Deployment
- [ ] Monitor first morning run (08:30 UTC tomorrow)
- [ ] Verify featured lock (13:30 UTC tomorrow)
- [ ] Check new refresh times (14:30, 17:30 tomorrow)
- [ ] Review CloudWatch metrics (24 hours)
- [ ] Deploy missing Lambda functions (results-poll, learning-deep)
- [ ] Complete 3-day evaluation
- [ ] Approve Phase 2 (if successful)

---

**Deployment Status**: ✅ **PHASE 1 COMPLETE**  
**Next Milestone**: 3-day monitoring period  
**Phase 2 Target**: Week of May 27, 2026

---

**Document Version**: 1.0  
**Created**: May 20, 2026  
**Author**: BetBudAI Engineering Team
