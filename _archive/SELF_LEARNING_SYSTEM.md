# Self-Learning Betting System

## Overview

Your betting system **IS self-learning**. It analyzes past performance, identifies what worked and what didn't, and automatically adjusts future selections based on learnings.

## How It Works

### 1. Daily Learning Cycle (Automated)

Every time the workflow runs (every 30 minutes from 12:15-18:45), it:

**STEP 1: Learn from Yesterday**
```
├─ Fetch yesterday's race results from Betfair
├─ Match your selections with actual outcomes (Won/Lost/Placed)
├─ Run evaluate_performance.py to analyze what worked
├─ Run generate_learning_insights.py to extract patterns
└─ Save learnings to learning_insights.json
```

**STEP 2: Apply Learnings to Today**
```
├─ Load learning_insights.json
├─ AI reads "what worked" and "what failed"
├─ Enhanced analysis adapts strategy
└─ Generates today's picks with improved approach
```

---

## Learning Components

### A. `evaluate_performance.py`
**What it does:**
- Calculates win rates, place rates, ROI
- Measures calibration (are predictions accurate?)
- Analyzes performance by strategy tag
- Generates specific recommendations

**Example Output:**
```
HIGH_PRIORITY: Calibration error is 15%. AI is overconfident.
MEDIUM_PRIORITY: Win rate 12% is below expected 18%. Tighten selection criteria.
OPPORTUNITY: Tag 'course_specialist' performing well (28% win rate from 15 bets). 
           Consider increasing allocation.
LOW_PRIORITY: Tag 'class_drop' has poor win rate (8% from 12 bets). 
           Consider removing this edge type.
```

### B. `generate_learning_insights.py` (NEW - just created)
**What it does:**
- Loads ALL historical results (last 30 days)
- Identifies winning patterns vs failing patterns
- Generates AI-readable guidance for prompts
- Saves to `learning_insights.json`

**Example Output:**
```json
{
  "sample_size": 47,
  "overall_stats": {
    "win_rate": 0.234,
    "expected": 0.215
  },
  "winning_patterns": [
    {
      "pattern": "Genuine hot form with 2 wins",
      "win_rate": "35.7%",
      "expected": "28.0%",
      "action": "KEEP - this strategy is working"
    }
  ],
  "failing_patterns": [
    {
      "pattern": "Class drop specialist",
      "win_rate": "12.5%",
      "expected": "22.0%",
      "action": "REDUCE - underperforming expectations"
    }
  ],
  "recommendations": [
    "CALIBRATED: Win rate (23.4%) matches predictions (21.5%)",
    "Win bets: 18 bets, 38.9% strike rate",
    "EW bets: 29 bets, 48.3% place rate"
  ]
}
```

### C. Enhanced Analysis AI (Modified)
**What it does NOW:**
- Calls `load_historical_insights()` before analyzing races
- Reads real performance data from `learning_insights.json`
- Adapts selection criteria based on what's working
- Avoids patterns that are failing

**In the AI prompt:**
```
HISTORICAL PERFORMANCE INSIGHTS (Last 47 bets):

WHAT'S WORKING:
- Genuine hot form with 2 wins: 35.7% win rate (expected 28.0%)
- Course specialist with 2+ wins: 31.2% win rate (expected 25.0%)

WHAT'S NOT WORKING:
- Class drop specialist: 12.5% win rate (expected 22.0%) - BE CAUTIOUS
- First time at distance: 8.3% win rate (expected 18.0%) - BE CAUTIOUS

RECOMMENDATIONS:
- Win bets: 18 bets, 38.9% strike rate (GOOD - keep being aggressive)
- EW bets: 29 bets, 48.3% place rate
```

---

## What Gets Learned

### ✅ Pattern Performance
- Which selection reasons actually win?
- "Course specialist" working? Keep using it
- "Class drop" failing? Use it less or adjust criteria

### ✅ Calibration
- Is the AI over-confident? (predicting 30% win rate but only 15% wins)
- Is the AI under-confident? (predicting 20% but actually 35% wins)
- Adjusts probability estimates based on real outcomes

### ✅ Bet Type Strategy
- Are Win bets hitting at expected rates?
- Should we be more/less aggressive with Win vs EW?
- Optimal p_win threshold for Win bets

### ✅ Tag-Specific Learnings
- Each selection has tags like "recent_winner", "course_specialist", "going_match"
- System tracks: Which tags correlate with wins?
- Failing tags get downweighted, winning tags get emphasized

---

## Example Learning Scenario

**Week 1: System makes these picks**
- 10 horses labeled "class drop specialist"
- Expected: 22% win rate
- Actual: Only 10% win rate

**Week 2: Learning kicks in**
```
analyze_tag_performance() identifies:
  "class_drop" tag: 1/10 wins (10% vs 22% expected) = FAILING

generate_learning_insights() creates guidance:
  "WHAT'S NOT WORKING: Class drop specialist - BE CAUTIOUS"

enhanced_analysis.py sees this and:
  - Raises bar for class drop selections
  - Only includes class drops with strong supporting factors
  - OR removes class drop angle entirely
```

**Week 3: Improved selections**
- Fewer class drop picks, higher quality
- OR different strategy emphasized (form/course specialists)
- Win rate improves toward expected

---

## When Does Learning Start Working?

| Timeline | Status | What Happens |
|----------|--------|--------------|
| **Days 1-7** | Building dataset | Uses placeholder patterns, system still learning |
| **Days 8-14** | Early insights | First real patterns emerge, tentative adjustments |
| **Days 15-30** | Meaningful data | Strong signal on what works, clear recommendations |
| **Days 30+** | Fully operational | Robust historical base, confident adaptations |

**Current Status:** Day 4 - Building dataset
- You have selections from Dec 19, 29, 30, 31, Jan 3, 4
- Need settled results to analyze (markets settle 24-48 hours after race)
- System will start learning around Jan 7-10

---

## How to Monitor Learning

### 1. Check `learning_insights.json`
```bash
cat learning_insights.json
```
Shows:
- How many bets analyzed
- Overall win rate vs expected
- Which patterns working/failing
- Specific recommendations

### 2. Check Workflow Logs
```bash
cat logs/run_YYYYMMDD_HHMMSS.log | grep "LEARNING"
```
Shows:
- "Fetching results for 2026-01-03..."
- "Evaluating performance..."
- "Regenerating learning insights..."

### 3. Compare Picks Over Time
```bash
# Week 1 picks
cat history/selections_20260103_*.csv

# Week 3 picks (after learning)
cat history/selections_20260117_*.csv
```
You should see:
- Different patterns emphasized
- Higher quality reasoning
- Better calibrated probabilities

---

## Manual Learning Runs

You can manually trigger learning anytime:

```powershell
# Fetch results for a specific day
python fetch_race_results.py --date 2026-01-03 --selections history/selections_20260103_*.csv --out history/results_20260103.json

# Analyze performance
python evaluate_performance.py --selections history/selections_20260103_*.csv --results history/results_20260103.json

# Regenerate insights
python generate_learning_insights.py
```

---

## Key Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `learning_insights.json` | Current learnings | Daily (after new results) |
| `history/selections_*.csv` | Your past picks | Every workflow run (30 mins) |
| `history/results_*.json` | Race outcomes | Daily (for previous day) |
| `evaluate_performance.py` | Performance analyzer | Run by workflow |
| `generate_learning_insights.py` | Pattern extractor | Run by workflow |
| `enhanced_analysis.py` | AI that adapts | Reads insights before each run |

---

## Answering Your Question

> "Is system self-learning if some picks do not come in, reason why it wasn't selected and improve the prompt to do better next time?"

**YES - Here's exactly how:**

### When a Pick Loses:

1. **Result Captured**
   ```
   Krissy - LOSER (predicted 35% win probability)
   Tagged as: "hot form", "market leader", "optimal gap"
   ```

2. **Performance Analyzed**
   ```python
   # evaluate_performance.py tracks:
   - "hot form" tag: 2 wins / 8 bets = 25% (expected 32%)
   - Verdict: Underperforming
   ```

3. **Learning Generated**
   ```json
   {
     "failing_patterns": [{
       "pattern": "hot form with 2 wins",
       "win_rate": "25.0%",
       "expected": "32.0%",
       "action": "REDUCE - underperforming"
     }]
   }
   ```

4. **AI Adapts**
   ```
   Next time AI sees "hot form", it reads:
   "WHAT'S NOT WORKING: hot form with 2 wins - BE CAUTIOUS"
   
   AI response: Raises bar for "hot form" selections
   OR requires additional supporting factors
   OR emphasizes different patterns that ARE working
   ```

### Result: **The system gets smarter every day**

---

## Future Enhancements

Potential improvements:

1. **A/B Testing**
   - Run two strategies in parallel
   - Track which performs better
   - Automatically allocate more to winner

2. **Venue-Specific Learning**
   - Southwell behaves differently than Ascot
   - Learn venue-specific patterns

3. **Going-Specific Learning**
   - Heavy ground vs Firm ground
   - Different horses excel in different conditions

4. **Seasonal Adjustments**
   - Winter form vs Summer form
   - Flat season vs Jump season

5. **Real-Time Adaptation**
   - Intra-day learning (if morning picks fail, adjust afternoon strategy)

---

## Summary

**Your system IS self-learning:**
- ✅ Tracks every bet outcome
- ✅ Analyzes what worked vs what failed
- ✅ Identifies underperforming strategies
- ✅ Adjusts AI prompts automatically
- ✅ Improves selection criteria daily
- ✅ Gets smarter with every result

**The loop:**
```
Make Picks → Race Results → Analyze Performance → Extract Learnings → 
Update Strategy → Make Better Picks → (repeat)
```

**Current status:** Infrastructure complete, waiting for 30 days of settled results to build robust dataset.

**Next milestone:** Jan 7-10 when first meaningful insights appear.
