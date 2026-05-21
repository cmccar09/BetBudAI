#!/usr/bin/env pwsh
# Quick script to generate today's picks and save to DynamoDB

param(
    [string]$Sport = "horses"  # Default to horses - greyhounds disabled
)

$sportDisplay = if ($Sport -eq "horses") { "Horse Racing" } else { "Greyhound Racing 🐕" }

Write-Host "="*60
Write-Host "Generate $sportDisplay Picks"
Write-Host "="*60

# Step 0: Validate existing picks (remove invalid ones)
Write-Host ""
Write-Host "Step 0: Validating existing picks..." -ForegroundColor Cyan
& C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe validate_existing_picks.py

# Load Betfair credentials and set environment variables
if (Test-Path "./betfair-creds.json") {
    $creds = Get-Content "./betfair-creds.json" | ConvertFrom-Json
    $env:BETFAIR_APP_KEY = $creds.app_key
    $env:BETFAIR_SESSION = $creds.session_token
    Write-Host ""
    Write-Host "Betfair Credentials: Loaded ✓" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "WARNING: betfair-creds.json not found" -ForegroundColor Yellow
}

# Step 1: Check for API access (AWS Bedrock preferred, API keys as fallback)
$anthropicKey = $env:ANTHROPIC_API_KEY
$openaiKey = $env:OPENAI_API_KEY

# Check if AWS credentials are configured
$awsConfigured = $false
try {
    $awsTest = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        $awsConfigured = $true
    }
} catch {}

if (-not $awsConfigured -and -not $anthropicKey -and -not $openaiKey) {
    Write-Host ""
    Write-Host "ERROR: No LLM API access found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Option 1 (Recommended): Configure AWS credentials for Bedrock" -ForegroundColor Yellow
    Write-Host '  aws configure'
    Write-Host ""
    Write-Host "Option 2: Set an API key:" -ForegroundColor Yellow
    Write-Host '  $env:ANTHROPIC_API_KEY = "your-anthropic-key"'
    Write-Host '  $env:OPENAI_API_KEY = "your-openai-key"'
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "LLM Provider: " -NoNewline
if ($awsConfigured) {
    Write-Host "AWS Bedrock (Claude via AWS) ✓" -ForegroundColor Green
} elseif ($anthropicKey) {
    Write-Host "Anthropic Claude ✓" -ForegroundColor Green
} else {
    Write-Host "OpenAI GPT ✓" -ForegroundColor Green
}

# Step 2: Generate selections with prompt logic
Write-Host ""
Write-Host "Step 1: Fetching live Betfair odds ($sportDisplay)..." -ForegroundColor Cyan
Write-Host ""

$pythonExe = "C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe"
$snapshotFile = "./response_live.json"

# Fetch live data from Betfair API
& $pythonExe betfair_delayed_snapshots.py --out $snapshotFile --hours 24 --max_races 50 --sport $Sport

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to fetch Betfair data" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Generating selections using prompt.txt logic..." -ForegroundColor Cyan
Write-Host ""

& $pythonExe run_saved_prompt.py --prompt ./prompt.txt --snapshot $snapshotFile --out ./today_picks.csv --max_races 5

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to generate selections" -ForegroundColor Red
    exit 1
}

# Check if file was created
if (-not (Test-Path "./today_picks.csv")) {
    Write-Host ""
    Write-Host "ERROR: No picks file generated" -ForegroundColor Red
    Write-Host "This could mean:" -ForegroundColor Yellow
    Write-Host "  - No races meet the ROI threshold (>20%)" -ForegroundColor Yellow
    Write-Host "  - No Betfair data available" -ForegroundColor Yellow
    Write-Host "  - LLM call failed" -ForegroundColor Yellow
    exit 1
}

# Step 3: Save to DynamoDB
Write-Host ""
Write-Host "Step 2: Saving to DynamoDB (EU-WEST-1)..." -ForegroundColor Cyan
Write-Host ""

& "C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe" save_selections_to_dynamodb.py --selections ./today_picks.csv --region eu-west-1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to save to DynamoDB" -ForegroundColor Red
    Write-Host "Check AWS credentials with: aws sts get-caller-identity" -ForegroundColor Yellow
    exit 1
}

# Step 4: Verify in DynamoDB
Write-Host ""
Write-Host "Step 3: Verifying in DynamoDB..." -ForegroundColor Cyan
Write-Host ""

# Use Python to query DynamoDB (more reliable than AWS CLI in PowerShell)
$pythonCode = @'
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's picks
today = datetime.now().strftime('%Y-%m-%d')
response = table.scan()
items = [item for item in response.get('Items', []) if item.get('date', '').startswith(today)]

if items:
    print(f'\n✓ Found {len(items)} picks for today:\n')
    for item in items[:5]:
        horse = item.get('horse', 'Unknown')
        course = item.get('course', 'Unknown')
        bet_type = item.get('bet_type', 'WIN')
        roi = float(item.get('roi', 0))
        print(f'  • {horse} @ {course} - {bet_type} (ROI: {roi:.1%})')
    if len(items) > 5:
        print(f'  ... and {len(items)-5} more')
else:
    print('\n⚠ No picks found in DynamoDB for today')
    print('   This could mean:')
    print('   - No races met the 5% ROI threshold')
    print('   - save_selections_to_dynamodb.py failed silently')
'@

.venv\Scripts\python.exe -c $pythonCode

Write-Host ""
Write-Host "="*60
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "="*60
Write-Host ""
Write-Host "✓ Picks generated: ./today_picks.csv"
Write-Host "✓ Saved to DynamoDB: SureBetBets table"
Write-Host "✓ Your React app should now show today's picks"
Write-Host ""
