#!/usr/bin/env pwsh
# Quick status check for betting system
# Run this anytime to verify everything is working

$ErrorActionPreference = "SilentlyContinue"

Write-Host "`n╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      BETTING SYSTEM STATUS - $(Get-Date -Format 'HH:mm:ss')     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Check scheduled task
$taskInfo = Get-ScheduledTaskInfo "BettingWorkflow_Continuous"
$taskState = (Get-ScheduledTask "BettingWorkflow_Continuous").State
Write-Host "⏰ SCHEDULED TASK:" -ForegroundColor Yellow
Write-Host "   Status: $taskState" -ForegroundColor $(if ($taskState -eq "Ready") { "Green" } else { "Red" })
Write-Host "   Last Run: $($taskInfo.LastRunTime.ToString('HH:mm'))" -ForegroundColor White
Write-Host "   Next Run: $($taskInfo.NextRunTime.ToString('HH:mm'))" -ForegroundColor White
Write-Host "   Result: $(if ($taskInfo.LastTaskResult -eq 0) { 'Success ✓' } else { 'Error' })" -ForegroundColor $(if ($taskInfo.LastTaskResult -eq 0) { "Green" } else { "Red" })

# 2. Check DynamoDB picks
Write-Host "`n📊 DYNAMODB PICKS:" -ForegroundColor Yellow
$dbCheck = python -c @"
import boto3
from datetime import datetime
table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': today})
items = response['Items']
now = datetime.now()
future = [i for i in items if i.get('race_time', '').replace('Z', '+00:00') > now.isoformat()]
print(f'{len(future)} future')
"@
Write-Host "   Future picks: $dbCheck" -ForegroundColor Green

# 3. Check API Gateway
Write-Host "`n🌐 API GATEWAY:" -ForegroundColor Yellow
try {
    $api = Invoke-RestMethod -Uri "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today" -TimeoutSec 5
    Write-Host "   Status: ✓ Online" -ForegroundColor Green
    Write-Host "   Picks: $($api.count)" -ForegroundColor $(if ($api.count -gt 0) { "Green" } else { "Yellow" })
} catch {
    Write-Host "   Status: ✗ Error" -ForegroundColor Red
}

# 4. Check if workflow is running
Write-Host "`n🔄 CURRENT WORKFLOW:" -ForegroundColor Yellow
$runningJob = Get-Job | Where-Object {$_.State -eq 'Running'}
if ($runningJob) {
    $runtime = ((Get-Date) - $runningJob.PSBeginTime).TotalMinutes
    Write-Host "   Status: RUNNING ($($runtime.ToString('0.0')) min)" -ForegroundColor Yellow
} else {
    Write-Host "   Status: Idle (waiting for next scheduled run)" -ForegroundColor Gray
}

Write-Host "`n═══════════════════════════════════════════════════`n" -ForegroundColor Cyan
