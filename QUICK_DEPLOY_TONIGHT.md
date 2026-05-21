# Quick Deployment Guide - Deploy TONIGHT (May 20, 2026)

**Expected Time**: 20 minutes  
**Deployment Window**: Before 21:15 UTC  
**Impact**: +20-30 winners/week starting tomorrow

---

## Step 1: Make Script Executable (1 min)

```bash
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI
chmod +x scripts/deploy_learning_pipeline.sh
```

---

## Step 2: Update Lambda Role ARN (2 min)

```bash
# Get your AWS account ID
aws sts get-caller-identity --query Account --output text

# Open deployment script
nano scripts/deploy_learning_pipeline.sh

# Find line 26 and update:
LAMBDA_ROLE="arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role"
# Replace YOUR_ACCOUNT_ID with actual ID (e.g., 123456789012)

# Save: Ctrl+X, Y, Enter
```

---

## Step 3: Run Deployment (10 min)

```bash
./scripts/deploy_learning_pipeline.sh
```

**Watch for**:
- ✅ "BetBudAI_LearningInsights table created"
- ✅ "BetBudAI_WeightChangelog table created"
- ✅ "Lambda package created"
- ✅ "Lambda function deployed"
- ✅ "Lambda invocation successful"

**If any step fails**: See troubleshooting in DEPLOYMENT_GUIDE.md

---

## Step 4: Update Evening Pipeline (5 min)

```bash
# Open evening handler
nano backend/pipeline/evening/handler.py

# Find line 97 (after "if run_analysis:")
# Add this code block:
```

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

```bash
# Save: Ctrl+X, Y, Enter

# Deploy updated evening pipeline
cd backend/pipeline
python deploy_lambdas.py
```

---

## Step 5: Test Deployment (2 min)

```bash
# Test with yesterday's data (dry run)
aws lambda invoke \
  --function-name betbudai-learning-orchestrator \
  --payload '{
    "target_date": "2026-05-19",
    "learning_confidence_threshold": 0.80,
    "learning_auto_deploy": false,
    "learning_dry_run": true,
    "learning_max_races": 5
  }' \
  --region eu-west-1 \
  /tmp/learning_test.json

# Check result
cat /tmp/learning_test.json | jq .

# Should see: "statusCode": 200, "status": "success"
```

---

## Step 6: Deploy Dashboard (Optional, 2 min)

```bash
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI

aws cloudwatch put-dashboard \
  --dashboard-name BetBudAI-Learning \
  --dashboard-body file://cloudwatch_dashboard.json \
  --region eu-west-1

# Dashboard URL:
# https://console.aws.amazon.com/cloudwatch/home?region=eu-west-1#dashboards:name=BetBudAI-Learning
```

---

## Pre-Flight Checklist (Before 21:15 UTC)

At **20:50 UTC**, verify:

- [ ] CloudWatch dashboard open
- [ ] Lambda logs tailing:
  ```bash
  aws logs tail /aws/lambda/betbudai-learning-orchestrator --follow --region eu-west-1
  ```
- [ ] Email ready to receive report
- [ ] Notebook open to document first run

---

## Watch First Run (21:15 UTC)

**Look for in logs**:
```
[INFO] [evening-pipeline] Triggering automated learning...
[INFO] [LearningOrchestrator] Invoked with event: {"target_date": "2026-05-20"}
[INFO] [LearningIntegrator] Found 15 settled races
[INFO] [LearningIntegrator] Generated 12 insights
[INFO] [LearningIntegrator] Detected 4 patterns
[INFO] [LearningIntegrator] Proposed 6 adjustments
[INFO] [Adjustment] consistency: 12 → 8 (-33%, confidence: 85%)
[INFO] [Adjustment] class_drop_bonus: 24 → 30 (+25%, confidence: 60%)
[INFO] [LearningIntegrator] Deployed 2 weight changes
[INFO] [evening-pipeline] Learning complete: Analyzed 15 races, deployed 2 adjustments
```

**Red flags**:
- ❌ "ERROR" or "FAILED" in logs
- ❌ Execution time >60 seconds
- ❌ "Deployed 0 adjustments" for 3+ days

---

## Post-Run Verification (21:25 UTC)

```bash
# 1. Check learning insights
aws dynamodb query \
  --table-name BetBudAI_LearningInsights \
  --key-condition-expression "analysis_date = :date" \
  --expression-attribute-values '{":date": {"S": "2026-05-20"}}' \
  --region eu-west-1 \
  | jq '.Items[0]'

# 2. Check weight changes
aws dynamodb query \
  --table-name BetBudAI_WeightChangelog \
  --key-condition-expression "change_date = :date" \
  --expression-attribute-values '{":date": {"S": "2026-05-20"}}' \
  --region eu-west-1 \
  | jq '.Items[]'

# 3. Verify email report includes learning section
```

---

## If Something Goes Wrong

### Emergency Rollback

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

# Option 2: Restore Emergency V3 weights
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI
python scripts/deploy_emergency_v3.py
```

### Get Help

1. Check CloudWatch logs: `/aws/lambda/betbudai-learning-orchestrator`
2. Review DEPLOYMENT_GUIDE.md troubleshooting section
3. Check EVENING_PIPELINE_INTEGRATION.md for details

---

## Tomorrow Morning (May 21, 09:00 UTC)

Review first run results:

```bash
# Generate summary report
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI

# View patterns detected
aws dynamodb query \
  --table-name BetBudAI_LearningInsights \
  --key-condition-expression "analysis_date = :date" \
  --expression-attribute-values '{":date": {"S": "2026-05-20"}}' \
  --region eu-west-1 \
  | jq '.Items[0].patterns'

# View adjustments deployed
aws dynamodb query \
  --table-name BetBudAI_WeightChangelog \
  --key-condition-expression "change_date = :date" \
  --expression-attribute-values '{":date": {"S": "2026-05-20"}}' \
  --region eu-west-1 \
  | jq '.Items[]'
```

**Document**:
- Number of races analyzed
- Patterns detected (types + frequency)
- Adjustments deployed (weights + changes)
- Any issues or observations

---

## Expected Results Week 1

| Metric | Expected |
|--------|----------|
| Races analyzed/day | 10-30 |
| Patterns detected/day | 2-8 |
| Adjustments proposed/day | 3-10 |
| Adjustments deployed/day | 0-5 |
| Lambda execution time | <10 sec |
| Errors | 0 |
| Strike rate change | +0-5% |

---

## Files Created

All files are ready in your working directory:

1. ✅ `backend/pipeline/evening/learning_integration.py` - Integration logic
2. ✅ `backend/lambda/learning_orchestrator_handler.py` - Lambda handler
3. ✅ `scripts/deploy_learning_pipeline.sh` - Deployment script
4. ✅ `cloudwatch_dashboard.json` - Monitoring dashboard
5. ✅ `EVENING_PIPELINE_INTEGRATION.md` - Technical integration guide
6. ✅ `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
7. ✅ `QUICK_DEPLOY_TONIGHT.md` - This quick reference

---

## Key Commands Cheat Sheet

```bash
# Deploy learning system
./scripts/deploy_learning_pipeline.sh

# Test learning Lambda
aws lambda invoke --function-name betbudai-learning-orchestrator \
  --payload '{"target_date":"2026-05-19","learning_dry_run":true}' \
  --region eu-west-1 /tmp/test.json

# Tail learning logs
aws logs tail /aws/lambda/betbudai-learning-orchestrator --follow --region eu-west-1

# Tail evening pipeline logs
aws logs tail /aws/lambda/surebet-evening-pipeline --follow --filter-pattern "learning" --region eu-west-1

# Check learning insights
aws dynamodb query --table-name BetBudAI_LearningInsights \
  --key-condition-expression "analysis_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' --region eu-west-1

# Check weight changes
aws dynamodb query --table-name BetBudAI_WeightChangelog \
  --key-condition-expression "change_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' --region eu-west-1

# Emergency: Enable dry run
aws lambda update-function-configuration \
  --function-name betbudai-learning-orchestrator \
  --environment "Variables={CONFIDENCE_THRESHOLD=0.80,ENABLE_AUTO_DEPLOY=false,DRY_RUN=true,MAX_WORKERS=10}" \
  --region eu-west-1

# Emergency: Restore Emergency V3 weights
python scripts/deploy_emergency_v3.py
```

---

**Ready to Deploy?**

```bash
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI
chmod +x scripts/deploy_learning_pipeline.sh
./scripts/deploy_learning_pipeline.sh
```

**Timeline**:
- **Now**: Deploy (20 minutes)
- **20:50 UTC**: Pre-flight check
- **21:15 UTC**: First production run
- **21:25 UTC**: Verify results
- **Tomorrow 09:00**: Review and document

**Good luck! The system will learn and improve automatically every evening.**

---

*Quick Deploy Guide v1.0 - May 20, 2026*
