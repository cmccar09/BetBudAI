# deploy_api.ps1 — Deploy BettingPicksAPI Lambda to BOTH functions
#
# The public API Gateway routes to 'betbudai-picks-api', NOT 'BettingPicksAPI'.
# Both functions must receive the same code on every deploy.
# NEVER deploy to only one — the browser will see stale code.
#
# Usage: .\scripts\deploy_api.ps1

param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$ROOT = Split-Path $PSScriptRoot -Parent
$SRC  = "$ROOT\backend\api\lambda_function.py"
$ZIP  = "$ROOT\backend\api\_api_lambda.zip"

Write-Host ""
Write-Host "====================================================="
Write-Host "  BettingPicksAPI deploy"
Write-Host "  Source: backend\api\lambda_function.py"
Write-Host "  Mode: $(if ($DryRun) { 'DRY RUN' } else { 'DEPLOY TO BOTH LAMBDAS' })"
Write-Host "====================================================="

if (-not (Test-Path $SRC)) {
    Write-Host "ERROR: $SRC not found" -ForegroundColor Red
    exit 1
}

# Zip the source
Add-Type -Assembly System.IO.Compression.FileSystem
if (Test-Path $ZIP) { Remove-Item $ZIP -Force }
$zip = [System.IO.Compression.ZipFile]::Open($ZIP, 'Create')
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $SRC, 'lambda_function.py') | Out-Null
$zip.Dispose()
$size = (Get-Item $ZIP).Length
Write-Host ""
Write-Host "  Zip built: $size bytes"

if ($DryRun) {
    Write-Host "  DRY RUN — skipping deploy"
    exit 0
}

# Deploy to both Lambdas
$LAMBDAS = @('BettingPicksAPI', 'betbudai-picks-api')
foreach ($fn in $LAMBDAS) {
    Write-Host ""
    Write-Host "  Deploying to $fn ..."
    aws lambda update-function-code `
        --function-name $fn `
        --zip-file "fileb://$ZIP" `
        --region eu-west-1 `
        --output text --query 'LastUpdateStatus' 2>&1
    # Wait for completion
    do {
        Start-Sleep -Seconds 2
        $status = aws lambda get-function-configuration `
            --function-name $fn --region eu-west-1 `
            --query 'LastUpdateStatus' --output text 2>&1
    } while ($status -eq 'InProgress')
    Write-Host "  $fn : $status"
}

Write-Host ""
Write-Host "Deploy complete. Both Lambdas updated."
Write-Host "Verify: curl https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/sports/golf"
