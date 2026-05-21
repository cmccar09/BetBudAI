#!/usr/bin/env pwsh
# Deploy Racing Post Scraper to AWS Lambda

Write-Host "`n📦 Creating Racing Post Scraper Lambda package...`n" -ForegroundColor Cyan

# Create package directory
$pkgDir = "scraper-package"
if (Test-Path $pkgDir) { Remove-Item -Recurse -Force $pkgDir }
New-Item -ItemType Directory -Path $pkgDir | Out-Null

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install beautifulsoup4 requests -t $pkgDir --quiet

Write-Host "Copying scraper..." -ForegroundColor Yellow
Copy-Item racing_post_scraper.py $pkgDir/lambda_function.py

# Create ZIP
$zipFile = "racing-post-scraper.zip"
if (Test-Path $zipFile) { Remove-Item -Force $zipFile }
Compress-Archive -Path "$pkgDir\*" -DestinationPath $zipFile

$size = (Get-Item $zipFile).Length / 1MB
Write-Host "`n✅ Created $zipFile ($([math]::Round($size,2)) MB)" -ForegroundColor Green

# Check if Lambda exists
$lambdaExists = aws lambda get-function --function-name RacingPostScraper --region eu-west-1 2>$null

if ($lambdaExists) {
    Write-Host "`nUpdating existing Lambda..." -ForegroundColor Yellow
    aws lambda update-function-code --function-name RacingPostScraper --region eu-west-1 --zip-file "fileb://$zipFile" --query 'FunctionName' --output text
} else {
    Write-Host "`nCreating new Lambda function..." -ForegroundColor Yellow
    
    # Get IAM role ARN (reuse betting role)
    $roleArn = (aws iam get-role --role-name betting-eu-role 2>$null | ConvertFrom-Json).Role.Arn
    
    if (-not $roleArn) {
        Write-Host "❌ Role not found. Using default Lambda execution role..." -ForegroundColor Red
        $roleArn = "arn:aws:iam::813281204422:role/betting-eu-role"
    }
    
    aws lambda create-function `
        --function-name RacingPostScraper `
        --runtime python3.11 `
        --role $roleArn `
        --handler lambda_function.lambda_handler `
        --zip-file "fileb://$zipFile" `
        --timeout 60 `
        --memory-size 256 `
        --region eu-west-1 `
        --query 'FunctionName' --output text
}

# Cleanup
Remove-Item -Recurse -Force $pkgDir

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`nTest with:" -ForegroundColor Cyan
Write-Host "  aws lambda invoke --function-name RacingPostScraper --region eu-west-1 scraper-output.json" -ForegroundColor Gray

# Test immediately
Write-Host "`nTesting scraper..." -ForegroundColor Yellow
aws lambda invoke --function-name RacingPostScraper --region eu-west-1 scraper-test.json 2>&1 | Out-Null
Start-Sleep -Seconds 5

if (Test-Path scraper-test.json) {
    $result = Get-Content scraper-test.json -Raw | ConvertFrom-Json
    if ($result.statusCode -eq 200) {
        $body = $result.body
        Write-Host "`n✅ Scraper working! Updated: $($body.updated) bets" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  Check scraper-test.json for details" -ForegroundColor Yellow
    }
}
