# New Dual Schedule Configuration - 2026-01-16

## Overview
Implemented a dual-speed analysis schedule to balance comprehensive coverage with responsive quick scans.

## Schedule Details

### 🔍 Morning Full Analysis
**Time**: 10:30 AM daily
**Window**: Next 4 hours
**Purpose**: Comprehensive scan of all races in the morning session
**Races Analyzed**: All races from 10:30am - 2:30pm

### ⚡ Quick Scans
**Times**: Every 30 minutes from 11:15am - 7:45pm
**Window**: Next 1 hour
**Purpose**: Responsive analysis focused on imminent races
**Frequency**: 18 runs per day

### Total Daily Runs: **19**

## Time Breakdown

| Time  | Type | Window | Purpose |
|-------|------|--------|---------|
| 10:30 | FULL | 4 hrs  | Comprehensive morning coverage |
| 11:15 | Quick | 1 hr   | Imminent races |
| 11:45 | Quick | 1 hr   | Imminent races |
| 12:15 | Quick | 1 hr   | Imminent races |
| 12:45 | Quick | 1 hr   | Imminent races |
| 13:15 | Quick | 1 hr   | Imminent races |
| 13:45 | Quick | 1 hr   | Imminent races |
| 14:15 | Quick | 1 hr   | Imminent races |
| 14:45 | Quick | 1 hr   | Imminent races |
| 15:15 | Quick | 1 hr   | Imminent races |
| 15:45 | Quick | 1 hr   | Imminent races |
| 16:15 | Quick | 1 hr   | Imminent races |
| 16:45 | Quick | 1 hr   | Imminent races |
| 17:15 | Quick | 1 hr   | Imminent races |
| 17:45 | Quick | 1 hr   | Imminent races |
| 18:15 | Quick | 1 hr   | Imminent races |
| 18:45 | Quick | 1 hr   | Imminent races |
| 19:15 | Quick | 1 hr   | Imminent races |
| 19:45 | Quick | 1 hr   | Imminent races |

## Technical Implementation

### Files Modified

#### 1. `run_enhanced_analysis.py`
- Added `--hours` command-line parameter (default: 1)
- Modified time window filtering to use dynamic hours
- Updated main() function signature to accept hours parameter

#### 2. `scheduled_workflow.ps1`
- Auto-detects if run time is 10:30am (±5 minutes)
- Sets `$analysisHours = 4` for morning run
- Sets `$analysisHours = 1` for all other runs
- Passes hours parameter to `run_enhanced_analysis.py`

#### 3. `update_schedule_with_morning_run.ps1` (NEW)
- Creates 19 triggers (1 at 10:30, 18 at :15/:45)
- Uses batch wrapper for reliability
- Configures proper task permissions

## How It Works

```powershell
# Morning Run (10:30am)
IF current_time == 10:30am (±5min)
  THEN analyze_hours = 4
  ANALYZE races from 10:30am - 2:30pm
  
# Quick Scans (11:15am - 7:45pm)
ELSE
  analyze_hours = 1
  ANALYZE races in next 1 hour only
```

## Benefits

### ✅ Comprehensive Coverage
- Morning run captures early/mid-day races that might be missed
- Ensures no valuable races are overlooked

### ✅ Responsive Analysis
- Quick 1-hour scans every 30 mins stay current
- Picks generated close to race time with fresh odds

### ✅ Efficient Resource Use
- Most runs analyze only 1 hour (faster, lower cost)
- Heavy 4-hour analysis only once per day

### ✅ Better Pick Quality
- Morning run can compare multiple races
- Quick scans focus on imminent value

## Monitoring

Check task execution:
```powershell
Get-ScheduledTaskInfo -TaskName "BettingWorkflow_Continuous"
```

View logs:
```powershell
Get-Content logs\run_*.log -Tail 50
```

## Next Scheduled Runs

- **Next Full Analysis**: Tomorrow 10:30 AM (4-hour window)
- **Next Quick Scan**: Today 11:15 AM (1-hour window)

---
*Combined with strict filtering (30% confidence, 20% p_win, 5% ROI, 1 pick/race), this should produce 2-4 high-quality picks per day.*
