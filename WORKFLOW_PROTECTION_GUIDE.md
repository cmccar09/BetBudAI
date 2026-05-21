# WORKFLOW FAILURE PREVENTION SYSTEM
## Created: February 13, 2026
## Purpose: Prevent daily workflow breakdowns

---

## 🛡️ PROTECTION LAYERS

### 1. **Daily Health Check** (`daily_health_check.py`)
**When to run:** Before workflow starts  
**What it checks:**
- ✓ response_horses.json exists and is recent (<24h)
- ✓ Form data present in race data
- ✓ Database has picks with valid scores
- ✓ No score mismatches (comprehensive_score vs combined_confidence)
- ✓ Required workflow files exist
- ✓ Scheduled task is active

**Usage:**
```powershell
python daily_health_check.py
```

**Exit codes:**
- 0 = All checks passed
- 1 = Critical issues found (workflow will fail)

---

### 2. **Auto Recovery** (`auto_recovery.py`)
**When to run:** If health check fails  
**What it fixes:**
- 🔄 Fetches fresh race data if missing/old
- 🔄 Synchronizes score fields in database
- 🔄 Cleans stale data (>2 days old, unresolved)

**Usage:**
```powershell
python auto_recovery.py
```

**Exit codes:**
- 0 = Recovery successful
- 1 = Manual intervention needed

---

### 3. **Safe Workflow Runner** (`run_safe_workflow.ps1`)
**THE NEW STANDARD FOR SCHEDULED TASKS**

**Workflow:**
```
1. Health Check → Pass? ✓ Continue
                → Fail? ✗ Run Recovery
2. Recovery     → Success? ✓ Continue
                → Fail? ✗ Abort & Alert
3. Run comprehensive_workflow.py
4. Verify picks created
```

**Usage:**
```powershell
.\run_safe_workflow.ps1
```

**Scheduled Task:** Runs every 30 mins (12pm-8pm daily)

---

### 4. **Validation Layer** (`validate_before_scoring.py`)
**Prevents 0-score disasters**

**Critical Requirements:**
- Horse must have: name, odds, form data
- Race must have: 90%+ runner coverage
- Rejects: Form='N/A', odds=0, missing data

**Integration Example:**
```python
from validate_before_scoring import safe_score_horse, validate_race_data

# Validate race first
is_valid, error, coverage = validate_race_data(race)
if not is_valid:
    print(f"SKIPPING: {error}")
    return None

# Score horses safely
for runner in race['runners']:
    score, reasons = safe_score_horse(runner, your_score_func)
```

---

## 🚨 FAILURE MODES & FIXES

| Symptom | Root Cause | Auto-Fix | Manual Fix |
|---------|-----------|----------|------------|
| No picks generated | Missing form data | ✓ Fetch fresh data | Run `betfair_odds_fetcher.py` |
| UI shows 0/100 | Score field mismatch | ✓ Sync scores | Run `fix_ui_scores.py` |
| All scores = 0 | Wrong scraper running | ✗ Update task | Use `run_safe_workflow.ps1` |
| Old data | response_horses.json stale | ✓ Fetch fresh | Delete old file |
| Low coverage | Racing Post scraper used | ✗ Switch scraper | Use Betfair API instead |

---

## 📋 DAILY CHECKLIST

**Morning (11:30 AM):**
1. Manual health check: `python daily_health_check.py`
2. If issues found: `python auto_recovery.py`
3. Verify scheduled task active: `Get-ScheduledTask -TaskName "SafeBettingWorkflow"`

**After First Run (12:30 PM):**
1. Check picks created: `python learning_summary.py`
2. Verify UI shows correct scores (not 0/100)
3. Check form data present in database

**Evening (8:30 PM):**
1. Check total picks for day: `python learning_summary.py`
2. Review any workflow failures in terminal output

---

## 🔧 MAINTENANCE COMMANDS

**Test health check:**
```powershell
python daily_health_check.py
```

**Force recovery:**
```powershell
python auto_recovery.py
```

**Manual workflow run:**
```powershell
.\run_safe_workflow.ps1
```

**Check scheduled task:**
```powershell
Get-ScheduledTask -TaskName "SafeBettingWorkflow"
```

**View task history:**
```powershell
Get-ScheduledTask -TaskName "SafeBettingWorkflow" | Get-ScheduledTaskInfo
```

---

## 📊 MONITORING ALERTS

**Red Flags (require immediate action):**
- ❌ Health check fails for 2+ consecutive runs
- ❌ 0 UI picks despite races available
- ❌ Form data missing from >10% of horses
- ❌ Scheduled task not running

**Yellow Flags (monitor):**
- ⚠️ response_horses.json >6 hours old
- ⚠️ <5 UI picks when 20+ races available
- ⚠️ Score mismatches detected
- ⚠️ Coverage <95% (but >90%)

---

## 🎯 SUCCESS CRITERIA

**Healthy System:**
- ✓ Health check passes daily
- ✓ 5-15 UI picks generated per day
- ✓ Form data present on all analyzed horses
- ✓ Scores display correctly on UI
- ✓ Scheduled task runs every 30 mins
- ✓ No manual intervention needed

---

## 📝 LESSONS LEARNED

### Feb 12-13, 2026 Incident
**Problem:** No picks for 2 days, all scores = 0  
**Root Causes:**
1. Wrong scraper (scheduled_racingpost_scraper.py gets results, not racecards)
2. No form data (Racing Post results pages don't include form)
3. Syntax errors in generate_ui_picks.py
4. Score field mismatch (comprehensive_score vs combined_confidence)

**Prevention:**
- ✓ Safe workflow runner validates before running
- ✓ Health check detects missing form data
- ✓ Auto-recovery fetches fresh data
- ✓ Validation layer rejects incomplete data
- ✓ Scheduled task uses comprehensive_workflow.py

---

## 🔄 RECOVERY PROCEDURE

**If workflow breaks:**

1. **Run health check:**
   ```powershell
   python daily_health_check.py
   ```

2. **Note issues reported**

3. **Attempt auto-recovery:**
   ```powershell
   python auto_recovery.py
   ```

4. **If recovery fails, manual steps:**
   - Check internet connection
   - Verify Betfair API accessible
   - Run: `python betfair_odds_fetcher.py`
   - Check AWS credentials: `aws sts get-caller-identity`
   - Review error logs

5. **After fixing, test:**
   ```powershell
   .\run_safe_workflow.ps1
   python learning_summary.py
   ```

---

**Last Updated:** February 13, 2026  
**Maintained By:** Automated workflow system  
**Review Schedule:** Weekly (Sundays)
