# Today's Run Status - May 20, 2026
**Triggered**: 10:58:38 UTC  
**Status**: 🔄 RUNNING  
**Target Date**: 2026-05-20

---

## 🎯 Pipeline Progress

### ✅ Completed Steps
1. ✅ **Betfair Fetch** (10:58:43) - Odds data retrieved
2. 🔄 **Analysis** (Started 10:58:43) - Comprehensive scoring in progress

### ⏳ Pending Steps
3. ⏳ **Validation** - Quality gate checks
4. ⏳ **Featured Meeting** - Featured course analysis
5. ⏳ **Notifications** - Subscriber alerts
6. ⏳ **Optimizations**:
   - Improver boost calculation (+30 / +10)
   - Apply improver-boosted picks
   - Featured improver enforcer
   - Field comparison

---

## 📊 What's Different Today

### NEW Settings Active
- ✅ **Weights Version 2** (deployed 10:39 UTC)
  - Form velocity: 18 (was 10)
  - Class drop: 24 (was 12)
  - Consistency: 12 (was 6)
  - Jockey/course: 15 (was 8)

- ✅ **Improver Boost Aggressive** (deployed 10:41 UTC)
  - Base boost: 30 points (was 15)
  - Trip boost: 10 points (was 5)
  - Confidence: 55 (was 70)
  - Win probability: 0.10 (was 0.15)

### Expected in Logs
Look for these key indicators:
```
[calculate-improver-boost-scores] Apply improver boost (+30 / +10)
[apply-improver-boosted-picks] Enforce improver-boosted ranking
[featured-improver-enforcer] Apply improver boost to featured course
```

---

## ⏰ Estimated Completion Time

**Total Pipeline Duration**: 2-5 minutes  
**Started**: 10:58:38 UTC  
**Expected Completion**: 11:01-11:04 UTC

**Current Time**: Check with:
```bash
date -u
```

---

## 🔍 How to Monitor

### Check Logs
```bash
# Watch live logs
aws logs tail /aws/lambda/betbudai-morning --follow --region eu-west-1

# Check recent logs
aws logs tail /aws/lambda/betbudai-morning --since 10m --region eu-west-1
```

### Check DynamoDB for Results
```bash
# Query today's picks
aws dynamodb query \
  --table-name SureBetBets \
  --index-name DateIndex \
  --key-condition-expression "bet_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' \
  --region eu-west-1
```

### Check for Improver Picks
```bash
# Look for improver-boosted picks in top 5
aws dynamodb query \
  --table-name SureBetBets \
  --index-name DateIndex \
  --key-condition-expression "bet_date = :date" \
  --filter-expression "pick_type = :official AND attribute_exists(improver_boost_applied)" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"},":official":{"S":"official"}}' \
  --region eu-west-1
```

---

## 📈 What to Expect

### Today's Picks Should Show
1. **2-3 improver-flagged horses in top 5** (was 0-1 before)
2. **Higher scores for**:
   - Horses showing form improvement (velocity)
   - Class droppers (now +24 instead of +12)
   - Consistent performers (now +12 instead of +6)
3. **Lower scores for**:
   - Recent one-off winners without pattern (now +14 vs +16)
   - Market favorites without form (correction now +5 vs +8)

### Compared to Yesterday
- **More aggressive improver backing**
- **Better weighting of form patterns**
- **Less reliance on market position**

---

## ✅ Success Indicators

### Technical Success
- ✅ Pipeline completes without errors
- ✅ Log shows "(+30 / +10)" for improver boost
- ✅ Improver picks appear in top 5
- ✅ Weights version 2 used in scoring

### Performance Success (Week 1)
- 🎯 2-3 improver picks in daily top 5
- 🎯 Improved scoring for class droppers
- 🎯 Better form velocity weighting
- 🎯 Strike rate trending toward 30%+

---

## 🚨 If Pipeline Fails

### Check CloudWatch for Errors
```bash
aws logs filter-pattern "ERROR" \
  --log-group-name /aws/lambda/betbudai-morning \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --region eu-west-1
```

### Common Issues
1. **Betfair API timeout** - Retry pipeline
2. **DynamoDB rate limit** - Wait 1 minute, retry
3. **Lambda timeout** - Normal, runs async
4. **Improver boost error** - Check Lambda env vars

### Rollback if Needed
```bash
# Disable optimizations
aws lambda update-function-configuration \
  --function-name betbudai-morning \
  --environment Variables="{run_optimizations=false}" \
  --region eu-west-1
```

---

## 📊 Results Location

### Where Picks Are Stored
- **DynamoDB Table**: `SureBetBets`
- **Date Index**: `bet_date = 2026-05-20`
- **Pick Types**: 
  - `official` - Top 5 official picks
  - `learning` - Learning picks
  - `watchlist` - Watchlist picks

### Key Fields to Check
- `horse_name` - Horse name
- `score` - Final score (should show weight changes)
- `improver_boost_applied` - True if improver boosted
- `original_score` - Score before improver boost
- `total_boost_applied` - How many points added
- `odds` - Betting odds
- `confidence_score` - Confidence level

---

## 🎯 Next Steps

### After Pipeline Completes
1. **Review picks** - Check for improver horses in top 5
2. **Compare to yesterday** - Look for scoring differences
3. **Monitor results** - Track winners tonight (20:00 UTC)
4. **Check ROI** - Evening pipeline will calculate

### Tomorrow Morning
- Regular 08:30 UTC run with new settings
- Expect consistent 2-3 improvers in top 5
- Week 1 target: 30-35% strike rate

---

**Status Updated**: 11:00 UTC  
**Pipeline Running**: Check logs for completion  
**Expected**: First picks with elite tipster settings  

🏇💰🚀
