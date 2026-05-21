#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Scheduled betting workflow - runs every 2 hours to fetch fresh data and generate picks
.DESCRIPTION
    1. Learns from yesterday's results (if available)
    2. Fetches live Betfair data
    3. Enriches with Racing Post data (form, ratings, trainer stats)
    4. Tracks odds movements (steam/drift signals)
    5. Applies prompt.txt logic via LLM with enhanced data
    6. Generates and saves picks to DynamoDB
    7. Logs everything for review
#>

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = "$PSScriptRoot\logs"
$logFile = "$logDir\run_$timestamp.log"

# Create logs directory
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log {
    param($Message, $Color = "White")
    $timeStr = Get-Date -Format "HH:mm:ss"
    $logMsg = "[$timeStr] $Message"
    Write-Host $logMsg -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMsg
}

Write-Log "========================================" "Cyan"
Write-Log "SCHEDULED BETTING WORKFLOW" "Cyan"
Write-Log "========================================" "Cyan"

# Load Betfair credentials
if (Test-Path "$PSScriptRoot\betfair-creds.json") {
    $creds = Get-Content "$PSScriptRoot\betfair-creds.json" | ConvertFrom-Json
    $env:BETFAIR_APP_KEY = $creds.app_key
    $env:BETFAIR_SESSION = $creds.session_token
    Write-Log "Betfair credentials loaded" "Green"
} else {
    Write-Log "WARNING: betfair-creds.json not found" "Yellow"
}

# Check for LLM API access (AWS Bedrock preferred, API keys as fallback)
$awsConfigured = $false
try {
    $awsTest = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        $awsConfigured = $true
        Write-Log "LLM Provider: AWS Bedrock (Claude via AWS)" "Green"
    }
} catch {}

if (-not $awsConfigured -and -not $env:ANTHROPIC_API_KEY -and -not $env:OPENAI_API_KEY) {
    Write-Log "ERROR: No LLM API access found!" "Red"
    Write-Log "Option 1: AWS Bedrock - run 'aws configure' to set up credentials" "Yellow"
    Write-Log "Option 2: Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable" "Yellow"
    exit 1
} elseif ($env:ANTHROPIC_API_KEY) {
    Write-Log "LLM Provider: Anthropic Claude" "Green"
} elseif ($env:OPENAI_API_KEY) {
    Write-Log "LLM Provider: OpenAI GPT" "Green"
}

$pythonExe = "C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe"

# STEP 0: Refresh Betfair session token using CERTIFICATE authentication
$credFile = "$PSScriptRoot\betfair-creds.json"
if (Test-Path $credFile) {
    $credModTime = (Get-Item $credFile).LastWriteTime
    $hoursSinceRefresh = ((Get-Date) - $credModTime).TotalHours
    
    if ($hoursSinceRefresh -gt 4) {
        Write-Log "`nSTEP 0: Refreshing Betfair session token..." "Cyan"
        Write-Log "  Last refresh: $($hoursSinceRefresh.ToString('0.0')) hours ago" "Yellow"
        
        # Use certificate-based authentication (no password required)
        & $pythonExe "$PSScriptRoot\betfair_login_local.py" 2>&1 | Tee-Object -Append -FilePath $logFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  Session token refreshed successfully (certificate auth)" "Green"
            # Reload credentials
            $creds = Get-Content "$PSScriptRoot\betfair-creds.json" | ConvertFrom-Json
            $env:BETFAIR_APP_KEY = $creds.app_key
            $env:BETFAIR_SESSION = $creds.session_token
        } else {
            Write-Log "  WARNING: Certificate login failed - continuing with existing token" "Yellow"
        }
    } else {
        Write-Log "  Betfair token is fresh ($($hoursSinceRefresh.ToString('0.0')) hours old)" "Gray"
    }
}

# STEP 1: Learn from yesterday (if enabled)
$enableLearning = $true
if ($enableLearning) {
    Write-Log "`nSTEP 1: Learning from yesterday's results..." "Cyan"
    
    $yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
    $yesterdaySlug = (Get-Date).AddDays(-1).ToString("yyyyMMdd")
    $selectionsFile = "$PSScriptRoot\history\selections_$yesterdaySlug*.csv" | Get-Item -ErrorAction SilentlyContinue | Select-Object -Last 1
    $resultsFile = "$PSScriptRoot\history\results_$yesterdaySlug.json"
    
    if ($selectionsFile) {
        $selectionsPath = $selectionsFile.FullName
        
        if (Test-Path $resultsFile) {
            Write-Log "  Results already fetched, evaluating performance for $yesterday..." "Yellow"
            & $pythonExe "$PSScriptRoot\evaluate_performance.py" --selections $selectionsPath --results $resultsFile --apply --analyze-losers 2>&1 | Tee-Object -Append -FilePath $logFile
            
            Write-Log "  Regenerating learning insights from all historical data..." "Yellow"
            & $pythonExe "$PSScriptRoot\generate_learning_insights.py" 2>&1 | Tee-Object -Append -FilePath $logFile
        } else {
            Write-Log "  Fetching results for $yesterday..." "Yellow"
            & $pythonExe "$PSScriptRoot\fetch_race_results.py" --date $yesterday --selections $selectionsPath --out $resultsFile 2>&1 | Tee-Object -Append -FilePath $logFile
            
            if (Test-Path $resultsFile) {
                Write-Log "  Evaluating performance..." "Yellow"
                & $pythonExe "$PSScriptRoot\evaluate_performance.py" --selections $selectionsPath --results $resultsFile --apply --analyze-losers 2>&1 | Tee-Object -Append -FilePath $logFile
                
                Write-Log "  Regenerating learning insights from all historical data..." "Yellow"
                & $pythonExe "$PSScriptRoot\generate_learning_insights.py" 2>&1 | Tee-Object -Append -FilePath $logFile
            } else {
                Write-Log "  WARNING: Results fetch failed - markets may be too old (>24hrs)" "Yellow"
                Write-Log "  Skipping learning for this day" "Gray"
            }
        }
    } else {
        Write-Log "  No yesterday's selections found - skipping learning" "Gray"
    }
}

# STEP 1.5: Fetch TODAY's results at end of day (before markets expire)
$currentHour = (Get-Date).Hour
if ($currentHour -ge 22) {  # 10pm or later
    Write-Log "`nSTEP 1.5: Fetching today's results (end of day)..." "Cyan"
    
    $today = (Get-Date).ToString("yyyy-MM-dd")
    $todaySlug = Get-Date -Format "yyyyMMdd"
    $todaySelectionsFile = "$PSScriptRoot\history\selections_$todaySlug*.csv" | Get-Item -ErrorAction SilentlyContinue | Select-Object -Last 1
    $todayResultsFile = "$PSScriptRoot\history\results_$todaySlug.json"
    
    if ($todaySelectionsFile -and -not (Test-Path $todayResultsFile)) {
        Write-Log "  Fetching results while markets are still available..." "Yellow"
        & $pythonExe "$PSScriptRoot\fetch_race_results.py" --date $today --selections $todaySelectionsFile.FullName --out $todayResultsFile 2>&1 | Tee-Object -Append -FilePath $logFile
        
        if (Test-Path $todayResultsFile) {
            Write-Log "  Successfully saved today's results for tomorrow's learning" "Green"
        }
    } elseif (Test-Path $todayResultsFile) {
        Write-Log "  Today's results already fetched" "Gray"
    } else {
        Write-Log "  No selections made today - skipping results fetch" "Gray"
    }
}

# STEP 2: Generate today's picks
Write-Log "`nSTEP 2: Generating today's picks..." "Cyan"

# Determine time window based on current time
$currentTime = Get-Date -Format "HH:mm"
$currentHour = (Get-Date).Hour
$currentMinute = (Get-Date).Minute

# Balanced approach: 2-hour window for quality bet detection
# (Still fast ~2min runtime, but catches more opportunities early)
$analysisHours = 2
Write-Log "  Analyzing next $analysisHours hours (balanced depth + speed)" "Cyan"

# Enhanced analysis saves directly to today_picks.csv
$outputCsv = "$PSScriptRoot\today_picks.csv"

# Create history directory
New-Item -ItemType Directory -Force -Path "$PSScriptRoot\history" | Out-Null

Write-Log "  Fetching live Betfair odds (Horses only - Greyhounds disabled)..." "Yellow"

# Fetch live data from Betfair API - HORSES ONLY
$horseFile = "$PSScriptRoot\response_horses.json"
$snapshotFile = "$PSScriptRoot\response_live.json"

# Fetch horses
Write-Log "    - Horse Racing..." "Gray"
& $pythonExe "$PSScriptRoot\betfair_delayed_snapshots.py" --out $horseFile --hours 24 --max_races 50 --sport horses 2>&1 | Tee-Object -Append -FilePath $logFile

if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: Failed to fetch horse racing data" "Red"
    exit 1
}

# Skip greyhounds completely (disabled for speed)

# Use horses only (greyhounds disabled for speed)
Write-Log "    - Using horse racing only..." "Gray"
$horsesData = Get-Content $horseFile | ConvertFrom-Json
$horseRaces = $horsesData.races
$combined = @{
    timestamp = $horsesData.timestamp
    races = $horseRaces
    total_races = $horseRaces.Count
}
$combined | ConvertTo-Json -Depth 100 | Set-Content $snapshotFile
Write-Log "    - Total races: $($combined.total_races) (horses only, greyhounds disabled)" "Green"

# STEP 2.1: Skip enrichment steps temporarily - they keep crashing
Write-Log "  Using Betfair data only (enrichment disabled)" "Yellow"
$finalFile = $snapshotFile

Write-Log "  Applying ENHANCED multi-pass AI analysis to enriched markets..." "Yellow"
# Update snapshot env variable for enhanced analysis to use
$env:SNAPSHOT_FILE = $finalFile

# Run AI analysis with direct execution (no Start-Job to avoid output capture issues)
Write-Log "Running AI analysis..."
$analysisOutput = & $pythonExe "$PSScriptRoot\run_enhanced_analysis.py" --hours $analysisHours 2>&1
$analysisOutput | Tee-Object -Append -FilePath $logFile

if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: AI analysis failed with exit code $LASTEXITCODE" "Red"
    exit 1
}

# Check if we got picks (enhanced analysis saves to today_picks.csv)
if (Test-Path $outputCsv) {
    $pickCount = (Get-Content $outputCsv | Measure-Object -Line).Lines - 1
    
    if ($pickCount -gt 0) {
        Write-Log "  Generated $pickCount pick(s)" "Green"
        
        # STEP 3: Save to DynamoDB (EU-WEST-1, breakeven threshold, 10-min minimum lead time)
        Write-Log "`nSTEP 3: Saving to DynamoDB EU-WEST-1 (ROI: 0%+, Lead time: 10+ min)..." "Cyan"
        & $pythonExe "$PSScriptRoot\save_selections_to_dynamodb.py" --selections $outputCsv --min_roi 0.0 --region eu-west-1 --min_lead_time 10 --max_future_hours 24 2>&1 | Tee-Object -Append -FilePath $logFile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  Successfully saved to database" "Green"
        } else {
            Write-Log "  WARNING: Failed to save to DynamoDB" "Yellow"
        }
        
    } else {
        Write-Log "  No picks met ROI threshold" "Yellow"
    }
} else {
    Write-Log "  No output file generated" "Red"
}

# STEP 4: Send daily summary email (only once per day at 6pm)
$currentHour = (Get-Date).Hour
if ($currentHour -eq 18) {
    Write-Log "`nSTEP 4: Sending daily summary email..." "Cyan"
    
    $recipientEmail = $env:SUMMARY_EMAIL
    if (-not $recipientEmail) {
        Write-Log "  WARNING: SUMMARY_EMAIL environment variable not set" "Yellow"
        Write-Log "  Set SUMMARY_EMAIL to receive daily summaries" "Yellow"
    } else {
        # Check if we already sent today
        $todaySlug = Get-Date -Format "yyyyMMdd"
        $sentMarker = "$PSScriptRoot\logs\email_sent_$todaySlug.txt"
        
        if (-not (Test-Path $sentMarker)) {
            & $pythonExe "$PSScriptRoot\send_daily_summary.py" --to $recipientEmail 2>&1 | Tee-Object -Append -FilePath $logFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Log "  Daily summary sent to $recipientEmail" "Green"
                New-Item -ItemType File -Path $sentMarker -Force | Out-Null
            } else {
                Write-Log "  WARNING: Failed to send email" "Yellow"
            }
        } else {
            Write-Log "  Daily summary already sent today" "Gray"
        }
    }
}

# Summary
Write-Log "`n========================================" "Cyan"
Write-Log "WORKFLOW COMPLETE" "Green"
Write-Log "========================================" "Cyan"
Write-Log "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Cyan"
Write-Log "Log file: $logFile" "Cyan"
Write-Log "========================================" "Cyan"
# Create execution marker for health checks
$executionLog = "$PSScriptRoot\workflow_execution.log"
$executionTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"$executionTime - Workflow completed successfully" | Out-File -FilePath $executionLog

# Run health check (if available)
if (Test-Path "$PSScriptRoot\daily_health_check.ps1") {
    Write-Log "`nRunning post-workflow health check..." "Cyan"
    try {
        & "$PSScriptRoot\daily_health_check.ps1"
        if ($LASTEXITCODE -eq 0) {
            Write-Log "[OK] Health check passed" "Green"
        } else {
            Write-Log "[WARNING] Health check found issues - check logs" "Yellow"
        }
    } catch {
        Write-Log "[WARNING] Health check failed to run: $_" "Yellow"
    }
}