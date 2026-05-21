# Get Lambda CloudWatch Logs
$logGroup = "/aws/lambda/BettingWorkflowScheduled"

Write-Host "Fetching latest Lambda logs..." -ForegroundColor Cyan

# Get latest log stream
$streams = aws logs describe-log-streams `
    --log-group-name $logGroup `
    --order-by LastEventTime `
    --descending `
    --max-items 1 `
    --output json | ConvertFrom-Json

$streamName = $streams.logStreams[0].logStreamName
Write-Host "Log stream: $streamName`n" -ForegroundColor Yellow

# Get recent events
$events = aws logs get-log-events `
    --log-group-name $logGroup `
    --log-stream-name $streamName `
    --limit 100 `
    --output json | ConvertFrom-Json

# Show last 40 log messages
Write-Host "=== RECENT LOGS ===" -ForegroundColor Cyan
$events.events | Select-Object -Last 40 | ForEach-Object {
    $msg = $_.message
    if ($msg -match "Error|ERROR|Failed|FAILED|403|401|❌") {
        Write-Host $msg -ForegroundColor Red
    } elseif ($msg -match "Success|SUCCESS|✓") {
        Write-Host $msg -ForegroundColor Green
    } elseif ($msg -match "WARNING|WARN") {
        Write-Host $msg -ForegroundColor Yellow
    } else {
        Write-Host $msg
    }
}
