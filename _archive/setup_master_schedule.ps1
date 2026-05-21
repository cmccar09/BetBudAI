# Master Scheduler - Coordinates all automated workflows
# Sets up complete learning system

$pythonPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe"
$workingDir = "C:\Users\charl\OneDrive\futuregenAI\Betting"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "MASTER SCHEDULER SETUP" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# Task 1: Racing Post Scraper (12pm-8pm every 30min)
Write-Host "Setting up Task 1: Racing Post Scraper..." -ForegroundColor White
$task1Name = "RacingPostScraper"
$task1Script = "$workingDir\scheduled_racingpost_scraper.py"

Unregister-ScheduledTask -TaskName $task1Name -Confirm:$false -ErrorAction SilentlyContinue

$task1Triggers = @()
for ($hour = 12; $hour -lt 20; $hour++) {
    $task1Triggers += New-ScheduledTaskTrigger -Daily -At "$($hour):00"
    $task1Triggers += New-ScheduledTaskTrigger -Daily -At "$($hour):30"
}

$task1Action = New-ScheduledTaskAction -Execute $pythonPath -Argument $task1Script -WorkingDirectory $workingDir
$task1Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

Register-ScheduledTask -TaskName $task1Name -Trigger $task1Triggers -Action $task1Action -Settings $task1Settings -Description "Scrapes Racing Post for results" -RunLevel Highest | Out-Null

Write-Host "  Task created: 16 triggers (12:00pm-8:00pm every 30min)" -ForegroundColor Green

# Task 2: Coordinated Learning Workflow (11am-7pm every 30min)
Write-Host "`nSetting up Task 2: Learning Workflow..." -ForegroundColor White
$task2Name = "CoordinatedLearning"
$task2Script = "$workingDir\coordinated_learning_workflow.py"

Unregister-ScheduledTask -TaskName $task2Name -Confirm:$false -ErrorAction SilentlyContinue

$task2Triggers = @()
for ($hour = 11; $hour -lt 19; $hour++) {
    $task2Triggers += New-ScheduledTaskTrigger -Daily -At "$($hour):00"
    $task2Triggers += New-ScheduledTaskTrigger -Daily -At "$($hour):30"
}

$task2Action = New-ScheduledTaskAction -Execute $pythonPath -Argument $task2Script -WorkingDirectory $workingDir
$task2Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 25)

Register-ScheduledTask -TaskName $task2Name -Trigger $task2Triggers -Action $task2Action -Settings $task2Settings -Description "Analyzes races, matches results, learns patterns" -RunLevel Highest | Out-Null

Write-Host "  Task created: 16 triggers (11:00am-7:00pm every 30min)" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Scheduled Tasks Created:`n" -ForegroundColor Yellow

Write-Host "1. RacingPostScraper (12:00pm-8:00pm, every 30min)" -ForegroundColor White
Write-Host "   - Scrapes race results from Racing Post" -ForegroundColor Gray
Write-Host "   - Saves to RacingPostRaces DynamoDB table`n" -ForegroundColor Gray

Write-Host "2. CoordinatedLearning (11:00am-7:00pm, every 30min)" -ForegroundColor White
Write-Host "   - Analyzes ALL races (learning data)" -ForegroundColor Gray
Write-Host "   - Matches Racing Post results with predictions" -ForegroundColor Gray
Write-Host "   - Learns from outcomes, adjusts weights" -ForegroundColor Gray
Write-Host "   - Promotes high-confidence picks to UI`n" -ForegroundColor Gray

Write-Host "How it works:" -ForegroundColor Yellow
Write-Host "  - System runs throughout racing day" -ForegroundColor White
Write-Host "  - Continuously learns from results" -ForegroundColor White
Write-Host "  - Improves predictions for later races" -ForegroundColor White
Write-Host "  - Only shows high-confidence picks on UI" -ForegroundColor White
Write-Host "  - Everything else stored as learning data`n" -ForegroundColor White

Write-Host "Verify tasks:" -ForegroundColor Yellow
Write-Host '  Get-ScheduledTask | Where-Object {$_.TaskName -like "*Racing*" -or $_.TaskName -like "*Learning*"}' -ForegroundColor Gray

Write-Host "`n========================================`n" -ForegroundColor Cyan
