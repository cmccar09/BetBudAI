# PowerShell script to schedule Racing Post scraper
# Runs every 30 minutes from 12pm to 8pm daily

$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\scheduled_racingpost_scraper.py"
$pythonPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe"
$taskName = "RacingPostScraper"

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create triggers for every 30 minutes from 12pm to 8pm
$triggers = @()

# 12:00 PM to 8:00 PM = 8 hours = 16 half-hour slots
$startHour = 12
$endHour = 20

for ($hour = $startHour; $hour -lt $endHour; $hour++) {
    # On the hour
    $trigger = New-ScheduledTaskTrigger -Daily -At "$($hour):00"
    $triggers += $trigger
    
    # Half past the hour
    $trigger = New-ScheduledTaskTrigger -Daily -At "$($hour):30"
    $triggers += $trigger
}

# Create action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

# Register the task
Register-ScheduledTask -TaskName $taskName -Trigger $triggers -Action $action -Settings $settings -Description "Racing Post scraper - runs every 30 min from 12pm-8pm" -RunLevel Highest

Write-Host "Task created successfully!"
Write-Host "Next run times:"

# Show next 5 run times
$task = Get-ScheduledTask -TaskName $taskName
$task.Triggers | Select-Object -First 5 | ForEach-Object {
    $time = $_.StartBoundary
    Write-Host "  - $time"
}

Write-Host "Done!"
