# Deploy Stripe Lambda Functions for SureBet Mobile App

Write-Host "🚀 Deploying Stripe Lambda Functions" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# Activate virtual environment
Write-Host "Activating Python environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install stripe package
Write-Host "`nInstalling Stripe package..." -ForegroundColor Yellow
pip install stripe --quiet

# Create deployment packages
$lambdas = @(
    @{Name="lambda_stripe_create_customer"; File="lambda_stripe_create_customer.py"},
    @{Name="lambda_stripe_create_subscription"; File="lambda_stripe_create_subscription.py"},
    @{Name="lambda_stripe_webhook"; File="lambda_stripe_webhook.py"}
)

$tempDir = "lambda_packages"
New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

foreach ($lambda in $lambdas) {
    Write-Host "`n📦 Packaging $($lambda.Name)..." -ForegroundColor Cyan
    
    $packageDir = Join-Path $tempDir $lambda.Name
    New-Item -ItemType Directory -Force -Path $packageDir | Out-Null
    
    # Copy Lambda function
    Copy-Item $lambda.File -Destination (Join-Path $packageDir "lambda_function.py")
    
    # Install dependencies to package directory
    pip install stripe boto3 -t $packageDir --quiet
    
    # Create ZIP file
    $zipFile = "$($lambda.Name).zip"
    if (Test-Path $zipFile) { Remove-Item $zipFile }
    
    Compress-Archive -Path "$packageDir\*" -DestinationPath $zipFile
    
    Write-Host "   ✅ Created $zipFile" -ForegroundColor Green
}

Write-Host "`n`n📋 DEPLOYMENT INSTRUCTIONS" -ForegroundColor Yellow
Write-Host "========================`n" -ForegroundColor Yellow

Write-Host "1. Go to AWS Lambda Console: https://console.aws.amazon.com/lambda/`n" -ForegroundColor White

Write-Host "2. Create 3 Lambda functions with these settings:`n" -ForegroundColor White

foreach ($lambda in $lambdas) {
    Write-Host "   📌 $($lambda.Name)" -ForegroundColor Cyan
    Write-Host "      - Runtime: Python 3.11 or later" -ForegroundColor Gray
    Write-Host "      - Architecture: x86_64" -ForegroundColor Gray
    Write-Host "      - Upload: $($lambda.Name).zip" -ForegroundColor Gray
    Write-Host "      - Handler: lambda_function.lambda_handler" -ForegroundColor Gray
    Write-Host "      - Timeout: 30 seconds" -ForegroundColor Gray
    Write-Host "      - Memory: 256 MB`n" -ForegroundColor Gray
}

Write-Host "3. Set Environment Variables for ALL functions:`n" -ForegroundColor White
Write-Host "   STRIPE_SECRET_KEY = sk_test_your_key_here" -ForegroundColor Yellow
Write-Host "   STRIPE_WEBHOOK_SECRET = whsec_your_secret_here (webhook function only)`n" -ForegroundColor Yellow

Write-Host "4. Add DynamoDB permissions to each Lambda's IAM role:`n" -ForegroundColor White
Write-Host "   - dynamodb:GetItem" -ForegroundColor Gray
Write-Host "   - dynamodb:PutItem" -ForegroundColor Gray
Write-Host "   - dynamodb:UpdateItem" -ForegroundColor Gray
Write-Host "   - dynamodb:Scan" -ForegroundColor Gray
Write-Host "   - Resource: arn:aws:dynamodb:eu-west-1:*:table/SureBetUsers`n" -ForegroundColor Gray

Write-Host "5. Create Function URLs for API access:`n" -ForegroundColor White
Write-Host "   - lambda_stripe_create_customer → POST /api/auth/register" -ForegroundColor Gray
Write-Host "   - lambda_stripe_create_subscription → POST /api/subscription/create" -ForegroundColor Gray
Write-Host "   - lambda_stripe_webhook → POST /stripe/webhook`n" -ForegroundColor Gray

Write-Host "`n✅ Lambda packages ready for deployment!" -ForegroundColor Green
Write-Host "`n📦 Files created:" -ForegroundColor Cyan
Get-ChildItem *.zip | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor White }

Write-Host "`n🔗 Next: Set up Stripe account (see STRIPE_SETUP_GUIDE.md)" -ForegroundColor Yellow
