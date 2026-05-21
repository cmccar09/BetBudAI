# Monitor scheduled workflow run
# This script waits for the next scheduled run and monitors its progress

param(
    [int]$CheckIntervalSeconds = 10
)

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "       WORKFLOW MONITORING - Waiting for 17:15" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Get next run time
$task = Get-ScheduledTaskInfo "BettingWorkflow_Continuous"
$nextRun = $task.NextRunTime
$now = Get-Date

Write-Host "Current time: $($now.ToString('HH:mm:ss'))" -ForegroundColor White
Write-Host "Next run: $($nextRun.ToString('HH:mm:ss'))" -ForegroundColor Yellow
$waitMinutes = [math]::Ceiling(($nextRun - $now).TotalMinutes)
Write-Host "Waiting: $waitMinutes minutes`n" -ForegroundColor White

# Wait until 1 minute before scheduled run
$waitUntil = $nextRun.AddMinutes(-1)
while ((Get-Date) -lt $waitUntil) {
    $remaining = [math]::Ceiling(($waitUntil - (Get-Date)).TotalMinutes)
    Write-Host "`r  Waiting... $remaining minutes until monitoring starts" -NoNewline -ForegroundColor Gray
    Start-Sleep -Seconds 30
}

Write-Host "`n`n✓ Starting monitoring...`n" -ForegroundColor Green

# Monitor for new log file
$monitorStart = Get-Date
$logFound = $false
$logFile = $null

Write-Host "Watching for new log file..." -ForegroundColor Cyan

while (-not $logFound -and ((Get-Date) - $monitorStart).TotalMinutes -lt 5) {
    $latestLog = Get-ChildItem logs\run_$(Get-Date -Format 'yyyyMMdd')_*.log -ErrorAction SilentlyContinue | 
                 Where-Object { $_.LastWriteTime -gt $monitorStart } | 
                 Sort-Object LastWriteTime -Descending | 
                 Select-Object -First 1
    
    if ($latestLog) {
        $logFound = $true
        $logFile = $latestLog.FullName
        Write-Host "✓ Found log: $($latestLog.Name)" -ForegroundColor Green
    } else {
        Write-Host "." -NoNewline -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if (-not $logFound) {
    Write-Host "`n✗ No log file created - workflow may not have started" -ForegroundColor Red
    exit 1
}

Write-Host "`nMonitoring workflow progress...`n" -ForegroundColor Cyan

# Monitor log file growth
$lastSize = 0
$noChangeCount = 0
$maxNoChange = 60  # 60 * 10 seconds = 10 minutes timeout

while ($noChangeCount -lt $maxNoChange) {
    Start-Sleep -Seconds $CheckIntervalSeconds
    
    $currentSize = (Get-Item $logFile).Length
    
    if ($currentSize -gt $lastSize) {
        # New content - show last few lines
        $content = Get-Content $logFile
        $newLines = $content | Select-Object -Last 3
        
        foreach ($line in $newLines) {
            if ($line -match "WORKFLOW COMPLETE") {
                Write-Host "`n✓ WORKFLOW COMPLETED SUCCESSFULLY!" -ForegroundColor Green
                Write-Host "`nFinal status:" -ForegroundColor Cyan
                Get-Content $logFile | Select-String -Pattern "saved|picks|Complete" | Select-Object -Last 5 | ForEach-Object {
                    Write-Host "  $($_.Line)" -ForegroundColor White
                }
                
                # Run health check
                Write-Host "`nRunning health check..." -ForegroundColor Cyan
                python check_picks_status.py
                
                exit 0
            }
            
            # Show progress indicators
            if ($line -match "STEP \d|Processing|saved|Filtered") {
                $timestamp = Get-Date -Format "HH:mm:ss"
                Write-Host "[$timestamp] $line" -ForegroundColor Gray
            }
        }
        
        $lastSize = $currentSize
        $noChangeCount = 0
    } else {
        $noChangeCount++
        if ($noChangeCount % 6 -eq 0) {  # Every minute
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    
    # Check if workflow completed
    $content = Get-Content $logFile -Raw
    if ($content -match "WORKFLOW COMPLETE") {
        Write-Host "`n✓ WORKFLOW COMPLETED!" -ForegroundColor Green
        break
    }
}

if ($noChangeCount -ge $maxNoChange) {
    Write-Host "`n⚠ Workflow appears to be stuck (no activity for 10 minutes)" -ForegroundColor Yellow
    Write-Host "Last log content:" -ForegroundColor Cyan
    Get-Content $logFile | Select-Object -Last 10 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
}

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Monitoring complete" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Cyan
