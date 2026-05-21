# RACING POST SCHEDULED SCRAPER SETUP

## Overview

Automated system that scrapes Racing Post every 30 minutes from 12pm-8pm daily to collect race previews and results, then matches with Betfair picks for learning.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ RACING POST SCRAPER (Every 30 min, 12pm-8pm)               │
│ scheduled_racingpost_scraper.py                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ RACINGPOST DYNAMODB TABLE                                   │
│ - Race previews (before race starts)                        │
│ - Race results (after race finishes)                        │
│ - Historical data for matching                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ MATCHING ENGINE (8:30pm daily)                              │
│ match_racingpost_to_betfair.py                              │
│ - Matches RacingPost results → Betfair picks                │
│ - Updates outcomes (won/lost)                               │
│ - Calculates profit/loss                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ LEARNING PIPELINE                                           │
│ complete_race_learning.py                                   │
│ - Uses updated outcomes to improve model                    │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Create DynamoDB Table

```bash
python create_racingpost_table.py
```

This creates `RacingPostRaces` table with:
- **Primary Key**: `raceKey` (course_date_time)
- **Sort Key**: `scrapeTime` (allows multiple scrapes)
- **Index**: `DateIndex` on `raceDate` for fast date queries

### 2. Schedule the Scraper

```powershell
.\setup_scraper_schedule.ps1
```

This creates a Windows Task Scheduler task that runs:
- Every 30 minutes from 12:00 PM to 8:00 PM
- Daily (including weekends)
- 16 executions per day

**Schedule:**
- 12:00, 12:30, 1:00, 1:30, 2:00, 2:30...
- ...7:00, 7:30, 8:00

### 3. Test Manual Run

```bash
python scheduled_racingpost_scraper.py
```

Should output:
```
============================================================
RACING POST SCRAPER - 2026-02-03 14:30
============================================================

1. Fetching race list...
   Found 15 races

2. Scraping races...
   [1/15] carlisle... OK [RESULTS] Winner: Irish Goodbye Right
   [2/15] fairyhouse... OK [PREVIEW] 12 runners
   ...
```

### 4. Match with Betfair Picks

Run after races finish (e.g., 8:30 PM):

```bash
python match_racingpost_to_betfair.py
```

Or for specific date:
```bash
python match_racingpost_to_betfair.py 2026-02-03
```

## Data Stored

### RacingPostRaces Table Schema

```python
{
  'raceKey': 'carlisle_20260203_1430',      # Primary key
  'scrapeTime': '2026-02-03T14:25:00',      # Sort key
  'raceDate': '2026-02-03',                 # Indexed
  'courseId': '8',
  'courseName': 'carlisle',
  'raceTime': '14:30',
  'raceId': '4803335',
  'url': 'https://www.racingpost.com/...',
  'hasResults': True,                        # False = preview, True = results
  'runnerCount': 12,
  'runners': [
    {
      'horse_name': 'Irish Goodbye Right',
      'position': '1',                       # or 'running' if no results yet
      'odds': 5.5,
      'jockey': 'J Smith'
    },
    ...
  ],
  'winner': 'Irish Goodbye Right'            # null if no results
}
```

## How It Works

### 1. During Racing Day (12pm-8pm)

Every 30 minutes:
1. Scraper fetches Racing Post results page
2. For each race URL found:
   - If race hasn't run yet → Saves **preview** (runners, odds, jockeys)
   - If race has finished → Saves **results** (positions, winner)
3. Data saved to RacingPostRaces table
4. Same race can be scraped multiple times (preview → results transition)

### 2. Matching Phase (8:30pm)

After all races finish:
1. Query RacingPostRaces for today's races with results
2. Query SureBetBets for today's Betfair picks
3. Match by:
   - Course name (normalized)
   - Race time (within 5 minutes tolerance)
   - Horse name (exact match required)
4. Update picks with:
   - `outcome`: "won" or "lost"
   - `actual_position`: finishing position
   - `profit_loss`: calculated P&L
   - `result_source`: "racingpost"

### 3. Learning Phase (9pm)

```bash
python complete_race_learning.py learn
```

Uses the updated outcomes to improve the model.

## Matching Logic

### Course Name Normalization
```python
"Wolverhampton (AW)" → "wolverhampton"
"Carlisle" → "carlisle"
"Kempton-AW" → "kempton"
```

### Horse Name Normalization
```python
"Irish Goodbye  Right" → "irish goodbye right"
"DIVAS DOYEN" → "divas doyen"
```

### Time Matching
```python
Pick: "14:35"
RacingPost: "14:30" → MATCH (within 5 min)
RacingPost: "14:50" → NO MATCH (>5 min difference)
```

### Match Scoring
```python
Course exact match: +10 points
Course partial match: +5 points
Time exact match: +10 points
Time close match: +5 points
Horse exact match: +20 points

Minimum score for update: 20 (horse must match)
```

## Benefits

### vs. Betfair API Results
- ✅ No 30-minute window limitation
- ✅ Results available indefinitely
- ✅ All UK/Irish races (not just Betfair markets)
- ✅ Preview data before race starts
- ✅ Multiple data points (preview + results)

### vs. Manual Entry
- ✅ Fully automated
- ✅ Runs throughout the day
- ✅ Zero manual work
- ✅ Catches both previews and results

## Monitoring

### Check Scraper Status
```powershell
Get-ScheduledTask -TaskName "RacingPostScraper"
```

### View Recent Scrapes
```bash
cat scraper_log.txt
```

### Check Table Contents
```bash
python -c "
import boto3
table = boto3.resource('dynamodb', region_name='eu-west-1').Table('RacingPostRaces')
response = table.query(
    IndexName='DateIndex',
    KeyConditionExpression='raceDate = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)
print(f'Races today: {len(response[\"Items\"])}')
with_results = [r for r in response['Items'] if r.get('hasResults')]
print(f'With results: {len(with_results)}')
"
```

### Manual Test Run
```powershell
Start-ScheduledTask -TaskName "RacingPostScraper"
```

## Troubleshooting

### Issue: No races found
**Solution**: Check date format, verify Racing Post URL is accessible

### Issue: Scraper crashes
**Solution**: Check scraper_log.txt, ensure ChromeDriver is up to date

### Issue: Matches not found
**Solution**: Check course name variations, verify time matching logic

### Issue: Task not running
**Solution**: Check Task Scheduler, ensure network available at scheduled times

## Complete Daily Workflow

```bash
# 12:00 PM - First scrape (previews for upcoming races)
# 12:30 PM - Second scrape (may catch early results)
# ... continues every 30 min ...
# 8:00 PM - Final scrape (all race results)

# 8:30 PM - Match results with picks
python match_racingpost_to_betfair.py

# 9:00 PM - Run learning
python complete_race_learning.py learn

# 9:30 PM - Adjust weights
python auto_adjust_weights.py
```

## Next Steps

1. **Create the table**: `python create_racingpost_table.py`
2. **Set up schedule**: `.\setup_scraper_schedule.ps1`
3. **Test scraper**: `python scheduled_racingpost_scraper.py`
4. **Test matching**: `python match_racingpost_to_betfair.py`
5. **Monitor logs**: Check `scraper_log.txt` and `matching_log.txt`

## Files Created

- `scheduled_racingpost_scraper.py` - Main scraper script
- `create_racingpost_table.py` - DynamoDB table setup
- `setup_scraper_schedule.ps1` - Task scheduler configuration
- `match_racingpost_to_betfair.py` - Matching engine
- `RACINGPOST_SCRAPER_SETUP.md` - This documentation

🎯 **Result: Fully automated race data collection and results matching!**
