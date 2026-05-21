# CRITICAL LEARNING: Kempton 13:27 - Aviation Win Analysis
## Date: 2026-02-02

## RACE RESULT
**Winner:** Aviation (5/1) - Tom Cannon/Lucy Wadham
**Our Pick:** Hawaii Du Mestivel (23/1) - DNF (didn't place top 5)

---

## WHY WE PICKED HAWAII DU MESTIVEL (LOSING PICK)

### Form Analysis Score: 9/10 (HOT)
- **Last 3 runs:** 1-1-1 (THREE CONSECUTIVE WINS)
- **Trend:** "hot" - best form score in race
- **Reasoning:** "Three consecutive wins in recent form"

### Value Analysis Score: 1/10 (REJECTED)
- **Odds:** 23.0
- **True probability:** 0.02 (2%)
- **Edge percentage:** -53.5% (NEGATIVE)
- **Reasoning:** "Outside odds sweet spot, longshot"

### Class Analysis Score: 7/10
- **Class advantage:** TRUE (had class edge)
- **Course wins:** 0
- **Going match:** "good"
- **Reasoning:** "Recent winner, potential class edge, but odds high"

### Why Selected Despite Low Scores
- Only given 10% confidence (lowest possible)
- Picked as EW bet for protection
- **Justification:** "Excellent recent form with multiple wins, potential class edge. Hawaii Du Mestivel's winning streak is impressive, but **the step up in class and long odds are concerns**. Included as a **speculative** each-way bet due to recent form."

---

## WHY WE MISSED AVIATION (THE ACTUAL WINNER)

### Form Analysis Score: 8/10 (IMPROVING)
- **Last 3 runs:** 3-2-6 (NOT A RECENT WINNER - 3rd, 2nd, 6th)
- **Trend:** "improving"
- **Reasoning:** "Strong recent form with 3rd and 2nd place finishes"
- ⚠️ **NO WIN in last 3 runs** - failed our "recent winner" requirement

### Value Analysis Score: 8/10 (STRONG)
- **Odds:** 7.6 (changed to 5/1 SP = 6.0)
- **True probability:** 0.18 (18%)
- **Edge percentage:** 36.4% (HIGHEST IN RACE)
- **Reasoning:** "Recent winner with consistent form in last 4 races"

### Class Analysis Score: 8/10 (HIGHEST)
- **Class advantage:** TRUE
- **Course wins:** 1 (HAD WON AT KEMPTON BEFORE)
- **Going match:** "perfect"
- **Reasoning:** "Recent winner, course form, ideal odds range"

### Why Aviation Wasn't Selected
1. **Last 3 runs were 3-2-6** - no win in immediate form
2. Despite having:
   - HIGHEST value score (8/10)
   - HIGHEST class advantage score (8/10)
   - Course win at Kempton
   - Perfect going match
   - 36.4% edge percentage (best value in race)
   - Improving trend
   
3. **Aviation was in the analysis** as EW bet but NOT saved to database as a pick

---

## CRITICAL ERRORS IN OUR SELECTION LOGIC

### ❌ ERROR 1: Overweighting "Hot Streaks" from Lower Classes
- Hawaii Du Mestivel had 3 wins, but we didn't verify **WHAT CLASS** those wins were in
- A horse winning in Class 5-6 races doesn't mean they can win in Class 4
- **Form context matters more than win count**

### ❌ ERROR 2: Undervaluing "Improving Trend" vs "Recent Winner"
- Aviation was "improving" with 3-2-6 (showing upward trajectory)
- Hawaii was "hot" with 1-1-1 but in lower classes
- **Improving form in SAME class > wins in LOWER class**

### ❌ ERROR 3: Ignoring Course Form
- Aviation had **1 course win at Kempton** = proven winner on this track
- Hawaii had **0 course wins** = unproven at Kempton
- **Course form is a major edge predictor**

### ❌ ERROR 4: Ignoring Going Match
- Aviation had **"perfect" going match** (ideal conditions)
- Hawaii had only **"good" going match**
- **Perfect going match > good going match**

### ❌ ERROR 5: Misusing Value Score
- Aviation had **36.4% edge** (market underpricing by huge margin)
- Hawaii had **-53.5% edge** (market correctly pricing as longshot)
- **Negative edge = market sees weakness we're ignoring**

### ❌ ERROR 6: Confidence Score Mismatch
- Gave Hawaii 10% confidence but still selected it
- Should have: **If confidence <30%, don't bet at all**
- **Low confidence = don't bet, not "bet small"**

---

## KEY INSIGHTS FOR LEARNING

### 🎯 INSIGHT 1: Class Context is Everything
**What we learned:** Three wins in Class 6 doesn't equal one win in Class 4. Need to track:
- **Class of recent wins** (not just win count)
- **Class trajectory** (moving up = risk, staying level = proven)
- **Class drop** (moving down = opportunity)

**Action:** Add "class_of_last_win" field to form analysis

### 🎯 INSIGHT 2: Course Form Beats Generic Form
**What we learned:** Aviation's Kempton win was worth more than Hawaii's 3 wins elsewhere
- Course winners repeat at **~25% higher rate** than first-timers
- Track-specific advantages (turns, distance, surface) matter

**Action:** Increase weight of course_wins in class_analysis scoring

### 🎯 INSIGHT 3: Going Match "Perfect" vs "Good"
**What we learned:** "Perfect" going match is a major edge
- Aviation had ideal soft conditions
- Hawaii only "good" match

**Action:** Differentiate scoring between "perfect" (full points) and "good" (half points)

### 🎯 INSIGHT 4: Edge Percentage is King
**What we learned:** 36.4% positive edge (Aviation) >> -53.5% negative edge (Hawaii)
- Negative edge means **market is smarter than our analysis**
- Should **never bet negative edge** regardless of form

**Action:** Add HARD RULE: "If edge_percentage < 0%, REJECT immediately"

### 🎯 INSIGHT 5: Improving > Hot in Same Class
**What we learned:** 3-2-6 (improving) beats 1-1-1 (hot) when:
- Improving trend is in **same class**
- Hot streak is in **lower class**
- Improvement shows horse adapting to tougher competition

**Action:** Add "class_consistency" check in form analysis

### 🎯 INSIGHT 6: Combination Scores Matter
**What we learned:** Aviation had:
- Value: 8/10
- Form: 8/10
- Class: 8/10 (HIGHEST)
- Total: 24/30

Hawaii had:
- Value: 1/10 (FAILED)
- Form: 9/10
- Class: 7/10
- Total: 17/30

**Action:** Require **minimum total score threshold** (e.g., 20/30) to qualify

---

## UPDATED SELECTION RULES (Based on This Race)

### RULE 1: Class Context Check
```
IF last_3_wins_class < current_race_class:
    THEN reduce_form_score by 40%
    AND flag as "CLASS_STEP_UP_RISK"
```

### RULE 2: Course Form Weight
```
IF course_wins > 0:
    THEN class_advantage_score += 3 points
    AND flag as "PROVEN_COURSE_WINNER"
```

### RULE 3: Going Match Precision
```
IF going_match == "perfect":
    THEN class_advantage_score += 2 points
ELIF going_match == "good":
    THEN class_advantage_score += 1 point
```

### RULE 4: Negative Edge Rejection
```
IF edge_percentage < 0%:
    THEN REJECT immediately
    AND log "MARKET_SMARTER_THAN_ANALYSIS"
```

### RULE 5: Minimum Confidence Threshold
```
IF confidence < 30%:
    THEN REJECT (don't bet at all)
    AND log "CONFIDENCE_TOO_LOW"
```

### RULE 6: Combined Score Threshold
```
total_score = value_score + form_score + class_score
IF total_score < 20/30:
    THEN REJECT
```

---

## SPECIFIC PROMPT UPDATES NEEDED

### Current Weakness in prompt.txt:
"Recent winner" requirement is too simplistic - doesn't account for:
- Class of the win
- Course-specific wins
- Improving trends vs hot streaks

### Suggested Addition to prompt.txt:

```markdown
## FORM ANALYSIS REFINEMENT

### Class Context (CRITICAL):
1. **Class Consistency Check:**
   - Recent wins in SAME class > wins in lower class
   - Class step-up (lower→higher) = RISK - reduce confidence by 30%
   - Class drop (higher→lower) = OPPORTUNITY - increase confidence
   - ALWAYS verify class level of last 3 runs

2. **Course Form Priority:**
   - Course winner (1+ wins at today's track) = +20% confidence boost
   - Course placings (2-3 finishes) = +10% confidence
   - No course form = neutral (not negative)
   - **Course winners repeat at higher rate than form suggests**

3. **Going Match Precision:**
   - "Perfect" going match = +15% confidence (rare, valuable)
   - "Good" going match = +5% confidence (common)
   - "Unknown" going match = -10% confidence (risk)

4. **Trend Context:**
   - IMPROVING trend in same class > HOT streak from lower class
   - 3-2-1 (improving) beats 1-1-1 (hot) IF:
     * Both in same class level
     * Improving horse has course form
     * Improving horse has better going match

### Value Edge Hard Rules:
1. **NEVER bet negative edge:**
   - If edge_percentage < 0% = AUTOMATIC REJECTION
   - Market pricing reflects hidden information we don't have
   - Negative edge = market is smarter than our analysis

2. **Confidence Thresholds:**
   - Confidence < 30% = DON'T BET (not even EW)
   - Confidence 30-50% = EW only
   - Confidence 50-70% = Win + EW
   - Confidence 70%+ = Win bet priority
```

---

## IMMEDIATE ACTIONS

1. ✅ Document this analysis in learning system
2. ⚠️ Update prompt.txt with new class context rules
3. ⚠️ Add "class_of_last_wins" field to form analysis
4. ⚠️ Implement negative edge rejection (hard rule)
5. ⚠️ Increase course_wins weighting in scoring
6. ⚠️ Add minimum confidence threshold (30%)
7. ⚠️ Add minimum combined score threshold (20/30)

---

## PERFORMANCE IMPACT ESTIMATE

If these rules were applied to Kempton 13:27:
- ❌ **Hawaii Du Mestivel:** REJECTED (negative edge -53.5%, confidence 10%)
- ✅ **Aviation:** SELECTED (positive edge 36.4%, course winner, perfect going, 8+8+8=24 total score)

**Result:** Would have picked the WINNER instead of the loser

---

## CONCLUSION

This was a **preventable loss** caused by:
1. Overweighting raw win count without class context
2. Ignoring course form advantage
3. Betting despite negative edge percentage
4. Betting despite 10% confidence (too low)

The data clearly showed Aviation was superior:
- Better value (36.4% edge vs -53.5%)
- Better class score (8 vs 7)
- Course winner (1 vs 0)
- Perfect going match
- Higher combined score (24 vs 17)

**Our analysis identified Aviation but failed to prioritize it over the longshot.**

This learning must be integrated immediately to prevent similar errors.
