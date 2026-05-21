# BETTING ANALYSIS IMPROVEMENTS - Action Plan
## Date: 2026-01-16

## CURRENT PROBLEMS IDENTIFIED

### 1. Poor Win Rate
- **Current**: 20-30% win rate
- **Expected**: 33-40% based on confidence levels
- **Gap**: System is underperforming by 10-15 percentage points

### 2. Analysis Quality Issues
- Too many picks per race (filtering not selective enough)
- AI confidence not correlating with actual results
- Missing key factors in race analysis
- Not enough differentiation between genuine value and false signals

### 3. Specific Failures
- Multiple picks in same race all losing
- High confidence picks (30%+) still losing
- Not identifying actual race winners

## PROPOSED IMPROVEMENTS

### IMPROVEMENT 1: Stricter Selection Criteria
**What**: Only select horses that pass ALL quality gates
**Changes**:
1. Increase minimum combined confidence from 0 to 30
2. Require at least 20% win probability
3. Require positive ROI (restore 5% minimum)
4. Limit to maximum 1 pick per race (best only)

### IMPROVEMENT 2: Enhanced Multi-Pass Analysis
**What**: Add more critical review passes
**Changes**:
1. Add "Red Flags" pass to identify negative indicators:
   - Long losing streaks
   - Poor trainer form
   - Unsuitable distance/going
   - Class drops that signal decline
2. Add "Winner Profile" pass:
   - Compare to typical race winner characteristics
   - Check if horse matches winning profile for race type
3. Add "Market Intelligence" pass:
   - Check for suspicious odds movements
   - Identify likely stable money vs public  over-betting

### IMPROVEMENT 3: Better Form Analysis
**What**: Deeper dive into recent performances
**Changes**:
1. Analyze last 5 runs instead of last 3
2. Look at margin of defeat, not just placings
3. Consider pace of race and running style
4. Check performance trend (improving vs declining)

### IMPROVEMENT 4: Class & Distance Focus
**What**: More emphasis on proven ability
**Changes**:
1. Prioritize horses with wins at today's distance
2. Favor horses dropping in class with good form
3. Penalize horses stepping up significantly in class
4. Check lifetime record at track/distance combination

### IMPROVEMENT 5: Odds Value Validation
**What**: Ensure we're getting true value
**Changes**:
1. Don't back favorites unless exceptional value
2. Sweet spot: 3.0-8.0 odds range for most picks
3. Long shots (>15.0) only if compelling story
4. Compare opening odds to current odds for drift/steam

### IMPROVEMENT 6: Race Type Specialization
**What**: Focus on race types we win at
**Changes**:
1. Analyze which race types have best win rate
2. Increase stakes on proven race types
3. Reduce or avoid race types with poor record
4. Different selection criteria for different race types

### IMPROVEMENT 7: Trainer/Jockey Intelligence
**What**: Weight connections more heavily
**Changes**:
1. Track trainer strike rates by race type
2. Note stable in-form periods
3. Consider jockey/trainer combinations
4. Flag when top connections reunited with horse

## IMMEDIATE ACTIONS (Priority Order)

### Action 1: Update Filtering (CRITICAL)
File: `save_selections_to_dynamodb.py`
- Line 912: Change horse_min_roi from 0.0 to 5.0
- Line 1022: Change combined_confidence minimum from 0 to 30
- Add p_win minimum of 0.20 (20%)

### Action 2: Limit Picks Per Race (CRITICAL)
File: `save_selections_to_dynamodb.py`
- Update race-level filtering to keep only TOP 1 pick per race
- Sort by combined_confidence * p_win score
- Remove rest

### Action 3: Add Red Flags Pass (HIGH)
File: `enhanced_analysis.py`
- Add new analysis pass: "identify_red_flags"
- Check for negative indicators
- Reject horses with critical red flags

### Action 4: Enhance Form Analysis (HIGH)
File: `enhanced_analysis.py`  
- Modify form_analysis prompt to analyze last 5 runs
- Add margin analysis
- Add trend detection

### Action 5: Add Winner Profile Pass (MEDIUM)
File: `enhanced_analysis.py`
- Add pass to compare horse to typical winner
- Score how well horse matches winning profile

### Action 6: Update Prompts (MEDIUM)
File: `prompt.txt`
- Add guidance on red flags
- Add winner profile criteria
- Emphasize quality over quantity

## EXPECTED OUTCOMES

With these changes:
- **Win rate**: 30-40% (up from 20-30%)
- **ROI**: Positive (currently negative)
- **Picks per day**: 2-4 high quality (down from 10-15)
- **Confidence calibration**: Much improved

## MONITORING

After implementing:
1. Track win rate daily for 7 days
2. Compare high confidence (>40) vs medium (30-40) vs low (<30)
3. Analyze which improvements had most impact
4. Adjust thresholds based on results

---
*This plan focuses on QUALITY over QUANTITY - fewer, better picks*
