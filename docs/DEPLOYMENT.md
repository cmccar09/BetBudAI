# Deployment Guide

## Prerequisites

- AWS Account (eu-west-1 region)
- AWS CLI configured with credentials
- Node.js 16+ (for frontend)
- Python 3.11+ (for backend)
- Docker (optional, for local testing)

## Local Development Setup

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/BetBudAI.git
cd BetBudAI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### 2. Environment Configuration
```bash
# Create .env file
cat > backend/.env << EOF
ENV=development
AWS_REGION=eu-west-1
DYNAMODB_TABLE_PICKS=SureBetBets
DYNAMODB_TABLE_USERS=BetBudAI_Subscribers
EOF

# Create frontend .env
cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENV=development
EOF
```

### GA4 Reporting Summary

To enable the live admin analytics summary, set the following backend environment values in production:

```bash
GA4_PROPERTY_ID=537650672
GA4_CREDENTIALS_JSON=...
# or:
GA4_CREDENTIALS_JSON_B64=...
# or:
GA4_CREDENTIALS_SECRET_NAME=ga4-service-account
```

The backend accepts either a service-account JSON blob or an OAuth user credential JSON blob in the secret.
The credential must have access to the GA4 property and the Analytics Data API enabled in Google Cloud.

### 3. Run Locally
```bash
# Terminal 1: Backend
cd backend
flask run  # or: python -m api.app

# Terminal 2: Frontend
cd frontend
npm start
```

Access the app at http://localhost:3000

## AWS Deployment

### 1. Prepare AWS Environment

#### Create IAM Role for Lambda
```bash
# Create role with policies
aws iam create-role \
  --role-name betbudai-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policies
aws iam attach-role-policy \
  --role-name betbudai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name betbudai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
  --role-name betbudai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

#### Create DynamoDB Tables
```bash
# Picks/bets table
aws dynamodb create-table \
  --table-name SureBetBets \
  --attribute-definitions \
    AttributeName=bet_date,AttributeType=S \
    AttributeName=bet_id,AttributeType=S \
  --key-schema \
    AttributeName=bet_date,KeyType=HASH \
    AttributeName=bet_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1

# Users table
aws dynamodb create-table \
  --table-name BetBudAI_Subscribers \
  --attribute-definitions \
    AttributeName=email,AttributeType=S \
    AttributeName=gsi_key,AttributeType=S \
  --key-schema \
    AttributeName=email,KeyType=HASH \
    AttributeName=gsi_key,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

### 2. Deploy Backend (Lambda)

```bash
cd backend/pipeline

# Update deploy.py with your AWS Account ID
sed -i 's/ACCOUNT_ID/YOUR_ACCOUNT_ID/g' deploy.py

# Deploy all Lambda functions
python deploy.py
```

Verify in AWS Lambda console that functions are deployed.

### 3. Create Step Functions State Machines

```bash
# Deploy morning state machine
aws stepfunctions create-state-machine \
  --name BetBudAI-Morning \
  --definition file://infrastructure/step_functions/morning_sm.json \
  --role-arn arn:aws:iam::YOUR_ACCOUNT_ID:role/StepFunctionsRole \
  --region eu-west-1

# Repeat for refresh, evening, learning state machines
```

### 4. Create EventBridge Rules

```bash
# Morning pipeline (08:30 UTC)
aws events put-rule \
  --name betbudai-morning-schedule \
  --schedule-expression 'cron(30 08 * * ? *)' \
  --state ENABLED \
  --region eu-west-1

aws events put-targets \
  --rule betbudai-morning-schedule \
  --targets "Id"="1","Arn"="arn:aws:states:eu-west-1:YOUR_ACCOUNT_ID:stateMachine:BetBudAI-Morning","RoleArn"="arn:aws:iam::YOUR_ACCOUNT_ID:role/EventBridgeRole"
```

### 5. Deploy Frontend (Amplify)

```bash
cd frontend

# Build production bundle
npm run build

# Deploy to Amplify (if connected)
# Or manually upload to S3 + CloudFront
aws s3 sync build/ s3://betbudai-frontend-prod/ --delete
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### 6. Configure API Gateway

```bash
# Create REST API (if not already created)
aws apigateway create-rest-api \
  --name BetBudAI-API \
  --region eu-west-1

# Create Lambda integration for /api/* paths
# (Can be done via AWS Console or boto3)
```

## Monitoring & Maintenance

### CloudWatch Dashboards
```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name BetBudAI-Monitoring \
  --dashboard-body file://infrastructure/cloudwatch-dashboard.json
```

### Set Up Alarms
```bash
# Pipeline failure alarm
aws cloudwatch put-metric-alarm \
  --alarm-name BetBudAI-Pipeline-Failed \
  --alarm-description "Alert on pipeline execution failure" \
  --metric-name ExecutionsFailed \
  --namespace AWS/States \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --alarm-actions arn:aws:sns:eu-west-1:YOUR_ACCOUNT_ID:betbudai-alerts
```

## Troubleshooting

### Lambda Cold Starts
- Increase provisioned concurrency for critical functions
- Use Lambda Layers for shared dependencies

### DynamoDB Throttling
- Enable auto-scaling
- Use on-demand billing mode (PAY_PER_REQUEST)

### API Latency
- Enable CloudFront caching for GET endpoints
- Implement request caching in Lambda

### Pipeline Failures
- Check CloudWatch Logs for specific Lambda
- Verify DynamoDB table access & permissions
- Confirm external API credentials (Betfair, Sporting Life)

## Rollback Procedure

If a deployment breaks production:
```bash
# Get previous Lambda version
aws lambda list-versions-by-function --function-name betbudai-analysis

# Rollback to previous version
aws lambda update-alias \
  --function-name betbudai-analysis \
  --name LIVE \
  --function-version PREVIOUS_VERSION_NUMBER
```

## Next Deployment Steps

1. ✅ Backend Lambda deployed
2. ✅ Step Functions created
3. ✅ EventBridge rules scheduled
4. ⏳ Frontend deployed to Amplify
5. ⏳ Database migration completed
6. ⏳ Smoke tests passed
7. ⏳ Production cutover
