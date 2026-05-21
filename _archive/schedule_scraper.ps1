#!/usr/bin/env pwsh
# Schedule Racing Post Scraper to run automatically

Write-Host "`n⏰ Setting up automatic results scraping...`n" -ForegroundColor Cyan

# Create EventBridge rule to run scraper every 2 hours
Write-Host "Creating EventBridge rule..." -ForegroundColor Yellow

$ruleName = "racing-results-scraper"

# Create or update rule
aws events put-rule `
    --name $ruleName `
    --schedule-expression "rate(2 hours)" `
    --description "Scrape Racing Post for race results every 2 hours" `
    --region eu-west-1 | Out-Null

# Get Lambda ARN
$lambdaArn = (aws lambda get-function --function-name RacingPostScraper --region eu-west-1 | ConvertFrom-Json).Configuration.FunctionArn

# Add Lambda as target
aws events put-targets `
    --rule $ruleName `
    --targets "Id"="1","Arn"="$lambdaArn" `
    --region eu-west-1 | Out-Null

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission `
    --function-name RacingPostScraper `
    --statement-id racing-scraper-event `
    --action 'lambda:InvokeFunction' `
    --principal events.amazonaws.com `
    --source-arn "arn:aws:events:eu-west-1:813281204422:rule/$ruleName" `
    --region eu-west-1 2>$null | Out-Null

Write-Host "`n✅ Automatic scraping scheduled!" -ForegroundColor Green
Write-Host "`nSchedule: Every 2 hours" -ForegroundColor Cyan
Write-Host "Function: RacingPostScraper" -ForegroundColor Gray
Write-Host "`nResults will be automatically captured and learning system will run!" -ForegroundColor Yellow
