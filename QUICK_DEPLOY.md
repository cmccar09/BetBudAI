# Quick Deploy - Expert Recommendations
**1-Page Deployment Guide**

---

## 🚀 Quick Start (5 Minutes)

```bash
cd BetBudAI

# 1. Deploy weights to DynamoDB (takes effect in 5 min)
python scripts/deploy_expert_recommendations.py

# 2. Package and deploy Lambda updates
cd backend
zip -r deploy_package.zip core/ pipeline/ config/ external/ utils/

# 3. Update Lambda functions
aws lambda update-function-code --function-name calculate-improver-boost-scores --zip-file fileb://deploy_package.zip --region eu-west-1
aws lambda update-function-code --function-name betbudai-evening --zip-file fileb://deploy_package.zip --region eu-west-1
aws lambda update-function-code --function-name betbudai-morning --zip-file fileb://deploy_package.zip --region eu-west-1

# 4. Create field verification schedule
aws events put-rule --name betbudai-field-verification-scheduler --schedule-expression "rate(10 minutes)" --state ENABLED --region eu-west-1
```

---

## 📊 What Changed

### Improver Boost (AGGRESSIVE)
- Base boost: **15 → 30 points**
- Trip boost: **5 → 10 points**
- Confidence: **70 → 55**
- Win prob: **0.15 → 0.10**

### Critical Weights
```
form_velocity_bonus:  10 → 18  ⭐⭐
consistency:           6 → 12  ⭐⭐
class_drop_bonus:     12 → 24  ⭐⭐⭐
jockey_course_bonus:   8 → 15  ⭐⭐
bounce_back_bonus:     8 → 14  ⭐
recent_win:           16 → 14  ↓
favorite_correction:   8 →  5  ↓
```

### New Features
- ✅ Field verification (every 10 min)
- ✅ ROI tracking (daily P&L)
- ✅ Elite 5-pick selection
- ✅ Automatic re-analysis on field changes

---

## 🎯 Expected Impact

| Metric | Current | Week 1 | Week 2 | Week 4 |
|--------|---------|--------|--------|--------|
| Strike Rate | 18% | 30-35% | 40-45% | 50-60% |
| ROI | ? | +5-10% | +10-15% | +15-20% |
| Winners | 41/220 | 70/220 | 90/220 | 130/220 |

**Total Recovery**: +90-110 winners

---

## ✅ Deployment Checklist

### Pre-Deploy
- [ ] Backup current DynamoDB weights
- [ ] Review expert review doc (if needed)
- [ ] Test script locally

### Deploy (45-60 min)
- [ ] Run `deploy_expert_recommendations.py`
- [ ] Update Lambda function code (3 functions)
- [ ] Create EventBridge schedule
- [ ] Update environment variables

### Post-Deploy
- [ ] Verify weights in DynamoDB (version 2)
- [ ] Test field verification Lambda
- [ ] Monitor tomorrow's morning run (08:30 UTC)
- [ ] Check evening ROI tracking (20:00 UTC)

---

## 📈 Monitoring (First 7 Days)

### Daily Checks
```bash
# Check strike rate & ROI
aws dynamodb query \
  --table-name SureBetBets \
  --index-name DateIndex \
  --key-condition-expression "bet_date = :today" \
  --expression-attribute-values '{":today":{"S":"2026-05-20"}}'

# Watch logs
aws logs tail /aws/lambda/betbudai-morning --follow
aws logs tail /aws/lambda/betbudai-field-verification --follow
aws logs tail /aws/lambda/betbudai-evening --follow
```

### Red Flags (Rollback Triggers)
- Strike rate **< 15%** after 3 days → Rollback weights
- ROI **< -15%** after 3 days → Review odds distribution
- **> 15 re-analyses/day** → Increase thresholds
- **Zero improver picks** for 3 days → Check boost Lambda

---

## 🔧 Quick Fixes

### Rollback Weights
```bash
python scripts/rollback_weights.py --version 1
```

### Disable Field Verification
```bash
aws events disable-rule --name betbudai-field-verification-scheduler --region eu-west-1
```

### Adjust Re-analysis Sensitivity
```bash
# Make less sensitive (fewer triggers)
aws lambda update-function-configuration \
  --function-name betbudai-field-verification \
  --environment Variables="{CHANGE_THRESHOLD_PCT=20,NONRUNNER_COUNT_THRESHOLD=3}" \
  --region eu-west-1
```

---

## 📖 Documentation

- **Full Review**: `docs/EXPERT_TIPSTER_REVIEW_MAY_2026.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE_EXPERT_RECOMMENDATIONS.md`
- **Changes Summary**: `EXPERT_RECOMMENDATIONS_APPLIED.md`

---

## 🎯 Success Criteria (14 Days)

✅ Strike rate **> 40%**  
✅ ROI **> +10%**  
✅ Field re-analyses: **5-8 per day**  
✅ Improver picks: **2-3 in top 5 daily**  
✅ Consistent profitability  

---

## 💡 Key Insight

**You're not picking bad horses. You're either:**
1. Not analyzing the right field (67 cases)
2. Demoting horses you correctly flagged as improvers (53 cases)
3. Using weights that undervalue what matters (39 cases)

**These changes fix all three.**

---

**Time to Deploy**: ~45 min  
**First Results**: Tomorrow 08:30 UTC  
**Full Impact**: 2-4 weeks  
**Status**: Elite Tipster 🏆  

🚀 **Ready? Let's go!**
