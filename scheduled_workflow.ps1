# Scheduled Workflow — runs every 30 minutes via BettingWorkflow_Continuous task
# Chain:
#   1. Build/refresh SL racecard (if stale or missing for today)
#   2. Convert to response_horses.json + run comprehensive_workflow.py (pick generation)
#
# Results are captured separately by SureBet-Hourly-ResultsFetcher every 30 min.

$ErrorActionPreference = 'Continue'
$ScriptDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"
$Python    = "$ScriptDir\.venv\Scripts\python.exe"
$LogFile   = "$ScriptDir\logs\scheduled_workflow.log"

# Ensure logs dir exists
if (-not (Test-Path "$ScriptDir\logs")) { New-Item -ItemType Directory "$ScriptDir\logs" | Out-Null }

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

Log "=== scheduled_workflow.ps1 starting ==="
Set-Location $ScriptDir

# ── Step 1: Check if racecard cache is fresh for today ────────────────────────
$today     = (Get-Date).ToString("yyyy-MM-dd")
$cacheFile = "$ScriptDir\racecard_cache.json"
$needRebuild = $true

if (Test-Path $cacheFile) {
    $age = (Get-Date) - (Get-Item $cacheFile).LastWriteTime
    # Rebuild if cache is older than 2 hours OR doesn't contain today's date
    if ($age.TotalHours -lt 2) {
        $content = Get-Content $cacheFile -Raw
        if ($content -match $today) {
            $needRebuild = $false
            Log "Racecard cache is fresh (age: $([int]$age.TotalMinutes) min)"
        }
    }
}

if ($needRebuild) {
    Log "Building racecard for $today..."
    $env:PYTHONUTF8 = '1'
    & $Python -X utf8 sl_racecard_fetcher.py 2>&1 | ForEach-Object { Log "  [racecard] $_" }
    Log "Racecard build complete (exit: $LASTEXITCODE)"
}

# ── Step 2: Run pick generation via SL adapter ────────────────────────────────
Log "Running pick generation (sl_to_workflow_adapter.py)..."
$env:PYTHONUTF8 = '1'
& $Python -X utf8 sl_to_workflow_adapter.py 2>&1 | ForEach-Object { Log "  [workflow] $_" }
$exitCode = $LASTEXITCODE
Log "Pick generation complete (exit: $exitCode)"

Log "=== scheduled_workflow.ps1 done ==="
exit $exitCode
