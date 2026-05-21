# Schedule Racing Post Learning Integration
# Runs every hour from 1pm to 9pm to process scraped results

$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\integrate_racingpost_learning.py"
$pythonPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe"
$taskName = "RacingPostLearning"

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create triggers for every hour from 1pm to 9pm
$triggers = @()

# 1pm to 9pm = 9 hourly triggers (13:00, 14:00, 15:00... 21:00)
for ($hour = 13; $hour -le 21; $hour++) {
    $trigger = New-ScheduledTaskTrigger -Daily -At "$($hour):00"
    $triggers += $trigger
}

# Create action
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $scriptPath -WorkingDirectory "C:\Users\charl\OneDrive\futuregenAI\Betting"

# Create task settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

# Register the task
Register-ScheduledTask -TaskName $taskName -Trigger $triggers -Action $action -Settings $settings -Description "Racing Post learning integration - matches results and triggers learning hourly" -RunLevel Highest

Write-Host "Learning integration task created!"
Write-Host "Schedule: Hourly from 1pm to 9pm"
Write-Host "Next run times:"

# Show triggers
$task = Get-ScheduledTask -TaskName $taskName
$task.Triggers | Select-Object -First 5 | ForEach-Object {
    $time = $_.StartBoundary
    Write-Host "  - $time"
}

Write-Host "Done!"
