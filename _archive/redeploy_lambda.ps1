# Redeploy Lambda with Latest Code
Write-Host "=== REDEPLOYING LAMBDA ===" -ForegroundColor Cyan

# Clean up old zip
if (Test-Path lambda-deployment.zip) {
    Remove-Item lambda-deployment.zip -Force
    Write-Host "Removed old ZIP" -ForegroundColor Yellow
}

# Create new deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
Set-Location lambda-workflow-package
Compress-Archive -Path * -DestinationPath ..\lambda-deployment.zip -Force -CompressionLevel Fastest
Set-Location ..

Write-Host "✓ Package created: $(((Get-Item lambda-deployment.zip).Length / 1MB).ToString('F2')) MB" -ForegroundColor Green

# Update Lambda
Write-Host "`nUploading to AWS Lambda..." -ForegroundColor Yellow
$result = aws lambda update-function-code `
    --function-name BettingWorkflowScheduled `
    --zip-file fileb://lambda-deployment.zip `
    --region eu-west-1 `
    --output json | ConvertFrom-Json

Write-Host "✓ Lambda updated: $($result.FunctionName)" -ForegroundColor Green
Write-Host "  Last Modified: $($result.LastModified)" -ForegroundColor White
Write-Host "  State: $($result.State)" -ForegroundColor White

# Wait for deployment
Write-Host "`nWaiting for deployment to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test execution
Write-Host "`n=== TESTING LAMBDA ===" -ForegroundColor Cyan
aws lambda invoke `
    --function-name BettingWorkflowScheduled `
    --region eu-west-1 `
    test-result.json | Out-Null

Start-Sleep -Seconds 15

Write-Host "`nReading result..." -ForegroundColor Yellow
$testResult = Get-Content test-result.json -Raw | ConvertFrom-Json

if ($testResult.statusCode -eq 200) {
    $body = $testResult.body | ConvertFrom-Json
    if ($body.success) {
        Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
        Write-Host "Picks generated: $($body.picks_count)" -ForegroundColor Green
        Write-Host "`nRefresh your UI to see real picks!" -ForegroundColor Cyan
    } else {
        Write-Host "`n❌ FAILED" -ForegroundColor Red
        Write-Host "Error: $($body.error)" -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ Lambda Error (Status: $($testResult.statusCode))" -ForegroundColor Red
    $testResult | ConvertTo-Json
}

Write-Host "`n=== COMPLETE ===" -ForegroundColor Cyan
