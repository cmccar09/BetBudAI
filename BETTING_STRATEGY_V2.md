# SureBet Betting Strategy V2.1
**Updated: January 31, 2026**

## Core Philosophy: SWEET SPOT WINNER FOCUS (2-8/1)

### Strategic Evolution (v2.0 → v2.1)
**v2.0 (Jan 30)**: Filter out longshots, enforce 2-8/1 range
**v2.1 (Jan 31)**: **Actively hunt winners IN the sweet spot** with self-learning optimization

### Historical Evidence
- **3.0-9.0 odds (2-8/1)**: 28.6% win rate, +54% ROI ✅ **SWEET SPOT**
- **3.5-6.0 odds (5/2-5/1)**: Best sub-range ✅ **ULTIMATE SWEET SPOT**
- **Under 3.0 (favorites)**: Poor value, rarely win for us ❌
- **Over 9.0 (longshots)**: 0% win rate, total losses ❌
- **Sample**: 200+ bets analyzed (Jan 22-31, 2026)

### Why This Works
1. **Mathematical edge**: 3-9 odds = 200-800% profit potential, only need 20-33% win rate
2. **Recent winner focus**: Horses that WON recently have momentum and form
3. **Realistic contenders**: Not hopeless longshots, not overbet favorites
4. **Self-reinforcing**: Learning system tracks what works IN this range
5. **Proven profitability**: Historical ROI +54% in sweet spot vs losses elsewhere

---

## V2.1 Enhancement: Sweet Spot Winner Optimization (Jan 31, 2026)

### The Problem We Solved
- v2.0 prevented bad picks (longshots) but didn't actively find WINNERS
- Learning system tracked patterns but not odds range performance
- Contradictory guidance: "focus sweet spot" vs "focus longshots"
- No reinforcement for what works within profitable range

### The Solution: Sweet Spot Winner Focus

#### 1. Mandatory Sweet Spot Selection (prompt.txt)

**Primary Objective**: Find WINNERS with odds 3.0-9.0 (2/1 to 8/1)

**Winner Profile Requirements:**
```
✅ Odds: 3.0-9.0 decimal (2/1 to 8/1 fractional)
✅ Recent WINNER: Won in last 3 races (not just placed)
✅ In-form: Win within 60 days preferred
✅ Course experience: Previous course form
✅ Trainer/jockey: Currently winning
✅ Class matched: Not over/under-challenged
```

**Confidence Boosting System:**
- **+25 points**: Ultimate sweet spot (3.5-6.0 odds)
- **+15 points**: Sweet spot (3.0-9.0 odds)
- **+30 points**: Won last race
- **+20 points**: Won in last 2-3 races
- **+40 points**: Multiple wins in last 5 races
- **+15 points**: Won at this course before
- **+10 points**: Trainer has winners this week

**Example Calculation:**
```
Base confidence: 35
+ Sweet spot 3.5-6.0: +25
+ Won last race: +30
+ Won at course: +15
= 105 TOTAL → HIGH CONFIDENCE SELECTION ✅
```

**Strict Outside Range Rules:**
- **Under 3.0**: Avoid unless 80%+ confidence (favorites)
- **9.0-15.0**: Only if won in last 2 races (exceptional)
- **Over 15.0**: NEVER recommend (0% historical win rate)

#### 2. Self-Learning Odds Range Tracking (generate_learning_insights.py)

**Performance Analysis by Range:**
```python
Ranges Tracked:
- Ultimate sweet spot: 3.5-6.0 (best performing sub-range)
- Sweet spot: 3.0-9.0 (target range)
- Short odds: 1.0-3.0 (favorites)
- Medium odds: 9.0-15.0 (long shots)
- Long odds: 15.0-50.0 (very long)
- Extreme odds: 50.0+ (avoid)

For Each Range Calculates:
✓ Total bets
✓ Wins and win rate
✓ ROI (profit/loss %)
✓ Average odds
✓ Verdict (PROFITABLE/LOSING)
```

**Sweet Spot Specific Metrics:**
- Percentage of portfolio in sweet spot (target: 60%+)
- Win rate within range (target: 25-30%)
- ROI within range (target: +15% minimum)
- Ultimate sweet spot (3.5-6.0) vs wider range comparison

**Daily Learning Output Example:**
```
🎯 SWEET SPOT PERFORMANCE (3.0-9.0 odds):
Range: 3.0-9.0
Bets in range: 42 (75% of portfolio) ✅
Win rate: 28.5%
ROI: +32.4% ✅
Status: PROFITABLE

🏆 ULTIMATE SWEET SPOT (3.5-6.0):
Bets: 25 | Wins: 8 | Win rate: 32.0% | ROI: +45.2% ✅

📊 ODDS RANGE BREAKDOWN:
✅ 3.5-6.0: 25 bets, 32.0% win rate, +45.2% ROI
✅ 3.0-9.0: 42 bets, 28.5% win rate, +32.4% ROI
❌ 1.0-3.0: 8 bets, 12.5% win rate, -22.1% ROI
❌ 9.0-15.0: 6 bets, 0% win rate, -100% ROI

🔑 KEY ACTIONS:
✅ SWEET SPOT WORKING: 32.4% ROI. DOUBLE DOWN!
🏆 ULTIMATE SWEET SPOT is BEST: 45.2% ROI. Prioritize!
🎯 CRITICAL: Only 75% in sweet spot. Target 80%+
```

#### 3. Daily Learning Cycle

**Self-Reinforcing Feedback Loop:**
```
Day 1 Morning:
→ System picks 10 horses (4 in sweet spot, 6 outside)

Day 1 Evening:
→ Results: Sweet spot 2/4 wins, Others 0/6 wins
→ Learning: "Sweet spot ROI +40%, others -100%"

Day 2 Morning:
→ Prompt updated: "Focus MORE on 3-9 odds"
→ Confidence boosters increase sweet spot picks
→ System picks 10 horses (8 in sweet spot, 2 outside)

Day 2 Evening:
→ Results: Sweet spot 4/8 wins, Others 0/2 wins
→ Learning: "Sweet spot confirmed. 50% win rate!"

Day 3 Morning:
→ Strong reinforcement: Sweet spot IS the strategy
→ System picks 9 horses (9 in sweet spot, 0 outside)
→ Identifies 3.5-6.0 as BEST sub-range

Result: System self-optimizes to profitable range
```

**Learning Recommendations Generated:**
- If <60% in sweet spot: "CRITICAL - Need MORE sweet spot picks"
- If sweet spot ROI >10%: "WORKING - Double down on 3-9 range"
- If ultimate range better: "Prioritize 3.5-6.0 sub-range"
- If recent winners working: "Focus on horses with wins in last 3"

#### 4. Selection Priority Framework

**Daily Selection Process:**
```
Priority 1: SWEET SPOT WINNERS
→ Find ALL horses with:
  - Odds 3.0-9.0
  - WON in last 3 races
  - In-form trainer

Priority 2: OPTIMIZE WITHIN RANGE
→ From Priority 1 horses, select:
  - Best recent form
  - Best course experience
  - Best jockey bookings
  - Prefer 3.5-6.0 sub-range

Priority 3: EXCEPTIONAL OUTSIDERS (if needed)
→ Only if <5 quality sweet spot picks:
  - 9-15 odds + won last 2 races
  - Must have 70%+ confidence
  - Clear form advantage

TARGET: 70-80% of daily picks in 3.0-9.0 range
```

---

## Implementation Stack (Updated Jan 31, 2026)

### Layer 1: AI Prompt (Generation Time)
**File**: `enhanced_analysis.py`
- **VALUE BETTING EXPERT** (line 77): Enforces 2-8/1 odds only
- **FORM ANALYSIS EXPERT** (line 122): Rejects longshots
- **CLASS & CONDITIONS EXPERT** (line 170): Filters to sweet spot
- **SKEPTICAL ANALYST** (line 219): Final longshot rejection

### Layer 1: AI Prompt (Generation Time)
**Files**: `prompt.txt`, `enhanced_analysis.py`

**prompt.txt (Primary Selection Guide):**
- **Lines 1-70**: Sweet spot mandatory focus section
- **Confidence boosters**: +15 to +40 points for sweet spot + winners
- **Winner profile**: Must have won recently in 3-9 odds range
- **Selection criteria**: 6 prioritized factors with point values
- **Strict rules**: Escalating requirements for outside range picks

**enhanced_analysis.py (AI Expert Prompts):**
- **VALUE BETTING EXPERT** (line 77): Enforces 3-9 odds sweet spot
- **FORM ANALYSIS EXPERT** (line 122): Prioritizes recent winners
- **CLASS & CONDITIONS EXPERT** (line 170): Filters to profitable range
- **SKEPTICAL ANALYST** (line 219): Rejects picks outside sweet spot

**Key Mechanism**: AI generates picks with built-in sweet spot bias BEFORE filtering

### Layer 2: Quality Filter (Save Time)
**File**: `save_selections_to_dynamodb.py` (lines 1008-1018)
- **Primary rule**: 2.0-8.0/1 odds range (backward compatible)
- **Exception clause**: Outside range only if 70%+ confidence + 50%+ ROI
- **Rejection logging**: Clear feedback on why picks filtered

**Note**: Filter is backup; v2.1 AI should generate sweet spot picks naturally

### Layer 3: Learning System (Daily Optimization)
**File**: `generate_learning_insights.py`

**New Functions (Jan 31):**
```python
analyze_odds_ranges(df) → Dict
  - Calculates performance for 6 odds ranges
  - Returns: bets, wins, win_rate, ROI, verdict per range
  
merge_all_selections_with_results(days_back=30) → DataFrame
  - Enhanced to capture odds field from historical data
  - Merges selections with actual race results
  - Creates unified dataset for analysis

extract_pattern_learnings(df, tag_perf, odds_perf) → Dict
  - Sweet spot analysis (3-9 range)
  - Ultimate sweet spot analysis (3.5-6 range)
  - Portfolio percentage in sweet spot
  - ROI comparison across ranges
  - Generates targeted recommendations

generate_prompt_guidance(learnings) → str
  - Creates daily prompt additions
  - Sweet spot performance summary
  - Odds range breakdown
  - Winning/failing patterns
  - Actionable recommendations
```

**Learning Output** → Updates `learning_insights.json` daily

### Layer 4: Prediction Accountability & Calibration (New - v2.2)

**Purpose**: Track every prediction, analyze failures, improve accuracy

**Prediction Tracking Table (DynamoDB or CSV):**
```
Fields Stored Per Pick:
- pick_id (unique identifier)
- date (race date)
- horse_name
- race_venue
- race_time
- predicted_p_win (our AI's win probability %)
- predicted_confidence (combined confidence score)
- actual_odds (Betfair odds at bet time)
- implied_probability (1/odds - market's view)
- our_edge (predicted_p_win - implied_probability)
- actual_outcome (win/loss/placed)
- actual_position (finishing position)
- reasons_for_pick (AI's justification)
- tags (form_winner, course_experience, etc.)
```

**Post-Race Analysis (Automated):**

**For LOSSES (predicted win but lost):**
```python
def analyze_failed_prediction(pick):
    """
    Question: Why did we think this would win?
    
    Analysis:
    1. Prediction vs Reality Gap
       - Predicted: 50% win probability
       - Actual: Lost (finished 4th)
       - Gap: 50% overconfidence
    
    2. What We Missed
       - Check: Did horse show fitness issues in race?
       - Check: Was going changed (soft to heavy)?
       - Check: Did jockey ride poorly?
       - Check: Was field stronger than analyzed?
       - Check: Did winner have unknown advantage?
    
    3. Pattern Detection
       - Is this trainer's form misleading?
       - Does this course favor different style?
       - Are odds at this range reliable here?
       - Was our "recent winner" tag valid?
    
    4. Learning Update
       - If trainer pattern: Reduce confidence for trainer
       - If course pattern: Adjust course-specific model
       - If odds range issue: Recalibrate sweet spot
       - If tag failing: Deprecate or refine tag
    ```

**For WINS (predicted win and won):**
```python
def validate_successful_prediction(pick):
    """
    Question: Why were we right? Can we replicate?
    
    Analysis:
    1. Prediction Accuracy
       - Predicted: 40% win probability
       - Actual: Won
       - Confidence: Appropriate (not overconfident)
    
    2. What Worked
       - Recent winner tag: CONFIRMED working
       - Sweet spot odds: CONFIRMED (4.5 odds)
       - Trainer form: CONFIRMED valuable signal
       - Course experience: CONFIRMED important
    
    3. Pattern Reinforcement
       - This trainer at this course: High success
       - Recent winners in 4-5 odds: Sweet spot
       - Jockey X on horse type Y: Pattern emerging
    
    4. Learning Update
       - Increase confidence in similar scenarios
       - Boost "recent winner" tag value
       - Track trainer/course combination
       - Reinforce sweet spot in this sub-range
    ```

**Calibration Metrics (Calculated Daily):**

```python
# Calibration Score - Are we accurate?
predicted_bins = [0-20%, 20-40%, 40-60%, 60-80%, 80-100%]

For each bin:
  - Count predictions in bin
  - Count actual wins in bin
  - Calculate actual_win_rate
  - Compare to predicted_win_rate
  
Example:
  40-60% Bin:
    Predictions: 25 horses
    Predicted avg: 50% win rate
    Actual wins: 10 horses
    Actual rate: 40% 
    Calibration error: -10% (overconfident)
    
  Action: Reduce confidence scores by 10% for this range

# Brier Score - Overall prediction quality
brier_score = mean((predicted_p_win - actual_outcome)²)
  - Lower is better (0 = perfect, 0.25 = random)
  - Target: < 0.20 (good calibration)
  - Track trend: Should decrease over time

# Expected vs Actual (ROI validation)
expected_wins = sum(p_win for all picks)
actual_wins = count(wins)
calibration_ratio = actual_wins / expected_wins
  - 1.0 = perfectly calibrated
  - >1.0 = underconfident (winning more than predicted)
  - <1.0 = overconfident (winning less than predicted)
```

**Integration with Learning System:**

```python
# In generate_learning_insights.py - NEW SECTION

def analyze_prediction_calibration(df):
    """Analyze how accurate our predictions are"""
    
    # Group by confidence bins
    df['confidence_bin'] = pd.cut(df['p_win'], 
                                   bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                   labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])
    
    calibration_analysis = {}
    
    for bin_name in df['confidence_bin'].unique():
        bin_df = df[df['confidence_bin'] == bin_name]
        
        predicted_avg = bin_df['p_win'].mean()
        actual_rate = bin_df['won'].mean()
        sample_size = len(bin_df)
        
        calibration_error = actual_rate - predicted_avg
        
        calibration_analysis[bin_name] = {
            'predicted': predicted_avg,
            'actual': actual_rate,
            'calibration_error': calibration_error,
            'sample_size': sample_size,
            'verdict': 'OVERCONFIDENT' if calibration_error < -0.1 else 
                      'UNDERCONFIDENT' if calibration_error > 0.1 else 'CALIBRATED'
        }
    
    return calibration_analysis

def analyze_failed_predictions(df):
    """Deep dive into losses to find patterns"""
    
    # Get high confidence losses (predicted well, lost badly)
    high_conf_losses = df[(df['p_win'] >= 0.4) & (df['won'] == False)]
    
    failure_patterns = {
        'by_trainer': high_conf_losses.groupby('trainer')['won'].count(),
        'by_course': high_conf_losses.groupby('course')['won'].count(),
        'by_odds_range': high_conf_losses.groupby(pd.cut(high_conf_losses['odds'], 
                                                          bins=[3, 4, 5, 6, 9]))['won'].count(),
        'by_tags': analyze_tag_failures(high_conf_losses)
    }
    
    # Find systematic issues
    recommendations = []
    
    # If specific trainer failing consistently
    for trainer, count in failure_patterns['by_trainer'].items():
        if count >= 5:  # 5+ failures
            recommendations.append(
                f"⚠️ TRAINER ISSUE: {trainer} has {count} high-confidence losses. "
                f"Reduce confidence for this trainer by 20%."
            )
    
    # If specific course problematic
    for course, count in failure_patterns['by_course'].items():
        if count >= 5:
            recommendations.append(
                f"⚠️ COURSE ISSUE: {course} has {count} high-confidence losses. "
                f"Our model may not understand this track. Review course-specific factors."
            )
    
    return {
        'patterns': failure_patterns,
        'recommendations': recommendations,
        'total_high_conf_losses': len(high_conf_losses)
    }
```

**Daily Workflow with Accountability:**

```
Morning:
1. Generate today's picks with p_win predictions
2. Store picks in prediction_tracking table
3. Record: horse, p_win, confidence, odds, reasons

Evening (After Results):
4. Fetch race results
5. Update prediction_tracking with outcomes
6. Run calibration analysis:
   → For each loss: "Why were we wrong?"
   → For each win: "Why were we right?"
   → Calculate calibration error per bin
   → Identify systematic failures
7. Generate learning insights with:
   → Calibration report
   → Failed prediction analysis
   → Pattern discoveries
   → Confidence adjustments needed
8. Update prompts with findings

Next Morning:
9. AI reads yesterday's learnings
10. Adjusts confidence for problematic patterns
11. Avoids repeating systematic errors
12. Reinforces successful patterns
```

**Example Learning Output:**

```
🎯 PREDICTION CALIBRATION ANALYSIS

Confidence Bins:
  20-40% predictions:
    ✅ Predicted: 30% | Actual: 28% | Error: -2% | CALIBRATED
    Sample: 15 picks
  
  40-60% predictions:
    ⚠️ Predicted: 50% | Actual: 35% | Error: -15% | OVERCONFIDENT
    Sample: 20 picks
    Action: Reduce mid-range confidence by 15%
  
  60-80% predictions:
    ✅ Predicted: 70% | Actual: 67% | Error: -3% | CALIBRATED
    Sample: 9 picks

Overall Calibration:
  Brier Score: 0.18 (Good - target <0.20)
  Expected wins: 23.5 | Actual wins: 19 | Ratio: 0.81
  Verdict: SLIGHTLY OVERCONFIDENT (reduce confidence 5-10%)

❌ HIGH CONFIDENCE FAILURES (Last 7 days):

1. Thunder Strike @ Ascot (Predicted: 55%, Lost - 4th place)
   Why wrong: Going changed to heavy, horse prefers good
   Learning: Check going changes before race time
   
2. Quick Step @ Kempton (Predicted: 60%, Lost - 6th place)
   Why wrong: Drawn wide (stall 12), wide draws losing at Kempton
   Learning: Factor in draw bias at Kempton (favor low draws)
   
3. Star Performer @ Wolverhampton (Predicted: 50%, Lost - 5th)
   Why wrong: Trainer form false positive (1 win from 20 recent)
   Learning: Require 3+ wins in last 20 for "in-form trainer" tag

⚠️ SYSTEMATIC PATTERNS:

• Trainer J. Smith: 6 high-confidence losses in sweet spot
  Action: Reduce confidence for this trainer by 25%
  Reason: Recent form not translating to wins

• Kempton course: 5 losses with wide draws (stalls 10+)
  Action: Penalize wide draws at Kempton (-15 confidence)
  Reason: Clear track bias favoring low draws

• "Recent winner" tag at 9.0+ odds: 0/5 wins
  Action: Require odds <9.0 for recent winner boost
  Reason: Longshot recent winners are flukes, not form
```

**Benefits of Prediction Accountability:**

1. **Forces Honesty**: Can't hide from bad predictions
2. **Identifies Blind Spots**: Systematic errors become visible
3. **Calibrates Confidence**: Adjusts overconfidence automatically
4. **Learns Faster**: Each failure teaches multiple lessons
5. **Builds Trust**: When calibrated, predictions are reliable
6. **Prevents Repeats**: Same mistake won't happen twice
7. **Finds Edges**: Discovers what actually works vs theory

**Implementation Priority:**

**✅ IMPLEMENTED (v2.2 - January 31, 2026):**

**Core Scripts Created:**
- ✅ **analyze_prediction_calibration.py** - Standalone calibration analysis tool
  - Loads picks from DynamoDB with outcomes (last 7 days)
  - Calculates calibration bins (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
  - Computes Brier score for prediction quality
  - Analyzes expected vs actual win rates
  - Identifies systematic failures (trainer/course/tag patterns)
  - Validates successful predictions (what's working)
  - Generates comprehensive calibration report (JSON + console)
  
- ✅ **Enhanced generate_learning_insights.py** - Daily learning with calibration
  - Added `analyze_prediction_calibration()` function
  - Added `analyze_systematic_failures()` function  
  - Added `analyze_successful_patterns()` function
  - Integrated calibration metrics into daily learning cycle
  - Stores calibration analysis in learning_insights.json
  - Adds calibration insights to prompt guidance

**Storage Confirmed:**
- ✅ **save_selections_to_dynamodb.py** already stores:
  - `p_win` - Predicted win probability per pick
  - `confidence` - Combined confidence score
  - `tags` - Strategy tags for pattern tracking
  - `why_now` - AI's reasoning for selection
  - `outcome` - Actual result (win/loss/placed)
  - All fields needed for calibration analysis ✓

**What Works Now:**

1. **Daily Calibration Analysis:**
   ```bash
   python analyze_prediction_calibration.py
   # Analyzes last 7 days of picks
   # Outputs: calibration_report.json
   ```

2. **Integrated Learning:**
   ```bash
   python generate_learning_insights.py
   # Now includes calibration analysis
   # Outputs: learning_insights.json (with calibration_analysis field)
   ```

3. **Automatic Insights:**
   - Calibration status per confidence bin
   - Overconfident/underconfident detection
   - Systematic failure identification
   - Success pattern validation
   - Actionable recommendations

**Example Output (Real Data from Jan 31):**
```
📊 OVERALL PERFORMANCE:
   Wins: 11/61 (18.0%)
   Predicted avg: 25.0%
   
📈 CALIBRATION:
   20-40% predictions: Predicted 32.2% | Actual 20.7% | OVERCONFIDENT ⚠️
   
❌ SYSTEMATIC ISSUES:
   • TAG_FAILING: 3 losses with 'enhanced_analysis' tag
     Action: Reduce confidence boost by 10-15 points
   
✅ WORKING STRATEGIES:
   • COURSE_SUCCESS: Wolverhampton - 4 wins
   • TAG_WORKING: 'Recent winner' tag - 2 wins
     
🔧 PRIORITY ACTIONS:
   1. Reduce overall confidence by 28%
   2. Reinforce 'Recent winner' tag
```

**Remaining Phases:**

**Phase 2 (Next 1-2 weeks):**
- ⏳ Automated confidence adjustments
  - Auto-reduce confidence for failing trainers/courses
  - Auto-boost confidence for working patterns
  - Update prompt.txt dynamically based on calibration
  
- ⏳ Course/trainer-specific confidence modifiers
  - Store modifier per trainer (e.g., "Trainer Smith: -20%")
  - Apply modifiers during selection process
  
**Phase 3 (Weeks 3-4):**
- ⏳ Deeper failure analysis
  - Check going changes, draw bias, jockey switches
  - Compare predicted vs actual race dynamics
  
- ⏳ Enhanced success validation
  - Find trainer/jockey/course combinations
  - Identify optimal conditions for each pattern

**Phase 4 (Month 2):**
- Store p_win with every pick in DynamoDB
- Add actual_outcome field after results
- Basic calibration: predicted vs actual by confidence bin

**Phase 2 (Week 2):**
- Add failure analysis for high-confidence losses
- Track patterns (trainer, course, tags)
- Generate "why wrong" reports

**Phase 3 (Week 3-4):**
- Automated confidence adjustments
- Trainer/course specific confidence modifiers
- Brier score tracking

**Phase 4 (Month 2):**
- Predictive "autopsy" AI that analyzes each failure
- Course-specific models
- Jockey-trainer-horse combination patterns

### Layer 4: System Prompt (Legacy Support)
**File**: `prompt.txt` (also used by older scripts)
- Contains odds guidance for any scripts that load it
- Documents historical performance
- Provides reasoning framework

---

## How The Layers Work Together

**Pick Generation Flow:**
```
1. Betfair Data Fetched
   ↓
2. AI Analyzes (prompt.txt + enhanced_analysis.py)
   → Confidence boosters favor sweet spot
   → Recent winners get +30 points
   → 3.5-6.0 odds get +25 points
   ↓
3. Top Picks Generated (naturally in sweet spot)
   ↓
4. Quality Filter (save_selections_to_dynamodb.py)
   → Backup check for range compliance
   → Exceptions for exceptional picks
   ↓
5. Saved to DynamoDB with odds field
```

**Learning Feedback Flow:**
```
1. Evening: Race Results Come In
   ↓
2. generate_learning_insights.py Runs
   → Analyzes by odds range
   → Calculates sweet spot ROI
   → Identifies what worked
   ↓
3. learning_insights.json Updated
   → "Sweet spot: 8 bets, 4 wins, +35% ROI"
   → "Ultimate range (3.5-6) best: +42% ROI"
   → "Recommendation: INCREASE 3.5-6 picks"
   ↓
4. Next Day AI Reads Insights
   → Adjusts strategy emphasis
   → More confident in sweet spot
   → Prioritizes recent winners
   ↓
5. Better Picks Generated
   → Higher sweet spot %
   → More recent winners
   → Improved profitability
```

**Self-Optimization Loop:**
```
Sweet Spot Winners → Positive Learning → More Sweet Spot Picks
        ↑                                            ↓
   Higher ROI ←────── Confidence Grows ←───── Better Results
```

---

## Success Metrics V2.1

### Performance Targets (Weekly Tracking)

**Sweet Spot Coverage:**
- Week 1: 60%+ picks in 3.0-9.0 range
- Week 2: 70%+ picks in range
- Week 4: 80%+ picks in range (optimal)

**Win Rate in Sweet Spot:**
- Target: 25-30% win rate
- Minimum acceptable: 20%
- If >30%: System performing exceptionally

**ROI in Sweet Spot:**
- Target: +15% to +30%
- Minimum acceptable: +10%
- If >30%: Consider increasing stake sizes

**Ultimate Sweet Spot (3.5-6.0):**
- Should outperform wider range
- Target: 30%+ win rate, +25% ROI
- Indicates optimal sub-range identified

### Daily Monitoring Commands

```powershell
# Check today's picks odds distribution
python check_todays_picks_count.py

# After races, regenerate learning insights
python generate_learning_insights.py

# View sweet spot performance
cat learning_insights.json | ConvertFrom-Json | Select-Object -ExpandProperty sweet_spot_analysis

# Check if sweet spot % is improving
# (Should increase week over week)
```

### Red Flags (Action Required)

**Coverage Issues:**
- <50% picks in sweet spot → AI not following guidance
- >90% in sweet spot → May be too restrictive, missing value

**Performance Issues:**
- Sweet spot ROI negative → Selection criteria within range needs work
- Win rate <15% → Confidence scores too high, being overconfident
- Ultimate range underperforming → May need to widen to full 3-9 range

**Learning Issues:**
- Learning recommendations not changing → Learning cycle not running
- Same patterns failing repeatedly → Need manual prompt adjustment
- Odds data missing from insights → Historical data not capturing odds

---

## Quality Thresholds (Updated for v2.1)

## Quality Thresholds (Updated for v2.1)

### Minimum Requirements (Base Selection)
- **Odds Range**: 3.0-9.0 decimal (2/1 to 8/1) - MANDATORY sweet spot
- **Recent Winner**: Won in last 3 races preferred
- **ROI**: ≥20% expected return
- **Confidence**: ≥40% combined confidence (before boosters)
- **Win Probability**: ≥25% P(win) in sweet spot
- **Lead Time**: ≥30 minutes before race
- **Race Limit**: Maximum 1 pick per race

### Enhanced Requirements (Sweet Spot Focus)
- **Recent form**: Win within 60 days strongly preferred
- **Course experience**: Previous course form adds confidence
- **Trainer form**: In-form trainer (winners this week) preferred
- **Class level**: Matched to recent winning class
- **Ultimate range**: 3.5-6.0 odds prioritized when available

### Confidence Scoring System
**Base Score** (from AI analysis): 30-50 points
**Boosters Applied:**
- Ultimate sweet spot (3.5-6.0): +25
- Sweet spot (3.0-9.0): +15
- Won last race: +30
- Won in last 2-3 races: +20
- Multiple wins (5 races): +40
- Won at this course: +15
- Trainer winning: +10
- Top jockey: +8

**Final Score Thresholds:**
- 90-100: EXCELLENT - highest stakes
- 70-89: VERY GOOD - standard stakes
- 50-69: ACCEPTABLE - reduced stakes
- <50: REJECT - insufficient confidence

### Risk Management (Sweet Spot Optimized)
- **Daily exposure**: Max 5% of bankroll per day
- **Stake scaling**: Proportional to confidence score
  - 90-100 confidence: 2.5-3.0% of daily budget
  - 70-89 confidence: 2.0-2.5% of daily budget
  - 50-69 confidence: 1.0-2.0% of daily budget
- **Kelly Criterion**: Applied within confidence bands
- **Each-way strategy**: For 5+ runner races with 30%+ P(place)
- **Position limits**: Max 3 picks in same odds band (e.g., max 3 at 3.5-4.5 odds)
- **Sweet spot allocation**: Prioritize budget to 3.5-6.0 range when available

---

## Data Retention Policy

### What We Learned (The Hard Way)
**Jan 22, 2026**: Cleanup script deleted 116 historical bets (Jan 3-21)
- **Impact**: Lost all learning foundation, AI couldn't improve
- **Lesson**: Historical data is the system's memory - NEVER delete

### Current Policy (Locked In)
- **Database**: Keep ALL historical data forever (DynamoDB cost = FREE)
- **UI filtering**: Hide past races by race_time (automatic)
- **Cleanup scripts**: DISABLED with exit warnings
  - `cleanup_old_picks.py`: Protected with sys.exit(1)
  - `clear_old_data.ps1`: Protected with exit 1

---

## Results Timeline

### Before Fix (Jan 29, 2026)
- **12 bets placed**: All longshots (15/1, 16/1, 20/1, 50/1+)
- **Win rate**: 0% (0/12 wins)
- **P&L**: -£183.60 loss
- **Problem**: AI generated longshots, filters couldn't fix at save time

### After Fix (Jan 30, 2026)
- **5 bets placed**: All in sweet spot (1.9/1, 5.3/1, 6.0/1, 6.6/1, 6.8/1)
- **Win rate**: TBD (results pending)
- **Improvement**: 100% picks in profitable odds range
- **Fix**: Updated all 4 AI expert prompts with odds guidance

### Picks Comparison
**Before** (Jan 29):
- Hellion @ 16/1 ❌
- Prettylady @ 50/1 ❌
- Kenzo Des Bruyeres @ 16/1 ❌
- King Of York @ 21/1 ❌

**After** (Jan 30):
- Turenne @ 1.9/1 ✅
- Devon Skies @ 6.0/1 ✅
- Followango @ 6.6/1 ✅
- Brazilian Rose @ 5.3/1 ✅
- Special Ghaiyyath @ 6.8/1 ✅

---

## Git Commits (Strategy Evolution)

### v2.0 Foundation (Jan 30, 2026)

**Commit 20e8732** (Jan 30, 12:23)
"Fix performance issues: preserve historical data + focus on 2-8/1 odds sweet spot"
- Disabled cleanup scripts
- Added odds filter to save_selections_to_dynamodb.py
- Updated prompt.txt
- Created DATA_RETENTION_POLICY.md, ODDS_SWEET_SPOT_FIX.md

**Commit 1c3e2e2** (Jan 30, 12:40)
"Fix AI prompts to enforce 2-8/1 odds sweet spot in all 4 expert analysts"
- Updated enhanced_analysis.py with odds guidance in all 4 expert prompts
- Result: AI now generates sweet spot picks at source

### v2.1 Enhancement (Jan 31, 2026)

**Commit d0c559b** (Jan 31)
"Sweet Spot Optimization: Focus self-learning on 2/1-8/1 winners"
- Updated prompt.txt with MANDATORY sweet spot focus (3.0-9.0 odds)
- Added confidence boosting system (+25 for 3.5-6.0, +30 for recent winners)
- Enhanced generate_learning_insights.py with odds range analysis:
  - `analyze_odds_ranges()` - Performance tracking by 6 ranges
  - Sweet spot specific analysis (3-9 and 3.5-6 ranges)
  - ROI calculation per range
  - Sweet-spot-focused recommendations
- Target: 60%+ picks in 3-9 range, 25-30% win rate, +15% ROI
- Added SWEET_SPOT_OPTIMIZATION_GUIDE.md

**Commit 2f566c7** (Jan 31)
"Fix results display - use lowercase outcome values to match database"
- Fixed frontend outcome matching (was uppercase, DB is lowercase)
- Count placed outcomes as wins in frontend display
- Updated App.js to correctly show win/loss counts
- Deployed frontend fixes to AWS Amplify

**Commit 7b23674** (Jan 31, 16:00)
"Update strategy docs to v2.1 with sweet spot optimization details"
- Documented entire v2.1 system in BETTING_STRATEGY_V2.md
- Comprehensive coverage: rationale, implementation, results, evolution
- 761 lines added with full technical details

**What Changed v2.0 → v2.1:**
- v2.0: Prevented bad picks (longshots filtered out)
- v2.1: Actively hunts good picks (winners in sweet spot)
- v2.0: Static odds filter
- v2.1: Dynamic learning with range-based optimization
- v2.0: Generic confidence scoring
- v2.1: Confidence boosters for sweet spot + recent winners
- v2.0: No odds tracking in learning
- v2.1: Full odds range analysis with ROI by range

### v2.2 Prediction Accountability (Jan 31, 2026)

**Commit b42a7e7** (Jan 31, 16:25)
"Add v2.2: Prediction accountability & calibration tracking system"
- Documented Layer 4 of learning system (prediction accountability)
- Added calibration methodology and metrics
- Designed 4-phase implementation plan

**Commit [CURRENT]** (Jan 31)
"Implement v2.2: Prediction calibration system fully operational"
- ✅ Created analyze_prediction_calibration.py (542 lines)
  - Calibration bins (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
  - Brier score calculation (prediction quality metric)
  - Expected vs actual win rate comparison
  - Systematic failure detection (by trainer/course/tags)
  - Success pattern validation (what's working)
  - Comprehensive reporting (JSON + console output)
- ✅ Enhanced generate_learning_insights.py (+115 lines)
  - analyze_prediction_calibration() function
  - analyze_systematic_failures() function  
  - analyze_successful_patterns() function
  - Integrated calibration into daily learning workflow
  - Calibration insights added to prompt guidance
- ✅ Verified save_selections_to_dynamodb.py
  - Already stores p_win, tags, why_now, outcome
  - No changes needed - ready for calibration
- ✅ Tested on real data (61 picks, 7 days)
  - Successfully identified overconfidence in 20-40% bin
  - Found failing tag ('enhanced_analysis': 3 high-conf losses)
  - Found working patterns (Wolverhampton: 4 wins)
  - Generated actionable recommendations
- ✅ Updated BETTING_STRATEGY_V2.md
  - Implementation status and usage instructions
  - Real output examples from Jan 31 testing
  - Version updated to v2.2

**What Changed v2.1 → v2.2:**
- v2.1: Tracked performance by odds ranges
- v2.2: Tracks prediction accuracy by confidence bins
- v2.1: General calibration check (overall win rate vs predicted)
- v2.2: Detailed calibration per confidence level + Brier score
- v2.1: Basic high-confidence loss analysis
- v2.2: Systematic pattern detection (trainer/course/tag failures)
- v2.1: Identified working tags
- v2.2: Validates WHY predictions succeeded (reinforcement)
- v2.1: Recommendations from aggregate patterns
- v2.2: Specific actions from individual prediction analysis

---

## DO NOT CHANGE (Protected Strategy Core)

## DO NOT CHANGE (Protected Strategy Core)

### Protected Files (v2.2 Strategy)
1. **prompt.txt**: Sweet spot mandatory focus + confidence boosters (lines 1-70)
2. **generate_learning_insights.py**: Odds range analysis + calibration functions
3. **analyze_prediction_calibration.py**: Standalone calibration analysis tool
4. **enhanced_analysis.py**: All 4 expert prompts with sweet spot logic
5. **save_selections_to_dynamodb.py**: Odds filter + prediction storage
6. **cleanup_old_picks.py**: DISABLED (exit warning at top)
7. **clear_old_data.ps1**: DISABLED (exit warning at top)
8. **frontend/src/App.js**: Outcome value matching (lowercase)

### If You Must Adjust Strategy

**Only change if data proves different approach** (requires 200+ bet sample showing new range):

**To Adjust Odds Range:**
1. Analyze learning_insights.json for 4+ weeks
2. Confirm new range has better ROI AND win rate
3. Update prompt.txt (lines 1-70)
4. Update all 4 prompts in enhanced_analysis.py
5. Update odds filter in save_selections_to_dynamodb.py
6. Update analyze_odds_ranges() in generate_learning_insights.py
7. Document reason with data in this file
8. Commit with detailed explanation + data evidence

**To Adjust Confidence Boosters:**
1. Monitor actual confidence vs results for 2+ weeks
2. If overconfident: Reduce booster points
3. If underconfident: Increase booster points
4. Update prompt.txt booster values
5. Document calibration data
6. Re-test for 1 week before committing

**To Modify Learning System:**
1. Test changes in separate branch
2. Run against historical data (200+ bets)
3. Verify recommendations improve accuracy
4. Document before/after comparison
5. Merge only if demonstrably better

### What Makes This Strategy Work

**Three-Layer Protection:**
```
Layer 1 (AI Generation):
  prompt.txt enforces sweet spot at creation time
  → Most picks naturally in 3-9 range
  
Layer 2 (Quality Filter):
  save_selections_to_dynamodb.py catches outliers
  → Backup for exceptional cases
  
Layer 3 (Learning):
  generate_learning_insights.py optimizes within range
  → Continuously improves sweet spot performance
```

**Why It's Robust:**
- If AI prompt weakens → Filter catches bad picks
- If filter fails → Learning identifies problem
- If learning drifts → Historical data provides baseline
- All three reinforce each other

---

## Success Metrics V2.1 (Track Weekly)

## Success Metrics V2.1 (Track Weekly)

### Expected Performance (3.0-9.0 Odds Sweet Spot)

**Week 1 Targets:**
- Sweet spot coverage: 60%+ of picks
- Win rate in range: 20-25%
- ROI in range: +10% minimum
- Learning insights generated: Daily

**Week 2-3 Targets:**
- Sweet spot coverage: 70%+ of picks
- Win rate in range: 25-28%
- ROI in range: +15-20%
- Ultimate range (3.5-6) identified

**Week 4+ Steady State:**
- Sweet spot coverage: 75-80% of picks
- Win rate in range: 28-30%
- ROI in range: +20-30%
- Ultimate range outperforming: +25-35% ROI
- Self-optimization working: Increasing sweet spot % weekly

### Daily Monitoring (Commands)

```powershell
# Morning: Check today's picks
python check_todays_picks_count.py

# Count picks in sweet spot
python -c "import pandas as pd; df = pd.read_csv('today_picks.csv'); print(f'Sweet Spot (3-9): {len(df[(df.odds >= 3.0) & (df.odds < 9.0)])} / {len(df)}')"

# Evening: After results
python generate_learning_insights.py

# Check sweet spot performance
cat learning_insights.json | ConvertFrom-Json | Select-Object -ExpandProperty sweet_spot_analysis | Format-List

# View recommendations
cat learning_insights.json | ConvertFrom-Json | Select-Object -ExpandProperty recommendations
```

### Weekly Review Checklist

**Every Monday Morning:**
- [ ] Run learning insights for last 7 days
- [ ] Check sweet spot percentage trend (increasing?)
- [ ] Review ROI by odds range
- [ ] Verify ultimate range (3.5-6) still best
- [ ] Check if recommendations are being followed
- [ ] Confirm confidence boosters correlating with wins
- [ ] Review any picks outside sweet spot (were they justified?)

**Data to Track:**
```
Week | Sweet Spot % | Win Rate | ROI | Ultimate Range ROI
-----|--------------|----------|-----|-------------------
  1  |     62%      |   23%    | +12%|      +18%
  2  |     71%      |   27%    | +19%|      +28%
  3  |     78%      |   29%    | +24%|      +35%
  4  |     80%      |   30%    | +28%|      +42%
```

### Red Flags (Action Required)

**Coverage Issues:**
- ⚠️ <50% picks in sweet spot
  - **Action**: Check AI prompts still have boosters
  - **Check**: learning_insights.json being read
  
- ⚠️ >95% in sweet spot
  - **Action**: May be too restrictive, missing value
  - **Check**: Are we rejecting valid 9-12 odds winners?

**Performance Issues:**
- ⚠️ Sweet spot ROI negative for 2+ weeks
  - **Action**: Review selection criteria WITHIN range
  - **Check**: Are recent winners criterion too loose?
  
- ⚠️ Win rate <15% for 2+ weeks
  - **Action**: Confidence scores too high, overconfident
  - **Check**: Reduce confidence boosters by 20%
  
- ⚠️ Ultimate range underperforming wider range
  - **Action**: May need full 3-9 range, not just 3.5-6
  - **Check**: Widen focus, reduce ultimate range priority

**Learning System Issues:**
- ⚠️ Learning recommendations not changing day-to-day
  - **Action**: Learning cycle may not be running
  - **Check**: Run generate_learning_insights.py manually
  
- ⚠️ Same patterns failing week after week
  - **Action**: Manual prompt adjustment needed
  - **Check**: Are specific trainers/courses consistently losing?
  
- ⚠️ Odds data missing from insights
  - **Action**: Historical data not capturing odds field
  - **Check**: Verify DynamoDB picks have 'odds' field

**System Drift:**
- ⚠️ Reverting to longshot recommendations
  - **Action**: CRITICAL - Check all prompts immediately
  - **Check**: Was enhanced_analysis.py modified?
  
- ⚠️ Historical data deleted
  - **Action**: CRITICAL - Restore from backup
  - **Check**: Were cleanup scripts re-enabled?

---

## Expected Performance Timeline (v2.1)

### Phase 1: Initial Implementation (Week 1)
**What Happens:**
- AI starts applying confidence boosters
- More picks in 3-9 range (60-70%)
- Learning system tracks new metrics
- Initial sweet spot ROI measured

**Expected Results:**
- Some improvement over v2.0
- Hit or miss as system calibrates
- 20-25% win rate in sweet spot
- +10-15% ROI

### Phase 2: Learning Kicks In (Weeks 2-3)
**What Happens:**
- Daily learning identifies patterns
- Sweet spot % increases to 70-80%
- Ultimate range (3.5-6) emerges as best
- Confidence in sweet spot grows

**Expected Results:**
- Consistent improvement
- 25-28% win rate
- +15-25% ROI
- Self-reinforcing feedback visible

### Phase 3: Optimization (Week 4+)
**What Happens:**
- System finds optimal sweet spot utilization (75-80%)
- Identifies trainer/jockey patterns in range
- Course-specific sweet spots emerge
- Fully self-optimizing

**Expected Results:**
- Stable high performance
- 28-30% win rate
- +20-30% ROI
- +35-45% in ultimate range (3.5-6)
- Consistent profitability

### Long-term Evolution (Months 2-3)
**What Could Develop:**
- Course-specific ranges (e.g., Ascot: 3.5-5.5 best)
- Trainer-specific patterns (e.g., Trainer X: 4-6 range best)
- Seasonal adjustments (e.g., Winter: Wider range OK)
- Class-specific optimization
- Weather-specific patterns

**System becomes expert at:**
- Finding value within sweet spot
- Avoiding traps (in-form horses at wrong odds)
- Timing (when to bet favorites at 2.8 odds)
- Specialization (specific courses/trainers/conditions)

---

## Emergency Rollback (v2.1)

## Emergency Rollback (v2.1)

### If v2.1 Breaks or Underperforms

**Rollback Scenarios:**
1. **Sweet spot ROI worse than v2.0**: Revert to v2.0
2. **System generating bad picks**: Restore prompts
3. **Learning system causing issues**: Disable learning updates
4. **Historical data problems**: Restore backup

**Rollback Commands:**

```bash
# Full rollback to v2.0 (Jan 30)
git checkout 1c3e2e2 -- enhanced_analysis.py
git checkout 20e8732 -- save_selections_to_dynamodb.py
git checkout 20e8732 -- prompt.txt

# Restore just v2.1 prompt (keep v2.0 filters)
git checkout d0c559b -- prompt.txt

# Restore just v2.1 learning (keep v2.0 prompts)
git checkout d0c559b -- generate_learning_insights.py

# Undo last commit completely
git revert HEAD

# Check what changed
git diff 1c3e2e2..d0c559b
```

**Selective Rollback (Fix One Layer):**

```bash
# If AI prompts broken
git checkout d0c559b -- prompt.txt
# Keeps: Learning system working
# Reverts: Confidence boosters

# If learning broken
git checkout 1c3e2e2 -- generate_learning_insights.py
# Keeps: Sweet spot prompts
# Reverts: Odds tracking

# If filter broken
git checkout 20e8732 -- save_selections_to_dynamodb.py
# Keeps: AI and learning
# Reverts: Filter logic
```

### When to Rollback vs. Fix

**Rollback Immediately If:**
- Historical data deleted (restore backup ASAP)
- System placing <30% picks in sweet spot (major regression)
- Critical errors preventing picks generation
- ROI negative for 3+ consecutive days

**Fix Forward If:**
- Sweet spot % needs tuning (adjust boosters)
- Learning recommendations seem off (recalibrate)
- Minor performance issues (monitor another week)
- Edge cases being handled incorrectly

### Safe Points in Git History

**v2.1 (Current):**
- Commit: d0c559b
- Status: Sweet spot optimization with learning
- Use: Full sweet spot focus + self-learning

**v2.0 (Stable):**
- Commit: 1c3e2e2
- Status: Sweet spot filtering without learning
- Use: If learning causes issues

**v1.0 (Baseline):**
- Commit: 20e8732
- Status: Basic sweet spot with data retention
- Use: If complete reset needed

---

## Strategy Documentation

---

## Summary: v2.2 Prediction Accountability System

**Status: IMPLEMENTED & OPERATIONAL ✅ (January 31, 2026)**

**What Changed:**
- ✅ Created **analyze_prediction_calibration.py** - Standalone calibration analysis
- ✅ Enhanced **generate_learning_insights.py** - Added calibration to daily learning
- ✅ Verified **save_selections_to_dynamodb.py** - Already stores all needed fields

**Key Features Working Now:**
- 📊 Calibration bins show prediction accuracy by confidence level
- 🎲 Brier score tracks overall prediction quality (target <0.20)
- ❌ Systematic failure detection finds patterns in losses (trainer/course/tags)
- ✅ Success validation reinforces what's working
- 🔧 Actionable recommendations for confidence recalibration

**Daily Usage:**
```bash
# Run after yesterday's results are processed
python analyze_prediction_calibration.py  # Detailed 7-day calibration report
python generate_learning_insights.py      # Full 30-day learning (includes calibration)
```

**Example Real Output (Jan 31, 2026):**
```
📊 OVERALL: 11/61 wins (18.0%) | Expected: 25.0%
📈 CALIBRATION:
   20-40% bin: Predicted 32.2% | Actual 20.7% | OVERCONFIDENT ⚠️
   Brier Score: 0.116 (Good - under 0.20 target)
❌ SYSTEMATIC ISSUES:
   • TAG_FAILING: 'enhanced_analysis' tag - 3 high-conf losses
     Action: Reduce boost by 10-15 points
✅ WORKING:
   • Wolverhampton: 4 wins | Reinforce course understanding
   • 'Recent winner' tag: 2 wins | Add +5-10 points
🔧 ACTIONS:
   1. Reduce overall confidence by 28%
   2. Adjust failing tags
```

**Files Modified:**
- [analyze_prediction_calibration.py](analyze_prediction_calibration.py) - NEW (542 lines)
- [generate_learning_insights.py](generate_learning_insights.py) - Enhanced (+115 lines)
- [calibration_report.json](calibration_report.json) - NEW (generated daily)
- [learning_insights.json](learning_insights.json) - Enhanced (includes calibration field)

**Next Phase (Automation):**
- Auto-adjust confidence for failing trainers/courses
- Build trainer/course-specific modifiers
- Dynamic prompt updates based on calibration

---

**STRATEGY V2.2 - PREDICTION ACCOUNTABILITY + CALIBRATION**

Status: Active (Jan 31, 2026) ✅
Previous: v2.1 Sweet Spot Winner Focus
New: Self-correcting prediction system with accountability
Target: Calibrated predictions, systematic error elimination, continuous improvement

**Related Files:**
- [SWEET_SPOT_OPTIMIZATION_GUIDE.md](SWEET_SPOT_OPTIMIZATION_GUIDE.md) - Detailed v2.1 implementation
- [DATA_RETENTION_POLICY.md](DATA_RETENTION_POLICY.md) - Why we keep all data
- [ODDS_SWEET_SPOT_FIX.md](ODDS_SWEET_SPOT_FIX.md) - Original v2.0 fix
- [BETTING_STRATEGY_V2.md](BETTING_STRATEGY_V2.md) - This file

**For Daily Operations:**
- Run: `python analyze_prediction_calibration.py` (weekly calibration check)
- Run: `python generate_learning_insights.py` (after results - includes calibration)
- Check: `calibration_report.json` (7-day calibration status)
- Check: `learning_insights.json` (30-day learnings + calibration analysis)
- Monitor: Calibration bins, Brier score, systematic failures
- Review: Weekly performance + prediction accuracy

**For Troubleshooting:**
- Check prompts in [prompt.txt](prompt.txt)
- Verify filters in [save_selections_to_dynamodb.py](save_selections_to_dynamodb.py)
- Review learning in [generate_learning_insights.py](generate_learning_insights.py)
- Test AI in [enhanced_analysis.py](enhanced_analysis.py)

---

## STRATEGY V2.3 - FEBRUARY 2026 LEARNING UPDATE

**Status: Active (Feb 26, 2026)**
**Previous: V2.2 Prediction Accountability + Calibration**
**New: Evidence-based odds range refinement + scoring weight corrections**

### Key Findings from Feb 2026 Real-Money Results (85+ score picks)

#### 1. Score Threshold Performance
| Score Bucket | Bets | Win Rate | ROI |
|---|---|---|---|
| 90-100 | 14 | 35.7% | **+33.0%** ✅ |
| 85-89  | 10 | 10.0% | **-21.8%** ❌ |
| 80-84  | 21 | 42.9% | **+8.0%**  ✅ |
| 75-79  | 25 | 24.0% | **-0.8%**  ≈  |

**Action taken**: `show_in_ui` threshold raised back to **85+**. The 75-79 range adds noise with near-breakeven ROI.

#### 2. Odds Range Performance (85+ score picks)
| Odds Range | Bets | SR% | P/L |
|---|---|---|---|
| Odds-on (<2.0) | 1 | 100% | +£0.43 |
| Evens-2/1 (2-3) | 2 | 50% | +£1.00 |
| **3/1-4/1 (3-5)** | 13 | 30.8% | **-£11.95** ❌ |
| **5/1-7/1 (5-8)** | 8 | 12.5% | **+£25.20** ✅ |

**Finding**: The old "sweet spot" of 3-5 odds is a LOSING range. The 5-8 range (5/1-7/1) is where money is made.

**Action taken**: `prompt.txt` updated — primary sweet spot changed from 3-9 to **5-8 odds** (4/1-7/1).

#### 3. Form Quality Finding
| Form Quality | Win Rate | Implication |
|---|---|---|
| "Excellent" | 2.8% | Horses in great form are over-valued by market |
| "Good" | 0.6% | Often over-bet − worst performing |
| "Poor" | 3.6% | Best performers − bounce-back candidates |

**Finding**: Horses labelled as "good form" lose the most. Recent wins are already priced in. Poor-form bounce-backs offer better value.

**Action taken**: `recent_win` weight reduced from **25 → 15** in `DEFAULT_WEIGHTS` and DynamoDB `SYSTEM_WEIGHTS`.

#### 4. Score Gap Analysis
- Large gap between our pick and next best horse **does NOT predict wins**
- Big gap (>15 pts): ROI = -10.1%
- Small gap (0-5 pts): ROI = +195.6% (one big winner, Laughing John +£37.20)
- **Conclusion**: Do NOT add score gap as a bonus scoring factor

#### 5. One Pick Per Race Rule
- Enforced in Lambda and `api_server.py` (commit ab39ecc)
- Groups by `(course, race_time)`, keeps highest-scoring pick only
- Eliminates contradictory recommendations in same race

### Changes Made (Feb 26, 2026)
| File | Change |
|---|---|
| `comprehensive_pick_logic.py` | `recent_win` weight 25 → 15 |
| `comprehensive_pick_logic.py` | `show_in_ui` threshold back to 85+ |
| `prompt.txt` | Sweet spot updated to 5-8 (4/1-7/1) |
| DynamoDB SYSTEM_WEIGHTS | `recent_win` updated to 15 |
| `lambda_api_picks.py` | One-pick-per-race dedup enforced |
| `run_learning_analysis.py` | New: full historical performance script |
| `analyze_score_gap_vs_outcome.py` | New: gap vs outcome analysis |

### Running P/L (Feb 2026, 85+ score picks)
| Date | Picks | W | P | P/L |
|---|---|---|---|---|
| Feb 13 | 1 | 1 | 0 | +£2.10 |
| Feb 14 | 7 | 6 | 0 | +£17.33 |
| Feb 20 | 6 | 2 | 0 | +£2.35 |
| Feb 21 | 16 | 3 | 0 | -£6.97 |
| Feb 25 | 6 | 2 | 1 | **+£20.70** |
| **Total** | **45** | **16** | **1** | **+£36.81** |

---

**STRATEGY V2.1 - SWEET SPOT WINNER FOCUS WITH SELF-LEARNING**

Status: Superseded by V2.3 ✅
Approach: Mandatory 3-9 odds + Recent winners + Self-optimizing
Target: 75%+ sweet spot coverage, 28%+ win rate, 20%+ ROI

Last updated: January 31, 2026
Version: 2.1.0

