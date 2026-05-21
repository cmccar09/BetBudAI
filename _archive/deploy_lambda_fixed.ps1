# Deploy updated Lambda function to AWS
Write-Host "Deploying Lambda Function to AWS"
Write-Host "================================="

# Create temporary deployment package directory
$deployDir = "lambda-deploy-temp"
if (Test-Path $deployDir) {
    Remove-Item -Recurse -Force $deployDir
}
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy Lambda function
Write-Host "Copying Lambda function..."
Copy-Item lambda_function.py "$deployDir/lambda_function.py"

# Create ZIP package
Write-Host "Creating deployment package..."
$zipFile = "lambda_deployment.zip"
if (Test-Path $zipFile) {
    Remove-Item -Force $zipFile
}

Compress-Archive -Path "$deployDir/*" -DestinationPath $zipFile

# Get Lambda function name from AWS
Write-Host "Looking for Lambda function..."
$functions = aws lambda list-functions --region eu-west-1 --query "Functions[?Runtime=='python3.12' || Runtime=='python3.11' || Runtime=='python3.10'].FunctionName" --output json | ConvertFrom-Json

Write-Host "Found Lambda functions:"
$functions | ForEach-Object { Write-Host "  -$_" }

# Try to find the picks API function
$functionName = $functions | Where-Object { $_ -like "*pick*" -or $_ -like "*api*" -or $_ -like "*betting*" } | Select-Object -First 1

if (-not $functionName) {
    Write-Host "No Lambda function found automatically"
    Write-Host "Available functions:"
    $functions | ForEach-Object { Write-Host "  - $_" }
    $functionName = Read-Host "Enter Lambda function name"
}

Write-Host "Deploying to function: $functionName"

# Upload to AWS Lambda
Write-Host "Uploading to AWS Lambda..."
aws lambda update-function-code --function-name $functionName --zip-file fileb://lambda_deployment.zip --region eu-west-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS Lambda function updated"
    Write-Host "Changes: Query yesterday data, Handle WON PLACED LOST outcomes, Show ALL races"
    Write-Host "Visit: https://main.d2hmpykfsdweob.amplifyapp.com/"
} else {
    Write-Host "FAILED Deployment error"
}

# Cleanup
Write-Host "Cleaning up..."
Remove-Item -Recurse -Force $deployDir

Write-Host "Done Deployment package: $zipFile"
