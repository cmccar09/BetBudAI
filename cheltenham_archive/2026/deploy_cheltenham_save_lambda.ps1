# ============================================================
# Deploy cheltenham-picks-save Lambda + EventBridge Schedule
# ============================================================
# Schedule:
#   Pre-festival  : EventBridge rate(30 minutes) → Lambda skips except 06:xx UTC
#   Race days     : EventBridge rate(30 minutes) → Lambda runs 11:00–18:30 UTC
#                   (10–13 March 2026)
# ============================================================

$ErrorActionPreference = "Stop"
$region    = "eu-west-1"
$account   = "813281204422"
$funcName  = "cheltenham-picks-save"
$roleArn   = "arn:aws:iam::${account}:role/BettingPicksAPIRole"
$ruleName  = "cheltenham-picks-schedule"
$tmpDir    = "$env:TEMP\cheltenham_lambda_build"

Write-Host "=== DEPLOY: $funcName ===" -ForegroundColor Cyan

# ── 1. Build zip ─────────────────────────────────────────────────────────────
Write-Host "`n[1/5] Building deployment package..." -ForegroundColor Yellow

if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
New-Item -ItemType Directory $tmpDir | Out-Null

# Main handler — Lambda expects lambda_function.lambda_handler
Copy-Item "save_cheltenham_picks.py"         "$tmpDir\lambda_function.py"
Copy-Item "cheltenham_deep_analysis_2026.py" "$tmpDir\"
Copy-Item "cheltenham_full_fields_2026.py"   "$tmpDir\"

# barrys package (scoring engine)
Copy-Item "barrys" "$tmpDir\barrys" -Recurse -Force

# Install Python dependencies needed by the Lambda (requests for Betfair API)
Write-Host "  Installing Python dependencies (requests)..." -ForegroundColor DarkYellow
& python -m pip install requests --target $tmpDir --quiet --upgrade
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: pip install failed" -ForegroundColor Red; exit 1 }
Write-Host "  Dependencies installed." -ForegroundColor Green

# Remove __pycache__ to keep zip small
Get-ChildItem $tmpDir -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force

# Zip it
$zipPath = "$env:TEMP\cheltenham_picks_save.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$tmpDir\*" -DestinationPath $zipPath -Force
$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
Write-Host "  Package: $sizeMB MB" -ForegroundColor Green

# ── 2. Create or update Lambda ───────────────────────────────────────────────
Write-Host "`n[2/5] Deploying Lambda ($funcName)..." -ForegroundColor Yellow

$funcExists = $false
try {
    aws lambda get-function --function-name $funcName --region $region 2>&1 | Out-Null
    $funcExists = ($LASTEXITCODE -eq 0)
} catch {}

if ($funcExists) {
    Write-Host "  Updating existing function..." -ForegroundColor DarkYellow
    aws lambda update-function-code `
        --function-name $funcName `
        --zip-file "fileb://$zipPath" `
        --region $region | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: update-function-code failed" -ForegroundColor Red; exit 1 }
} else {
    Write-Host "  Creating new function..." -ForegroundColor DarkYellow
    aws lambda create-function `
        --function-name $funcName `
        --runtime python3.12 `
        --handler lambda_function.lambda_handler `
        --role $roleArn `
        --zip-file "fileb://$zipPath" `
        --timeout 300 `
        --memory-size 512 `
        --region $region | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: create-function failed" -ForegroundColor Red; exit 1 }
    Write-Host "  Created." -ForegroundColor Green

    # Wait for active state
    Write-Host "  Waiting for Lambda to become Active..." -ForegroundColor DarkYellow
    Start-Sleep -Seconds 8
}
Write-Host "  Lambda deployed." -ForegroundColor Green

# ── 3. EventBridge rule: rate(30 minutes) ───────────────────────────────────
Write-Host "`n[3/5] Creating EventBridge rule ($ruleName)..." -ForegroundColor Yellow

aws events put-rule `
    --name $ruleName `
    --schedule-expression "rate(30 minutes)" `
    --state ENABLED `
    --description "Cheltenham picks save — every 30 min (Lambda filters by time/date)" `
    --region $region | Out-Null

if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: put-rule failed" -ForegroundColor Red; exit 1 }
Write-Host "  Rule created/updated." -ForegroundColor Green

# ── 4. Add Lambda as target ───────────────────────────────────────────────────
Write-Host "`n[4/5] Adding Lambda as EventBridge target..." -ForegroundColor Yellow

$funcArn = "arn:aws:lambda:${region}:${account}:function:${funcName}"

aws events put-targets `
    --rule $ruleName `
    --targets "[{`"Id`":`"1`",`"Arn`":`"$funcArn`",`"Input`":`"{}`"}]" `
    --region $region | Out-Null

# Allow EventBridge to invoke the Lambda
$existing = aws lambda get-policy --function-name $funcName --region $region 2>&1
if ($existing -notmatch "cheltenham-schedule-invoke") {
    aws lambda add-permission `
        --function-name $funcName `
        --statement-id "cheltenham-schedule-invoke" `
        --action "lambda:InvokeFunction" `
        --principal "events.amazonaws.com" `
        --source-arn "arn:aws:events:${region}:${account}:rule/$ruleName" `
        --region $region | Out-Null
    Write-Host "  Lambda permission granted to EventBridge." -ForegroundColor Green
} else {
    Write-Host "  Lambda permission already exists." -ForegroundColor DarkGreen
}

# ── 5. Summary ────────────────────────────────────────────────────────────────
Write-Host "`n[5/5] Verifying..." -ForegroundColor Yellow

$ruleDetails = aws events describe-rule --name $ruleName --region $region 2>&1 | ConvertFrom-Json
Write-Host "  Rule:     $($ruleDetails.Name)" -ForegroundColor White
Write-Host "  Schedule: $($ruleDetails.ScheduleExpression)" -ForegroundColor White
Write-Host "  State:    $($ruleDetails.State)" -ForegroundColor White

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Lambda : $funcArn" -ForegroundColor White
Write-Host "  Rule   : $ruleName — every 30 minutes" -ForegroundColor White
Write-Host ""
Write-Host "  Scheduling logic (in lambda_handler):" -ForegroundColor White
Write-Host "    Pre-festival    → runs only at 06:xx UTC (daily pick)" -ForegroundColor DarkGray
Write-Host "    Race days 10-13 March → runs 11:00–18:30 UTC every 30 min" -ForegroundColor DarkGray
Write-Host "    Post-festival   → skips (no save needed)" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Manual test:" -ForegroundColor White
Write-Host "    aws lambda invoke --function-name $funcName --region $region /tmp/out.json" -ForegroundColor DarkGray

# Clean up temp
Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
