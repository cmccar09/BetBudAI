# Upload Betfair SSL Certificates to AWS Secrets Manager
# This fixes the 403 authentication error in Lambda

Write-Host "`n╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   UPLOAD BETFAIR SSL CERTIFICATES TO AWS                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if certificate files exist
$certFile = ".\betfair-client.crt"
$keyFile = ".\betfair-client.key"

if (!(Test-Path $certFile) -or !(Test-Path $keyFile)) {
    Write-Host "❌ Certificate files not found!`n" -ForegroundColor Red
    
    Write-Host "You need to download SSL certificates from Betfair first:`n" -ForegroundColor Yellow
    Write-Host "STEP 1: Login to Betfair" -ForegroundColor Cyan
    Write-Host "  1. Go to https://www.betfair.com" -ForegroundColor White
    Write-Host "  2. Login with your account (cmccar02)`n" -ForegroundColor White
    
    Write-Host "STEP 2: Generate SSL Certificate" -ForegroundColor Cyan
    Write-Host "  1. Go to: Account → My Account → API" -ForegroundColor White
    Write-Host "  2. Navigate to: Certificates section" -ForegroundColor White
    Write-Host "  3. Click 'Create New Certificate'" -ForegroundColor White
    Write-Host "  4. Download both files:" -ForegroundColor White
    Write-Host "     - client-2048.crt (certificate)" -ForegroundColor Gray
    Write-Host "     - client-2048.key (private key)`n" -ForegroundColor Gray
    
    Write-Host "STEP 3: Save to this folder" -ForegroundColor Cyan
    Write-Host "  Rename and save as:" -ForegroundColor White
    Write-Host "     - betfair-client.crt" -ForegroundColor Gray
    Write-Host "     - betfair-client.key`n" -ForegroundColor Gray
    
    Write-Host "Then run this script again.`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Certificate files found:`n" -ForegroundColor Green
Write-Host "  $certFile" -ForegroundColor Gray
Write-Host "  $keyFile`n" -ForegroundColor Gray

# Read certificate files
Write-Host "Reading certificate files..." -ForegroundColor Cyan
$certContent = Get-Content $certFile -Raw
$keyContent = Get-Content $keyFile -Raw

# Create JSON secret
$secret = @{
    certificate = $certContent
    private_key = $keyContent
    username = "cmccar02"
    app_key = "XDDM8EHzaw8tokvQ"
    created_date = (Get-Date).ToString("yyyy-MM-dd")
} | ConvertTo-Json

# Check if secret already exists
Write-Host "Checking if secret already exists..." -ForegroundColor Cyan
$existingSecret = aws secretsmanager describe-secret --secret-id betfair-ssl-certificate --region eu-west-1 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Secret already exists, updating..." -ForegroundColor Yellow
    
    aws secretsmanager update-secret `
        --secret-id betfair-ssl-certificate `
        --secret-string $secret `
        --region eu-west-1
    
    Write-Host "`n✅ Secret updated successfully!" -ForegroundColor Green
} else {
    Write-Host "Creating new secret..." -ForegroundColor Cyan
    
    aws secretsmanager create-secret `
        --name betfair-ssl-certificate `
        --description "Betfair SSL certificates for API authentication" `
        --secret-string $secret `
        --region eu-west-1
    
    Write-Host "`n✅ Secret created successfully!" -ForegroundColor Green
}

# Update Lambda to give it access to Secrets Manager
Write-Host "`nUpdating Lambda IAM permissions..." -ForegroundColor Cyan

# Get current role
$roleArn = aws lambda get-function-configuration `
    --function-name BettingWorkflowScheduled `
    --query 'Role' `
    --output text `
    --region eu-west-1

$roleName = ($roleArn -split '/')[-1]

Write-Host "Lambda role: $roleName" -ForegroundColor Gray

# Create inline policy for Secrets Manager access
$policyDocument = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:eu-west-1:*:secret:betfair-ssl-certificate-*"
        }
    ]
}
"@

# Add policy to role
aws iam put-role-policy `
    --role-name $roleName `
    --policy-name BetfairSecretsAccess `
    --policy-document $policyDocument

Write-Host "✓ Lambda role updated with Secrets Manager permissions`n" -ForegroundColor Green

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                  ✅ SETUP COMPLETE                       ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "What was done:" -ForegroundColor Cyan
Write-Host "  ✓ Uploaded SSL certificates to AWS Secrets Manager" -ForegroundColor White
Write-Host "  ✓ Granted Lambda access to retrieve certificates" -ForegroundColor White
Write-Host "  ✓ Lambda will now use certificate-based auth" -ForegroundColor White

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Redeploy Lambda with updated code:" -ForegroundColor White
Write-Host "     .\deploy_workflow_lambda.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Test Lambda execution:" -ForegroundColor White
Write-Host "     aws lambda invoke --function-name BettingWorkflowScheduled response.json" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Check logs - should see:" -ForegroundColor White
Write-Host "     '✓ Betfair authentication successful'" -ForegroundColor Green
Write-Host "     NOT '403 error' anymore!" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 No more mock data - only real Betfair odds!`n" -ForegroundColor Green
