# CORRECTED Performance Analysis - Featured vs Daily Top Picks

**Date:** 2026-05-20  
**Status:** CORRECTED - Previous analysis was wrong

---

## APOLOGY: Previous Analysis Was Incorrect

**My mistake:** I thought you were showing 300+ picks to users. You're not.

**Reality:**
- **Database:** 400 total picks generated algorithmically (internal candidates)
- **Shown to users:** Only 9 picks with `show_in_ui=True` (your "top 5 picks" system)
- **Featured meeting:** 5 curated picks separately

You already have a quality filter - `show_in_ui=True` - that selects only the best picks!

---

## REAL Question: Why Featured (80%) Beats Top Daily Picks (~44%)?

### May 20, 2026 Performance

**Daily Top Picks API (`/api/results/today`):**
- Picks shown: 9
- Winners: 4
- **Win Rate: 44.4%** (not 4.3% - that was internal picks!)
- This is actually GOOD performance

**Featured Meeting (Gowran Park):**
- Picks shown: 5
- Winners: 4
- **Win Rate: 80%**
- ROI: +295%

**Gap:** Featured is 35.6 percentage points better (80% vs 44.4%)

---

## The Real Difference: Curation Strategy

### Daily Top Picks Selection

Looking at the 9 picks shown on May 20:
```
Pick Ranks: [2.0, 1.0, 5.0, 3.0, 1.0, 2.0, 3.0, 4.0, 4.0]
```

This shows picks are selected as "top X from each meeting":
- Multiple picks with rank=1 (top pick from different meetings)
- Multiple picks with rank=2, rank=3, etc.
- Spreading across 6 different courses

**Strategy:** "Best pick from each major meeting"

### Featured Meeting Selection

**Strategy:** "Top 5 picks from ONE meeting only"
- All 5 picks from Gowran Park
- Deep analysis of single meeting
- Course-specific knowledge applied

---

## Why Featured Outperforms: Hypothesis

### 1. **Focus vs Diversification**

**Daily Picks:** Best pick from Meeting A + Best pick from Meeting B + Best pick from Meeting C...
- Pros: Diversified across courses
- Cons: No deep expertise on any single course

**Featured:** Top 5 picks from Meeting A only
- Pros: Deep course expertise, ground conditions, jockey/trainer stats for that venue
- Cons: All eggs in one basket (if meeting is rained off, all picks gone)

**Winner:** Featured (80%) vs Daily (44%)

Evidence: When you focus on ONE meeting deeply, you catch patterns the algorithm misses across multiple meetings.

---

### 2. **Expert Curation Layer**

**Daily Picks:** Algorithmic selection
- score + confidence_grade + pick_rank
- No human review layer

**Featured:** Algorithmic + Expert Review
- Algorithm generates candidates
- Human expert reviews and curates final 5
- Expert can override algorithm based on:
  - Recent course changes
  - Weather impact on going
  - Jockey booking patterns
  - Stable confidence

**Winner:** Featured (with expert layer)

---

### 3. **Sample Size Effect** (May not be sustainable)

**Important Consideration:**
- Featured: 5 picks (small sample)
- Daily: 9 picks (slightly larger sample)
- **80% win rate on 5 picks = 4 winners**
- If one more pick had won, featured would be 60% (not 80%)
- If one more pick had lost, daily would be 33% (not 44%)

**Question:** Is 80% sustainable, or was May 20 an outlier?

Need to check: Historical featured meeting performance over 30+ days

---

## Historical Validation Needed

To understand if featured truly outperforms, we need:

### 1. Featured Meeting Long-Term Stats
- Last 30 days of featured meetings
- Average win rate
- Average ROI
- Consistency (standard deviation)

### 2. Daily Picks Long-Term Stats
- Last 30 days of top daily picks
- Average win rate
- Average ROI
- Consistency

### 3. Statistical Significance
- Is the difference statistically significant?
- Or is May 20 just a lucky day for featured?

**Current Data:** We have cumulative ROI of 54.8% over 216 races, but this doesn't separate:
- Daily picks performance
- Featured meeting performance
- Which contributes more to overall ROI?

---

## What We Actually Know

### Confirmed Facts:

1. **You DO filter picks** ✅
   - Database: 400 internal picks
   - Shown to users: 9 picks
   - Filter: `show_in_ui=True` + `pick_rank > 0`

2. **Featured does better (May 20)** ✅
   - Featured: 4/5 (80%)
   - Daily: 4/9 (44%)

3. **Overall system is profitable** ✅
   - 54.8% ROI over 216 races
   - This is EXCELLENT for betting

### Unknown:

1. **Is 80% featured win rate sustainable?**
   - Need 30+ days of data
   - May 20 could be outlier

2. **Does daily picks strategy need changing?**
   - 44% win rate is actually good
   - Maybe it's fine as-is

3. **Should we do MORE featured meetings?**
   - If featured consistently beats daily picks
   - Could do 2-3 featured meetings per day

---

## Revised Recommendations

### Do NOT Change Daily Picks Algorithm

**Your current system is working:**
- Filters 400 candidates → 9 top picks
- 44% win rate on May 20 (good!)
- 54.8% ROI overall (excellent!)

**Original recommendation to "add score >80 filter" was wrong** - you already have an effective filter!

---

### DO Investigate Featured Meeting Strategy

**Questions to answer:**

1. **Sustainability Test:**
   ```sql
   -- Get last 30 days of featured meetings
   -- Calculate win rate per meeting
   -- Calculate average win rate across all meetings
   -- Is 80% an anomaly or typical?
   ```

2. **Compare Apples to Apples:**
   - Featured meeting: 5 picks from 1 course
   - Daily picks: 9 picks from 6 courses
   - **Better comparison:** What if we picked top 5 from Gowran Park in daily system?
   - Would daily system ALSO have picked those 4 winners?

3. **Attribution Analysis:**
   - Of the 54.8% overall ROI (216 races):
     - How much from daily picks?
     - How much from featured meetings?
     - Which strategy contributes more profit?

---

### DO Expand Featured Meetings (If Data Supports)

**If historical data shows featured consistently outperforms:**

**Current:**
- 1 featured meeting per day
- 5 picks per meeting

**Proposed:**
- 2-3 featured meetings per day
- 5 picks per meeting
- Total: 10-15 featured picks/day

**Benefits:**
- More of what works (if data proves it works)
- Premium tier justification
- Better user engagement (curated quality)

**Risks:**
- Need to maintain expert review for 2-3 meetings (more work)
- If one meeting is poor, affects multiple picks
- Less diversification across courses

---

## Action Plan

### Week 1: Data Collection ✅

```python
# Script: scripts/analyze_featured_historical_performance.py

# Query last 60 days of featured meetings
# For each meeting, calculate:
#   - Date
#   - Course
#   - Number of picks
#   - Winners
#   - Win rate
#   - ROI
#   - Profit

# Calculate:
#   - Average win rate across all featured meetings
#   - Standard deviation (consistency)
#   - Compare to daily picks average over same period
```

### Week 2: Decision Point

**If featured average win rate > 60% consistently:**
→ Expand to 2-3 featured meetings per day

**If featured average win rate = 40-50%:**
→ Keep current strategy (1 meeting/day)
→ Featured is good but not dramatically better

**If featured average win rate < 40%:**
→ May 20 was an outlier
→ Don't expand featured strategy

---

## Corrected Conclusion

**What I Got Wrong:**
- Thought you showed 300+ picks to users (you don't)
- Thought you had no quality filter (you do - `show_in_ui=True`)
- Recommended adding a filter (you already have one!)

**What's Actually True:**
- You show 9 curated picks to users (not 300+)
- Daily picks: 44% win rate on May 20 (GOOD)
- Featured: 80% win rate on May 20 (EXCELLENT, but is it sustainable?)
- Overall: 54.8% ROI (EXCELLENT)

**Real Question:**
- Is featured meeting strategy consistently better?
- Or was May 20 just a good day?
- Need historical data to answer

**Real Recommendation:**
- DON'T change daily picks algorithm (it's working!)
- DO analyze historical featured meeting performance
- DO expand featured meetings if data supports it
- DON'T fix what isn't broken

---

**Corrected By:** Claude Sonnet 4.5  
**Date:** 2026-05-20  
**Status:** Ready for historical data analysis
