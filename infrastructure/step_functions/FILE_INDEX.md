# Step Functions Implementation - File Index

**Created:** May 14, 2026  
**Status:** ✅ All files created and ready for development

---

## 📋 Quick Navigation

### Step Function Definitions (AWS State Machines)
| File | Purpose | Deployed | Status |
|------|---------|----------|--------|
| `0_master_orchestration.json` | Orchestrates all 3 pipelines | No | Ready ✅ |
| `1_nonrunner_tracking_and_field_verification.json` | Real-time field tracking | No | Ready ✅ |
| `2_improver_scoring_boost.json` | Improver score boost logic | No | Ready ✅ |
| `3_model_miss_deep_analysis.json` | Deep analysis of 39 misses | No | Ready ✅ |

### Implementation Guides
| File | Content | Purpose |
|------|---------|---------|
| `IMPLEMENTATION_SUMMARY.md` | Overview & checklist | 📍 START HERE |
| `DEPLOYMENT_GUIDE.md` | Step-by-step deployment | Deploy & monitor |
| `LAMBDA_FUNCTIONS_SPECIFICATION.md` | 25 Lambda function specs | Development guide |

### Related Documents (Root)
| File | Content |
|------|---------|
| `RACE_REVIEW_2026-05-01-to-2026-05-14.md` | 2-week analysis that led to these recommendations |

---

## 🚀 Getting Started

### Step 1: Understand the Scope (30 minutes)
1. Read `IMPLEMENTATION_SUMMARY.md` (this folder)
2. Review `RACE_REVIEW_2026-05-01-to-2026-05-14.md` (root folder)
3. Understand why these 3 steps were prioritized

### Step 2: Plan Development (1 hour)
1. Read `DEPLOYMENT_GUIDE.md` (prerequisites section)
2. Read `LAMBDA_FUNCTIONS_SPECIFICATION.md` (overview)
3. Create development plan for 25 Lambda functions

### Step 3: Prepare Infrastructure (2-4 hours)
1. Create 3 DynamoDB tables (see DEPLOYMENT_GUIDE)
2. Verify S3 bucket exists
3. Verify IAM roles configured
4. Create dev/staging environments

### Step 4: Develop Lambda Functions (3-4 weeks)
1. Follow specs in `LAMBDA_FUNCTIONS_SPECIFICATION.md`
2. Organize by domain (6 + 10 + 9 functions)
3. Test incrementally
4. Deploy to dev → staging → prod

### Step 5: Deploy Step Functions (1 week)
1. Create state machines in AWS
2. Test each in isolation
3. Test orchestration flow
4. Deploy to production

### Step 6: Monitor & Iterate (ongoing)
1. Track hit rate improvement
2. Review model analysis output
3. Implement recommendations
4. Measure ROI

---

## 📊 What Each Step Function Does

### Step 1: Nonrunner Tracking (Duration: ~20-120 minutes)
**Entry Point:** `1_nonrunner_tracking_and_field_verification.json`

```
Continuous Loop (T-120 to race time):
├─ Every 30 mins: Fetch BetFair current field
├─ Compare to our model field
├─ If 15%+ change or 2+ nonrunners:
│  ├─ Store nonrunner record
│  ├─ Re-analyze race with new field
│  └─ Update picks
└─ Continue monitoring

At T-5: Final field verification
```

**Impact:** Fix ~40 winners we missed because they weren't in our original field

---

### Step 2: Improver Scoring Boost (Duration: ~15 minutes)
**Entry Point:** `2_improver_scoring_boost.json`

```
Sequence:
├─ Load all horse scores
├─ Identify improver-flagged horses
├─ Boost improver scores by +15 points
├─ Re-rank all horses
├─ Extract top 3 improver picks
├─ Validate they meet quality thresholds
├─ PROMOTE them to OFFICIAL picks (not learning)
└─ Store metrics for tracking effectiveness

Key Change: Making improver picks official instead of watchlist
```

**Impact:** Fix ~40 winners we identified as improvers but didn't pick

---

### Step 3: Model Miss Analysis (Duration: ~25 minutes)
**Entry Point:** `3_model_miss_deep_analysis.json`

```
Parallel Analysis (5 concurrent):
├─ Load 39 model miss races
├─ Analyze each race for patterns
│  ├─ What beat our top pick?
│  ├─ What characteristics did winner have?
│  └─ What factors did we miss?
├─ Aggregate findings
├─ Calculate field strength impact
├─ Calculate pace dynamics impact
├─ Identify 10 missing scoring factors
├─ Validate factors on test set
├─ Compile recommendations
└─ Publish report to S3
```

**Impact:** Find systematic model weaknesses, fix ~15 misses with better scoring

---

## 💰 Expected Financial Impact

**Current:** 41 wins/220 races = 18.64% hit rate  
**Target:** 130-150 wins/220 races = 59-68% hit rate  
**Improvement:** +90-110 wins/week  
**Value:** £2,250-2,750/week (at £25/win average)  
**Annual Impact:** £117,000-143,000 from hit rate improvement alone

(Not including EV improvement, odds improvement, or long-term compounding)

---

## 🔧 Key Configuration Values

Can be adjusted without code changes:

### Nonrunner Tracking
- **Check interval:** 30 min (lower = more frequent checks)
- **Field change threshold:** 15% (lower = more sensitive)
- **Nonrunner count threshold:** 2 (lower = triggers on 1 nonrunner)

### Improver Boost
- **Base boost:** +15 points (increase for more aggressive promotion)
- **Trip bonus:** +5 points (increase if trip is important)
- **Min confidence:** 70 (lower = more picks promoted)
- **Min win prob:** 15% (lower = more picks promoted)

### Model Analysis
- **Correlation threshold:** 0.15 (higher = more selective)
- **Top factors:** 10 (increase to explore more)
- **Min impact:** 5 races (lower = include minor factors)

---

## 🎯 Success Criteria (Week 1)

✅ All state machines deployed  
✅ All Lambda functions operational  
✅ Zero errors in first 100 races  
✅ Nonrunner tracking capturing all field changes  
✅ Improver picks being promoted to official  
✅ Model analysis report generated with recommendations  

---

## ⚠️ Known Limitations

1. **Nonrunner tracking** relies on real-time BetFair API - may have latency
2. **Improver boost** depends on improver flag already working - if flag is wrong, boost won't help
3. **Model analysis** is retrospective - identifies past problems, not future predictions
4. All three require reliable DynamoDB and S3 access

---

## 📞 Support

**Questions about content?**
→ See specific documentation file

**Questions about deployment?**
→ See DEPLOYMENT_GUIDE.md

**Questions about Lambda specs?**
→ See LAMBDA_FUNCTIONS_SPECIFICATION.md

**Need the original analysis?**
→ See RACE_REVIEW_2026-05-01-to-2026-05-14.md (root folder)

---

## 📝 File Manifest

```
infrastructure/step_functions/
├── 0_master_orchestration.json                      (350 lines)
├── 1_nonrunner_tracking_and_field_verification.json (200 lines)
├── 2_improver_scoring_boost.json                    (180 lines)
├── 3_model_miss_deep_analysis.json                  (250 lines)
├── DEPLOYMENT_GUIDE.md                             (400 lines)
├── LAMBDA_FUNCTIONS_SPECIFICATION.md               (600 lines)
├── IMPLEMENTATION_SUMMARY.md                       (300 lines)
├── FILE_INDEX.md                                   (this file)
└── README.md                                       (when created)

Total: 8 files, ~2,280 lines of documentation + JSON definitions
```

---

**Last Updated:** May 14, 2026 18:45 UTC  
**Next Review:** May 15, 2026 (post-deployment)  
**Archive Location:** `/infrastructure/step_functions/` 
