# Cloud Automation Plan - SureBet System

## Problem
Current system relies on local Windows scheduled tasks that only run when laptop is on.

## Solution: Fully Cloud-Based Architecture

### Phase 1: Move Results Fetching to AWS Lambda (EASY - 30 mins)

**Create Lambda Function: BettingResultsFetcher**
- Runtime: Python 3.11
- Trigger: EventBridge (every hour)
- Code: betfair_results_fetcher_v2.py
- Dependencies: boto3, requests
- Environment: Betfair credentials in Secrets Manager
- Permissions: DynamoDB read/write access

**Steps:**
1. Create Lambda function
2. Store Betfair cert/key in AWS Secrets Manager
3. Configure EventBridge rule: `cron(0 * * * ? *)` (hourly)
4. Test and verify results updating

### Phase 2: Move Workflow to AWS Lambda (MEDIUM - 2 hours)

**Create Lambda Function: BettingWorkflowGenerator**
- Runtime: Python 3.11
- Memory: 512MB (for AI analysis)
- Timeout: 5 minutes
- Trigger: EventBridge (every 30 mins during racing hours 10:00-20:00)
- Code: scheduled_workflow.ps1 → Python script
- Dependencies: boto3, anthropic (AWS Bedrock SDK)
- Environment: AWS Bedrock access for Claude

**Components to migrate:**
1. `betfair_login_local.py` → Use Secrets Manager
2. `betfair_odds_fetcher.py` → Already Python
3. AI analysis → Use AWS Bedrock (Claude 3.5 Sonnet)
4. `save_selections_to_dynamodb.py` → Already Python
5. Learning system → Python evaluation

**EventBridge Schedule:**
```
cron(30,0 10-19 * * ? *)  # Every 30 mins 10:00-20:00 UTC
```

### Phase 3: Daily Learning Automation (EASY - 1 hour)

**Create Lambda Function: BettingDailyLearning**
- Trigger: EventBridge daily at 22:00 UTC
- Code: evaluate_performance.py + learning insights
- Updates: prompt.txt in S3
- Outputs: Performance reports to S3

**EventBridge Schedule:**
```
cron(0 22 * * ? *)  # Daily at 22:00 UTC
```

### Phase 4: Email Reports (EASY - 30 mins)

**Update existing Lambda or create new:**
- Use AWS SES for email delivery
- Daily summary at 10:00 next day
- Yesterday's results + today's picks

## Architecture Diagram

```
┌─────────────────┐
│  EventBridge    │
│  (Schedulers)   │
└────────┬────────┘
         │
         ├──► 🕐 Every 30 mins ──► λ BettingWorkflowGenerator
         │                          ├─► Betfair API (odds)
         │                          ├─► AWS Bedrock (Claude AI)
         │                          └─► DynamoDB (save picks)
         │
         ├──► 🕐 Every hour ────► λ BettingResultsFetcher
         │                          ├─► Betfair API (results)
         │                          └─► DynamoDB (update outcomes)
         │
         ├──► 🕐 Daily 22:00 ───► λ BettingDailyLearning
         │                          ├─► DynamoDB (read results)
         │                          ├─► S3 (update prompt.txt)
         │                          └─► Generate insights
         │
         └──► 🕐 Daily 10:00 ───► λ BettingEmailReport
                                    ├─► DynamoDB (read data)
                                    └─► SES (send email)

         ┌──────────────┐
         │   DynamoDB   │◄────── All Lambdas
         │ SureBetBets  │
         └──────────────┘

         ┌──────────────┐
         │      S3      │◄────── Learning system
         │  bet-config/ │        (prompt.txt, reports)
         └──────────────┘
```

## Cost Estimate (Monthly)

- **Lambda Executions:**
  - Workflow: 30 runs/day × 30 days = 900 runs × $0.0000002 = $0.18
  - Results: 24 runs/day × 30 days = 720 runs × $0.0000002 = $0.14
  - Learning: 30 runs × $0.0000002 = $0.006
  - **Total Lambda:** ~$0.33/month

- **AWS Bedrock (Claude):**
  - ~10 AI calls/run × 30 runs/day × 30 days = 9,000 calls
  - Avg 5K tokens input, 2K output per call
  - Claude 3.5 Sonnet: $3/M input, $15/M output
  - **Total Bedrock:** ~$27/month

- **DynamoDB:**
  - Current usage: ~500 reads/writes per day
  - **Total DynamoDB:** $1-2/month (on-demand)

- **S3 + Secrets Manager + EventBridge:** < $1/month

**TOTAL COST: ~$30/month** (mostly AI costs)

## Benefits

✅ **No laptop needed** - Runs 24/7 in cloud
✅ **More reliable** - AWS uptime vs laptop being on
✅ **Faster execution** - Lambda cold start < 3 seconds
✅ **Scalable** - Can handle more frequent updates
✅ **Monitoring** - CloudWatch logs & alerts
✅ **Disaster recovery** - All code in git, infrastructure as code

## Migration Steps (Priority Order)

### Step 1: Results Fetcher (TODAY - 30 mins)
```bash
# Create Lambda
aws lambda create-function \
  --function-name BettingResultsFetcher \
  --runtime python3.11 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR_ACCOUNT:role/LambdaExecutionRole

# Upload code
zip -r results.zip betfair_results_fetcher_v2.py
aws lambda update-function-code \
  --function-name BettingResultsFetcher \
  --zip-file fileb://results.zip

# Create EventBridge rule
aws events put-rule \
  --name BettingResultsHourly \
  --schedule-expression "cron(0 * * * ? *)"

aws events put-targets \
  --rule BettingResultsHourly \
  --targets "Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT:function:BettingResultsFetcher"
```

### Step 2: Workflow Generator (THIS WEEK - 2 hours)
- Convert PowerShell workflow to Python
- Integrate AWS Bedrock for Claude access
- Test locally first
- Deploy Lambda + EventBridge

### Step 3: Daily Learning (THIS WEEK - 1 hour)
- Automate performance evaluation
- Store prompt updates in S3
- Email reports via SES

### Step 4: Monitoring & Alerts (OPTIONAL)
- CloudWatch alarms for failures
- SNS notifications
- Dashboard for performance

## Next Actions

**Immediate (This Week):**
1. ✅ Set up AWS Secrets Manager with Betfair credentials
2. ✅ Create BettingResultsFetcher Lambda function
3. ✅ Test results fetching in cloud
4. ✅ Disable local SureBet-Hourly-ResultsFetcher task

**Short-term (Next Week):**
1. Convert workflow to Python Lambda
2. Set up AWS Bedrock access
3. Deploy workflow Lambda with EventBridge
4. Test end-to-end cloud execution

**Long-term (Month 2):**
1. Add monitoring & alerts
2. Optimize costs
3. Add historical backtesting
4. Scale to more sports/markets
