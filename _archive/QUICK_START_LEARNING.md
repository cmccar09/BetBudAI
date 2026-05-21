# QUICK START: Embedded Learning System

## ✅ System Status

**Automated Learning:** ACTIVE  
**Next Run:** Tomorrow at 8:00 AM  
**Task Name:** BettingWorkflow_AutoLearning  
**Current Weights:** Optimized (Feb 2, 2026)

## 🔄 What Happens Automatically

Every day at 8:00 AM:

1. ✓ Fetches yesterday's results
2. ✓ Analyzes performance patterns  
3. ✓ **Auto-adjusts scoring weights** ← NEW
4. ✓ Fetches today's races
5. ✓ Generates picks with updated weights
6. ✓ Saves to DynamoDB (visible in UI)

**No manual intervention required!**

## 📊 Today's Learning (Feb 2, 2026)

### What Was Learned:
- Poor form horses won 83.3% of the time
- Optimal odds (3-6) had 66.7% win rate
- Form analysis may be too strict

### Weights Adjusted:
```
optimal_odds: 20 → 25 (+5pts) ← More predictive
recent_win: 25 → 23 (-2pts)   ← Less predictive
sweet_spot: 30 (unchanged)    ← Performing well
```

### Impact on Tomorrow:
- Horses with optimal odds get higher scores
- Form importance slightly reduced
- Fairer evaluation of horses with poor recent form

## 🎯 Quick Commands

### Check Task Status:
```powershell
Get-ScheduledTask -TaskName "BettingWorkflow_AutoLearning"
```

### Run Manually (Test):
```powershell
python daily_automated_workflow.py
```

### View Current Weights:
```powershell
python demonstrate_learning.py
```

### Check Today's Adjustments:
```powershell
python auto_adjust_weights.py
```

### View Logs:
```powershell
Get-Content .\logs\daily_workflow.log -Tail 50
```

## 📈 Performance Tracking

### View Learning Summary:
```python
import boto3
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
weights = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
print(weights['Item']['learning_summary'])
```

### Check Weight History:
Weights are updated in DynamoDB after each day's analysis.  
View `last_updated` timestamp to see when last learning occurred.

## 🔧 Troubleshooting

### If Task Doesn't Run:
```powershell
# Check task state
Get-ScheduledTask -TaskName "BettingWorkflow_AutoLearning" | Select State

# Check last run result
Get-ScheduledTaskInfo -TaskName "BettingWorkflow_AutoLearning" | Select LastRunTime, LastTaskResult

# Re-run setup if needed
.\setup_automated_learning.ps1
```

### If Weights Not Updating:
```powershell
# Run weight adjustment manually
python auto_adjust_weights.py

# Check for errors
Get-Content .\logs\daily_workflow.log -Tail 100
```

### Reset Weights to Defaults:
```python
import boto3
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
table.delete_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
print("✓ Weights reset - system will use defaults on next run")
```

## 📁 Key Files

- `daily_automated_workflow.py` - Main automation script
- `auto_adjust_weights.py` - Learning engine
- `comprehensive_pick_logic.py` - Uses dynamic weights
- `setup_automated_learning.ps1` - Task scheduler setup
- `EMBEDDED_LEARNING_SYSTEM.md` - Full documentation

## 🎓 Learning Cycle

```
Day 1: Results → Learn → optimal_odds +5
Day 2: Results → Learn → recent_win -1  
Day 3: Results → Learn → sweet_spot +2
...
Day N: Continuously optimized weights
```

## ⚙️ Advanced

### Disable Automated Learning:
```powershell
Disable-ScheduledTask -TaskName "BettingWorkflow_AutoLearning"
```

### Re-enable:
```powershell
Enable-ScheduledTask -TaskName "BettingWorkflow_AutoLearning"
```

### Change Schedule:
```powershell
# Edit setup_automated_learning.ps1
# Modify: -Daily -At "08:00AM"
# Then re-run the setup script
```

## 📞 Support

All documentation in:
- `EMBEDDED_LEARNING_SYSTEM.md` - Complete guide
- `HIGH_CONFIDENCE_FILTER.md` - UI filtering details
- `IMPLEMENTATION_SUMMARY.md` - System architecture

---

**Status:** Production Ready  
**Last Updated:** 2026-02-02  
**Next Learning:** 2026-02-03 08:00 AM
