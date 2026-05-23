# =============================================================================
# build_analysis_lambda.ps1
# Canonical build + deploy script for the surebet-analysis Lambda.
#
# ALWAYS run this script to deploy analysis changes — never edit the zip
# directly. This is the single source of truth for what goes into the Lambda.
#
# Usage:
#   .\scripts\build_analysis_lambda.ps1            # build + deploy
#   .\scripts\build_analysis_lambda.ps1 -DryRun    # build only, don't deploy
# =============================================================================

param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ROOT = Split-Path $PSScriptRoot -Parent
$ZIP  = "$ROOT\_analysis_lambda.zip"

# Canonical source file map: zip entry name → source path (relative to repo root)
# THIS IS THE SINGLE AUTHORITATIVE LIST. If you add a new source file to the
# analysis Lambda, add it here — do not manually patch the zip.
$FILES = [ordered]@{
    'sf_analysis.py'              = 'step_functions\lambdas\sf_analysis.py'
    'complete_daily_analysis.py'  = 'complete_daily_analysis.py'
    'comprehensive_pick_logic.py' = 'comprehensive_pick_logic.py'
    'form_enricher.py'            = 'form_enricher.py'
    'betfair_odds_fetcher.py'     = 'betfair_odds_fetcher.py'
    'notify_picks.py'             = 'notify_picks.py'
    'weather_going_inference.py'  = 'backend\utils\weather_going_inference.py'
}

Write-Host ""
Write-Host "============================================================"
Write-Host "  surebet-analysis Lambda build"
Write-Host "  Zip : $ZIP"
Write-Host "  Mode: $(if ($DryRun) { 'DRY RUN (no deploy)' } else { 'BUILD + DEPLOY' })"
Write-Host "============================================================"

# Verify all source files exist before touching the zip
$missing = @()
foreach ($entry in $FILES.GetEnumerator()) {
    $src = Join-Path $ROOT $entry.Value
    if (-not (Test-Path $src)) {
        $missing += "  MISSING: $($entry.Value)"
    }
}
if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR — source files missing:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

if (-not (Test-Path $ZIP)) {
    Write-Host "ERROR — base zip not found: $ZIP" -ForegroundColor Red
    Write-Host "The zip must exist with Python dependencies already bundled." -ForegroundColor Yellow
    exit 1
}

# Update the zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipArchive = [System.IO.Compression.ZipFile]::Open($ZIP, 'Update')

foreach ($entry in $FILES.GetEnumerator()) {
    $zipName = $entry.Key
    $srcPath = Join-Path $ROOT $entry.Value

    $existing = $zipArchive.Entries | Where-Object { $_.FullName -eq $zipName }
    if ($existing) { $existing.Delete() }

    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $zipArchive, $srcPath, $zipName
    ) | Out-Null

    $size = (Get-Item $srcPath).Length
    Write-Host ("  {0,-36} <- {1}  ({2:N0} bytes)" -f $zipName, $entry.Value, $size)
}

$zipArchive.Dispose()
Write-Host ""
Write-Host "Zip updated." -ForegroundColor Green

if ($DryRun) {
    Write-Host "DRY RUN — skipping deploy." -ForegroundColor Yellow
    exit 0
}

# Deploy
Write-Host "Deploying to surebet-analysis (eu-west-1)..."
$result = aws lambda update-function-code `
    --function-name surebet-analysis `
    --zip-file "fileb://$ZIP" `
    --region eu-west-1 `
    --query "FunctionName" `
    --output text 2>&1

Write-Host "Deployed: $result" -ForegroundColor Green
Write-Host ""
Write-Host "To verify: invoke the Lambda with today's S3 key and check picks_count > 0"
