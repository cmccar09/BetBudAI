# COORDINATED LEARNING SYSTEM - Complete Guide

## Overview
Fully automated system that continuously learns throughout the racing day and improves predictions in real-time.

## Architecture

### Dual-Track System
1. **Learning Track** (`show_in_ui=False`)
   - Analyzes 100% of horses in ALL races
   - Builds comprehensive learning dataset
   - No filtering - everything is valuable data
   - Used to detect patterns and adjust weights

2. **UI Track** (`show_in_ui=True`)
   - Only high-confidence picks (>=85 score) — **UPDATED Feb 26, 2026** (was 70; data shows 85+ = +33% ROI)
   - Validated and promoted from learning data
   - What users see in the interface
   - Continuously updated as confidence improves

## Automated Schedule

### Task 1: Racing Post Scraper
- **When**: 12:00pm - 8:00pm, every 30 minutes (16 runs/day)
- **What**: Scrapes race results from Racing Post website
- **Output**: Saves to `RacingPostRaces` DynamoDB table
- **Why**: Betfair API only shows results for 30min - Racing Post has permanent records

### Task 2: Coordinated Learning Workflow  
- **When**: 11:00am - 7:00pm, every 30 minutes (16 runs/day)
- **What**: Complete learning cycle (4 steps)
- **Steps**:
  1. Analyze all upcoming races
  2. Match Racing Post results with predictions
  3. Learn from outcomes, adjust weights
  4. Promote high-confidence picks to UI

## How It Works

### Morning (11:00am - 12:00pm)
- Learning workflow starts analyzing races
- All horses scored and saved (show_in_ui=False)
- No results yet (scraper starts at noon)

### Afternoon (12:00pm - 5:00pm) - Peak Learning
1. **12:00pm**: First races start
2. **12:30pm**: Racing Post scraper captures first results
3. **1:00pm**: Learning workflow matches results
   - Sees which horses actually won
   - Compares with predictions
   - Adjusts weights (e.g., "jockey form matters more than expected")
4. **1:30pm**: Next batch of races analyzed
   - Uses UPDATED weights from learning
   - Predictions now more accurate
5. **Cycle repeats** - continuous improvement

### Evening (5:00pm - 8:00pm)
- Last races analyzed and results captured
- Final learning adjustments applied
- System ready for next day with improved weights

## Data Flow

```
Upcoming Races
     ↓
Analyze ALL horses → Save to DB (show_in_ui=False)
     ↓
High confidence (>=70)? → Promote to UI (show_in_ui=True)
     ↓
Race finishes
     ↓
Racing Post Scraper → Captures result
     ↓
Match with predictions → Did we predict correctly?
     ↓
Learn from outcome → Adjust weights
     ↓
Next race uses IMPROVED weights
```

## Key Files

### Workflows
- `coordinated_learning_workflow.py` - Master workflow (4 steps)
- `scheduled_racingpost_scraper.py` - Scrapes Racing Post
- `match_racingpost_to_betfair.py` - Matches results with predictions
- `auto_adjust_weights.py` - Learns from outcomes
- `analyze_all_races_comprehensive.py` - Analyzes all horses

### Setup
- `setup_master_schedule.ps1` - Creates both scheduled tasks
- `setup_scraper_schedule.ps1` - Just scraper (already done)
- `setup_learning_schedule.ps1` - Just learning (old, replaced by master)

### Database Tables
- `SureBetBets` - All predictions and picks
  - `show_in_ui=False` - Learning data (majority)
  - `show_in_ui=True` - UI picks (high confidence)
- `RacingPostRaces` - Race results from Racing Post
  - Permanent storage of all race outcomes
  - Used for matching and learning

## Installation

### Quick Setup (Recommended)
```powershell
Start-Process powershell -Verb RunAs -ArgumentList "-NoExit","-Command","cd C:\Users\charl\OneDrive\futuregenAI\Betting; .\setup_master_schedule.ps1"
```

This creates both scheduled tasks automatically.

### Verify Setup
```powershell
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Racing*" -or $_.TaskName -like "*Learning*"}
```

Should show:
- `RacingPostScraper` - Ready, Next Run: tomorrow 12:00pm
- `CoordinatedLearning` - Ready, Next Run: tomorrow 11:00am

## Manual Testing

### Test Coordinated Workflow
```powershell
python coordinated_learning_workflow.py
```

### Test Racing Post Scraper
```powershell
python scheduled_racingpost_scraper.py
```

### Test Result Matching
```powershell
python match_racingpost_to_betfair.py
```

### Check System Status
```powershell
python check_db_state.py
```

## Monitoring

### Check Today's Activity
```powershell
# See UI picks
python show_todays_ui_picks.py

# See learning data
python check_db_state.py

# See Racing Post scrapes
python check_racingpost_data.py  # (create if needed)
```

### View Logs
- `scraper_log.txt` - Racing Post scraper activity
- `matching_log.txt` - Result matching activity
- Task Scheduler logs - In Windows Event Viewer

## How Learning Improves Picks

### Example: Jockey Form Discovery
1. **Morning**: System uses default jockey weight (1.0x)
2. **1:00pm**: Three races finish
   - Top jockey won 2/3 races
   - Our predictions missed these (jockey underweighted)
3. **Learning step**: Adjust jockey weight 1.0x → 1.3x
4. **1:30pm**: New races analyzed
   - Same top jockey riding again
   - Now gets higher score (jockey boost applied)
   - Pick confidence increases 65 → 73
   - Promoted to UI (crossed 70 threshold)
5. **Race finishes**: Top jockey wins again
6. **Learning step**: Further boost jockey weight 1.3x → 1.5x

Result: System learned jockey form matters and adjusted in real-time.

## Benefits

1. **Continuous Learning** - Gets smarter throughout the day
2. **Real-Time Adaptation** - Learns from early races, applies to later ones
3. **Comprehensive Data** - Analyzes everything, not just favorites
4. **Permanent Results** - Racing Post scraper captures all outcomes
5. **Quality Control** - Only high-confidence picks reach UI
6. **Automatic** - Runs all day with zero manual intervention

## Troubleshooting

### No UI picks showing
- Check learning data exists: `python check_db_state.py`
- May need manual promotion: Adjust confidence threshold
- Verify races analyzed: Check for `show_in_ui=False` entries

### Scraper not running
- Check Task Scheduler: `Get-ScheduledTask -TaskName "RacingPostScraper"`
- View last run: `Get-ScheduledTaskInfo -TaskName "RacingPostScraper"`
- Check logs: `scraper_log.txt`

### Learning not improving
- Verify results matching: `python match_racingpost_to_betfair.py`
- Check Racing Post data: Query `RacingPostRaces` table
- Ensure auto_adjust running: Check for weight updates

### Tasks not running at scheduled time
- Ensure computer is on and awake
- Check Task Scheduler history (enable if disabled)
- Verify RunLevel is "Highest" (admin privileges)

## Next Steps

After setup:
1. Wait for tomorrow 11:00am (first learning run)
2. Monitor progress at 12:30pm (first results captured)
3. Check 1:00pm+ for learning in action
4. Review UI picks to see promoted selections
5. Let system run for 3-5 days to establish patterns

## Success Metrics

- **Coverage**: 90%+ horses analyzed per race
- **UI Picks**: 5-15 high-confidence selections per day
- **Learning Data**: 100+ horses analyzed daily
- **Results Matched**: 80%+ of finished races matched
- **Weight Adjustments**: 3-5 weight updates per day
- **Confidence Growth**: Picks promoted from learning to UI

---

**Status**: System ready to deploy
**Last Updated**: 2026-02-04
**Version**: 1.0 - Coordinated Learning
