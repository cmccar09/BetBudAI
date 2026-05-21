#!/bin/bash

# Deploy Enhanced Lambda Functions
# =================================
# Packages and deploys the enhanced pick selector to Lambda

set -e

echo "=========================================="
echo "DEPLOYING ENHANCED BETTING STRATEGY"
echo "=========================================="
echo ""

# Configuration
REGION="eu-west-1"
FUNCTION_NAME_ANALYSIS="surebet-analysis"
FUNCTION_NAME_API="betbudai-api"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Create deployment package
echo -e "${YELLOW}[Step 1/5]${NC} Creating deployment package..."
cd "$(dirname "$0")/.."

# Create temp directory
DEPLOY_DIR="lambda_deploy_enhanced"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy Lambda functions
echo "  - Copying Lambda handlers..."
cp -r backend/lambda/* "$DEPLOY_DIR/"

# Copy enhanced core modules
echo "  - Copying enhanced core modules..."
mkdir -p "$DEPLOY_DIR/backend/core"
cp backend/core/ev_calculator.py "$DEPLOY_DIR/backend/core/"
cp backend/core/race_quality_filter.py "$DEPLOY_DIR/backend/core/"
cp backend/core/enhanced_pick_selector.py "$DEPLOY_DIR/backend/core/"
cp backend/core/scoring/__init__.py "$DEPLOY_DIR/backend/core/" || true

# Copy existing scoring modules if they exist
if [ -d "backend/core/scoring" ]; then
    echo "  - Copying scoring modules..."
    mkdir -p "$DEPLOY_DIR/backend/core/scoring"
    cp -r backend/core/scoring/* "$DEPLOY_DIR/backend/core/scoring/" || true
fi

# Copy signals (Phase 1)
if [ -d "backend/core/signals" ]; then
    echo "  - Copying Phase 1 signals..."
    mkdir -p "$DEPLOY_DIR/backend/core/signals"
    cp -r backend/core/signals/* "$DEPLOY_DIR/backend/core/signals/" || true
fi

# Create __init__.py files
touch "$DEPLOY_DIR/backend/__init__.py"
touch "$DEPLOY_DIR/backend/core/__init__.py"

echo -e "${GREEN}✓${NC} Deployment package created"
echo ""

# Step 2: Create ZIP file
echo -e "${YELLOW}[Step 2/5]${NC} Creating ZIP archive..."
cd "$DEPLOY_DIR"
zip -r ../enhanced_lambda.zip . -q
cd ..
echo -e "${GREEN}✓${NC} ZIP file created: enhanced_lambda.zip"
echo ""

# Step 3: Test package locally
echo -e "${YELLOW}[Step 3/5]${NC} Testing package integrity..."
python3 << 'PYTHON_TEST'
import sys
import zipfile
import os

try:
    with zipfile.ZipFile('enhanced_lambda.zip', 'r') as z:
        files = z.namelist()

        # Check required files exist
        required = [
            'backend/core/ev_calculator.py',
            'backend/core/race_quality_filter.py',
            'backend/core/enhanced_pick_selector.py',
            'sf_analysis.py'
        ]

        missing = []
        for req in required:
            if req not in files:
                missing.append(req)

        if missing:
            print(f"❌ Missing files in package: {missing}")
            sys.exit(1)

        print(f"✓ Package contains {len(files)} files")
        print(f"✓ All required modules present")

except Exception as e:
    print(f"❌ Package validation failed: {e}")
    sys.exit(1)

PYTHON_TEST

if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Package validation failed"
    exit 1
fi

echo -e "${GREEN}✓${NC} Package validated successfully"
echo ""

# Step 4: Deploy to AWS Lambda
echo -e "${YELLOW}[Step 4/5]${NC} Deploying to AWS Lambda..."
echo "  Region: $REGION"
echo "  Function: $FUNCTION_NAME_ANALYSIS"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} AWS CLI not configured. Please run 'aws configure'"
    exit 1
fi

# Deploy analysis function
echo "  Updating Lambda function code..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME_ANALYSIS" \
    --zip-file fileb://enhanced_lambda.zip \
    --region "$REGION" \
    --no-cli-pager

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Lambda function updated successfully"
else
    echo -e "${RED}✗${NC} Lambda deployment failed"
    exit 1
fi

echo ""

# Step 5: Update environment variables
echo -e "${YELLOW}[Step 5/5]${NC} Updating Lambda configuration..."

aws lambda update-function-configuration \
    --function-name "$FUNCTION_NAME_ANALYSIS" \
    --region "$REGION" \
    --environment "Variables={ENHANCED_SELECTOR_ENABLED=true,LOG_LEVEL=INFO}" \
    --timeout 300 \
    --memory-size 512 \
    --no-cli-pager

echo -e "${GREEN}✓${NC} Configuration updated"
echo ""

# Cleanup
echo "Cleaning up temporary files..."
rm -rf "$DEPLOY_DIR"
# Keep the ZIP file for reference
# rm enhanced_lambda.zip

echo ""
echo "=========================================="
echo -e "${GREEN}DEPLOYMENT COMPLETE!${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Enhanced pick selector deployed"
echo "  • EV calculator integrated"
echo "  • Race quality filter active"
echo "  • Max 5 picks enforced"
echo "  • 2x 4/1+ requirement enforced"
echo ""
echo "Next steps:"
echo "  1. Test with: aws lambda invoke --function-name $FUNCTION_NAME_ANALYSIS test-output.json"
echo "  2. Check CloudWatch logs for '[surebet-analysis] Enhanced selection' messages"
echo "  3. Verify picks include bet_tier, ev_pct, stake_units fields"
echo "  4. Update UI to display new fields"
echo ""
echo "ZIP package saved at: $(pwd)/enhanced_lambda.zip"
echo ""
