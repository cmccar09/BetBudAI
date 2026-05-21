#!/usr/bin/env pwsh
# Create API Gateway HTTP API for Lambda function

$functionName = "BettingPicksAPI"
$apiName = "SureBetAPI"
$region = "eu-west-1"

Write-Host "Creating API Gateway HTTP API..." -ForegroundColor Cyan

# Get Lambda ARN
$lambdaArn = (aws lambda get-function --function-name $functionName --region $region --query 'Configuration.FunctionArn' --output text)

# Create API
$apiId = (aws apigatewayv2 create-api --name $apiName --protocol-type HTTP --target $lambdaArn --region $region --query 'ApiId' --output text)

Write-Host "  ✓ Created API: $apiId" -ForegroundColor Green

# Add permission for API Gateway to invoke Lambda
aws lambda add-permission `
    --function-name $functionName `
    --statement-id apigateway-invoke `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${region}:*:${apiId}/*" `
    --region $region 2>$null

# Get API endpoint
$apiEndpoint = (aws apigatewayv2 get-api --api-id $apiId --region $region --query 'ApiEndpoint' --output text)

Write-Host ""
Write-Host "="*60 -ForegroundColor Green
Write-Host "  API Gateway Created Successfully!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host ""
Write-Host "API Endpoint: $apiEndpoint" -ForegroundColor White
Write-Host ""
Write-Host "Test URLs:" -ForegroundColor Cyan
Write-Host "  $apiEndpoint/picks/today" -ForegroundColor White
Write-Host "  $apiEndpoint/picks" -ForegroundColor White
Write-Host ""

# Test the API
Write-Host "Testing API..." -ForegroundColor Yellow
try {
    $result = Invoke-RestMethod -Uri "$apiEndpoint/picks/today" -Method Get
    Write-Host "  ✓ API is working! Found $($result.count) picks" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ API test failed: $_" -ForegroundColor Yellow
}
