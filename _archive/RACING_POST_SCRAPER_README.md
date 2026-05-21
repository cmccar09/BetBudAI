# Racing Post Scraper - DEPLOYED ✅

## What Was Built

A web scraper that fetches race results from racingpost.com and updates your DynamoDB bets with actual outcomes.

### Files Created:
1. **racing_post_scraper.py** - Main scraper logic
2. **deploy_scraper.ps1** - Deployment script
3. **schedule_scraper.ps1** - Auto-scheduling script

### Lambda Function:
- **Name**: RacingPostScraper
- **Runtime**: Python 3.11
- **Region**: eu-west-1
- **Timeout**: 60 seconds

## How It Works

1. **Scrapes Racing Post** - Fetches today's race results from racingpost.com
2. **Finds Pending Bets** - Queries DynamoDB for bets without results
3. **Matches Bets to Winners** - Matches by course name and race time
4. **Updates Database** - Adds `actual_result`, `race_winner`, `profit` fields

## Usage

### Manual Run:
```powershell
aws lambda invoke --function-name RacingPostScraper --region eu-west-1 output.json
```

### Schedule Automatic Runs:
```powershell
.\schedule_scraper.ps1
```
This sets up EventBridge to run every 2 hours

### Local Testing:
```powershell
python racing_post_scraper.py
```

Or for specific date:
```powershell
python racing_post_scraper.py 2026-01-07
```

## What Happens Next

Once results are captured:

1. **Winner Analysis** runs (BettingWinnerAnalysis Lambda)
   - Compares your picks to actual winners
   - Identifies why you missed winners
   - Generates learning insights

2. **Insights Stored** in S3 (betting-insights bucket)
   - winner_analysis.json with learnings

3. **Future Picks Improved**
   - Betting Lambda loads insights
   - Applies learnings to prompt
   - Better predictions over time

## Checking Results

```powershell
# Count bets with results
aws dynamodb scan --table-name SureBetBets --region eu-west-1 --filter-expression "attribute_exists(actual_result)" --select COUNT

# View sample results
aws dynamodb scan --table-name SureBetBets --region eu-west-1 --filter-expression "attribute_exists(actual_result)" --limit 5
```

## Troubleshooting

If no results captured:
1. Racing Post may have changed their HTML structure
2. Course names might not match (check normalize_course_name function)
3. Race times might be off (scraper allows ±10 minutes)
4. Races might not have finished yet (need 1+ hours after race)

To debug, check Lambda logs:
```powershell
aws logs tail /aws/lambda/RacingPostScraper --since 30m --region eu-west-1
```

## Alternative: Betfair Results

The Betfair results fetcher (BettingResultsFetcher) is still available if you fix the authentication issues. Racing Post scraper is a free alternative that doesn't require API credentials.

## Next Steps

1. ✅ Scraper deployed
2. ⏳ Wait for races to finish (1+ hours after race time)
3. ⏳ Run scraper to capture results
4. ⏳ Verify results in database
5. ⏳ Schedule automatic runs
6. ⏳ Winner analysis will run automatically
7. ⏳ Learning system becomes active
