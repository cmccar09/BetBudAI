# Deploy Enhanced Lambda Functions
# =================================
# Packages and deploys the enhanced pick selector to Lambda

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DEPLOYING ENHANCED BETTING STRATEGY" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$Region = "eu-west-1"
$FunctionNameAnalysis = "surebet-analysis"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Step 1: Create deployment package
Write-Host "[Step 1/5] Creating deployment package..." -ForegroundColor Yellow

$DeployDir = "lambda_deploy_enhanced"
if (Test-Path $DeployDir) {
    Remove-Item -Recurse -Force $DeployDir
}
New-Item -ItemType Directory -Path $DeployDir | Out-Null

# Copy Lambda functions
Write-Host "  - Copying Lambda handlers..."
Copy-Item -Path "backend\lambda\*" -Destination "$DeployDir\" -Recurse -Force

# Copy enhanced core modules
Write-Host "  - Copying enhanced core modules..."
New-Item -ItemType Directory -Path "$DeployDir\backend\core" -Force | Out-Null
Copy-Item -Path "backend\core\ev_calculator.py" -Destination "$DeployDir\backend\core\"
Copy-Item -Path "backend\core\race_quality_filter.py" -Destination "$DeployDir\backend\core\"
Copy-Item -Path "backend\core\enhanced_pick_selector.py" -Destination "$DeployDir\backend\core\"

# Copy scoring modules if they exist
if (Test-Path "backend\core\scoring") {
    Write-Host "  - Copying scoring modules..."
    Copy-Item -Path "backend\core\scoring\*" -Destination "$DeployDir\backend\core\scoring\" -Recurse -Force
}

# Copy signals (Phase 1)
if (Test-Path "backend\core\signals") {
    Write-Host "  - Copying Phase 1 signals..."
    Copy-Item -Path "backend\core\signals\*" -Destination "$DeployDir\backend\core\signals\" -Recurse -Force
}

# Create __init__.py files
New-Item -ItemType File -Path "$DeployDir\backend\__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "$DeployDir\backend\core\__init__.py" -Force | Out-Null

Write-Host "✓ Deployment package created" -ForegroundColor Green
Write-Host ""

# Step 2: Create ZIP file
Write-Host "[Step 2/5] Creating ZIP archive..." -ForegroundColor Yellow

$ZipPath = Join-Path $ProjectRoot "enhanced_lambda.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

# Use .NET compression
Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Join-Path $ProjectRoot $DeployDir),
    $ZipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

Write-Host "✓ ZIP file created: enhanced_lambda.zip" -ForegroundColor Green
Write-Host ""

# Step 3: Test package locally
Write-Host "[Step 3/5] Testing package integrity..." -ForegroundColor Yellow

$TestScript = @'
import sys
import zipfile

try:
    with zipfile.ZipFile('enhanced_lambda.zip', 'r') as z:
        files = z.namelist()

        # Check required files exist
        required = [
            'backend/core/ev_calculator.py',
            'backend/core/race_quality_filter.py',
            'backend/core/enhanced_pick_selector.py',
            'sf_analysis.py'
        ]

        missing = []
        for req in required:
            # Handle both forward and backslash
            if not any(req.replace('/', '\\') in f or req in f for f in files):
                missing.append(req)

        if missing:
            print(f"Missing files: {missing}")
            sys.exit(1)

        print(f"Package contains {len(files)} files")
        print("All required modules present")

except Exception as e:
    print(f"Validation failed: {e}")
    sys.exit(1)
'@

$TestScript | python

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Package validation failed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Package validated successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Deploy to AWS Lambda
Write-Host "[Step 4/5] Deploying to AWS Lambda..." -ForegroundColor Yellow
Write-Host "  Region: $Region"
Write-Host "  Function: $FunctionNameAnalysis"
Write-Host ""

# Check if AWS CLI is configured
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "✗ AWS CLI not configured. Please run 'aws configure'" -ForegroundColor Red
    exit 1
}

# Deploy analysis function
Write-Host "  Updating Lambda function code..."
aws lambda update-function-code `
    --function-name $FunctionNameAnalysis `
    --zip-file "fileb://enhanced_lambda.zip" `
    --region $Region `
    --no-cli-pager

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Lambda function updated successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Lambda deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 5: Update environment variables
Write-Host "[Step 5/5] Updating Lambda configuration..." -ForegroundColor Yellow

aws lambda update-function-configuration `
    --function-name $FunctionNameAnalysis `
    --region $Region `
    --environment "Variables={ENHANCED_SELECTOR_ENABLED=true,LOG_LEVEL=INFO}" `
    --timeout 300 `
    --memory-size 512 `
    --no-cli-pager

Write-Host "✓ Configuration updated" -ForegroundColor Green
Write-Host ""

# Cleanup
Write-Host "Cleaning up temporary files..."
Remove-Item -Recurse -Force $DeployDir

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  • Enhanced pick selector deployed"
Write-Host "  • EV calculator integrated"
Write-Host "  • Race quality filter active"
Write-Host "  • Max 5 picks enforced"
Write-Host "  • 2x 4/1+ requirement enforced"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test with: aws lambda invoke --function-name $FunctionNameAnalysis test-output.json"
Write-Host "  2. Check CloudWatch logs for '[surebet-analysis] Enhanced selection' messages"
Write-Host "  3. Verify picks include bet_tier, ev_pct, stake_units fields"
Write-Host "  4. Update UI to display new fields"
Write-Host ""
Write-Host "ZIP package saved at: $ZipPath" -ForegroundColor Yellow
Write-Host ""
