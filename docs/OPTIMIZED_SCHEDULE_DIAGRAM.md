# BetBudAI Optimized Schedule - Visual Diagram

**Date**: 2026-05-20  
**Status**: Proposed Schedule (Ready for Deployment)

---

## Daily Timeline (UTC)

```
00:00 ─────────────────────────────────────────────────────────────── Midnight
      │
      │  QUIET HOURS - No Racing
      │  (No results polling)
      │
08:00 ├─────────────────────────────────────────────────────────────
08:30 │ ███ MORNING PIPELINE ███
      │ ├─ Fetch Betfair odds
      │ ├─ Run 50-signal analysis
      │ ├─ Validate picks
      │ ├─ Featured meeting analysis
      │ └─ Send notifications
      │ Duration: 2.75 min (target)
09:00 ├─────────────────────────────────────────────────────────────
      │
      │  UK Racing Starts (~12:30-13:00 BST)
      │
12:00 ├─────────────────────────────────────────────────────────────
      │ ███ REFRESH PIPELINE ███
      │ Re-fetch odds, re-score, update picks
      │ Duration: ~2 min
      │
13:00 ├─────────────────────────────────────────────────────────────
      │
      │ ┌─ RESULTS POLLING BEGINS (every 20 min) ─┐
      │ │                                          │
13:30 │ │ ███ FEATURED MEETING LOCK ███ ⚠️ CRITICAL│
      │ │ Final featured picks for the day        │
      │ │ DO NOT CHANGE THIS TIMING               │
      │ │                                          │
14:00 ├─┤ ⏱️ Poll results                          │
14:20 │ │ ⏱️ Poll results                          │
14:30 │ │ ███ REFRESH PIPELINE ███ (NEW)          │
14:40 │ │ ⏱️ Poll results                          │
15:00 ├─┤ ⏱️ Poll results                          │
15:20 │ │ ⏱️ Poll results                          │
15:40 │ │ ⏱️ Poll results                          │
16:00 ├─┤ ███ REFRESH PIPELINE ███                 │
16:20 │ │ ⏱️ Poll results                          │
16:40 │ │ ⏱️ Poll results                          │
17:00 ├─┤ ⏱️ Poll results                          │
17:20 │ │ ⏱️ Poll results                          │
17:30 │ │ ███ REFRESH PIPELINE ███ (NEW)          │
17:40 │ │ ⏱️ Poll results                          │
18:00 ├─┤ ⏱️ Poll results                          │
18:20 │ │ ⏱️ Poll results                          │
18:40 │ │ ⏱️ Poll results                          │
19:00 ├─┤ ⏱️ Poll results                          │
19:20 │ │ ⏱️ Poll results                          │
19:40 │ │ ⏱️ Poll results                          │
20:00 ├─┤ ███ EVENING PIPELINE ███                 │
      │ │ ├─ Fetch SL results                     │
      │ │ ├─ Fetch Betfair results                │
      │ │ ├─ Update favourite outcomes            │
      │ │ ├─ Cache ROI                            │
      │ │ ├─ Analyze misses                       │
      │ │ ├─ Run learning                         │
      │ │ └─ Send P&L report                      │
      │ │ Duration: 3.7 min (target)              │
20:20 │ │ ⏱️ Poll results                          │
20:40 │ │ ⏱️ Poll results                          │
21:00 ├─┴─ RESULTS POLLING ENDS ───────────────────┘
      │
22:00 ├─────────────────────────────────────────────────────────────
      │ ███ LEARNING DEEP DIVE ███ (NEW)
      │ ├─ Analyze yesterday's patterns
      │ ├─ Calculate weight adjustments
      │ └─ Deploy improvements
      │ Duration: ~2 min
      │
23:00 ├─────────────────────────────────────────────────────────────
      │
      │  QUIET HOURS - No Racing
      │  (No results polling)
      │
00:00 ─────────────────────────────────────────────────────────────── Midnight
```

---

## Before vs After Comparison

### Before (Current Schedule)

```
08:30 │ ███ MORNING (3.8 min)
12:00 │ ███ REFRESH
13:30 │ ███ FEATURED LOCK ⚠️
14:00 │ ███ REFRESH           ← Too close to 13:30
16:00 │ ███ REFRESH
18:00 │ ███ REFRESH           ← Marginal value
20:00 │ ███ EVENING (6.5 min)

Results Polling: Every 30 min, 24/7  ← Wasteful overnight
```

### After (Optimized Schedule)

```
08:30 │ ███ MORNING (2.75 min)  ← 28% faster
12:00 │ ███ REFRESH
13:30 │ ███ FEATURED LOCK ⚠️    ← No change
14:30 │ ███ REFRESH             ← Better spacing
16:00 │ ███ REFRESH
17:30 │ ███ REFRESH             ← Better evening coverage
20:00 │ ███ EVENING (3.7 min)   ← 43% faster
22:00 │ ███ LEARNING DEEP       ← New analysis window

Results Polling: Every 20 min, 13:00-21:00 only  ← Active hours only
```

---

## Fanout Parallel Execution (Phase 2+)

### Morning Pipeline (Parallel)

```
08:30:00 │ START
         │
08:30:05 │ Betfair Fetch ──────────────────────────┐
         │                                          │ 60s
08:31:05 │                                          ▼
         │                    ┌─ Analysis ──────────┐
         │                    │                     │ 90s
         │                    │                     │
         │                    ├─ Free Feeds ────────┤
         │                    │                     │ 60s
08:32:35 │                    └─────────────────────▼
         │                    ┌─ Validate ──────────┐
         │                    │                     │ 20s
         │                    ├─ Improver Boost ────┤
         │                    │                     │ 30s
         │                    ├─ Featured ──────────┤
         │                    │                     │ 45s
08:33:20 │                    └─────────────────────▼
         │ Notify ─────────────────────────────────┐
         │                                          │ 15s
08:33:35 │ COMPLETE (165 seconds = 2.75 min)       ▼
```

**Savings**: 65 seconds (28% faster)

### Evening Pipeline (Parallel)

```
20:00:00 │ START
         │
20:00:05 │                    ┌─ SL Results ────────┐
         │                    │                     │ 45s
         │                    ├─ Betfair Results ───┤
         │                    │                     │ 45s
20:00:50 │                    └─────────────────────▼
         │                    ┌─ Fav Results ───────┐
         │                    │                     │ 20s
         │                    ├─ Cache ROI ─────────┤
         │                    │                     │ 15s
         │                    ├─ Miss Analysis ─────┤
         │                    │                     │ 60s
20:01:50 │                    └─────────────────────▼
         │ Learning ───────────────────────────────┐
         │                                          │ 90s
20:03:20 │                                          ▼
         │ Loss Report ────────────────────────────┐
         │                                          │ 30s
20:03:50 │ COMPLETE (230 seconds = 3.8 min)        ▼
```

**Savings**: 75 seconds (24% faster)

---

## Key Changes Summary

### Removed ❌

- **14:00 Refresh**: Too close to 13:30 featured lock (redundant)
- **18:00 Refresh**: Most racing done by then (marginal value)
- **Overnight Polling**: No racing 21:00-13:00 UTC (wasteful)

### Added ✅

- **14:30 Refresh**: Better 1-hour spacing after featured lock
- **17:30 Refresh**: Better evening coverage (was 18:00)
- **22:00 Learning**: Dedicated deep analysis window
- **20-min Polling**: Faster results (was 30-min)
- **Active-Hours Only**: Polling 13:00-21:00 only

### Optimized ⚡

- **Morning Pipeline**: Parallel execution (28% faster)
- **Evening Pipeline**: Parallel execution (24% faster)
- **Refresh Pipeline**: Parallel execution (25% faster, Phase 3)

---

## Impact Summary

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Morning Duration | 3.8 min | 2.75 min | **-28%** |
| Evening Duration | 6.5 min | 4.9 min | **-25%** |
| Results Latency | 30 min avg | 20 min avg | **-33%** |
| First Pick Time | 08:35 UTC | 08:33 UTC | **-2 min** |

### Cost Reduction

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Daily Invocations | 85 | 73 | **-14%** |
| Overnight Invocations | 16 | 0 | **-100%** |
| Refresh Invocations | 5 | 5 | 0% (better timing) |
| Monthly Cost | ~$120 | ~$85 | **~$35/month** |

### Coverage Improvements

✅ **Better Refresh Timing**: 14:30 and 17:30 vs 14:00 and 18:00  
✅ **Faster Results**: 20-minute vs 30-minute polling  
✅ **Active Hours Only**: No wasteful overnight polling  
✅ **New Learning Window**: 22:00 UTC for deep analysis  

---

## Critical Timing Rules

### DO NOT CHANGE ⚠️

1. **13:30 UTC Featured Lock**: CRITICAL - This locks featured meeting picks
2. **08:30 UTC Morning**: Optimal for UK racing start times
3. **20:00 UTC Evening**: Optimal for daily wrap-up after racing ends

### Safe to Adjust 🟢

1. **Refresh times**: 12:00, 14:30, 16:00, 17:30 (can shift ±30 min)
2. **Results polling**: Frequency and hours (currently 20 min, 13:00-21:00)
3. **Learning window**: 22:00 (can move to 21:00-23:00)

---

## Deployment Phases

### Phase 1: Schedule Optimization (Week 1) ✅ Ready

**Changes**:
- Update EventBridge rules
- Remove 14:00, 18:00 refreshes
- Add 14:30, 17:30 refreshes
- Change polling to 20-min, active-hours only

**Risk**: Low  
**Rollback**: 5 minutes  

### Phase 2: Morning + Evening Fanout (Week 2)

**Changes**:
- Deploy parallel Step Functions
- Update orchestrator handlers
- Monitor execution times

**Risk**: Low-Medium  
**Rollback**: 2 minutes  

### Phase 3: Refresh Fanout (Week 3)

**Changes**:
- Deploy parallel refresh Step Function
- 3 parallel groups
- Maintain featured lock timing

**Risk**: Medium  
**Rollback**: 5 minutes  

---

## Success Criteria

### Phase 1 ✅
- [ ] All new schedules running
- [ ] Invocations reduced by 12/day
- [ ] Results arriving 33% faster
- [ ] No timing errors

### Phase 2 ✅
- [ ] Morning pipeline <2.75 min
- [ ] Evening pipeline <3.7 min
- [ ] No parallel execution errors
- [ ] DynamoDB writes successful

### Phase 3 ✅
- [ ] Refresh pipeline <1.9 min
- [ ] Featured lock still works
- [ ] No race conditions
- [ ] Cost reduction achieved

---

## Monitoring Dashboard URLs

**CloudWatch Dashboard**:
https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#dashboards:name=BetBudAI-Performance

**Step Functions Console**:
https://console.aws.amazon.com/states/home?region=eu-west-1#/statemachines

**Lambda Console**:
https://console.aws.amazon.com/lambda/home?region=eu-west-1#/functions

**EventBridge Rules**:
https://console.aws.amazon.com/events/home?region=eu-west-1#/rules

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-20  
**Status**: Ready for Phase 1 Deployment
