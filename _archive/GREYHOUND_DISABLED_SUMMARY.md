# Greyhound Schedules Disabled - Changes Summary

## Date: January 10, 2026

## Overview
Greyhound racing schedules have been disabled while preserving all horse racing functionality, including surebet analysis, results tracking, and self-learning systems.

## Changes Made

### 1. Updated `generate_todays_picks.ps1`
**File**: [generate_todays_picks.ps1](generate_todays_picks.ps1#L5)

**Change**: Changed default sport parameter from `greyhounds` to `horses`

```powershell
# Before:
param(
    [string]$Sport = "greyhounds"  # Default to greyhounds now
)

# After:
param(
    [string]$Sport = "horses"  # Default to horses - greyhounds disabled
)
```

**Impact**: Any manual runs of this script will now default to horses instead of greyhounds.

---

### 2. Updated `scheduled_workflow.ps1`
**File**: [scheduled_workflow.ps1](scheduled_workflow.ps1#L168)

**Change**: Added explicit `--sport horses` parameter to Betfair data fetching

```powershell
# Before:
& $pythonExe "$PSScriptRoot\betfair_delayed_snapshots.py" --out $snapshotFile --hours 24 --max_races 50 2>&1 | Tee-Object -Append -FilePath $logFile

# After:
& $pythonExe "$PSScriptRoot\betfair_delayed_snapshots.py" --out $snapshotFile --hours 24 --max_races 50 --sport horses 2>&1 | Tee-Object -Append -FilePath $logFile
```

**Impact**: All scheduled runs will now only fetch horse racing data from Betfair API.

---

### 3. Created `remove_greyhound_schedules.ps1`
**File**: [remove_greyhound_schedules.ps1](remove_greyhound_schedules.ps1)

**Purpose**: New script to remove any existing greyhound scheduled tasks from Windows Task Scheduler

**Usage**:
```powershell
.\remove_greyhound_schedules.ps1
```

This script will:
- Search for all scheduled tasks with "Greyhound" in the name
- Display found tasks
- Ask for confirmation before removal
- Remove all greyhound-related scheduled tasks

---

## Systems That Remain ACTIVE ✓

### Horse Racing Picks Generation
- All scheduled workflows continue for horse racing
- EventBridge schedules on AWS Lambda (7 times daily: 10am, 12pm, 2pm, 4pm, 6pm, 8pm, 10pm)
- Windows Task Scheduler (if configured)

### Surebet Results Tracking
- [fetch_race_results.py](fetch_race_results.py) - Fetches results for horse races
- [betfair_results_fetcher_v2.py](betfair_results_fetcher_v2.py) - Results from Betfair API
- Results are sport-agnostic and work with any picks in DynamoDB

### Self-Learning System
- [daily_learning_cycle.py](daily_learning_cycle.py) - Analyzes performance
- [evaluate_performance.py](evaluate_performance.py) - Tracks win rates and ROI
- [generate_learning_insights.py](generate_learning_insights.py) - Creates insights
- [daily_learning_workflow.py](daily_learning_workflow.py) - Automated learning loop

All learning systems work with horse racing data and are sport-agnostic.

---

## Files NOT Changed

### AWS Lambda Functions
- [lambda-workflow-package/lambda_function.py](lambda-workflow-package/lambda_function.py) - Already hardcoded to eventTypeId "7" (horses only)
- [lambda_api_picks.py](lambda_api_picks.py) - API endpoint `/picks/greyhounds` will simply return no results (no picks generated)

### Frontend
- [frontend/src/App.js](frontend/src/App.js) - Greyhound filter button remains but will show no picks

### Betfair Integration
- [betfair_delayed_snapshots.py](betfair_delayed_snapshots.py) - Sport parameter now defaults to 'horses'
- [betfair_odds_fetcher.py](betfair_odds_fetcher.py) - Already defaults to 'horse_racing'

---

## How to Run the Removal Script

1. **Open PowerShell as Administrator**

2. **Navigate to the project directory**:
   ```powershell
   cd "C:\Users\charl\OneDrive\futuregenAI\Betting"
   ```

3. **Run the removal script**:
   ```powershell
   .\remove_greyhound_schedules.ps1
   ```

4. **Confirm the removal when prompted**

---

## Verification Steps

### Check for remaining scheduled tasks:
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like '*Greyhound*' }
```

Should return no results after running the removal script.

### Check active betting tasks:
```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like '*Betting*' }
```

Should show only horse racing related tasks (BettingWorkflow*).

### Verify horse racing picks are being generated:
```powershell
.\generate_todays_picks.ps1
```

Should generate horse racing picks without needing to specify `-Sport horses`.

---

## Re-enabling Greyhounds (If Needed)

If you need to re-enable greyhound racing in the future:

1. **Revert `generate_todays_picks.ps1`**:
   ```powershell
   # Change parameter back to:
   param([string]$Sport = "greyhounds")
   ```

2. **Revert `scheduled_workflow.ps1`**:
   ```powershell
   # Remove the --sport horses parameter or change to --sport greyhounds
   ```

3. **Run the greyhound scheduler**:
   ```powershell
   .\schedule_greyhound_picks.ps1
   ```

---

## Notes

- **No database changes required** - The DynamoDB schema supports both horses and greyhounds via the `sport` field
- **No AWS Lambda changes required** - Lambda functions are already configured for horses only
- **Frontend remains functional** - Greyhound filter will work if greyhound picks are manually added
- **Learning systems are universal** - They work with any sport type in the database

---

## Contact

If you have any issues or questions about these changes, refer to:
- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md)
- [DAILY_TRAINING_SYSTEM.md](DAILY_TRAINING_SYSTEM.md)
- [CONTINUOUS_LEARNING_SYSTEM.md](CONTINUOUS_LEARNING_SYSTEM.md)
