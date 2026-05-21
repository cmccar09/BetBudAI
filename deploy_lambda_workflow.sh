#!/bin/bash
# Deploy Complete Betting Workflow to Lambda
# This replaces laptop dependency with full AWS automation

echo "======================================================================="
echo "BetBudAI - Lambda Workflow Deployment"
echo "======================================================================="
echo ""

# Configuration
LAMBDA_NAME="betting"
REGION="eu-west-1"
HANDLER="lambda_workflow_complete.lambda_handler"
RUNTIME="python3.11"
TIMEOUT=900  # 15 minutes
MEMORY=2048  # 2GB
ROLE_ARN="arn:aws:iam::813281204422:role/service-role/betting-role-gx8a3t0f"

# Create deployment package
echo "[1/6] Creating deployment package..."
rm -f lambda_workflow_deploy.zip

# Create temp directory
mkdir -p lambda_temp
cd lambda_temp

# Copy core workflow files
echo "  - Copying workflow files..."
cp ../lambda_workflow_complete.py .
cp ../comprehensive_pick_logic.py .
cp ../enforce_comprehensive_analysis.py .
cp ../betfair_odds_fetcher.py .
cp ../betfair_cert_auth.py . 2>/dev/null || true

# Copy any Betfair certificates
if [ -f ../client-2048.crt ]; then
    cp ../client-2048.crt .
fi
if [ -f ../client-2048.key ]; then
    cp ../client-2048.key .
fi

# Zip everything
echo "  - Creating zip file..."
zip -r ../lambda_workflow_deploy.zip . -q

cd ..
rm -rf lambda_temp

echo "  [OK] Package created: lambda_workflow_deploy.zip"
FILE_SIZE=$(ls -lh lambda_workflow_deploy.zip | awk '{print $5}')
echo "  Size: $FILE_SIZE"
echo ""

# Update Lambda configuration
echo "[2/6] Updating Lambda configuration..."
aws lambda update-function-configuration \
    --function-name $LAMBDA_NAME \
    --timeout $TIMEOUT \
    --memory-size $MEMORY \
    --handler $HANDLER \
    --runtime $RUNTIME \
    --region $REGION \
    --output text

echo "  [OK] Configuration updated (15 min timeout, 2GB memory)"
echo ""

# Wait for configuration update
echo "[3/6] Waiting for configuration update..."
aws lambda wait function-updated \
    --function-name $LAMBDA_NAME \
    --region $REGION

echo "  [OK] Configuration active"
echo ""

# Upload code
echo "[4/6] Uploading Lambda code..."
aws lambda update-function-code \
    --function-name $LAMBDA_NAME \
    --zip-file fileb://lambda_workflow_deploy.zip \
    --region $REGION \
    --output text

echo "  [OK] Code uploaded"
echo ""

# Wait for code update
echo "[5/6] Waiting for code deployment..."
aws lambda wait function-updated \
    --function-name $LAMBDA_NAME \
    --region $REGION

echo "  [OK] Code deployed"
echo ""

# Update EventBridge schedule to 11:00 AM BST (10:00 UTC)
echo "[6/6] Updating EventBridge schedule..."
SCHEDULE_NAME="BettingWorkflow-11AM"

# Delete old schedules
aws scheduler delete-schedule --name "BettingWorkflow-15Min" --region $REGION 2>/dev/null || true
aws scheduler delete-schedule --name "BettingWorkflow-45Min" --region $REGION 2>/dev/null || true

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function --function-name $LAMBDA_NAME --region $REGION --query 'Configuration.FunctionArn' --output text)

# Get EventBridge role ARN
ROLE=$(aws iam get-role --role-name EventBridgeSchedulerLambdaRole --query 'Role.Arn' --output text 2>/dev/null)

if [ -z "$ROLE" ]; then
    echo "  [WARN] EventBridgeSchedulerLambdaRole not found - using Lambda execution role"
    ROLE=$ROLE_ARN
fi

# Create new schedule for 11:00 AM BST (10:00 UTC in summer, 11:00 UTC in winter)
# Using 10:00 UTC for BST
aws scheduler create-schedule \
    --name $SCHEDULE_NAME \
    --schedule-expression "cron(0 10 ? * * *)" \
    --schedule-expression-timezone "Europe/London" \
    --description "Generate daily picks at 11:00 AM BST" \
    --flexible-time-window Mode=OFF \
    --target "{\"Arn\":\"$LAMBDA_ARN\",\"RoleArn\":\"$ROLE\",\"RetryPolicy\":{\"MaximumRetryAttempts\":2}}" \
    --region $REGION 2>/dev/null || \
aws scheduler update-schedule \
    --name $SCHEDULE_NAME \
    --schedule-expression "cron(0 10 ? * * *)" \
    --schedule-expression-timezone "Europe/London" \
    --description "Generate daily picks at 11:00 AM BST" \
    --flexible-time-window Mode=OFF \
    --target "{\"Arn\":\"$LAMBDA_ARN\",\"RoleArn\":\"$ROLE\",\"RetryPolicy\":{\"MaximumRetryAttempts\":2}}" \
    --region $REGION

echo "  [OK] Schedule updated: Daily at 11:00 AM BST"
echo ""

echo "======================================================================="
echo "SUCCESS! Lambda Workflow Deployed"
echo "======================================================================="
echo ""
echo "Configuration:"
echo "  Function: $LAMBDA_NAME"
echo "  Handler: $HANDLER"
echo "  Timeout: 15 minutes"
echo "  Memory: 2GB"
echo "  Schedule: Daily at 11:00 AM BST (10:00 UTC)"
echo ""
echo "Next Steps:"
echo "  1. Test the function now:"
echo "     aws lambda invoke --function-name $LAMBDA_NAME --region $REGION output.json"
echo ""
echo "  2. Check logs:"
echo "     MSYS_NO_PATHCONV=1 aws logs tail \"/aws/lambda/$LAMBDA_NAME\" --region $REGION --follow"
echo ""
echo "  3. Verify schedule:"
echo "     aws scheduler get-schedule --name $SCHEDULE_NAME --region $REGION"
echo ""
echo "  4. Tomorrow at 11:00 AM BST, picks will generate automatically!"
echo ""
echo "======================================================================="
