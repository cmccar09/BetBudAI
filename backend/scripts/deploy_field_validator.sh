#!/bin/bash
# Deploy Race Field Validator Lambda Function
# Creates quality gate that ensures every horse in every race is analyzed

set -e

FUNCTION_NAME="betbudai-field-validator"
REGION="eu-west-1"
ROLE_ARN="arn:aws:iam::813281204422:role/lambda-dynamodb-role"

echo "========================================="
echo "Deploying Race Field Validator Lambda"
echo "========================================="

# Create deployment package
echo "Creating deployment package..."
cd "$(dirname "$0")/../pipeline/validation"

# Create clean package directory
rm -rf package
mkdir -p package

# Copy handler
cp race_field_validator.py package/

# Install dependencies if needed
# pip install -r requirements.txt -t package/

# Create zip
cd package
zip -r ../field_validator.zip . > /dev/null
cd ..

echo "✓ Package created: field_validator.zip"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo "Updating existing function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://field_validator.zip \
        --region $REGION \
        --output json > /dev/null

    echo "Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --handler race_field_validator.lambda_handler \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{STAGE=production}" \
        --region $REGION \
        --output json > /dev/null

    echo "✓ Function updated: $FUNCTION_NAME"
else
    echo "Creating new function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler race_field_validator.lambda_handler \
        --zip-file fileb://field_validator.zip \
        --timeout 300 \
        --memory-size 512 \
        --environment Variables="{STAGE=production}" \
        --description "Quality gate: validates all horses in every race are analyzed" \
        --region $REGION \
        --output json > /dev/null

    echo "✓ Function created: $FUNCTION_NAME"
fi

# Grant permissions for morning pipeline to invoke
echo "Granting invoke permissions to morning pipeline..."
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id AllowMorningPipelineInvoke \
    --action lambda:InvokeFunction \
    --principal lambda.amazonaws.com \
    --source-arn "arn:aws:lambda:$REGION:813281204422:function:betbudai-morning" \
    --region $REGION \
    --output json > /dev/null 2>&1 || echo "  (permission already exists)"

# Cleanup
rm -rf package field_validator.zip

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""
echo "Next steps:"
echo "1. Run: python backend/scripts/create_validation_table.py"
echo "2. Test: aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"target_date\":\"2026-05-20\"}' output.json"
echo "3. Morning pipeline will now validate field completeness automatically"
echo ""
