# BetBudAI Job Schedule Optimization Analysis

**Created**: 2026-05-20  
**Purpose**: Review and optimize all scheduled jobs and step functions for timing efficiency

---

## Current Schedule Overview

### Daily Pipeline Schedule (All times UTC)

| Time (UTC) | Job Type | Function | Purpose | Duration | Priority |
|------------|----------|----------|---------|----------|----------|
| **08:30** | Morning | `betbudai-morning` | Initial odds fetch + analysis | ~3-5 min | CRITICAL |
| **12:00** | Refresh | `betbudai-refresh` | Re-fetch odds + re-score | ~2-3 min | HIGH |
| **13:30** | Featured Lock | SF: `surebet-refresh-live` | Lock featured meeting picks | ~2-3 min | HIGH |
| **14:00** | Refresh | `betbudai-refresh` | Mid-day odds update | ~2-3 min | MEDIUM |
| **16:00** | Refresh | `betbudai-refresh` | Pre-evening update | ~2-3 min | MEDIUM |
| **18:00** | Refresh | `betbudai-refresh` | Evening update | ~2-3 min | MEDIUM |
| **20:00** | Evening | `betbudai-evening` | Settle races + P&L + learning | ~5-8 min | CRITICAL |
| **Every 30m** | Results Poll | SF: `surebet-results-poll` | Update results continuously | ~1-2 min | MEDIUM |

### Step Functions

#### 1. Refresh Pipeline (`sf-refresh-live-fixed.json`)
**Schedule**: 12:00, 13:30, 14:00, 16:00, 18:00 UTC  
**Flow**:
1. FetchBetfairOdds
2. RunAnalysis
3. RunPhaseFreeFeeds (Phase 1+2 enrichment)
4. ValidatePicks
5. CalculateImproverBoost (+30/+10 aggressive tuning)
6. ApplyImproverBoostedPicks
7. CompareRaceFields (detect non-runners)
8. AnalyzeFeaturedMeeting (lock at 13:30)
9. ApplyFeaturedImproverBoost
10. SendNotifications
11. RefreshSLResults (early settlement)
12. RefreshFavResults
13. RefreshBetfairResults

**Optimization Notes**:
- 13:30 run is SPECIAL: locks featured meeting picks for the day
- Steps 5-9 are non-blocking optimizations
- Results settlement runs at end of each refresh

#### 2. Results Poll Pipeline (`sf-results-poll-live-fixed.json`)
**Schedule**: Every 30 minutes  
**Flow**:
1. RefreshSLResults (Sporting Life scrape)
2. RefreshFavResults (update favourite outcomes)
3. RunLearning (automated weight nudges)

**Optimization Notes**:
- Runs continuously to catch results as they happen
- Learning runs immediately after each result batch
- Non-blocking: failures don't stop pipeline

#### 3. Evening Pipeline (`evening-sf-def-fixed.json`)
**Schedule**: 20:00 UTC  
**Flow**:
1. FetchSLResults (PRIMARY results source)
2. UpdateFavResults
3. FetchResults (Betfair backup)
4. ApplyLearning
5. SendLossReport (email)
6. CacheROI
7. AnalyzeMisses (8 categories)

**Optimization Notes**:
- Most comprehensive daily wrap-up
- Triggers automated learning system
- Generates next-day recommendations

---

## Lambda Functions Inventory

### Core Pipeline Functions

| Function Name | Triggered By | Purpose | Avg Duration |
|---------------|--------------|---------|--------------|
| `betbudai-morning` | EventBridge 08:30 | Morning orchestration | 3-5 min |
| `betbudai-refresh` | EventBridge 12:00-18:00 | Refresh orchestration | 2-3 min |
| `betbudai-evening` | EventBridge 20:00 | Evening orchestration | 5-8 min |
| `surebet-betfair-fetch` | Orchestrator | Fetch Betfair odds | 30-60s |
| `surebet-analysis` | Orchestrator | 50-signal scoring | 60-90s |
| `surebet-validate` | Orchestrator | Quality gate | 10-20s |
| `surebet-featured-meeting` | Orchestrator | Featured race analysis | 30-45s |
| `surebet-notify` | Orchestrator | Push notifications | 10-15s |
| `surebet-free-feeds` | Step Function | Phase 1+2 enrichment | 45-90s |

### Optimization Functions (Non-blocking)

| Function Name | Purpose | When to Run | Duration |
|---------------|---------|-------------|----------|
| `calculate-improver-boost-scores` | Apply +30/+10 boost | Each refresh | 20-30s |
| `apply-improver-boosted-picks` | Enforce boosted ranking | After boost calc | 10-15s |
| `featured-improver-enforcer` | Boost featured picks | After featured analysis | 15-20s |
| `compare-race-fields` | Detect non-runners | Each refresh | 10-15s |

### Settlement Functions

| Function Name | Purpose | When to Run | Duration |
|---------------|---------|-------------|----------|
| `surebet-sl-results` | Sporting Life scrape | Every 30m + refreshes | 30-45s |
| `surebet-fav-results` | Update fav outcomes | After SL results | 15-20s |
| `surebet-results-fetch` | Betfair settlement | Evening + refreshes | 30-45s |

### Analysis Functions

| Function Name | Purpose | When to Run | Duration |
|---------------|---------|-------------|----------|
| `surebet-loss-report` | Email P&L report | Evening 20:00 | 20-30s |
| `surebet-cache-roi` | Pre-calc ROI | Evening 20:00 | 10-15s |
| `evening-miss-analysis` | Analyze losses | Evening 20:00 | 45-60s |
| `betbudai-learning-orchestrator` | Automated learning | Evening 20:00 | 1-2 min |

---

## Optimal Timing Analysis

### Morning Pipeline (08:30 UTC = 09:30 BST)
**Current**: ✅ OPTIMAL  
**Reasoning**:
- UK racing typically starts 12:30-13:00 BST
- 08:30 UTC gives 3-4 hours before first race
- Early enough to catch overnight market moves
- Late enough that Betfair markets are liquid

**Recommendation**: Keep at 08:30 UTC

---

### Refresh Cycles

#### 12:00 UTC (13:00 BST)
**Current**: ✅ OPTIMAL  
**Reasoning**:
- ~30 mins before typical first race
- Catches morning market moves
- Updates odds for early afternoon racing

**Recommendation**: Keep at 12:00 UTC

#### 13:30 UTC (14:30 BST) - FEATURED MEETING LOCK
**Current**: ✅ CRITICAL TIMING  
**Reasoning**:
- This is when featured meeting picks are LOCKED for the day
- Typically just before main afternoon racing starts
- Gives users stable picks to follow

**Recommendation**: Keep at 13:30 UTC - DO NOT CHANGE

#### 14:00 UTC (15:00 BST)
**Current**: ⚠️ TOO CLOSE TO 13:30  
**Reasoning**:
- Only 30 minutes after featured lock
- May not capture meaningful odds movement
- Wastes compute resources

**Recommendation**: 
- **OPTION A**: Move to 14:30 UTC (1 hour after lock)
- **OPTION B**: Remove entirely if 13:30 + 16:00 sufficient

#### 16:00 UTC (17:00 BST)
**Current**: ✅ GOOD  
**Reasoning**:
- Mid-afternoon update
- Catches late-running odds changes
- Prepares for evening racing

**Recommendation**: Keep at 16:00 UTC

#### 18:00 UTC (19:00 BST)
**Current**: ⚠️ MARGINAL VALUE  
**Reasoning**:
- Most UK racing finished by 18:00-19:00
- Only 2 hours before evening wrap-up
- Limited races still to run

**Recommendation**:
- **OPTION A**: Move to 17:00 UTC (capture late afternoon better)
- **OPTION B**: Remove if 16:00 + 20:00 sufficient

---

### Evening Pipeline (20:00 UTC = 21:00 BST)
**Current**: ✅ OPTIMAL  
**Reasoning**:
- All UK racing complete by 20:00-20:30
- Allows 30-60 min for results to settle
- Perfect timing for daily wrap-up
- Triggers automated learning before midnight

**Recommendation**: Keep at 20:00 UTC

---

### Results Polling (Every 30 minutes)
**Current**: ✅ GOOD BUT OPTIMIZE  
**Reasoning**:
- Continuous polling catches results quickly
- Runs even during non-racing hours (wasteful)

**Recommendation**: 
- **Active Hours**: Poll every 20 minutes from 13:00-21:00 UTC
- **Quiet Hours**: Disable polling 21:00-07:00 UTC (no racing)
- **Savings**: ~10 invocations/day (30%)

---

## Recommended Optimized Schedule

### New Schedule (All times UTC)

| Time | Job | Change | Reason |
|------|-----|--------|--------|
| 08:30 | Morning | No change | ✅ Optimal |
| 12:00 | Refresh | No change | ✅ Optimal |
| 13:00-21:00 | Results Poll | Every 20 min (was 30) | ⬆️ Catch results faster |
| 13:30 | Featured Lock | No change | ✅ CRITICAL - DO NOT CHANGE |
| ~~14:00~~ | ~~Refresh~~ | **REMOVE** | ❌ Too close to 13:30 |
| 14:30 | Refresh | **NEW** | ✅ Better spacing (1hr after lock) |
| 16:00 | Refresh | No change | ✅ Good timing |
| 17:30 | Refresh | **NEW** (was 18:00) | ✅ Catch late racing better |
| 20:00 | Evening | No change | ✅ Optimal |
| 22:00 | Learning Deep Dive | **NEW** | ✅ Post-day analysis window |

### Expected Benefits

**Performance**:
- Results arrive 33% faster (20min vs 30min polls)
- Better odds capture at 14:30 and 17:30
- Reduced redundant processing (remove 14:00)

**Cost Savings**:
- Remove 14:00 refresh: -1 invocation/day
- Remove 18:00 refresh: -1 invocation/day  
- Quiet-hour polling: -10 invocations/day
- **Total savings**: ~12 invocations/day (~40% reduction in refresh calls)

**Improved Coverage**:
- 14:30 catches post-lunch market moves
- 17:30 better positioned for evening racing
- 22:00 learning window for deep analysis

---

## Fanout Architecture Opportunities

### Current Sequential Bottlenecks

1. **Morning Pipeline**: Runs 5 functions sequentially (3-5 min total)
2. **Refresh Pipeline**: Runs 13 steps sequentially (2-3 min total)
3. **Evening Pipeline**: Runs 7 steps sequentially (5-8 min total)

### Parallelization Opportunities

#### 1. Morning Pipeline Fanout

**Current Flow** (Sequential):
```
betfair-fetch → analysis → validate → featured → notify
   60s           90s        20s        45s       15s
Total: ~230 seconds (3.8 minutes)
```

**Optimized Flow** (Parallel):
```
                    ┌→ validate (20s)
betfair-fetch (60s) → analysis (90s) ┼→ featured (45s)
                                    └→ improver-boost (30s)
                    ↓
                    aggregate + notify (15s)
Total: ~165 seconds (2.75 minutes) - 28% faster
```

#### 2. Refresh Pipeline Fanout

**Parallelizable Groups**:

**Group 1** (After odds fetch):
- `RunAnalysis` (90s)
- `RunPhaseFreeFeeds` (60s) - can run in parallel with analysis

**Group 2** (After analysis):
- `ValidatePicks` (20s)
- `CalculateImproverBoost` (30s)
- `CompareRaceFields` (15s)
All run in parallel → Max 30s instead of 65s

**Group 3** (After picks selected):
- `AnalyzeFeaturedMeeting` (45s)
- `ApplyImproverBoostedPicks` (15s)
Run in parallel → Max 45s instead of 60s

**Savings**: ~50-60 seconds per refresh (25% faster)

#### 3. Evening Pipeline Fanout

**Parallelizable**:

**Group 1** (Results fetching):
- `FetchSLResults` (45s)
- `FetchBetfairResults` (45s)
Run in parallel → Max 45s instead of 90s

**Group 2** (After results):
- `UpdateFavResults` (20s)
- `CacheROI` (15s)
- `AnalyzeMisses` (60s)
Run in parallel → Max 60s instead of 95s

**Savings**: ~80 seconds per evening run (25% faster)

---

## Fanout Task Recommendations

### Priority 1: High-Impact Parallelization (Deploy First)

#### A. Morning Pipeline Fanout
- **Impact**: Save ~65 seconds (28%)
- **Complexity**: Low
- **Risk**: Low (independent functions)
- **Deploy**: Week 1

#### B. Evening Results Fanout
- **Impact**: Save ~80 seconds (25%)
- **Complexity**: Low
- **Risk**: Low (SL + Betfair independent)
- **Deploy**: Week 1

### Priority 2: Medium-Impact Parallelization (Deploy Second)

#### C. Refresh Pipeline Optimization Groups
- **Impact**: Save ~50-60 seconds (25%)
- **Complexity**: Medium (need state management)
- **Risk**: Medium (dependencies between groups)
- **Deploy**: Week 2-3

### Priority 3: Advanced Parallelization (Future)

#### D. Learning System Fanout (Already Implemented!)
- ✅ Uses ThreadPoolExecutor for race analysis
- ✅ 10 parallel workers
- ✅ Processes 10 races in ~1 minute (vs 5+ minutes sequential)
- See: `FAN_OUT_ARCHITECTURE.md`

#### E. Per-Race Analysis Fanout
- Parallelize race-level operations across all races
- Use Lambda concurrent invocations
- Deploy: Month 2+

---

## Implementation Plan

### Week 1: Schedule Optimization Only
**Tasks**:
1. Update EventBridge rules:
   - Remove 14:00 refresh trigger
   - Add 14:30 refresh trigger  
   - Change 18:00 → 17:30 trigger
   - Update results poll to 20-minute intervals (13:00-21:00 only)

2. Deploy updated `deploy_lambdas.py` with new schedule

3. Monitor for 3 days to confirm improved coverage

**Deliverable**: New schedule running in production

---

### Week 2: Morning + Evening Fanout
**Tasks**:
1. Create new Step Function: `morning-fanout.json`
   - Parallel execution of validate/featured/improver

2. Create new Step Function: `evening-fanout.json`
   - Parallel execution of SL + Betfair results

3. Update orchestrator handlers to invoke new step functions

4. Deploy and monitor timing improvements

**Deliverable**: 25-28% faster morning and evening pipelines

---

### Week 3: Refresh Pipeline Fanout
**Tasks**:
1. Redesign `sf-refresh-live.json` with Map states
2. Implement parallel groups (see Group 1-3 above)
3. Add aggregation steps between groups
4. Deploy to staging, then production

**Deliverable**: 25% faster refresh pipeline

---

### Week 4: Advanced Monitoring
**Tasks**:
1. Add CloudWatch metrics for parallel execution
2. Set up timing alerts for slow runs
3. Create fanout performance dashboard
4. Document learnings

**Deliverable**: Production-ready fanout monitoring

---

## Risk Mitigation

### Race Conditions
**Risk**: Parallel tasks write to same DynamoDB item  
**Mitigation**: 
- Use DynamoDB conditional writes
- Implement optimistic locking with version attributes
- Separate write paths for each function

### Increased Costs
**Risk**: More concurrent Lambda invocations  
**Mitigation**:
- Parallelization saves time, not invocations
- Schedule optimization reduces total invocations
- Net cost: **REDUCTION** (~12 fewer invocations/day)

### Complexity
**Risk**: Harder to debug parallel failures  
**Mitigation**:
- Comprehensive logging with correlation IDs
- Step Function visual debugging
- Rollback plan: revert to sequential

### Dependency Failures
**Risk**: Parallel task fails, blocks downstream  
**Mitigation**:
- Non-blocking design (use Catch blocks)
- Graceful degradation
- Retry policies per function

---

## Success Metrics

### Performance KPIs

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Morning pipeline duration | 3.8 min | 2.75 min | CloudWatch execution time |
| Refresh pipeline duration | 2.5 min | 1.9 min | CloudWatch execution time |
| Evening pipeline duration | 6.5 min | 4.9 min | CloudWatch execution time |
| Results polling frequency | 30 min | 20 min | EventBridge schedule |
| Daily Lambda invocations | ~85 | ~73 | CloudWatch metrics |

### Business KPIs

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time to first pick | 08:35 UTC | 08:33 UTC | User-facing timestamp |
| Results settlement latency | 30 min avg | 20 min avg | Result timestamp - race time |
| Odds refresh coverage | 5 times/day | 5 times/day | Maintained |
| System reliability | 98.5% | 99.0% | Uptime monitoring |

---

## Rollback Plan

If fanout causes issues:

1. **Immediate rollback**: Revert to old Step Function definitions (saved in git)
2. **Partial rollback**: Keep schedule changes, revert to sequential execution
3. **Gradual rollback**: Disable fanout for specific pipelines only

**Rollback triggers**:
- Error rate >5% on any pipeline
- Duration increase >20%
- User-reported issues with picks timing

---

## Next Steps

1. **Review this document** with team
2. **Approve schedule changes** (Week 1)
3. **Approve fanout architecture** (Weeks 2-4)
4. **Assign implementation** owners
5. **Set deployment dates**

---

## Appendix: Cron Schedule Reference

```bash
# Current EventBridge cron expressions
cron(30 8 * * ? *)   # 08:30 UTC daily (Morning)
cron(0 12 * * ? *)   # 12:00 UTC daily (Refresh)
cron(30 13 * * ? *)  # 13:30 UTC daily (Featured Lock)
cron(0 14 * * ? *)   # 14:00 UTC daily (Refresh) ← REMOVE
cron(0 16 * * ? *)   # 16:00 UTC daily (Refresh)
cron(0 18 * * ? *)   # 18:00 UTC daily (Refresh) ← CHANGE
cron(0 20 * * ? *)   # 20:00 UTC daily (Evening)
rate(30 minutes)     # Results poll ← CHANGE

# Proposed new schedule
cron(30 8 * * ? *)   # 08:30 UTC (Morning) - no change
cron(0 12 * * ? *)   # 12:00 UTC (Refresh) - no change
cron(30 13 * * ? *)  # 13:30 UTC (Featured Lock) - no change
cron(30 14 * * ? *)  # 14:30 UTC (Refresh) - NEW
cron(0 16 * * ? *)   # 16:00 UTC (Refresh) - no change
cron(30 17 * * ? *)  # 17:30 UTC (Refresh) - MOVED from 18:00
cron(0 20 * * ? *)   # 20:00 UTC (Evening) - no change
cron(0 22 * * ? *)   # 22:00 UTC (Learning) - NEW
# Results poll: Custom schedule 13:00-21:00 every 20 min
```

---

**Document Version**: 1.0  
**Author**: BetBudAI Engineering  
**Last Updated**: 2026-05-20
