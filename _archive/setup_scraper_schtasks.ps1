# Create scheduled task using schtasks.exe (alternative to PowerShell cmdlets)
# This may work without full admin rights in some Windows configurations

$scriptPath = "C:\Users\charl\OneDrive\futuregenAI\Betting\run_scraper.bat"
$taskName = "RacingPostScraper"

Write-Host "`nCreating scheduled task using schtasks.exe...`n" -ForegroundColor Cyan

# Delete existing task if it exists
schtasks /delete /tn $taskName /f 2>$null

# Create task that runs every 30 minutes from 12pm to 8pm
# We'll create multiple tasks for each 30-min interval

$times = @(
    "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00"
)

foreach ($time in $times) {
    $taskNameWithTime = "${taskName}_$($time.Replace(':', ''))"
    
    # Delete if exists
    schtasks /delete /tn $taskNameWithTime /f 2>$null
    
    # Create new task
    $result = schtasks /create /tn $taskNameWithTime /tr $scriptPath /sc daily /st $time /f
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Created task for $time" -ForegroundColor Green
    } else {
        Write-Host "[FAILED] Could not create task for $time" -ForegroundColor Red
    }
}

Write-Host "`nScheduled tasks created!`n" -ForegroundColor Green
Write-Host "To view all tasks:"
Write-Host "  schtasks /query /tn RacingPostScraper* /fo list`n"
Write-Host "To run a task manually:"
Write-Host "  schtasks /run /tn RacingPostScraper_1200`n"
Write-Host "To delete all tasks:"
Write-Host "  for %i in (1200 1230 1300 1330 1400 1430 1500 1530 1600 1630 1700 1730 1800 1830 1900 1930 2000) do schtasks /delete /tn RacingPostScraper_%i /f`n"
