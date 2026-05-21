#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Send daily email with betting picks
.DESCRIPTION
    Sends an email to charles.mccarthy@gmail.com with the day's betting picks at 2pm
#>

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = "$PSScriptRoot\logs"
$logFile = "$logDir\email_$timestamp.log"

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
Write-Log "SENDING DAILY EMAIL SUMMARY" "Cyan"
Write-Log "========================================" "Cyan"

$pythonExe = "C:/Users/charl/OneDrive/futuregenAI/Betting/.venv/Scripts/python.exe"
$emailRecipient = "charles.mccarthy@gmail.com"

Write-Log "Sending daily summary to: $emailRecipient" "Cyan"

# Run the email script
& $pythonExe "$PSScriptRoot\send_daily_summary.py" --to $emailRecipient 2>&1 | Tee-Object -Append -FilePath $logFile

if ($LASTEXITCODE -eq 0) {
    Write-Log "Email sent successfully!" "Green"
} else {
    Write-Log "Failed to send email. Check log for details." "Red"
    
    # Fallback: try with SMTP if SES failed
    Write-Log "Attempting fallback to SMTP..." "Yellow"
    & $pythonExe "$PSScriptRoot\send_daily_summary.py" --to $emailRecipient --use-smtp 2>&1 | Tee-Object -Append -FilePath $logFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Email sent via SMTP!" "Green"
    } else {
        Write-Log "Both SES and SMTP failed. Please check configuration." "Red"
    }
}

Write-Log "========================================" "Cyan"
Write-Log "Email workflow complete" "Cyan"
Write-Log "========================================" "Cyan"
