#!/usr/bin/env pwsh
# Monitor betting workflow and ensure picks are generated

param(
    [int]$WaitMinutes = 12  # Max time to wait for workflow completion
)

$startTime = Get-Date
Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      BETTING WORKFLOW MONITOR                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Check if workflow job is running
$job = Get-Job | Where-Object {$_.State -eq 'Running' -and $_.Name -like 'Job*'} | Select-Object -First 1

if ($job) {
    Write-Host "`n⏳ Workflow currently running..." -ForegroundColor Yellow
    Write-Host "   Started: $($job.PSBeginTime.ToString('HH:mm:ss'))" -ForegroundColor White
    Write-Host "   Waiting up to $WaitMinutes minutes for completion...`n" -ForegroundColor White
    
    # Wait for job to complete
    $timeout = $startTime.AddMinutes($WaitMinutes)
    while ((Get-Date) -lt $timeout) {
        $currentJob = Get-Job -Id $job.Id -ErrorAction SilentlyContinue
        
        if (-not $currentJob -or $currentJob.State -ne 'Running') {
            Write-Host "✓ Workflow completed!" -ForegroundColor Green
            break
        }
        
        $elapsed = ((Get-Date) - $job.PSBeginTime).TotalMinutes
        Write-Host "  Runtime: $($elapsed.ToString('0.0')) minutes..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    }
} else {
    Write-Host "`nℹ No workflow currently running" -ForegroundColor Yellow
}

# Check for today's picks in DynamoDB
Write-Host "`n📊 Checking DynamoDB for today's picks..." -ForegroundColor Cyan

$checkScript = @"
import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
now = datetime.now()

# Filter for future races only
future_picks = []
for item in items:
    race_time_str = item.get('race_time', '')
    if race_time_str:
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            if race_time.replace(tzinfo=None) > now:
                future_picks.append(item)
        except:
            pass

print(f'Total picks today: {len(items)}')
print(f'Future picks: {len(future_picks)}')
for pick in future_picks[:5]:
    print(f\"  - {pick['horse']} @ {pick['course']} {pick['race_time']}\")
"@

$checkScript | Out-File -FilePath "temp_check_picks.py" -Encoding UTF8
python temp_check_picks.py
Remove-Item "temp_check_picks.py" -ErrorAction SilentlyContinue

# Test API Gateway
Write-Host "`n🌐 Testing API Gateway endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod/picks/today" -Method GET
    Write-Host "   API Status: SUCCESS" -ForegroundColor Green
    Write-Host "   Picks count: $($response.count)" -ForegroundColor $(if ($response.count -gt 0) { "Green" } else { "Red" })
} catch {
    Write-Host "   API Status: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# Check scheduled task
Write-Host "`n⏰ Scheduled Task Status:" -ForegroundColor Cyan
$taskInfo = Get-ScheduledTask "BettingWorkflow_Continuous" -ErrorAction SilentlyContinue | Get-ScheduledTaskInfo
if ($taskInfo) {
    Write-Host "   Last Run: $($taskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "   Next Run: $($taskInfo.NextRunTime)" -ForegroundColor Yellow
    Write-Host "   Last Result: $(if ($taskInfo.LastTaskResult -eq 0) { 'Success ✓' } else { 'Error: ' + $taskInfo.LastTaskResult })" -ForegroundColor $(if ($taskInfo.LastTaskResult -eq 0) { "Green" } else { "Red" })
}

Write-Host "`n╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      MONITORING COMPLETE                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
