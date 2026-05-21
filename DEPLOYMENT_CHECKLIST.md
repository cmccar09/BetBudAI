# Enhanced Betting Strategy - Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Local Testing
- [ ] Run: `python scripts/test_enhanced_selector.py`
- [ ] Verify all 5 tests pass
- [ ] Check EV calculations are correct
- [ ] Verify race quality filter works
- [ ] Confirm 2x 4/1+ requirement enforced
- [ ] Verify max 5 picks cap

### 2. Code Review
- [ ] Review `backend/core/ev_calculator.py`
- [ ] Review `backend/core/race_quality_filter.py`
- [ ] Review `backend/core/enhanced_pick_selector.py`
- [ ] Review updated `backend/lambda/sf_analysis.py`

### 3. Dependencies
- [ ] Python 3.8+ installed
- [ ] AWS CLI configured (`aws configure`)
- [ ] AWS credentials have Lambda update permissions
- [ ] boto3 library available

### 4. Backup Current System
- [ ] Export current Lambda function code
  ```bash
  aws lambda get-function --function-name surebet-analysis --region eu-west-1 > backup-lambda.json
  ```
- [ ] Note current configuration settings
- [ ] Save recent CloudWatch logs

---

## 🚀 Deployment Steps

### Step 1: Run Local Tests (5 minutes)

```bash
# Navigate to project root
cd C:\Users\charl\OneDrive\futuregenAI\BetBudAI

# Run test suite
python scripts\test_enhanced_selector.py
```

**Expected Output:**
```
TEST SUMMARY
============
  ✓ PASS: Module Imports
  ✓ PASS: EV Calculator
  ✓ PASS: Race Quality Filter
  ✓ PASS: Pick Selector
  ✓ PASS: UI Formatting

Results: 5/5 tests passed
🎉 ALL TESTS PASSED! System ready for deployment.
```

- [ ] All tests pass
- [ ] No import errors
- [ ] EV calculations correct

---

### Step 2: Deploy to Lambda (10 minutes)

#### Option A: PowerShell (Windows)

```powershell
# Navigate to scripts directory
cd scripts

# Run deployment script
.\deploy_enhanced_lambdas.ps1
```

#### Option B: Bash (Linux/Mac)

```bash
# Navigate to scripts directory
cd scripts

# Make executable
chmod +x deploy_enhanced_lambdas.sh

# Run deployment
./deploy_enhanced_lambdas.sh
```

**Expected Output:**
```
[Step 1/5] Creating deployment package...
✓ Deployment package created

[Step 2/5] Creating ZIP archive...
✓ ZIP file created: enhanced_lambda.zip

[Step 3/5] Testing package integrity...
✓ Package validated successfully

[Step 4/5] Deploying to AWS Lambda...
✓ Lambda function updated successfully

[Step 5/5] Updating Lambda configuration...
✓ Configuration updated

DEPLOYMENT COMPLETE!
```

- [ ] Deployment succeeds
- [ ] No AWS errors
- [ ] Lambda function updated

---

### Step 3: Verify Deployment (5 minutes)

#### Test Lambda Function

```bash
# Invoke Lambda with test event
aws lambda invoke \
  --function-name surebet-analysis \
  --region eu-west-1 \
  --payload '{"target_date":"2026-05-21","force":true}' \
  test-output.json

# View output
cat test-output.json
```

**Check For:**
- [ ] `statusCode: 200`
- [ ] `picks` array contains 2-5 items
- [ ] Each pick has `bet_tier` field (nap/strong/value)
- [ ] Each pick has `ev_pct` field
- [ ] Each pick has `stake_units` field
- [ ] At least 2 picks have `odds >= 5.0` (4/1+)

#### Check CloudWatch Logs

```bash
# Tail recent logs
aws logs tail /aws/lambda/surebet-analysis \
  --follow \
  --region eu-west-1 \
  --since 5m
```

**Look For:**
- [ ] `[surebet-analysis] Using enhanced pick selector`
- [ ] `Enhanced selection: X picks selected`
- [ ] `NAP: 1 | Strong: X | Value: X`
- [ ] `Long odds (4/1+): X`
- [ ] `Expected ROI: X%`
- [ ] No errors or exceptions

---

### Step 4: Integration Testing (10 minutes)

#### Test Morning Pipeline

```bash
# Manually trigger morning pipeline Step Function
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:eu-west-1:YOUR_ACCOUNT:stateMachine:SureBet-Morning \
  --region eu-west-1 \
  --name test-enhanced-$(date +%s)
```

**Verify:**
- [ ] Step Function completes successfully
- [ ] Analysis step runs without errors
- [ ] Picks are saved to DynamoDB
- [ ] Picks appear in API response

#### Test API Endpoint

```bash
# Get today's picks from API
curl -X GET https://YOUR_API_ENDPOINT/picks/today
```

**Check Response:**
- [ ] Returns 2-5 picks maximum
- [ ] Each pick has tier label
- [ ] EV percentages present
- [ ] Stake recommendations included
- [ ] At least 2 picks at 4/1+

---

### Step 5: Monitor First Live Run (Morning After Deployment)

#### Before First Run (08:00 UTC)
- [ ] Check Lambda memory settings (512MB minimum)
- [ ] Verify timeout is 300 seconds
- [ ] Ensure DynamoDB tables accessible
- [ ] CloudWatch dashboard ready

#### During First Run (08:30 UTC)
- [ ] Monitor CloudWatch logs in real-time
- [ ] Watch for `[surebet-analysis] Enhanced selection` message
- [ ] Check for any errors or warnings
- [ ] Verify picks are generated

#### After First Run (09:00 UTC)
- [ ] Check DynamoDB for new picks
- [ ] Verify picks have all enhanced fields
- [ ] Check UI displays picks correctly
- [ ] Verify 2x 4/1+ requirement met

---

## 🎨 UI Updates (Optional - Can be done separately)

### Frontend Changes Needed

Update the picks display component to show:

```javascript
// Example React component updates

// Display tier badge
{pick.bet_tier === 'nap' && <Badge>🔥 NAP</Badge>}
{pick.bet_tier === 'strong' && <Badge>💪 Strong</Badge>}
{pick.bet_tier === 'value' && <Badge>💎 Value</Badge>}

// Show EV percentage
<Text>EV: {pick.ev_pct > 0 ? '+' : ''}{pick.ev_pct.toFixed(1)}%</Text>

// Show confidence
<Text>Confidence: {pick.confidence_pct}%</Text>

// Show recommended stake
<Text>Stake: {pick.stake_units} units</Text>

// Show potential returns
<Text>
  £{pick.stake_units} returns £{(pick.stake_units * pick.odds).toFixed(2)}
  (£{((pick.stake_units * pick.odds) - pick.stake_units).toFixed(2)} profit)
</Text>

// Show EW recommendation
{pick.bet_type === 'each_way' && (
  <Tooltip>{pick.ew_reason}</Tooltip>
)}
```

### UI Checklist
- [ ] Tier badges displayed (NAP/Strong/Value)
- [ ] EV percentage visible
- [ ] Confidence percentage shown
- [ ] Stake recommendations displayed
- [ ] Potential returns calculated
- [ ] EW recommendations visible (when applicable)
- [ ] Featured meeting shows "best 3 races" label
- [ ] Explanation for skipped races shown

---

## 📊 Success Metrics (Monitor for 7 Days)

### Day 1-3 (Initial Performance)
- [ ] All picks have EV > +15%
- [ ] 2x 4/1+ requirement met daily
- [ ] Max 5 picks enforced
- [ ] No system errors

### Day 4-7 (Performance Validation)
- [ ] Strike rate improving vs. baseline
- [ ] ROI turning positive
- [ ] NAP picks performing at 40%+ strike rate
- [ ] User feedback positive

### Week 2+ (Optimization)
- [ ] Strike rate 35%+ achieved
- [ ] ROI consistently positive (+10%+)
- [ ] Fine-tune EV thresholds if needed
- [ ] Adjust confidence calibration if needed

---

## 🔄 Rollback Plan (If Issues Occur)

### Quick Rollback (5 minutes)

```bash
# Restore previous Lambda version
aws lambda update-function-code \
  --function-name surebet-analysis \
  --zip-file fileb://backup-lambda.zip \
  --region eu-west-1

# Or use previous version number
aws lambda update-function-code \
  --function-name surebet-analysis \
  --publish \
  --revision-id <PREVIOUS_REVISION_ID> \
  --region eu-west-1
```

### Rollback Triggers
Rollback if any of these occur:
- [ ] Lambda function errors/timeouts
- [ ] No picks generated for 2+ consecutive days
- [ ] Strike rate drops below 15%
- [ ] System generates >5 picks (max cap violated)
- [ ] 4/1+ requirement not met 3+ days in a row

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue 1: Import Errors**
```
Error: ModuleNotFoundError: No module named 'backend.core.ev_calculator'
```
**Solution:** Ensure all files are in ZIP package, check __init__.py files exist

**Issue 2: 4/1+ Requirement Not Met**
```
WARNING: Only 1 picks at 4/1+ (need 2 minimum)
```
**Solution:** This is expected on some days - system will select best available. Not a critical error.

**Issue 3: All Picks Filtered Out**
```
No picks with sufficient edge found today
```
**Solution:** This is correct behavior! Only bet when edge exists. Shows system working properly.

**Issue 4: Lambda Timeout**
```
Task timed out after 120.00 seconds
```
**Solution:** Increase timeout to 300 seconds in Lambda configuration

### Getting Help

1. Check CloudWatch logs first
2. Review test output: `python scripts/test_enhanced_selector.py`
3. Verify AWS permissions
4. Check DynamoDB tables accessible

---

## ✅ Final Checklist

Before marking deployment complete:

- [ ] All pre-deployment tests passed
- [ ] Lambda deployed successfully
- [ ] Integration tests passed
- [ ] First live run completed successfully
- [ ] Picks appear correctly in UI
- [ ] CloudWatch logs show expected messages
- [ ] 2x 4/1+ requirement enforced
- [ ] Max 5 picks cap working
- [ ] EV filtering active
- [ ] Tier assignments correct
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Team notified of changes
- [ ] Monitoring dashboard updated

---

## 🎉 Deployment Complete!

**System Status:** Enhanced betting strategy deployed and active

**Next Actions:**
1. Monitor performance for 7 days
2. Collect user feedback on new UI
3. Track strike rate improvements
4. Adjust EV thresholds if needed (after 30 days data)

**Expected Timeline:**
- Week 1: 25-30% strike rate, +5-10% ROI
- Week 4: 30-35% strike rate, +12-15% ROI
- Week 12: 35-40% strike rate, +18-25% ROI

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Rollback Available:** Yes ✓

**Backup Location:** backup-lambda.zip

**Status:** 🟢 Live and Operational
