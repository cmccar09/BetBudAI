# Continuous Learning System Runner
# Runs every 30 minutes for 2 weeks

param(
    [int]$DurationDays = 14
)

$ErrorActionPreference = "Continue"
$scriptPath = $PSScriptRoot
$venvPath = Join-Path $scriptPath ".venv\Scripts\Activate.ps1"
$logFile = Join-Path $scriptPath "logs\continuous_learning.log"

# Ensure log directory exists
$logDir = Join-Path $scriptPath "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "="*80
Write-Log "CONTINUOUS LEARNING SYSTEM STARTED"
Write-Log "Duration: $DurationDays days"
Write-Log "="*80

# Activate virtual environment
& $venvPath

$endTime = (Get-Date).AddDays($DurationDays)
$cycleNumber = 0

while ((Get-Date) -lt $endTime) {
    $cycleNumber++
    
    Write-Log ""
    Write-Log "="*80
    Write-Log "CYCLE #$cycleNumber - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Log "="*80
    
    try {
        # Step 1: Fetch current race data
        Write-Log "Step 1: Fetching race data..."
        $fetchResult = & python betfair_odds_fetcher.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  ✓ Race data fetched"
        } else {
            Write-Log "  ⚠️ Race fetch had issues (continuing anyway)"
        }
        
        # Step 2: Analyze ALL races (not just picks)
        Write-Log "Step 2: Analyzing all UK/Ireland races..."
        $analyzeResult = & python analyze_all_races_comprehensive.py 2>&1
        
        # Only show detailed output if picks were found
        $pickLines = $analyzeResult | Select-String -Pattern "TODAY'S PICKS"
        if ($pickLines) {
            # Show full output when picks found
            Write-Log "  $analyzeResult"
        } else {
            # Just show summary for background learning
            $summaryLine = $analyzeResult | Select-String -Pattern "Background analysis"
            if ($summaryLine) {
                Write-Log "  $summaryLine"
            } else {
                Write-Log "  Background learning complete (no picks)"
            }
        }
        
        # Step 3: Fetch and process results
        Write-Log "Step 3: Processing completed races..."
        $resultsResult = & python automated_results_analyzer.py 2>&1
        # Only log if there were actual results processed
        $resultsLine = $resultsResult | Select-String -Pattern "learnings generated|results processed"
        if ($resultsLine) {
            Write-Log "  $resultsLine"
        } else {
            Write-Log "  No new results yet"
        }
        
        # Step 4: Update statistics every 10 cycles
        if ($cycleNumber % 10 -eq 0) {
            Write-Log "Step 4: Generating learning summary..."
            $summaryResult = & python generate_learning_summary.py 2>&1
            Write-Log "  $summaryResult"
        }
        
        # Check if we should continue
        $timeRemaining = $endTime - (Get-Date)
        Write-Log ""
        Write-Log "Time remaining: $($timeRemaining.Days) days, $($timeRemaining.Hours) hours"
        Write-Log "Cycles completed: $cycleNumber"
        
        # Wait 30 minutes before next cycle
        $nextRun = (Get-Date).AddMinutes(30)
        Write-Log "Next cycle: $($nextRun.ToString('HH:mm:ss'))"
        Write-Log ""
        
        Start-Sleep -Seconds 1800  # 30 minutes
        
    } catch {
        Write-Log "❌ Error in cycle: $_"
        Write-Log $_.Exception.StackTrace
        Write-Log "Waiting 5 minutes before retry..."
        Start-Sleep -Seconds 300
    }
}

Write-Log ""
Write-Log "="*80
Write-Log "CONTINUOUS LEARNING COMPLETED"
Write-Log "Total cycles: $cycleNumber"
Write-Log "Duration: $DurationDays days"
Write-Log "="*80
Write-Log ""
Write-Log "Generating final report..."
& python generate_final_learning_report.py

Write-Log "Learning system finished successfully"
