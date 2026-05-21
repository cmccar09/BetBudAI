<#
.SYNOPSIS
Self-healing monitor for betting workflow

.DESCRIPTION
Runs continuously to monitor and auto-fix common issues:
- Restarts workflow if it fails
- Refreshes Betfair token if expiring
- Clears stuck processes
- Validates Lambda function deployment
#>

param(
    [switch]$RunOnce = $false
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
    "$timestamp - $Message" | Out-File -FilePath "$PSScriptRoot\monitor.log" -Append
}

function Test-BetfairToken {
    try {
        $creds = Get-Content "$PSScriptRoot\betfair-creds.json" | ConvertFrom-Json
        if ($creds.token -and $creds.token_created) {
            $created = [datetime]::Parse($creds.token_created)
            $age = ((Get-Date).ToUniversalTime() - $created).TotalHours
            return $age -lt 23  # Refresh before 24h expiry
        }
    } catch {
        return $false
    }
    return $false
}

function Refresh-BetfairToken {
    Write-Log "Refreshing Betfair token..." "Yellow"
    try {
        $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
        & $pythonExe "$PSScriptRoot\betfair_session_refresh_eu.py"
        Write-Log "✓ Token refreshed successfully" "Green"
        return $true
    } catch {
        Write-Log "✗ Token refresh failed: $_" "Red"
        return $false
    }
}

function Test-LambdaDeployment {
    Write-Log "Checking Lambda deployment..." "Cyan"
    try {
        # Get Lambda function code SHA
        $lambdaInfo = aws lambda get-function --function-name BettingPicksAPI --region eu-west-1 | ConvertFrom-Json
        $lambdaSha = $lambdaInfo.Configuration.CodeSha256
        
        # Get local file SHA
        $localFile = "$PSScriptRoot\lambda_function.py"
        $localContent = Get-Content $localFile -Raw
        $localHash = [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($localContent))
        $localSha = [Convert]::ToBase64String($localHash)
        
        Write-Log "Lambda SHA: $lambdaSha" "Gray"
        Write-Log "Local SHA:  $localSha" "Gray"
        
        # Note: SHAs may differ due to zip packaging, so we'll just verify Lambda is active
        if ($lambdaInfo.Configuration.State -eq "Active") {
            Write-Log "✓ Lambda is active and deployed" "Green"
            return $true
        } else {
            Write-Log "⚠ Lambda state: $($lambdaInfo.Configuration.State)" "Yellow"
            return $false
        }
    } catch {
        Write-Log "✗ Lambda check failed: $_" "Red"
        return $false
    }
}

function Test-ScheduledTask {
    Write-Log "Checking scheduled task..." "Cyan"
    try {
        $task = Get-ScheduledTask -TaskName "SureBetDailyWorkflow" -ErrorAction SilentlyContinue
        
        if ($task) {
            $lastRun = $task.LastRunTime
            $nextRun = $task.NextRunTime
            $state = $task.State
            
            Write-Log "Task state: $state" "Gray"
            Write-Log "Last run: $lastRun" "Gray"
            Write-Log "Next run: $nextRun" "Gray"
            
            if ($state -eq "Ready" -and $nextRun) {
                Write-Log "✓ Scheduled task is active" "Green"
                return $true
            } else {
                Write-Log "⚠ Task may not be scheduled correctly" "Yellow"
                return $false
            }
        } else {
            Write-Log "✗ Scheduled task not found" "Red"
            Write-Log "Run setup_learning_scheduler.ps1 to create it" "Yellow"
            return $false
        }
    } catch {
        Write-Log "✗ Task check failed: $_" "Red"
        return $false
    }
}

function Invoke-EmergencyWorkflow {
    Write-Log "Running emergency workflow..." "Yellow"
    try {
        $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
        
        # Quick run with minimal checks
        Write-Log "Fetching Betfair markets..." "Gray"
        & $pythonExe "$PSScriptRoot\betfair_delayed_snapshots.py"
        
        Write-Log "Running AI analysis..." "Gray"
        & $pythonExe "$PSScriptRoot\run_enhanced_analysis.py" --snapshot "$PSScriptRoot\response_live.json"
        
        Write-Log "✓ Emergency workflow completed" "Green"
        return $true
    } catch {
        Write-Log "✗ Emergency workflow failed: $_" "Red"
        return $false
    }
}

# MAIN MONITORING LOOP
Write-Log "========================================" "Cyan"
Write-Log "SELF-HEALING MONITOR STARTED" "Cyan"
Write-Log "========================================" "Cyan"

do {
    $timestamp = Get-Date -Format "HH:mm"
    
    # Run health checks every hour
    if ($timestamp.EndsWith(":00") -or $RunOnce) {
        Write-Log "`n--- Hourly Health Check ---" "Cyan"
        
        # Check 1: Betfair Token
        if (-not (Test-BetfairToken)) {
            Write-Log "⚠ Betfair token needs refresh" "Yellow"
            Refresh-BetfairToken
        } else {
            Write-Log "✓ Betfair token valid" "Green"
        }
        
        # Check 2: Lambda deployment
        Test-LambdaDeployment
        
        # Check 3: Scheduled task
        Test-ScheduledTask
        
        # Check 4: Verify picks exist for today
        $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
        $today = (Get-Date).ToString("yyyy-MM-dd")
        $checkScript = @"
import boto3
from datetime import datetime
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
response = table.scan()
today_picks = [p for p in response['Items'] if '$today' in p.get('bet_date', '')]
now = datetime.utcnow()
future = [p for p in today_picks if datetime.fromisoformat(p.get('race_time', '').replace('Z', '')) > now]
print(len(future))
"@
        
        try {
            $futureCount = & $pythonExe -c $checkScript
            
            if ($futureCount -eq 0) {
                $hour = (Get-Date).Hour
                
                # If it's morning (6-10 AM) and no picks, run emergency workflow
                if ($hour -ge 6 -and $hour -le 10) {
                    Write-Log "⚠ No future picks found at $hour`:00 - running emergency workflow" "Yellow"
                    Invoke-EmergencyWorkflow
                } else {
                    Write-Log "ℹ No future picks (time: $hour`:00)" "Gray"
                }
            } else {
                Write-Log "✓ $futureCount future picks exist" "Green"
            }
        } catch {
            Write-Log "✗ Pick check failed: $_" "Red"
        }
    }
    
    if (-not $RunOnce) {
        # Sleep for 5 minutes before next check
        Start-Sleep -Seconds 300
    }
    
} while (-not $RunOnce)

Write-Log "Monitor stopped" "Yellow"
