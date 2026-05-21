# Deploy BettingPicksAPI Lambda Function
# This script ensures correct deployment of the API Lambda

Write-Host "=== DEPLOYING BettingPicksAPI Lambda ===" -ForegroundColor Cyan

# Validate source file exists
if (-not (Test-Path lambda_api_picks.py)) {
    Write-Host "ERROR: lambda_api_picks.py not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Source file found: lambda_api_picks.py" -ForegroundColor Green

# Copy to lambda_function.py (required by Lambda handler)
Write-Host "`nPreparing deployment package..." -ForegroundColor Yellow
Copy-Item lambda_api_picks.py lambda_function.py -Force

# Clean up old zip
if (Test-Path lambda_deployment.zip) {
    Remove-Item lambda_deployment.zip -Force
}

# Create deployment package
Compress-Archive -Path lambda_function.py -DestinationPath lambda_deployment.zip -Force
$zipSize = [math]::Round((Get-Item lambda_deployment.zip).Length / 1KB, 2)
Write-Host "✓ Package created: $zipSize KB" -ForegroundColor Green

# Deploy to AWS
Write-Host "`nUploading to AWS Lambda (eu-west-1)..." -ForegroundColor Yellow
$result = aws lambda update-function-code `
    --function-name BettingPicksAPI `
    --zip-file fileb://lambda_deployment.zip `
    --region eu-west-1 `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "  Function: $($result.FunctionName)" -ForegroundColor White
    Write-Host "  Updated: $($result.LastModified)" -ForegroundColor White
    Write-Host "  Runtime: $($result.Runtime)" -ForegroundColor White
    Write-Host "  Size: $($result.CodeSize) bytes" -ForegroundColor White
} else {
    Write-Host "`n❌ DEPLOYMENT FAILED!" -ForegroundColor Red
    exit 1
}

# Clean up temp file
Remove-Item lambda_function.py -Force -ErrorAction SilentlyContinue

# Wait for Lambda to be ready
Write-Host "`nWaiting for Lambda to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test the deployment
Write-Host "`n=== TESTING API ===" -ForegroundColor Cyan
Write-Host "Testing /api/picks/today endpoint..." -ForegroundColor Yellow

$testUrl = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today"
try {
    $response = Invoke-RestMethod -Uri $testUrl -Method Get -TimeoutSec 10
    Write-Host "✓ API responding successfully" -ForegroundColor Green
    Write-Host "  Total picks: $($response.total_picks)" -ForegroundColor White
} catch {
    Write-Host "⚠ Warning: API test failed - check logs" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host "`n=== DEPLOYMENT COMPLETE ===" -ForegroundColor Cyan
Write-Host "Lambda function is live at:" -ForegroundColor White
Write-Host "  https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/" -ForegroundColor Cyan
