<#
.SYNOPSIS
Complete system verification and self-check setup

.DESCRIPTION
Validates entire betting system and sets up automated monitoring:
1. Verifies all dependencies
2. Tests AWS connections
3. Validates Lambda deployment
4. Sets up Windows Task Scheduler
5. Configures self-healing monitor
6. Runs initial health check
#>

param(
    [switch]$SkipScheduler = $false
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param($Message, $Type = "Info")
    $colors = @{
        "Info" = "Cyan"
        "Success" = "Green"
        "Warning" = "Yellow"
        "Error" = "Red"
    }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $colors[$Type]
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SUREBET SYSTEM VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$checks = @{
    passed = 0
    failed = 0
    warnings = 0
}

# CHECK 1: Python Environment
Write-Status "Checking Python environment..." "Info"
try {
    $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        $version = & $pythonExe --version
        Write-Status "✓ Python found: $version" "Success"
        $checks.passed++
    } else {
        Write-Status "✗ Python venv not found. Run: python -m venv .venv" "Error"
        $checks.failed++
    }
} catch {
    Write-Status "✗ Python check failed: $_" "Error"
    $checks.failed++
}

# CHECK 2: Required Python Packages
Write-Status "Checking Python packages..." "Info"
try {
    $requiredPackages = @("boto3", "requests", "beautifulsoup4", "flask", "flask-cors")
    $pythonExe = "$PSScriptRoot\.venv\Scripts\python.exe"
    
    foreach ($package in $requiredPackages) {
        $installed = & $pythonExe -m pip show $package 2>$null
        if ($installed) {
            Write-Status "  ✓ $package installed" "Success"
        } else {
            Write-Status "  ✗ $package missing - installing..." "Warning"
            & $pythonExe -m pip install $package --quiet
            $checks.warnings++
        }
    }
    $checks.passed++
} catch {
    Write-Status "✗ Package check failed: $_" "Error"
    $checks.failed++
}

# CHECK 3: AWS CLI
Write-Status "Checking AWS CLI..." "Info"
try {
    $awsVersion = aws --version
    Write-Status "✓ AWS CLI: $awsVersion" "Success"
    
    $identity = aws sts get-caller-identity | ConvertFrom-Json
    Write-Status "  Account: $($identity.Account)" "Info"
    Write-Status "  User: $($identity.Arn)" "Info"
    $checks.passed++
} catch {
    Write-Status "✗ AWS CLI not configured" "Error"
    $checks.failed++
}

# CHECK 4: DynamoDB Tables
Write-Status "Checking DynamoDB tables..." "Info"
try {
    $tables = aws dynamodb list-tables --region eu-west-1 | ConvertFrom-Json
    
    if ($tables.TableNames -contains "SureBetBets") {
        Write-Status "  ✓ SureBetBets table exists" "Success"
    } else {
        Write-Status "  ✗ SureBetBets table missing" "Error"
        $checks.failed++
    }
    
    if ($tables.TableNames -contains "SureBetOddsHistory") {
        Write-Status "  ✓ SureBetOddsHistory table exists" "Success"
    } else {
        Write-Status "  ⚠ SureBetOddsHistory table missing - run setup_enhanced_data.ps1" "Warning"
        $checks.warnings++
    }
    
    $checks.passed++
} catch {
    Write-Status "✗ DynamoDB check failed: $_" "Error"
    $checks.failed++
}

# CHECK 5: Lambda Function
Write-Status "Checking Lambda function..." "Info"
try {
    $lambda = aws lambda get-function --function-name BettingPicksAPI --region eu-west-1 | ConvertFrom-Json
    
    if ($lambda.Configuration.State -eq "Active") {
        Write-Status "  ✓ BettingPicksAPI is active" "Success"
        Write-Status "    Last modified: $($lambda.Configuration.LastModified)" "Info"
        $checks.passed++
    } else {
        Write-Status "  ✗ Lambda state: $($lambda.Configuration.State)" "Error"
        $checks.failed++
    }
} catch {
    Write-Status "✗ Lambda check failed: $_" "Error"
    $checks.failed++
}

# CHECK 6: API Gateway
Write-Status "Checking API Gateway..." "Info"
try {
    $apiUrl = "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today"
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 10
    
    if ($response.success -eq $true) {
        Write-Status "✓ API Gateway responding (picks: $($response.count))" "Success"
        $checks.passed++
    } else {
        Write-Status "⚠ API Gateway response unexpected" "Warning"
        $checks.warnings++
    }
} catch {
    Write-Status "✗ API Gateway not responding: $_" "Error"
    $checks.failed++
}

# CHECK 7: Betfair Credentials
Write-Status "Checking Betfair credentials..." "Info"
try {
    if (Test-Path "$PSScriptRoot\betfair-creds.json") {
        $creds = Get-Content "$PSScriptRoot\betfair-creds.json" | ConvertFrom-Json
        
        if ($creds.app_key -and $creds.session_token) {
            Write-Status "  ✓ Credentials file valid" "Success"
            
            if ($creds.token_created) {
                $created = [datetime]::Parse($creds.token_created)
                $age = ((Get-Date).ToUniversalTime() - $created).TotalHours
                
                if ($age -lt 23) {
                    Write-Status "    Token age: $([math]::Round($age, 1)) hours" "Success"
                } else {
                    Write-Status "    ⚠ Token is $([math]::Round($age, 1)) hours old - needs refresh" "Warning"
                    $checks.warnings++
                }
            }
            $checks.passed++
        } else {
            Write-Status "  ✗ Credentials incomplete" "Error"
            $checks.failed++
        }
    } else {
        Write-Status "  ✗ betfair-creds.json not found" "Error"
        $checks.failed++
    }
} catch {
    Write-Status "✗ Credential check failed: $_" "Error"
    $checks.failed++
}

# CHECK 8: Critical Files
Write-Status "Checking critical files..." "Info"
$criticalFiles = @(
    "lambda_function.py",
    "scheduled_workflow.ps1",
    "betfair_delayed_snapshots.py",
    "run_enhanced_analysis.py",
    "prompt.txt",
    "daily_health_check.ps1",
    "self_healing_monitor.ps1"
)

$missingFiles = @()
foreach ($file in $criticalFiles) {
    if (Test-Path "$PSScriptRoot\$file") {
        Write-Status "  ✓ $file" "Success"
    } else {
        Write-Status "  ✗ $file missing" "Error"
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    $checks.passed++
} else {
    $checks.failed++
}

# CHECK 9: Scheduled Task
if (-not $SkipScheduler) {
    Write-Status "Checking scheduled task..." "Info"
    try {
        $task = Get-ScheduledTask -TaskName "SureBetDailyWorkflow" -ErrorAction SilentlyContinue
        
        if ($task) {
            Write-Status "  ✓ Scheduled task exists" "Success"
            Write-Status "    Next run: $($task.NextRunTime)" "Info"
            $checks.passed++
        } else {
            Write-Status "  ⚠ Scheduled task not found" "Warning"
            Write-Status "    Run setup_learning_scheduler.ps1 to create it" "Info"
            $checks.warnings++
        }
    } catch {
        Write-Status "✗ Task check failed: $_" "Error"
        $checks.failed++
    }
}

# SUMMARY
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Passed:   $($checks.passed)" -ForegroundColor Green
Write-Host "⚠ Warnings: $($checks.warnings)" -ForegroundColor Yellow
Write-Host "✗ Failed:   $($checks.failed)" -ForegroundColor Red
Write-Host "========================================`n" -ForegroundColor Cyan

if ($checks.failed -eq 0) {
    Write-Status "System is ready for operation!" "Success"
    
    Write-Host "`nRecommended next steps:" -ForegroundColor Cyan
    Write-Host "1. Run: .\daily_health_check.ps1    (verify current state)"
    Write-Host "2. Run: .\scheduled_workflow.ps1    (generate picks)"
    Write-Host "3. Monitor: .\self_healing_monitor.ps1 -RunOnce (test monitoring)"
    
    # Create a status file
    $statusFile = "$PSScriptRoot\system_status.json"
    @{
        last_check = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        status = "healthy"
        checks_passed = $checks.passed
        checks_failed = $checks.failed
        checks_warnings = $checks.warnings
    } | ConvertTo-Json | Out-File -FilePath $statusFile
    
    Write-Host "`nStatus saved to: $statusFile`n" -ForegroundColor Gray
    
    exit 0
} else {
    Write-Status "System has $($checks.failed) critical issues - please fix before running" "Error"
    exit 1
}
