# Quick Start: Deploy Cloud Automation in 30 Minutes

## Step 1: Store Betfair Credentials in AWS Secrets Manager (5 mins)

```bash
# Create secret with Betfair credentials
aws secretsmanager create-secret \
  --name BetfairCredentials \
  --description "Betfair API credentials for automated betting" \
  --secret-string '{
    "username": "cmccar02",
    "password": "YOUR_PASSWORD",
    "app_key": "YOUR_APP_KEY",
    "cert_content": "CERT_BASE64_ENCODED",
    "key_content": "KEY_BASE64_ENCODED"
  }' \
  --region eu-west-1
```

## Step 2: Create IAM Role for Lambda (3 mins)

```bash
# Create trust policy
cat > lambda-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name BettingLambdaRole \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name BettingLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name BettingLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
  --role-name BettingLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
```

## Step 3: Deploy Results Fetcher Lambda (10 mins)

```bash
# Package dependencies
cd C:\Users\charl\OneDrive\futuregenAI\Betting
pip install --target ./package requests boto3
cd package
zip -r ../results_lambda.zip .
cd ..
zip -g results_lambda.zip lambda_results_fetcher.py

# Create Lambda function
aws lambda create-function \
  --function-name BettingResultsFetcher \
  --runtime python3.11 \
  --role arn:aws:iam::813281204422:role/BettingLambdaRole \
  --handler lambda_results_fetcher.lambda_handler \
  --zip-file fileb://results_lambda.zip \
  --timeout 60 \
  --memory-size 256 \
  --region eu-west-1 \
  --environment "Variables={DYNAMODB_TABLE=SureBetBets}"

# Test the function
aws lambda invoke \
  --function-name BettingResultsFetcher \
  --region eu-west-1 \
  output.json

cat output.json
```

## Step 4: Create EventBridge Schedule (2 mins)

```bash
# Create EventBridge rule for hourly execution
aws events put-rule \
  --name BettingResultsHourly \
  --schedule-expression "cron(0 * * * ? *)" \
  --state ENABLED \
  --description "Fetch Betfair results every hour" \
  --region eu-west-1

# Add Lambda permission for EventBridge
aws lambda add-permission \
  --function-name BettingResultsFetcher \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:eu-west-1:813281204422:rule/BettingResultsHourly \
  --region eu-west-1

# Add Lambda as target
aws events put-targets \
  --rule BettingResultsHourly \
  --targets "Id"="1","Arn"="arn:aws:lambda:eu-west-1:813281204422:function:BettingResultsFetcher" \
  --region eu-west-1
```

## Step 5: Verify & Monitor (5 mins)

```bash
# Check CloudWatch logs
aws logs tail /aws/lambda/BettingResultsFetcher --follow --region eu-west-1

# Check next scheduled run
aws events describe-rule --name BettingResultsHourly --region eu-west-1

# Test manually
aws lambda invoke \
  --function-name BettingResultsFetcher \
  --region eu-west-1 \
  --log-type Tail \
  output.json

# Disable local scheduled task
Get-ScheduledTask -TaskName "SureBet-Hourly-ResultsFetcher" | Disable-ScheduledTask
```

## Step 6: Deploy Workflow Generator (Future - 2 hours)

This will move the pick generation to Lambda:

```bash
# Convert scheduled_workflow.ps1 to Python
# Package with dependencies:
#   - boto3 (AWS SDK)
#   - anthropic (Claude API)
#   - requests (Betfair API)

# Create Lambda with larger memory & timeout
aws lambda create-function \
  --function-name BettingWorkflowGenerator \
  --runtime python3.11 \
  --role arn:aws:iam::813281204422:role/BettingLambdaRole \
  --handler lambda_workflow.lambda_handler \
  --zip-file fileb://workflow_lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --region eu-west-1

# Schedule for every 30 mins during racing hours (10:00-20:00)
aws events put-rule \
  --name BettingWorkflow30Min \
  --schedule-expression "cron(0,30 10-19 * * ? *)" \
  --state ENABLED \
  --region eu-west-1
```

## Monitoring Dashboard

```bash
# View Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=BettingResultsFetcher \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region eu-west-1
```

## Cost Optimization

- Use on-demand Lambda (no reserved capacity needed)
- DynamoDB on-demand pricing for variable traffic
- CloudWatch log retention: 7 days (reduce from default 30)
- Use Lambda layers for shared dependencies

## Rollback Plan

If cloud automation fails:
1. Re-enable local scheduled task: `Enable-ScheduledTask -TaskName "SureBet-Hourly-ResultsFetcher"`
2. Delete EventBridge rule: `aws events delete-rule --name BettingResultsHourly`
3. Delete Lambda: `aws lambda delete-function --function-name BettingResultsFetcher`

## Success Criteria

✅ Lambda executes hourly without errors
✅ DynamoDB results update correctly
✅ CloudWatch logs show successful executions
✅ No need for laptop to be on
✅ Total cost < $2/month (excluding AI costs)
