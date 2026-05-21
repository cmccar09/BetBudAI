# INTRADAY MONITORING SYSTEM
**Created:** February 21, 2026  
**Purpose:** Learn from earlier races to improve later picks

---

## 🎯 HOW IT WORKS

The system monitors races as they happen throughout the day and applies learnings to upcoming picks in real-time.

### 1. **Race Monitor** (`race_monitor.py`)
Shows all upcoming recommended picks and what to watch:

```powershell
python race_monitor.py
```

**Output:**
- Lists all recommended picks (85+ scores) for today
- Shows time until each race
- Highlights intelligence to gather before each pick
- Identifies trainer/odds/track patterns to watch

---

### 2. **Intraday Learning System** (`intraday_learning_system.py`)
Analyzes completed races and generates insights:

```powershell
python intraday_learning_system.py
```

**Runs after races finish to identify:**
- 🔥 Hot trainers (winning today)
- ❄️ Cold trainers (losing today)
- 💰 Best performing odds ranges
- 📍 Track-specific patterns

**Saves to:** `intraday_learnings.json` for workflow integration

---

## 📋 DAILY WORKFLOW

### Morning (9:00 AM)
```powershell
# 1. Run comprehensive workflow (generates picks)
.\run_safe_workflow.ps1

# 2. Check upcoming picks
python race_monitor.py
```

### Throughout the Day (Every 2 Hours)
```powershell
# 1. Update learnings from finished races
python intraday_learning_system.py

# 2. Check monitor dashboard
python race_monitor.py

# 3. Review insights for upcoming picks
Get-Content intraday_learnings.json
```

### Before Late Races (4:00 PM onwards)
```powershell
# 1. Final learning update
python intraday_learning_system.py

# 2. Re-run workflow with fresh insights
python comprehensive_workflow.py

# 3. Verify picks align with day's patterns
python race_monitor.py
```

---

## 🔍 WHAT TO WATCH

### Before Each Pick:

1. **Trainer Performance**
   - Has this trainer won/lost earlier today?
   - Win rate in similar races today?

2. **Odds Range Performance**
   - Are favorites winning or outsiders?
   - Is sweet spot (3-9) performing as expected?

3. **Track Patterns**
   - Average winner odds at this track today
   - Going conditions affecting results?

4. **Going Conditions** (Turf only)
   - Heavy going favoring certain horses?
   - All-weather performing consistently?

---

## 📊 USING INSIGHTS

### Example Scenario:

**Morning Pick:** Hold The Serve @ 3.35 (13:10 Kempton)
- Trainer: O Murphy
- Score: 98/100
- Odds range: Sweet spot (3-9)

**By 12:00 PM, learnings show:**
```json
{
  "hot_trainers": [["O Murphy", {"wins": 2, "total": 2, "win_rate": 1.0}]],
  "winning_odds_range": ["sweet_spot_3-9", {"win_rate": 0.75}]
}
```

**Action:** ✅ **INCREASE CONFIDENCE** - Both trainer and odds range performing excellently

---

**Opposite Scenario:**

**Afternoon Pick:** Example Horse @ 4.5 (15:30 Venue)
- Trainer: D Pipe
- Score: 85/100

**By 14:00 PM, learnings show:**
```json
{
  "cold_trainers": [["D Pipe", {"losses": 3, "total": 3}]]
}
```

**Action:** ⚠️ **REDUCE STAKE** or **SKIP** - Trainer 0% win rate today

---

## 💡 INTEGRATION

The comprehensive workflow automatically loads intraday learnings:

```python
# In comprehensive_workflow.py
intraday_learnings = load_intraday_learnings()
# Displays key insights before analyzing races
```

This ensures picks are influenced by real-time patterns, not just historical data.

---

## 🎲 STAKE ADJUSTMENT GUIDE

Based on intraday learnings:

| Pattern | Original Stake | Adjusted Stake |
|---------|---------------|----------------|
| Trainer 100% win rate today | 1.0x | 1.5x |
| Trainer 50%+ win rate today | 1.0x | 1.2x |
| Trainer 0% win rate today | 1.0x | 0.5x or SKIP |
| Odds range 75%+ win rate | 1.0x | 1.3x |
| Odds range 0% win rate | 1.0x | 0.5x or SKIP |

**Note:** Never increase stake beyond 2.0x of base recommendation

---

## ⚡ QUICK COMMANDS

```powershell
# Monitor dashboard (run anytime)
python race_monitor.py

# Update learnings (after races finish)
python intraday_learning_system.py

# View learnings file
Get-Content intraday_learnings.json | ConvertFrom-Json

# Re-run workflow with fresh insights
python comprehensive_workflow.py
```

---

## 📈 SUCCESS METRICS

Track these to measure system effectiveness:

1. **Early picks vs Late picks win rate**
   - Late picks should improve with more data

2. **Hot trainer hit rate**
   - Trainers winning early should continue

3. **Cold trainer avoidance**
   - Skipping cold trainers should reduce losses

4. **Odds range adaptation**
   - Following best-performing range improves ROI

---

## 🚨 ALERTS TO WATCH

**RED FLAGS:**
- Trainer 0/3+ today → SKIP or reduce stake
- All early favorites lost → Reconsider short-odds picks
- Sweet spot 0/5+ → Pattern breakdown (rare but critical)

**GREEN FLAGS:**
- Trainer 3/3+ today → Increase confidence
- Track has clear pattern (e.g., avg odds 4.5) → Focus on range
- Going conditions stable → Trust form analysis

---

## 📝 FILES GENERATED

- `intraday_learnings.json` - Latest patterns from today's races
- Race monitor displays real-time dashboard
- Workflow integrates learnings automatically

---

**Remember:** The goal is to make **BETTER** decisions on late races by learning from early races, not to chase patterns blindly.
