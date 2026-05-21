# BetBudAI Fanout Task Deployment Plan

**Created**: 2026-05-20  
**Target**: Optimize all jobs and step functions for parallel execution  
**Expected Impact**: 25-40% faster pipelines, 40% fewer invocations

---

## Executive Summary

This deployment optimizes BetBudAI's daily pipeline execution through:

1. **Schedule Optimization** (Phase 1): Better timing, remove redundancy
2. **Parallel Execution** (Phase 2-3): Fanout independent tasks
3. **Cost Reduction**: ~40% fewer daily invocations

**Timeline**: 4 weeks  
**Risk**: Low (rollback available)  
**Approval Required**: Phase 1 schedule changes

---

## Current State Analysis

### Daily Job Schedule (All times UTC)

| Time | Job | Purpose | Duration | Status |
|------|-----|---------|----------|--------|
| 08:30 | Morning | Initial odds + analysis | 3-5 min | ✅ Optimal |
| 12:00 | Refresh | Pre-racing update | 2-3 min | ✅ Optimal |
| 13:30 | Featured Lock | Lock featured picks | 2-3 min | ✅ CRITICAL |
| 14:00 | Refresh | Mid-day update | 2-3 min | ❌ Too close to 13:30 |
| 16:00 | Refresh | Afternoon update | 2-3 min | ✅ Good |
| 18:00 | Refresh | Evening update | 2-3 min | ⚠️ Marginal value |
| 20:00 | Evening | Settle + P&L + learn | 5-8 min | ✅ Optimal |
| Every 30m | Results Poll | Update results | 1-2 min | ⚠️ Runs 24/7 |

### Problems Identified

1. **14:00 refresh** runs only 30 minutes after featured lock (redundant)
2. **18:00 refresh** runs during quiet period (most racing done)
3. **Results polling** runs during non-racing hours (wasteful)
4. **Sequential execution** causes artificial delays
5. **No parallelization** of independent tasks

---

## Proposed Changes

### Phase 1: Schedule Optimization (Week 1)

**Changes**:
- ❌ Remove 14:00 refresh trigger
- ✅ Add 14:30 refresh trigger (1hr after featured lock)
- ❌ Remove 18:00 refresh trigger
- ✅ Add 17:30 refresh trigger (better evening coverage)
- ✅ Change results polling to 20-minute intervals
- ✅ Disable results polling 21:00-13:00 (non-racing hours)
- ✅ Add 22:00 deep learning window

**New Schedule**:

| Time | Job | Change | Reason |
|------|-----|--------|--------|
| 08:30 | Morning | No change | ✅ Optimal |
| 12:00 | Refresh | No change | ✅ Optimal |
| 13:00-21:00 | Results Poll | Every 20 min (was 30) | ⬆️ Faster results |
| 13:30 | Featured Lock | No change | ✅ CRITICAL |
| 14:30 | Refresh | NEW (was 14:00) | ✅ Better spacing |
| 16:00 | Refresh | No change | ✅ Good timing |
| 17:30 | Refresh | NEW (was 18:00) | ✅ Better evening coverage |
| 20:00 | Evening | No change | ✅ Optimal |
| 22:00 | Learning Deep | NEW | ✅ Post-day analysis |

**Benefits**:
- ✅ Better coverage at 14:30 and 17:30
- ✅ Results arrive 33% faster (20min vs 30min)
- ✅ Reduce ~12 invocations/day (~40% reduction)
- ✅ No quiet-hour polling waste

---

### Phase 2: Morning + Evening Fanout (Week 2)

**Morning Pipeline Parallelization**:

```
Current (Sequential):
betfair-fetch (60s) → analysis (90s) → validate (20s) → featured (45s) → notify (15s)
Total: ~230 seconds (3.8 minutes)

Optimized (Parallel):
betfair-fetch (60s) → [analysis (90s) | free-feeds (60s)] → 
                      [validate (20s) | improver (30s) | featured (45s)] → 
                      notify (15s)
Total: ~165 seconds (2.75 minutes) - 28% faster
```

**Evening Pipeline Parallelization**:

```
Current (Sequential):
SL-results (45s) → fav-results (20s) → betfair-results (45s) → 
cache-roi (15s) → miss-analysis (60s) → learning (90s) → report (30s)
Total: ~305 seconds (5.1 minutes)

Optimized (Parallel):
[SL-results (45s) | betfair-results (45s)] → 
[fav-results (20s) | cache-roi (15s) | miss-analysis (60s)] → 
learning (90s) → report (30s)
Total: ~220 seconds (3.7 minutes) - 28% faster
```

**Implementation**:
- Create new Step Functions with Parallel states
- Use AWS Step Functions Map for fanout
- Non-blocking failure handling
- Correlation IDs for debugging

---

### Phase 3: Refresh Pipeline Fanout (Week 3)

**Parallelization Groups**:

**Group 1** (After odds fetch):
- Run analysis + free feeds in parallel
- Max 90s instead of 150s

**Group 2** (After analysis):
- Validate + improver boost + field comparison in parallel
- Max 30s instead of 65s

**Group 3** (After picks):
- Featured meeting + improver enforcement in parallel
- Max 45s instead of 60s

**Total savings**: ~50-60 seconds per refresh (25% faster)

---

## Deployment Steps

### Week 1: Phase 1 - Schedule Optimization

#### Day 1: Preparation

```bash
# 1. Review analysis document
cat OPTIMIZED_JOB_SCHEDULE_ANALYSIS.md

# 2. Backup current EventBridge rules
aws events list-rules --region eu-west-1 > backup/eventbridge-rules-$(date +%Y%m%d).json

# 3. Test deployment script (dry run)
python scripts/deploy_fanout_tasks.py --phase 1 --dry-run
```

#### Day 2: Deploy Schedule Changes

```bash
# Deploy new schedules
python scripts/deploy_fanout_tasks.py --phase 1

# Verify rules created
aws events list-rules --region eu-west-1 | grep betbudai

# Check Lambda permissions
aws lambda get-policy --function-name betbudai-refresh | jq .
```

#### Day 3-5: Monitor

**Metrics to watch**:
- Lambda invocation count (should decrease ~12/day)
- Results settlement latency (should improve 33%)
- Pipeline execution times (no regression)
- Error rates (should remain <1%)

**Success Criteria**:
- ✅ All new schedules running
- ✅ No increase in errors
- ✅ Invocation count reduced
- ✅ Results arriving faster

---

### Week 2: Phase 2 - Morning + Evening Fanout

#### Day 1: Create Step Functions

```bash
# Deploy fanout Step Functions
python scripts/deploy_fanout_tasks.py --phase 2

# Verify Step Functions created
aws stepfunctions list-state-machines --region eu-west-1 | grep fanout
```

#### Day 2: Update Orchestrator Handlers

1. Update `backend/pipeline/morning/handler.py`:
   - Add logic to invoke `betbudai-morning-fanout` Step Function
   - Keep fallback to sequential if Step Function fails

2. Update `backend/pipeline/evening/handler.py`:
   - Add logic to invoke `betbudai-evening-fanout` Step Function
   - Keep fallback to sequential if Step Function fails

3. Deploy updated Lambda functions:
```bash
cd backend/pipeline
python deploy_lambdas.py
```

#### Day 3: Staged Rollout

**Morning**: Enable fanout for 20% of executions (test mode)
```python
# In morning handler
use_fanout = random.random() < 0.2  # 20% traffic
```

**Monitor**:
- Execution time improvements
- Parallel task success rates
- DynamoDB write conflicts (should be zero)

#### Day 4-5: Full Rollout

- Increase to 100% if no issues
- Monitor for 48 hours
- Rollback if error rate >2%

**Success Criteria**:
- ✅ Morning pipeline <2.75 min (target)
- ✅ Evening pipeline <3.7 min (target)
- ✅ No increase in errors
- ✅ DynamoDB writes successful

---

### Week 3: Phase 3 - Refresh Pipeline Fanout

#### Day 1-2: Design Parallel Refresh SF

1. Create `sf-refresh-parallel.json` with:
   - Parallel Group 1: Analysis + Free Feeds
   - Parallel Group 2: Validate + Improver + Field Compare
   - Parallel Group 3: Featured + Improver Enforcement

2. Test in staging environment

#### Day 3: Deploy to Production

```bash
# Deploy new refresh Step Function
aws stepfunctions create-state-machine \
  --name surebet-refresh-parallel \
  --definition file://sf-refresh-parallel.json \
  --role-arn arn:aws:iam::813281204422:role/StepFunctionsExecutionRole \
  --region eu-west-1
```

#### Day 4-5: Monitor

**Success Criteria**:
- ✅ Refresh pipeline <1.9 min (target)
- ✅ No race conditions
- ✅ Results settlement still works
- ✅ Featured meeting picks still lock at 13:30

---

### Week 4: Advanced Monitoring

#### Setup CloudWatch Dashboard

```bash
# Deploy monitoring dashboard
aws cloudwatch put-dashboard \
  --dashboard-name BetBudAI-Fanout-Performance \
  --dashboard-body file://dashboards/fanout-metrics.json \
  --region eu-west-1
```

**Dashboard Metrics**:
- Pipeline execution times (trend)
- Parallel task success rates
- DynamoDB throttling events
- Error rates by pipeline
- Cost comparison (before/after)

#### Create Alarms

```bash
# Morning pipeline duration alarm
aws cloudwatch put-metric-alarm \
  --alarm-name betbudai-morning-slow \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 180000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region eu-west-1

# Evening pipeline duration alarm
aws cloudwatch put-metric-alarm \
  --alarm-name betbudai-evening-slow \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 240000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region eu-west-1
```

---

## Rollback Procedures

### Emergency Rollback (If issues detected)

#### Phase 1 Rollback (Schedule)
```bash
# Restore old schedule from backup
python scripts/deploy_fanout_tasks.py --rollback --phase 1

# Manually restore old rules if needed
aws events put-rule \
  --name betbudai-refresh-14-trigger \
  --schedule-expression "cron(0 14 * * ? *)" \
  --state ENABLED \
  --region eu-west-1
```

#### Phase 2 Rollback (Fanout)
```bash
# Disable Step Function invocation in handlers
# Edit handler.py: use_fanout = False

# Redeploy handlers
cd backend/pipeline
python deploy_lambdas.py

# Disable Step Functions (optional)
aws stepfunctions update-state-machine \
  --state-machine-arn <arn> \
  --role-arn arn:aws:iam::813281204422:role/StepFunctionsExecutionRole-DISABLED \
  --region eu-west-1
```

#### Phase 3 Rollback (Refresh)
```bash
# Revert to old Step Function definition
aws stepfunctions update-state-machine \
  --state-machine-arn <arn> \
  --definition file://backup/sf-refresh-live-fixed.json \
  --region eu-west-1
```

---

## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schedule change breaks picks timing | Low | High | Test in staging first, monitor closely |
| Parallel tasks write conflicts | Medium | Medium | Use DynamoDB conditional writes |
| Increased AWS costs | Low | Low | Parallelization saves time, not invocations |
| Step Function failures | Low | Medium | Fallback to sequential in handler |
| Results polling gaps | Low | High | Active hours only, test thoroughly |

### Monitoring Plan

**Pre-Deployment**:
- ✅ Backup all EventBridge rules
- ✅ Backup all Step Function definitions
- ✅ Document current baseline metrics
- ✅ Test deployment scripts (dry run)

**During Deployment**:
- ✅ Deploy during quiet hours (23:00 UTC)
- ✅ Monitor CloudWatch Logs in real-time
- ✅ Check first execution of each pipeline
- ✅ Verify DynamoDB writes successful

**Post-Deployment** (48 hours):
- ✅ Compare execution times vs targets
- ✅ Check error rates (<2% threshold)
- ✅ Verify results settlement working
- ✅ Confirm picks still arriving on time
- ✅ Review cost implications

---

## Success Metrics

### Performance KPIs (Target vs Actual)

| Metric | Baseline | Target | Actual | Status |
|--------|----------|--------|--------|--------|
| Morning duration | 3.8 min | 2.75 min | TBD | 🔄 |
| Refresh duration | 2.5 min | 1.9 min | TBD | 🔄 |
| Evening duration | 6.5 min | 4.9 min | TBD | 🔄 |
| Results latency | 30 min | 20 min | TBD | 🔄 |
| Daily invocations | 85 | 73 | TBD | 🔄 |
| Error rate | <1% | <2% | TBD | 🔄 |

### Business KPIs

| Metric | Baseline | Target | Actual | Status |
|--------|----------|--------|--------|--------|
| Time to first pick | 08:35 UTC | 08:33 UTC | TBD | 🔄 |
| Results update frequency | 30 min | 20 min | TBD | 🔄 |
| System uptime | 98.5% | 99.0% | TBD | 🔄 |
| User satisfaction | - | +10% | TBD | 🔄 |

---

## Documentation Updates

After deployment, update:

1. **DEPLOYMENT_GUIDE.md**: Add fanout architecture notes
2. **README.md**: Update pipeline timing details
3. **SYSTEM_DASHBOARD.md**: Add fanout performance metrics
4. **CLAUDE.md**: Document new Step Functions (if exists)
5. **API docs**: Update latency expectations

---

## Approval Checklist

### Phase 1: Schedule Optimization
- [ ] Business owner approval (timing changes)
- [ ] Technical lead review (architecture)
- [ ] Backup procedures verified
- [ ] Monitoring dashboard ready
- [ ] Rollback plan tested

### Phase 2: Morning + Evening Fanout
- [ ] Phase 1 successful (3+ days stable)
- [ ] Step Function definitions reviewed
- [ ] Parallel execution tested in staging
- [ ] DynamoDB write patterns validated
- [ ] Rollback plan tested

### Phase 3: Refresh Pipeline Fanout
- [ ] Phase 2 successful (1+ week stable)
- [ ] Complex parallel logic reviewed
- [ ] Featured meeting lock timing verified
- [ ] Results settlement tested
- [ ] Performance targets achieved

---

## Post-Deployment Review (Week 5)

### Review Meeting Agenda

1. **Performance Analysis**
   - Compare actual vs target metrics
   - Identify bottlenecks remaining
   - Discuss further optimization opportunities

2. **Cost Analysis**
   - Review AWS bill changes
   - Confirm invocation reduction
   - Calculate ROI

3. **Incident Review**
   - List any issues encountered
   - Document root causes
   - Update runbooks

4. **User Feedback**
   - Collect user reports on timing
   - Assess picks quality (unchanged?)
   - Review results latency improvements

5. **Next Steps**
   - Approve advanced parallelization (if applicable)
   - Plan further optimizations
   - Update roadmap

---

## Support & Contacts

**Deployment Lead**: BetBudAI Engineering  
**On-Call**: PagerDuty rotation  
**Escalation**: Slack #betbudai-incidents  

**Emergency Rollback Authority**: Engineering Lead (24/7)

**Documentation**: 
- This plan: `FANOUT_DEPLOYMENT_PLAN.md`
- Analysis: `OPTIMIZED_JOB_SCHEDULE_ANALYSIS.md`
- Script: `scripts/deploy_fanout_tasks.py`

---

## Appendix A: Quick Reference Commands

### Deploy Commands
```bash
# Phase 1: Schedule optimization
python scripts/deploy_fanout_tasks.py --phase 1 --dry-run
python scripts/deploy_fanout_tasks.py --phase 1

# Phase 2: Morning + Evening fanout
python scripts/deploy_fanout_tasks.py --phase 2 --dry-run
python scripts/deploy_fanout_tasks.py --phase 2

# Phase 3: Refresh fanout
python scripts/deploy_fanout_tasks.py --phase 3 --dry-run
python scripts/deploy_fanout_tasks.py --phase 3
```

### Monitoring Commands
```bash
# Check EventBridge rules
aws events list-rules --region eu-west-1 | grep betbudai

# Check Step Function executions
aws stepfunctions list-executions \
  --state-machine-arn <arn> \
  --max-results 10 \
  --region eu-west-1

# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=betbudai-morning \
  --start-time 2026-05-20T00:00:00Z \
  --end-time 2026-05-21T00:00:00Z \
  --period 3600 \
  --statistics Average \
  --region eu-west-1
```

### Rollback Commands
```bash
# Rollback to sequential
python scripts/deploy_fanout_tasks.py --rollback --dry-run
python scripts/deploy_fanout_tasks.py --rollback

# Manual rule deletion
aws events delete-rule \
  --name betbudai-refresh-14-30-trigger \
  --region eu-west-1
```

---

**Document Version**: 1.0  
**Author**: BetBudAI Engineering  
**Last Updated**: 2026-05-20  
**Next Review**: 2026-06-20 (post-deployment)
