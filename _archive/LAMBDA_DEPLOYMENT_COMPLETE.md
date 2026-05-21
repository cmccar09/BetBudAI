# AWS Lambda Deployment Complete ✅

**Deployment Date**: January 3, 2026  
**Status**: Fully automated betting workflow running in AWS cloud

## What Was Deployed

### Lambda Function: `BettingWorkflowScheduled`
- **Region**: us-east-1
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 15 minutes (900 seconds)
- **Role**: BettingWorkflowLambdaRole

### Capabilities
✅ Fetches live Betfair odds (UK & IRE horse racing)  
✅ Calls Claude Sonnet 4 via AWS Bedrock  
✅ Generates top 5 betting picks every 2 hours  
✅ Stores picks in DynamoDB (`SureBetBets` table)  
✅ Frontend automatically displays picks  
✅ **Runs 24/7 - laptop can be OFF** 🎉

## Automated Schedule

The workflow runs automatically at these times (UTC):

| Time (UTC) | Time (GMT/IST) | Purpose |
|------------|----------------|---------|
| 10:00 | 10:00 AM | Generate picks |
| 12:00 | 12:00 PM | Generate picks |
| 14:00 | 2:00 PM | Generate picks |
| 16:00 | 4:00 PM | Generate picks |
| 18:00 | 6:00 PM | Generate picks |
| 20:00 | 8:00 PM | Generate picks |
| 22:00 | 10:00 PM | Generate picks + fetch results |

### EventBridge Rules
All 7 scheduled triggers are **ENABLED** and active:
- `BettingWorkflow10AM`
- `BettingWorkflow12PM`
- `BettingWorkflow2PM`
- `BettingWorkflow4PM`
- `BettingWorkflow6PM`
- `BettingWorkflow8PM`
- `BettingWorkflow10PM`

## How It Works

```
Every 2 Hours (Automated):
├─ EventBridge triggers Lambda function
├─ Lambda fetches live Betfair odds
├─ Calls Claude via AWS Bedrock
├─ Generates 5 best betting picks
└─ Stores in DynamoDB

Frontend (Continuous):
├─ Amplify hosts React app
├─ Reads picks from DynamoDB
└─ Displays mobile-friendly betting picks
```

## Benefits vs Local Setup

### Before (Windows Task Scheduler)
❌ Laptop must be powered on  
❌ Depends on local Python environment  
❌ Can fail if laptop sleeps  
❌ Limited to when you're home  

### After (AWS Lambda)
✅ Runs 24/7 in AWS cloud  
✅ Works even when laptop is OFF  
✅ No maintenance required  
✅ Highly reliable infrastructure  
✅ Scales automatically  
✅ CloudWatch logging & monitoring  

## Monitoring

### View Logs
```powershell
# View recent logs
aws logs tail /aws/lambda/BettingWorkflowScheduled --follow --region us-east-1

# View specific time range
aws logs tail /aws/lambda/BettingWorkflowScheduled --since 1h --region us-east-1
```

### Check DynamoDB Picks
```powershell
# Today's picks
aws dynamodb scan --table-name SureBetBets --filter-expression "begins_with(#d, :today)" --expression-attribute-names "{`"#d`":`"date`"}" --expression-attribute-values "{`":today`":{`"S`":`"2026-01-03`"}}" --region us-east-1

# All picks
aws dynamodb scan --table-name SureBetBets --region us-east-1 --max-items 10
```

### Manually Trigger
```powershell
# Test run
aws lambda invoke --function-name BettingWorkflowScheduled --region us-east-1 output.json

# View response
Get-Content output.json | ConvertFrom-Json
```

## Configuration

### Environment Variables (Set)
- `BETFAIR_USERNAME` = ✅ Configured
- `BETFAIR_PASSWORD` = ✅ Configured
- `BETFAIR_APP_KEY` = ✅ Configured
- `SUREBET_DDB_TABLE` = SureBetBets
- `ENABLE_AUTO_BETTING` = false (dry-run mode)

### IAM Permissions
The Lambda function has access to:
- ✅ CloudWatch Logs (logging)
- ✅ DynamoDB Full Access (store picks)
- ✅ Bedrock Full Access (Claude AI)

## Cost Estimate

### Lambda
- **Executions**: 7 per day × 30 days = 210/month
- **Duration**: ~13 seconds average
- **Memory**: 512 MB
- **Cost**: ~$0.01/month (within free tier)

### Bedrock (Claude)
- **Calls**: 7 per day × 30 days = 210/month
- **Tokens**: ~4,000 per call
- **Cost**: ~$2-5/month

### DynamoDB
- **On-demand pricing**
- **Items**: ~150 picks/month
- **Cost**: ~$0.10/month (within free tier)

### EventBridge
- **Rules**: 7 rules
- **Invocations**: 210/month
- **Cost**: Free (within free tier)

**Total Estimated Monthly Cost**: $2-5 (mostly Bedrock)

## Next Steps

### Current State
✅ Lambda deployed and tested  
✅ Schedule configured and active  
✅ DynamoDB storing picks  
✅ Frontend displaying picks  
✅ Works with laptop OFF  

### Optional Enhancements

1. **Add Email Notifications**
   - Configure SNS to email when picks are generated
   - Alert on errors

2. **Enable Auto-Betting** (when ready)
   - Set `ENABLE_AUTO_BETTING=true`
   - Requires Paddy Power/Betfair betting modules

3. **Add Results Tracking**
   - Extend Lambda to fetch race results
   - Update DynamoDB with outcomes
   - Track performance metrics

4. **Dashboard & Analytics**
   - CloudWatch dashboard for monitoring
   - Track pick accuracy over time
   - ROI analysis

## Troubleshooting

### Lambda Not Running
```powershell
# Check EventBridge rules
aws events list-rules --name-prefix "BettingWorkflow" --region us-east-1

# Check Lambda logs
aws logs tail /aws/lambda/BettingWorkflowScheduled --since 1h --region us-east-1
```

### No Picks in DynamoDB
```powershell
# Manual test
aws lambda invoke --function-name BettingWorkflowScheduled --region us-east-1 test-output.json

# Check logs
aws logs tail /aws/lambda/BettingWorkflowScheduled --follow --region us-east-1
```

### Betfair Credentials Issue
```powershell
# Update credentials
aws lambda update-function-configuration --function-name BettingWorkflowScheduled --environment "Variables={BETFAIR_USERNAME=your_username,BETFAIR_PASSWORD=your_password,BETFAIR_APP_KEY=your_key,SUREBET_DDB_TABLE=SureBetBets,ENABLE_AUTO_BETTING=false}" --region us-east-1
```

## Files Created

- ✅ `deploy_workflow_lambda.ps1` - Deployment script
- ✅ `lambda_workflow_handler.py` - Lambda function code
- ✅ `lambda-workflow-package/` - Deployment package
- ✅ `betting-workflow.zip` - Lambda ZIP (22.53 MB)

## Summary

**Your betting system is now fully cloud-based!** 🎉

- Lambda runs automatically every 2 hours
- No need to keep laptop on
- Picks appear on frontend automatically
- Monitor via CloudWatch Logs
- Reliable 24/7 operation

The local `scheduled_workflow.ps1` is now **optional** - you can keep it as a backup or remove the Windows Task Scheduler tasks if you prefer running entirely in the cloud.

---

**Questions or Issues?**

Check CloudWatch Logs:
```powershell
aws logs tail /aws/lambda/BettingWorkflowScheduled --follow --region us-east-1
```

Manually trigger to test:
```powershell
aws lambda invoke --function-name BettingWorkflowScheduled --region us-east-1 output.json
```
