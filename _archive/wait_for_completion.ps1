#!/usr/bin/env pwsh
# Wait for workflow completion and verify picks were generated

Write-Host "⏳ Waiting for workflow AI analysis to complete..." -ForegroundColor Yellow
Write-Host "   Checking every 30 seconds...`n" -ForegroundColor White

$maxWait = 7  # 7 more minutes (workflow started at 14:18, it's now ~14:22)
$waited = 0

while ($waited -lt ($maxWait * 60)) {
    # Check if job still running
    $job = Get-Job | Where-Object {$_.State -eq 'Running'} | Select-Object -First 1
    
    if (-not $job) {
        Write-Host "✓ Workflow job completed!" -ForegroundColor Green
        break
    }
    
    $runtime = ((Get-Date) - $job.PSBeginTime).TotalMinutes
    Write-Host "  [$(Get-Date -Format 'HH:mm:ss')] Still running... ($($runtime.ToString('0.1')) min)" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 30
    $waited += 30
}

# Check log for completion
Write-Host "`n📄 Checking workflow log..." -ForegroundColor Cyan
$logFile = Get-ChildItem "logs\run_20260124_141803.log" -ErrorAction SilentlyContinue
if ($logFile) {
    $lastLines = Get-Content $logFile.FullName -Tail 20
    
    if ($lastLines -match "saved to DynamoDB" -or $lastLines -match "Final pick count") {
        Write-Host "✓ Picks were generated and saved!" -ForegroundColor Green
    } elseif ($lastLines -match "timed out" -or $lastLines -match "ERROR") {
        Write-Host "⚠ Workflow encountered an error" -ForegroundColor Red
        $lastLines | Select-Object -Last 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "⏳ Still processing..." -ForegroundColor Yellow
        $lastLines | Select-Object -Last 3 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    }
}

# Quick DB check
Write-Host "`n🔍 Checking DynamoDB for new picks..." -ForegroundColor Cyan
python -c "import boto3; from datetime import datetime; table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets'); response = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': datetime.now().strftime('%Y-%m-%d')}); items = response['Items']; future = [i for i in items if i.get('race_time', '') > datetime.now().isoformat()]; print(f'Future picks: {len(future)}'); [print(f\"  - {i['horse']} @ {i['course']}\") for i in future[:3]]"

Write-Host "`n✓ Monitoring complete" -ForegroundColor Green
