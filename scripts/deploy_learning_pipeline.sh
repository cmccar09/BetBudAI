#!/bin/bash

##############################################################################
# Deploy Learning Pipeline to AWS
##############################################################################
# This script deploys the automated learning system to production.
#
# Prerequisites:
# 1. AWS CLI configured with credentials
# 2. DynamoDB tables created (see below)
# 3. Lambda execution role with permissions
#
# Usage:
#   ./scripts/deploy_learning_pipeline.sh [--dry-run]
#
# Deployment Steps:
# 1. Create/verify DynamoDB tables
# 2. Update evening pipeline handler
# 3. Deploy learning orchestrator Lambda
# 4. Configure EventBridge schedule
# 5. Deploy monitoring dashboard
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
AWS_REGION="${AWS_REGION:-eu-west-1}"
LAMBDA_NAME="betbudai-learning-orchestrator"
LAMBDA_ROLE="arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role"  # UPDATE THIS
LAMBDA_TIMEOUT=600
LAMBDA_MEMORY=1024
DRY_RUN=false

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            log_warning "DRY RUN MODE - No changes will be made"
            ;;
    esac
done

##############################################################################
# Step 1: Create DynamoDB Tables
##############################################################################
create_dynamodb_tables() {
    log_info "Creating DynamoDB tables..."

    # BetBudAI_LearningInsights table
    if aws dynamodb describe-table --table-name BetBudAI_LearningInsights --region "$AWS_REGION" > /dev/null 2>&1; then
        log_success "BetBudAI_LearningInsights table already exists"
    else
        log_info "Creating BetBudAI_LearningInsights table..."
        if [ "$DRY_RUN" = false ]; then
            aws dynamodb create-table \
                --table-name BetBudAI_LearningInsights \
                --attribute-definitions \
                    AttributeName=analysis_date,AttributeType=S \
                    AttributeName=analysis_type,AttributeType=S \
                --key-schema \
                    AttributeName=analysis_date,KeyType=HASH \
                    AttributeName=analysis_type,KeyType=RANGE \
                --billing-mode PAY_PER_REQUEST \
                --region "$AWS_REGION"

            # Wait for table to be active
            aws dynamodb wait table-exists --table-name BetBudAI_LearningInsights --region "$AWS_REGION"

            # Enable TTL
            aws dynamodb update-time-to-live \
                --table-name BetBudAI_LearningInsights \
                --time-to-live-specification "Enabled=true, AttributeName=ttl_timestamp" \
                --region "$AWS_REGION"

            log_success "BetBudAI_LearningInsights table created with TTL (90 days)"
        fi
    fi

    # BetBudAI_WeightChangelog table
    if aws dynamodb describe-table --table-name BetBudAI_WeightChangelog --region "$AWS_REGION" > /dev/null 2>&1; then
        log_success "BetBudAI_WeightChangelog table already exists"
    else
        log_info "Creating BetBudAI_WeightChangelog table..."
        if [ "$DRY_RUN" = false ]; then
            aws dynamodb create-table \
                --table-name BetBudAI_WeightChangelog \
                --attribute-definitions \
                    AttributeName=change_date,AttributeType=S \
                    AttributeName=change_timestamp,AttributeType=S \
                --key-schema \
                    AttributeName=change_date,KeyType=HASH \
                    AttributeName=change_timestamp,KeyType=RANGE \
                --billing-mode PAY_PER_REQUEST \
                --region "$AWS_REGION"

            aws dynamodb wait table-exists --table-name BetBudAI_WeightChangelog --region "$AWS_REGION"
            log_success "BetBudAI_WeightChangelog table created"
        fi
    fi
}

##############################################################################
# Step 2: Package Lambda Function
##############################################################################
package_lambda() {
    log_info "Packaging Lambda function..."

    cd "$PROJECT_ROOT"

    # Create deployment package directory
    DEPLOY_DIR="$PROJECT_ROOT/_lambda_deploy_learning"
    rm -rf "$DEPLOY_DIR"
    mkdir -p "$DEPLOY_DIR"

    # Copy Lambda handler
    cp backend/lambda/learning_orchestrator_handler.py "$DEPLOY_DIR/lambda_function.py"

    # Copy backend modules
    mkdir -p "$DEPLOY_DIR/backend"
    cp -r backend/pipeline "$DEPLOY_DIR/backend/"
    cp -r backend/config "$DEPLOY_DIR/backend/"
    cp -r backend/core "$DEPLOY_DIR/backend/"

    # Create __init__.py files
    touch "$DEPLOY_DIR/backend/__init__.py"

    # Create deployment package
    cd "$DEPLOY_DIR"
    zip -r lambda_package.zip . -x "*.pyc" -x "__pycache__/*" > /dev/null
    cd "$PROJECT_ROOT"

    log_success "Lambda package created: $DEPLOY_DIR/lambda_package.zip"
}

##############################################################################
# Step 3: Deploy Lambda Function
##############################################################################
deploy_lambda() {
    log_info "Deploying Lambda function: $LAMBDA_NAME..."

    DEPLOY_DIR="$PROJECT_ROOT/_lambda_deploy_learning"
    PACKAGE_PATH="$DEPLOY_DIR/lambda_package.zip"

    if [ "$DRY_RUN" = false ]; then
        # Check if Lambda exists
        if aws lambda get-function --function-name "$LAMBDA_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
            log_info "Updating existing Lambda function..."
            aws lambda update-function-code \
                --function-name "$LAMBDA_NAME" \
                --zip-file "fileb://$PACKAGE_PATH" \
                --region "$AWS_REGION" > /dev/null

            # Update configuration
            aws lambda update-function-configuration \
                --function-name "$LAMBDA_NAME" \
                --timeout "$LAMBDA_TIMEOUT" \
                --memory-size "$LAMBDA_MEMORY" \
                --environment "Variables={
                    CONFIDENCE_THRESHOLD=0.80,
                    ENABLE_AUTO_DEPLOY=true,
                    DRY_RUN=false,
                    MAX_WORKERS=10
                }" \
                --region "$AWS_REGION" > /dev/null

            log_success "Lambda function updated"
        else
            log_info "Creating new Lambda function..."
            aws lambda create-function \
                --function-name "$LAMBDA_NAME" \
                --runtime python3.11 \
                --role "$LAMBDA_ROLE" \
                --handler lambda_function.lambda_handler \
                --zip-file "fileb://$PACKAGE_PATH" \
                --timeout "$LAMBDA_TIMEOUT" \
                --memory-size "$LAMBDA_MEMORY" \
                --environment "Variables={
                    CONFIDENCE_THRESHOLD=0.80,
                    ENABLE_AUTO_DEPLOY=true,
                    DRY_RUN=false,
                    MAX_WORKERS=10
                }" \
                --region "$AWS_REGION" > /dev/null

            log_success "Lambda function created"
        fi

        # Grant permissions to evening pipeline to invoke
        aws lambda add-permission \
            --function-name "$LAMBDA_NAME" \
            --statement-id AllowEveningPipelineInvoke \
            --action lambda:InvokeFunction \
            --principal lambda.amazonaws.com \
            --region "$AWS_REGION" 2>/dev/null || true

        log_success "Lambda permissions configured"
    fi
}

##############################################################################
# Step 4: Update Evening Pipeline
##############################################################################
update_evening_pipeline() {
    log_info "Evening pipeline update instructions:"
    echo ""
    echo "Add the following to backend/pipeline/evening/handler.py:"
    echo ""
    cat << 'EOF'
# After optional analysis steps (around line 97), add:

# Trigger automated learning
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
                f"{learning_results.get('adjustments_deployed', 0)} adjustments deployed"
            )
            analysis_results['automated_learning'] = learning_results

            # Generate enhanced report
            enhanced_report = generate_enhanced_daily_report(
                base_report={'roi_data': analysis_results.get('daily_roi', {})},
                learning_results=learning_results,
                target_date=target_date
            )

            # Send enhanced report email (optional)
            # ... your email sending logic here ...

        else:
            logger.warning(
                f"[evening-pipeline] Learning skipped: "
                f"{learning_results.get('reason', learning_results.get('error', 'unknown'))}"
            )
            analysis_results['automated_learning'] = learning_results

    except Exception as e:
        logger.error(f"[evening-pipeline] Learning failed: {e}", exc_info=True)
        analysis_results['automated_learning'] = {'error': str(e)}
EOF
    echo ""
}

##############################################################################
# Step 5: Test Deployment
##############################################################################
test_deployment() {
    log_info "Testing Lambda deployment..."

    if [ "$DRY_RUN" = false ]; then
        # Test invoke with yesterday's data
        TEST_DATE=$(date -u -d "yesterday" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d)

        TEST_PAYLOAD=$(cat <<EOF
{
    "target_date": "$TEST_DATE",
    "learning_confidence_threshold": 0.80,
    "learning_auto_deploy": false,
    "learning_dry_run": true,
    "learning_max_races": 5
}
EOF
)

        log_info "Invoking Lambda with test payload..."
        RESPONSE=$(aws lambda invoke \
            --function-name "$LAMBDA_NAME" \
            --payload "$TEST_PAYLOAD" \
            --region "$AWS_REGION" \
            /tmp/lambda_response.json)

        if [ $? -eq 0 ]; then
            log_success "Lambda invocation successful"
            log_info "Response:"
            cat /tmp/lambda_response.json | jq .
        else
            log_error "Lambda invocation failed"
            exit 1
        fi
    fi
}

##############################################################################
# Step 6: Deploy CloudWatch Dashboard
##############################################################################
deploy_dashboard() {
    log_info "Deploy CloudWatch dashboard manually using:"
    echo "aws cloudwatch put-dashboard --dashboard-name BetBudAI-Learning --dashboard-body file://cloudwatch_dashboard.json"
}

##############################################################################
# Main Execution
##############################################################################
main() {
    log_info "Starting Learning Pipeline Deployment"
    log_info "Region: $AWS_REGION"
    log_info "Dry Run: $DRY_RUN"
    echo ""

    # Step 1: Create tables
    create_dynamodb_tables
    echo ""

    # Step 2: Package Lambda
    package_lambda
    echo ""

    # Step 3: Deploy Lambda
    deploy_lambda
    echo ""

    # Step 4: Evening pipeline instructions
    update_evening_pipeline
    echo ""

    # Step 5: Test
    test_deployment
    echo ""

    # Step 6: Dashboard
    deploy_dashboard
    echo ""

    log_success "Deployment complete!"
    echo ""
    echo "Next steps:"
    echo "1. Update evening pipeline handler (see instructions above)"
    echo "2. Deploy evening pipeline: cd backend/pipeline && python deploy_lambdas.py"
    echo "3. Deploy CloudWatch dashboard: aws cloudwatch put-dashboard ..."
    echo "4. Monitor first learning run tonight at 21:15 UTC"
    echo ""
}

main
