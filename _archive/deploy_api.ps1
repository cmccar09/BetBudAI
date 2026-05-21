#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy Lambda function with API Gateway for betting picks
.DESCRIPTION
    Creates Lambda function and API Gateway to serve picks to Amplify frontend
#>

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Deploy Betting Picks API to AWS" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

$functionName = "BettingPicksAPI"
$roleName = "BettingPicksAPIRole"
$region = "eu-west-1"

# Step 1: Create Lambda execution role (if it doesn't exist)
Write-Host "Step 1: Checking IAM role..." -ForegroundColor Yellow

$existingRole = aws iam get-role --role-name $roleName 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Creating IAM role..." -ForegroundColor Gray
    
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    Service = "lambda.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    
    aws iam create-role `
        --role-name $roleName `
        --assume-role-policy-document $trustPolicy
    
    # Attach policies
    aws iam attach-role-policy `
        --role-name $roleName `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    
    aws iam attach-role-policy `
        --role-name $roleName `
        --policy-arn "arn:aws:iam::aws:policy/AmazonDynamoDBReadOnlyAccess"
    
    Write-Host "  ✓ Created role: $roleName" -ForegroundColor Green
    Write-Host "  Waiting 10 seconds for role to propagate..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
} else {
    Write-Host "  ✓ Role exists: $roleName" -ForegroundColor Green
}

# Get role ARN
$roleArn = (aws iam get-role --role-name $roleName --query 'Role.Arn' --output text)
Write-Host "  Role ARN: $roleArn" -ForegroundColor Cyan

# Step 2: Package Lambda function
Write-Host ""
Write-Host "Step 2: Packaging Lambda function..." -ForegroundColor Yellow

$tempDir = "lambda-api-package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Copy-Item lambda_api_picks.py -Destination "$tempDir/lambda_function.py"

# Create deployment package
Push-Location $tempDir
Compress-Archive -Path * -DestinationPath ../lambda-api.zip -Force
Pop-Location
Remove-Item -Recurse -Force $tempDir

Write-Host "  ✓ Created lambda-api.zip" -ForegroundColor Green

# Step 3: Create/Update Lambda function
Write-Host ""
Write-Host "Step 3: Deploying Lambda function..." -ForegroundColor Yellow

$existingFunction = aws lambda get-function --function-name $functionName --region $region 2>$null

if ($LASTEXITCODE -ne 0) {
    # Create new function
    Write-Host "  Creating Lambda function..." -ForegroundColor Gray
    
    aws lambda create-function `
        --function-name $functionName `
        --runtime python3.11 `
        --role $roleArn `
        --handler lambda_function.lambda_handler `
        --zip-file fileb://lambda-api.zip `
        --timeout 30 `
        --memory-size 256 `
        --region $region
    
    Write-Host "  ✓ Created Lambda function: $functionName" -ForegroundColor Green
} else {
    # Update existing function
    Write-Host "  Updating Lambda function code..." -ForegroundColor Gray
    
    aws lambda update-function-code `
        --function-name $functionName `
        --zip-file fileb://lambda-api.zip `
        --region $region | Out-Null
    
    Write-Host "  ✓ Updated Lambda function: $functionName" -ForegroundColor Green
}

# Step 4: Create Lambda function URL (simpler than API Gateway)
Write-Host ""
Write-Host "Step 4: Creating function URL..." -ForegroundColor Yellow

$urlConfig = aws lambda get-function-url-config --function-name $functionName --region $region 2>$null

if ($LASTEXITCODE -ne 0) {
    $result = aws lambda create-function-url-config `
        --function-name $functionName `
        --auth-type NONE `
        --cors "AllowOrigins='*',AllowMethods='GET,OPTIONS',AllowHeaders='Content-Type'" `
        --region $region | ConvertFrom-Json
    
    $functionUrl = $result.FunctionUrl
    Write-Host "  ✓ Created function URL" -ForegroundColor Green
} else {
    $functionUrl = ($urlConfig | ConvertFrom-Json).FunctionUrl
    Write-Host "  ✓ Function URL exists" -ForegroundColor Green
}

# Add permission for public access
aws lambda add-permission `
    --function-name $functionName `
    --statement-id FunctionURLAllowPublicAccess `
    --action lambda:InvokeFunctionUrl `
    --principal "*" `
    --function-url-auth-type NONE `
    --region $region 2>$null | Out-Null

Write-Host ""
Write-Host "="*60 -ForegroundColor Green
Write-Host "✓ Deployment Complete!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host ""
Write-Host "API Endpoint:" -ForegroundColor Cyan
Write-Host "  $functionUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host "Test endpoints:" -ForegroundColor Cyan
Write-Host "  ${functionUrl}picks/today" -ForegroundColor White
Write-Host "  ${functionUrl}picks" -ForegroundColor White
Write-Host "  ${functionUrl}health" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update frontend/.env:" -ForegroundColor White
Write-Host "   REACT_APP_API_URL=$functionUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Rebuild and deploy frontend:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run build" -ForegroundColor Gray
Write-Host "   git add ." -ForegroundColor Gray
Write-Host "   git commit -m 'Update API URL'" -ForegroundColor Gray
Write-Host "   git push" -ForegroundColor Gray
Write-Host ""

# Test the endpoint
Write-Host "Testing API..." -ForegroundColor Yellow
$testResult = Invoke-RestMethod -Uri "${functionUrl}health" -Method Get -ErrorAction SilentlyContinue
if ($testResult) {
    Write-Host "✓ API is responding!" -ForegroundColor Green
    Write-Host "  Status: $($testResult.status)" -ForegroundColor White
} else {
    Write-Host "⚠ API test failed - may need a minute to activate" -ForegroundColor Yellow
}
