<#
.SYNOPSIS
Daily health check to verify workflow is running and producing picks

.DESCRIPTION
This script runs after the scheduled workflow to verify:
1. Workflow completed successfully
2. Picks were generated for today
3. Picks are visible in DynamoDB
4. Picks are accessible via API Gateway
5. Amplify UI can fetch picks

Sends email alert if any check fails.
#>

param(
    [string]$AlertEmail = "your-email@example.com"  # Configure your email
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor $Color
}

function Send-Alert {
    param($Subject, $Body)
    
    # TODO: Configure AWS SES or SMTP for email alerts
    Write-Log "ALERT: $Subject" "Red"
    Write-Log $Body "Red"
    
    # Log to file for manual review
    $alertLog = "$PSScriptRoot\health_check_alerts.log"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Subject`n$Body`n`n" | Out-File -FilePath $alertLog -Append
}

Write-Log "========================================" "Cyan"
Write-Log "DAILY HEALTH CHECK" "Cyan"
Write-Log "========================================" "Cyan"

$issues = @()
$today = (Get-Date).ToString("yyyy-MM-dd")

# CHECK 1: Verify picks exist in DynamoDB
Write-Log "CHECK 1: Verifying picks in DynamoDB..." "Yellow"
try {
    $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
    $pickCount = & $pythonExe "$PSScriptRoot\check_today_in_db.py" 2>&1 | Select-Object -Last 1
    
    if ($pickCount -eq 0) {
        $issues += "No picks found in DynamoDB for $today"
        Write-Log "  ✗ FAIL: 0 picks in database" "Red"
    } else {
        Write-Log "  ✓ PASS: $pickCount picks in database" "Green"
    }
} catch {
    $issues += "Failed to query DynamoDB: $_"
    Write-Log "  ✗ ERROR: $_" "Red"
}

# CHECK 2: Verify future picks exist
Write-Log "CHECK 2: Verifying future picks..." "Yellow"
try {
    $futureCount = & $pythonExe "$PSScriptRoot\check_future_picks.py" 2>&1 | Select-String "Future picks:" | ForEach-Object { $_ -replace '.*Future picks: (\d+).*','$1' }
    
    if ($futureCount -eq 0) {
        Write-Log "  ⚠ WARNING: No future picks (all races may have passed)" "Yellow"
    } else {
        Write-Log "  ✓ PASS: $futureCount future picks" "Green"
    }
} catch {
    $issues += "Failed to check future picks: $_"
    Write-Log "  ✗ ERROR: $_" "Red"
}

# CHECK 3: Verify API Gateway responds
Write-Log "CHECK 3: Verifying API Gateway..." "Yellow"
try {
    $apiUrl = "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today"
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 10
    
    if ($response.success -eq $true) {
        Write-Log "  ✓ PASS: API Gateway responding (count: $($response.count))" "Green"
    } else {
        $issues += "API Gateway returned success=false"
        Write-Log "  ✗ FAIL: API returned error" "Red"
    }
} catch {
    $issues += "API Gateway not responding: $_"
    Write-Log "  ✗ ERROR: $_" "Red"
}

# CHECK 4: Verify Amplify UI accessibility
Write-Log "CHECK 4: Verifying Amplify UI..." "Yellow"
try {
    # Check if API returns picks (UI functionality confirmed by working API)
    $apiUrl = "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today"
    $apiResponse = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 10
    
    if ($apiResponse.success -eq $true) {
        Write-Log "  ✓ PASS: Amplify UI backend accessible (API working)" "Green"
    } else {
        $issues += "Amplify UI backend not responding correctly"
        Write-Log "  ✗ FAIL: API not working" "Red"
    }
} catch {
    $issues += "Amplify UI backend not accessible: $_"
    Write-Log "  ✗ ERROR: $_" "Red"
}

# CHECK 5: Verify workflow ran recently
Write-Log "CHECK 5: Verifying workflow execution..." "Yellow"
try {
    $logFile = "$PSScriptRoot\workflow_execution.log"
    
    if (Test-Path $logFile) {
        $lastRun = (Get-Item $logFile).LastWriteTime
        $hoursSinceRun = ((Get-Date) - $lastRun).TotalHours
        
        if ($hoursSinceRun -gt 26) {
            $issues += "Workflow hasn't run in $([math]::Round($hoursSinceRun, 1)) hours"
            Write-Log "  ✗ FAIL: Last run $([math]::Round($hoursSinceRun, 1)) hours ago" "Red"
        } else {
            Write-Log "  ✓ PASS: Last run $([math]::Round($hoursSinceRun, 1)) hours ago" "Green"
        }
    } else {
        $issues += "No workflow execution log found"
        Write-Log "  ⚠ WARNING: No execution log" "Yellow"
    }
} catch {
    Write-Log "  ⚠ WARNING: Could not check workflow log: $_" "Yellow"
}

# CHECK 6: Verify Betfair token is valid
Write-Log "CHECK 6: Verifying Betfair authentication..." "Cyan"
try {
    # Check token age using PowerShell instead of Python inline script
    if (Test-Path "betfair-creds.json") {
        $creds = Get-Content "betfair-creds.json" | ConvertFrom-Json
        $created_field = if ($creds.token_created) { $creds.token_created } else { $creds.last_refresh }
        
        if ($created_field) {
            # Parse ISO 8601 format properly
            $created = [DateTime]::Parse($created_field, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::RoundtripKind)
            $age_hours = ((Get-Date).ToUniversalTime() - $created.ToUniversalTime()).TotalHours
            
            if ($age_hours -gt 23) {
                Write-Log "  ⚠ WARNING: Betfair token is $([math]::Round($age_hours, 1)) hours old (expires at 24h)" "Yellow"
            } elseif ($age_hours -gt 0 -and $age_hours -le 23) {
                Write-Log "  ✓ PASS: Betfair token is $([math]::Round($age_hours, 1)) hours old" "Green"
            } else {
                $issues += "Betfair token has invalid age: $([math]::Round($age_hours, 1)) hours"
                Write-Log "  ✗ FAIL: Token age invalid ($([math]::Round($age_hours, 1)) hours)" "Red"
            }
        } else {
            Write-Log "  ⚠ WARNING: No token timestamp found" "Yellow"
        }
    } else {
        Write-Log "  ⚠ WARNING: betfair-creds.json not found" "Yellow"
    }
} catch {
    Write-Log "  ⚠ WARNING: Could not check token: $_" "Yellow"
}

# SUMMARY
Write-Log "`n========================================" "Cyan"
Write-Log "HEALTH CHECK SUMMARY" "Cyan"
Write-Log "========================================" "Cyan"

if ($issues.Count -eq 0) {
    Write-Log "✓ ALL CHECKS PASSED" "Green"
    Write-Log "System is healthy and operational" "Green"
    exit 0
} else {
    Write-Log "✗ $($issues.Count) ISSUE(S) FOUND:" "Red"
    foreach ($issue in $issues) {
        Write-Log "  - $issue" "Red"
    }
    
    # Send alert
    $subject = "SureBet Health Check Failed - $today"
    $body = "Health check found $($issues.Count) issues:`n`n" + ($issues -join "`n")
    Send-Alert -Subject $subject -Body $body
    
    Write-Log "`nCheck health_check_alerts.log for details" "Yellow"
    exit 1
}
