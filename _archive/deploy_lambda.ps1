# Deploy updated Lambda function to AWS
# This updates the Lambda function that serves data to your Amplify frontend

Write-Host "=" * 80
Write-Host "Deploying Lambda Function to AWS"
Write-Host "=" * 80

# Create temporary deployment package directory
$deployDir = "lambda-deploy-temp"
if (Test-Path $deployDir) {
    Remove-Item -Recurse -Force $deployDir
}
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy Lambda function
Write-Host "`nCopying Lambda function..."
Copy-Item lambda_function.py "$deployDir/lambda_function.py"

# Create ZIP package
Write-Host "Creating deployment package..."
$zipFile = "lambda_deployment.zip"
if (Test-Path $zipFile) {
    Remove-Item -Force $zipFile
}

Compress-Archive -Path "$deployDir/*" -DestinationPath $zipFile

# Get Lambda function name from AWS
Write-Host "`nLooking for Lambda function..."
$functions = aws lambda list-functions --region eu-west-1 --query "Functions[?Runtime=='python3.12' || Runtime=='python3.11' || Runtime=='python3.10'].FunctionName" --output json | ConvertFrom-Json

Write-Host "Found Lambda functions:"
$functions | ForEach-Object { Write-Host "  - $_" }

# Try to find the picks API function
$functionName = $functions | Where-Object { $_ -like "*pick*" -or $_ -like "*api*" -or $_ -like "*betting*" } | Select-Object -First 1

if (-not $functionName) {
    Write-Host "`nNo Lambda function found automatically. Please specify:"
    Write-Host "Available functions:"
    $functions | ForEach-Object { Write-Host "  - $_" }
    $functionName = Read-Host "`nEnter Lambda function name"
}

Write-Host "`nDeploying to function: $functionName"

# Upload to AWS Lambda
Write-Host "Uploading to AWS Lambda..."
aws lambda update-function-code `
    --function-name $functionName `
    --zip-file fileb://lambda_deployment.zip `
    --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Lambda function updated successfully!" -ForegroundColor Green
    Write-Host "`nThe changes include:" -ForegroundColor Cyan
    Write-Host "  1. Query both today and yesterday's bet_date"
    Write-Host "  2. Filter for today's race times"
    Write-Host "  3. Handle UPPERCASE outcomes WON PLACED LOST"
    Write-Host "  4. Show ALL today's races not just future"
    Write-Host "  5. Calculate proper ROI from completed races"
    Write-Host "`nYour UI should now show today's 3 results!" -ForegroundColor Green
    Write-Host "Visit: https://main.d2hmpykfsdweob.amplifyapp.com/" -ForegroundColor Cyan
} else {
    Write-Host "`n✗ Deployment failed!" -ForegroundColor Red
    Write-Host "Check AWS credentials and permissions"
}

# Cleanup
Write-Host "`nCleaning up..."
Remove-Item -Recurse -Force $deployDir

Write-Host "`nDone Deployment package saved as $zipFile"
