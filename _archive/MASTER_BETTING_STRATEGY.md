# 🎯 Master Betting Strategy - Complete System Overview

## The Ultimate Goal

**GREEN STATUS PICKS:** 75%+ confidence, 20%+ ROI, "DO IT" rating
- These are the bets where the top of the card turns green
- Indicates exceptional value and high probability
- The system trains daily to generate more GREEN picks

---

## Core Principles

### 1. Progressive Daily Training
The system learns and improves every day through:
- Analyzing what worked and what didn't
- Adjusting confidence calibration
- Refining ROI thresholds
- Identifying profitable patterns
- Eliminating losing patterns

### 2. Data-Driven Decisions
Every adjustment is based on actual results:
- Win rates by odds range
- ROI by course, trainer, jockey
- Loss pattern analysis
- Quality metric tracking
- No guessing - only what the data proves

### 3. Value Over Volume
Quality beats quantity:
- Better to skip 50 races and find 5 winners
- Than bet 100 races and lose on 80
- Focus on HIGH and GREEN confidence picks
- Avoid LOW confidence bets entirely

---

## The Complete Strategy Framework

### Strategy 1: Favorite vs Non-Favorite (67% Rule) 🎯

**The Core Insight:**
- Favorites (odds <3.0) win ~33% but at poor odds = Low value
- Non-favorites (odds ≥3.0) win ~67% at better odds = HIGH value
- **Goal:** Capture 35-40% of the 67% = Consistent profits

**Classification:**
```python
Favorite: odds < 3.0
  - Expected win rate: 33%
  - Typical ROI: 0-8% (low value)
  - Strategy: SELECTIVE - only exceptional value

Non-Favorite: odds ≥ 3.0
  - Expected win rate: 25-35% (when well-selected)
  - Typical ROI: 15-30% (high value)
  - Strategy: PRIORITIZE - this is where the money is
```

**Automatic Adjustments:**
```python
IF non_favorite_ROI > favorite_ROI:
    BOOST non-favorite confidence by +10%
    REDUCE favorite confidence by -10%
    Lower ROI threshold for non-favorites to 12%
    
IF favorite_ROI negative:
    STOP backing favorites completely
    Confidence penalty: -25% on all odds <3.0
    
IF capture_rate < 20% (missing non-fav wins):
    IMPROVE selection criteria
    Study winning non-favorites we didn't back
    Expand odds range to 3.0-10.0
```

**Expected Portfolio Mix (Week 12+):**
- 85% non-favorites (odds 3.5-7.0)
- 15% value favorites (odds 2.8-4.0 only)
- Overall ROI: 20-25%

**Reference:** [FAVORITE_VS_NON_FAVORITE_STRATEGY.md](FAVORITE_VS_NON_FAVORITE_STRATEGY.md)

---

### Strategy 2: Form Hiding Detection 🔍

**The Problem:**
Trainers/jockeys don't try hard in small races to:
- Keep odds long for bigger target races
- Hide form from bookmakers
- Use as fitness/prep work
- Avoid handicap rises

**Race Classification:**

**SMALL RACES (Prep runs - CAUTION!):**
- Prize money <£5,000
- Selling/Claiming races
- Novice/Maiden at minor tracks
- **Risk:** Form hiding LIKELY
- **Adjustment:** -15% confidence, require 22% ROI

**BIG RACES (Competitive):**
- Prize money £15k-30k
- Listed races, Stakes
- Good handicaps
- **Risk:** Form hiding POSSIBLE
- **Adjustment:** +5% confidence, require 15% ROI

**Pattern Detection:**
```python
Suspicious Pattern:
  Small race: Lost with >50% confidence (prep run)
  + Big race: Won at >4.0 odds soon after
  = FORM HIDING DETECTED

Action:
  Flag trainer as suspicious
  Small races: REDUCE confidence -15% more
  Big races: BOOST confidence +10% (they're targeting this!)
```

**Class Movement:**
```python
Class Rises Won > 2:
  → Horses competitive at higher levels
  → BOOST confidence +10% on class rises
  
Class Drops Won > Class Rises × 2:
  → Only beating weaker horses
  → DEMAND 18%+ ROI, don't overpay
```

**Strategic Behavior Tracking:**
- Trainer patterns (small vs big race performance)
- Prep race losses followed by target race wins
- Improvement after poor runs (hiding form)
- Watchlist of suspicious trainers

**Reference:** [FORM_HIDING_DETECTION.md](FORM_HIDING_DETECTION.md)

---

### Strategy 3: Elite Race Emphasis 🏆

**The Critical Difference:**
Elite races = EVERYONE trying to win!
- No form hiding at Group 1/2/3 level
- Maximum effort for prestige and money
- True form - predictions more reliable
- Higher certainty justifies bigger stakes

**3-Tier Classification:**

**TIER 1 - ELITE RACES (🏆 Highest Priority):**
```python
Criteria:
  - Group 1/2/3 or Grade 1/2/3
  - Major meetings: Cheltenham, Royal Ascot, Aintree, Goodwood,
    Epsom, York, Newmarket, Doncaster, Curragh, Leopardstown, Punchestown
  - Prize money >£30k at premier tracks

Adjustments:
  - Confidence: +20% boost
  - ROI threshold: 12% (lowered)
  - Stake: 1.5x normal
  - Trust: MAXIMUM (form is genuine)

Expected Performance:
  - Win rate: 30-40%
  - ROI: 18-25%
```

**TIER 2 - BIG RACES (💰 Standard):**
```python
Criteria:
  - Listed races, Stakes
  - Prize £15k-30k
  - Competitive handicaps

Adjustments:
  - Confidence: +5% boost
  - ROI threshold: 15%
  - Stake: 1.0x normal
```

**TIER 3 - SMALL RACES (🔻 Avoid):**
```python
Criteria:
  - Prize <£5k
  - Selling/Claiming races
  - Minor tracks

Adjustments:
  - Confidence: -15% reduction
  - ROI threshold: 22%
  - Stake: 0.5x or SKIP
  - Risk: Form hiding likely
```

**Major Meetings Auto-Detected:**
- UK: Cheltenham, Ascot, Aintree, Goodwood, Epsom, York, Newmarket, Doncaster
- Ireland: Curragh, Leopardstown, Punchestown

**Portfolio Target (Week 12+):**
- 70%+ stakes on big/elite races
- <20% stakes on small races
- Focus on Group races for consistency

**Reference:** [ELITE_RACE_STRATEGY.md](ELITE_RACE_STRATEGY.md)

---

### Strategy 4: Progressive Training System 🎓

**7-Week Training Phases:**

**PHASE 1: Foundation (Weeks 1-2)**
```
Goals:
  - Establish baseline win rate, ROI
  - Track favorite vs non-favorite performance
  - Identify best odds ranges
  - Learn course strengths/weaknesses

Adjustments:
  - Minimal (data gathering)
  - Focus on learning, not profits
  - Avoid overconfidence
```

**PHASE 2: Quality Refinement (Weeks 3-4)**
```
Goals:
  - Increase GREEN picks from 0% to 5%
  - Improve overall win rate to 25%+
  - Identify losing patterns to eliminate

Adjustments:
  - Confidence calibration: ±5-10%
  - ROI thresholds refined
  - Shift toward non-favorites if profitable
  - Reduce longshot bets (>10.0 odds)
```

**PHASE 3: GREEN Push (Weeks 5-6)**
```
Goals:
  - Increase GREEN picks to 10-15%
  - Overall ROI target: 15%+
  - High-quality picks dominate (60%+)

Adjustments:
  - Tighten "DO IT" criteria
  - Boost confidence on proven patterns
  - Eliminate courses with negative ROI
  - Focus on 3.5-7.0 odds range
```

**PHASE 4: Mastery (Weeks 7+)**
```
Goals:
  - GREEN picks: 15-20%+
  - Overall ROI: 20-25%+
  - Consistent daily quality score 70+

Adjustments:
  - Fine-tuning only
  - Course-specific mastery
  - Elite race specialization
  - Maintain discipline (no bad bets)
```

**Quality Metrics Tracked:**
- 🟢 GREEN picks (75%+ conf, 20%+ ROI) - The goal!
- 🟡 HIGH picks (60%+ conf)
- 🟠 MODERATE picks (45%+ conf)
- ⚪ LOW picks (<45% conf) - Avoid these

**Daily Quality Score:**
```python
Score = (GREEN × 4) + (HIGH × 2) + (MODERATE × 1) - (LOW × 2)
Target: 70+ daily quality score
```

**Reference:** [DAILY_TRAINING_SYSTEM.md](DAILY_TRAINING_SYSTEM.md)

---

## Decision Framework (How Picks Are Made)

### Step 1: Data Collection
```python
For each race:
  - Fetch Betfair odds (live market data)
  - Get race details (class, prize, course, time)
  - Retrieve horse form (last 3-5 runs)
  - Check trainer/jockey stats
  - Analyze pace, track conditions
  - Review recent results
```

### Step 2: Base Analysis (Claude 4.5 Sonnet)
```python
Claude analyzes:
  - Recent form and consistency
  - Pace and running style
  - Track/distance suitability
  - Class level (stepping up/down?)
  - Trainer/jockey strength
  - Draw position
  - Weight carried
  - Ground conditions

Outputs:
  - Base confidence (0-100%)
  - Expected ROI
  - Reasoning
  - Risk factors
```

### Step 3: Learning Adjustments Applied
```python
# Historical Performance Integration
confidence = base_confidence × learning_calibration

# Course-specific adjustments
IF course has positive ROI history:
    confidence += course_boost (e.g., +5%)
ELIF course has negative ROI:
    confidence -= course_penalty (e.g., -10%)

# Trainer/jockey patterns
IF trainer/jockey has strong record:
    confidence += pattern_boost

# Odds range adjustments
IF odds in profitable range (3.5-7.0):
    confidence += odds_boost
```

### Step 4: Strategy Overlays

**A. Favorite vs Non-Favorite:**
```python
IF odds < 3.0 (favorite):
    IF favorite_ROI_history < 0:
        confidence × 0.75  # -25% penalty
    ELIF favorite_ROI < 5%:
        confidence × 0.85  # -15% penalty
        require ROI > 20%
ELSE (non-favorite):
    IF non_favorite_ROI_history > 15%:
        confidence × 1.10  # +10% boost
        require ROI > 12%  # Lower threshold
```

**B. Form Hiding Detection:**
```python
IF race is SMALL and trainer has suspicious patterns:
    confidence × 0.85 × 0.80  # -15% then -20%
    require ROI > 22%
    # Often results in SKIP

IF race is BIG and trainer has suspicious patterns:
    confidence × 1.10  # +10% boost
    # They're targeting this race!
```

**C. Elite Race Boost:**
```python
IF race is ELITE (Group 1/2/3, major meeting):
    confidence × 1.20  # +20% boost
    require ROI > 12%  # Lower threshold
    stake × 1.5  # Bet more on certainty
    # Everyone trying = More reliable
```

### Step 5: Decision Rating
```python
IF confidence ≥ 75% AND roi ≥ 20%:
    rating = "DO IT" (GREEN)
    stake = base_stake × 1.5
    
ELIF confidence ≥ 60%:
    rating = "HIGH"
    stake = base_stake × 1.2
    
ELIF confidence ≥ 45%:
    rating = "MODERATE"
    stake = base_stake × 1.0
    
ELSE:
    rating = "SKIP"
    stake = 0
```

### Step 6: Final Validation
```python
# Safety checks
IF roi < minimum_threshold:
    SKIP (not enough value)
    
IF odds > 15.0:
    SKIP (too risky, longshot)
    
IF confidence < 45%:
    SKIP (too uncertain)
    
IF course has -20%+ negative ROI:
    SKIP (proven losing track)

# If all checks pass:
STORE bet in database
RETURN pick to user
```

---

## Confidence Calibration System

### Base Confidence (From Claude)
```python
40-50% = Low confidence (uncertain)
50-60% = Moderate confidence (reasonable chance)
60-70% = High confidence (strong chance)
70-80% = Very high confidence (excellent chance)
80%+ = Maximum confidence (near certain)
```

### Learning Calibration (Applied Daily)
```python
IF recent picks overconfident (losses at >70% conf):
    calibration = 0.85-0.90  # Reduce all by 10-15%
    
ELIF recent picks underconfident (wins at <50% conf):
    calibration = 1.10-1.15  # Increase all by 10-15%
    
ELSE (well-calibrated):
    calibration = 1.0  # No change needed
```

### Pattern Boosts (Proven Winners)
```python
Trainer/Jockey combo has 40%+ win rate:
    confidence += 5%
    
Horse won last 2 races at course:
    confidence += 8%
    
Odds range 3.5-7.0 has 25%+ ROI historically:
    confidence += 10%
```

### Pattern Penalties (Proven Losers)
```python
Course has -15%+ ROI historically:
    confidence -= 10%
    
Horse hasn't won in 12+ runs:
    confidence -= 5%
    
Trainer form hiding pattern detected:
    confidence -= 15%
```

---

## ROI Threshold Management

### Standard Thresholds
```python
GREEN picks: ROI ≥ 20%
HIGH picks: ROI ≥ 15%
MODERATE picks: ROI ≥ 12%
SKIP: ROI < 12%
```

### Dynamic Adjustments
```python
Elite races (Group 1/2/3):
    Minimum ROI = 12% (lowered for quality)
    
Small races (potential form hiding):
    Minimum ROI = 22% (raised for risk)
    
Favorites (odds <3.0):
    Minimum ROI = 20% (low odds = need value)
    
Non-favorites performing well:
    Minimum ROI = 12% (more opportunities)
```

### ROI Calculation
```python
roi = ((odds - 1) × win_probability) - (1 - win_probability)
roi_percentage = roi × 100

Example:
  Odds: 5.0
  Win probability: 30% (confidence/100)
  ROI = ((5-1) × 0.30) - (1 - 0.30)
      = (4 × 0.30) - 0.70
      = 1.20 - 0.70
      = 0.50 = 50% ROI ✅
```

---

## Loss Analysis & Pattern Elimination

### What We Track
```python
Every loss analyzed for:
  - Odds range (favorite, medium, longshot)
  - Confidence level (was it overconfident?)
  - Decision rating (did "DO IT" fail?)
  - Finishing position (close or nowhere?)
  - Course (specific track issues?)
  - Trainer/jockey (patterns?)
  - Race type (small, big, elite)
```

### Losing Patterns Detected

**Pattern 1: Losing on Favorites**
```python
IF favorites_lost > total_losses × 0.30:
    WARNING: "Overestimating favorites"
    ACTION: Reduce favorite confidence by 15-20%
            Only back favorites with 20%+ ROI
```

**Pattern 2: Losing on Longshots**
```python
IF longshots_lost > total_losses × 0.40:
    WARNING: "Backing too many outsiders"
    ACTION: Avoid odds >8.0 completely
            Focus on 3.5-7.0 range
```

**Pattern 3: High Confidence Failures**
```python
IF high_confidence_losses > 3 (>70% conf but lost):
    WARNING: "Model overconfident"
    ACTION: Reduce ALL confidence by 10-15%
            Recalibrate expectations
```

**Pattern 4: "DO IT" Rating Failures**
```python
IF do_it_losses / do_it_total > 0.40:
    WARNING: "'DO IT' threshold too loose"
    ACTION: Require 80%+ confidence (was 75%)
            Require 25%+ ROI (was 20%)
```

**Pattern 5: Finishing Positions**
```python
IF close_finishes (2nd-4th) > total_losses × 0.50:
    INSIGHT: "Picking right horses, wrong bet type"
    ACTION: Switch WIN bets to EACH WAY
            Get place returns for close calls

IF nowhere (5th+) > total_losses × 0.60:
    WARNING: "Poor selection - uncompetitive picks"
    ACTION: Stricter form filters
            Review selection criteria
```

---

## Stake Management

### Base Stake
```python
Standard bet: £10 (configurable)
```

### Stake Multipliers
```python
Decision Rating:
  - "DO IT" (GREEN): 1.5x = £15
  - "HIGH": 1.2x = £12
  - "MODERATE": 1.0x = £10
  - "SKIP": 0x = £0

Race Tier:
  - ELITE: Additional 1.5x multiplier
  - BIG: 1.0x (no change)
  - SMALL: 0.5x or SKIP

Combined Example (ELITE + GREEN):
  Base: £10
  GREEN rating: × 1.5 = £15
  ELITE race: × 1.5 = £22.50
  Final stake: £22.50
```

### Bankroll Management
```python
Maximum single bet: 5% of bankroll
Daily betting limit: 20% of bankroll
Never chase losses (no double-up strategies)
Withdraw profits at 50%+ bankroll growth
```

---

## What Makes a GREEN Pick? 🟢

The ultimate goal - when the top of the card turns green!

### GREEN Status Criteria
```python
confidence ≥ 75%
AND roi ≥ 20%
AND decision_rating == "DO IT"
```

### How to Generate More GREENS

**1. Data Quality (Week 1-2)**
```
Gather enough results to identify:
  - Which odds ranges work best
  - Which courses are profitable
  - Which trainers/jockeys succeed
  - What race types suit our analysis
```

**2. Confidence Calibration (Week 3-4)**
```
Fine-tune confidence scoring:
  - Eliminate overconfidence
  - Boost proven patterns
  - Penalize losing patterns
  - Target 75%+ only on best bets
```

**3. Value Identification (Week 5-6)**
```
Focus on high-ROI opportunities:
  - Non-favorites at 3.5-7.0 odds
  - Elite races (reliable, valuable)
  - Horses stepping up in class (underrated)
  - Trainers targeting big races
```

**4. Discipline (Week 7+)**
```
Only back GREEN picks:
  - Skip everything below 75% confidence
  - Require 20%+ ROI minimum
  - Wait for perfect opportunities
  - Quality over quantity wins
```

### GREEN Pick Example
```
Horse: "Thunder Storm"
Race: Royal Ascot Group 2 (ELITE)
Odds: 5.5
Course: Ascot (historically profitable)
Trainer: William Haggas (Royal Ascot specialist)

Base Analysis:
  - Recent form: 121 (won last 2)
  - Suited to distance and ground
  - Draw advantage
  - Base confidence: 62%

Adjustments:
  - Elite race boost: +20% → 74.4%
  - Course positive ROI: +3% → 77.4%
  - Trainer pattern boost: +2% → 79.4%
  - Non-favorite boost: +5% → 84.4%

Final Confidence: 84.4% ✅
Expected ROI: 24.8% ✅
Decision Rating: "DO IT" ✅

STATUS: 🟢 GREEN PICK!
Stake: £22.50 (£10 × 1.5 × 1.5)
```

---

## Performance Metrics & Tracking

### Daily Metrics
```python
Total bets placed
Win rate (%)
Place rate (%)
Overall ROI (%)
Total P&L (£)
GREEN picks count
HIGH picks count
Daily quality score (0-100)
```

### Weekly Metrics
```python
Favorite vs Non-favorite performance
  - Win rate, ROI, total P&L for each
  - Capture rate (% of non-fav wins caught)

Elite vs Big vs Small race performance
  - Win rate, ROI, total P&L by tier

Course performance
  - Best/worst courses
  - ROI by course

Odds range performance
  - Win rate by range
  - ROI by range

Trainer/Jockey patterns
  - Form hiding detection
  - Success rates
```

### Training Progress
```python
Current training phase
Days to GREEN estimate
Improvement needed areas
Training adjustments applied
Confidence calibration factor
ROI threshold changes
Pattern boosts/penalties
```

---

## Success Timeline

### Week 1-2: Foundation
```
✓ System operational
✓ Data collection started
✓ Baseline metrics established
✓ Learning from every bet

Expected:
  - Win rate: 20-25%
  - ROI: 5-10%
  - GREEN picks: 0-2%
```

### Week 3-4: Quality Refinement
```
✓ Confidence calibration working
✓ Losing patterns eliminated
✓ Profitable patterns identified
✓ Non-favorites prioritized

Expected:
  - Win rate: 25-30%
  - ROI: 10-15%
  - GREEN picks: 5-8%
```

### Week 5-6: GREEN Push
```
✓ High-quality picks dominate
✓ Small races avoided
✓ Elite races targeted
✓ Form hiding detected

Expected:
  - Win rate: 28-35%
  - ROI: 15-20%
  - GREEN picks: 10-15%
```

### Week 7+: Mastery
```
✓ GREEN picks regular occurrence
✓ Consistent profitability
✓ Elite race specialization
✓ Value hunting mastered

Expected:
  - Win rate: 32-40%
  - ROI: 20-25%+
  - GREEN picks: 15-20%+
  - 🎉 TOP OF CARD TURNING GREEN!
```

---

## Quick Reference Cheat Sheet

### When to BACK IT (DO IT - GREEN) 🟢
```
✅ Confidence ≥75%
✅ ROI ≥20%
✅ Non-favorite (odds 3.5-7.0) OR value favorite
✅ Elite race OR proven profitable course
✅ No form hiding concerns
✅ Strong recent form
→ STAKE: £15-22.50
```

### When to CONSIDER (HIGH) 🟡
```
✅ Confidence 60-74%
✅ ROI ≥15%
✅ Big race or competitive event
✅ Decent recent form
→ STAKE: £12
```

### When to MAYBE (MODERATE) 🟠
```
⚠️ Confidence 45-59%
⚠️ ROI ≥12%
⚠️ Some concerns but acceptable
→ STAKE: £10 (use caution)
```

### When to SKIP ⚪
```
❌ Confidence <45%
❌ ROI <12%
❌ Small race with form hiding risk
❌ Favorite with poor historical ROI
❌ Longshot >10.0 odds
❌ Course with negative ROI
❌ High-confidence recent failures
→ STAKE: £0 (NO BET)
```

---

## The Complete Pick Generation Flow

```
1. FETCH races from Betfair
   ↓
2. For each race, COLLECT data:
   - Odds, form, trainer, jockey, course, class, prize
   ↓
3. ANALYZE with Claude 4.5:
   - Form analysis → base confidence
   - ROI calculation → expected value
   ↓
4. APPLY learning adjustments:
   - Historical calibration
   - Course-specific boosts/penalties
   - Trainer/jockey patterns
   ↓
5. APPLY strategy overlays:
   - Favorite vs Non-favorite adjustments
   - Form hiding detection
   - Elite race boost
   ↓
6. CLASSIFY race tier:
   - ELITE: +20% confidence
   - BIG: +5% confidence
   - SMALL: -15% confidence
   ↓
7. CALCULATE final values:
   - Adjusted confidence
   - Adjusted ROI
   - Stake amount
   ↓
8. ASSIGN decision rating:
   - GREEN (DO IT): 75%+ conf, 20%+ ROI
   - HIGH: 60-74% conf, 15%+ ROI
   - MODERATE: 45-59% conf, 12%+ ROI
   - SKIP: <45% conf or <12% ROI
   ↓
9. VALIDATE & FILTER:
   - Safety checks
   - Minimum thresholds
   - Risk limits
   ↓
10. STORE & DISPLAY:
    - Save to database
    - Show to user
    - Track for learning
```

---

## Continuous Improvement Loop

```
Every Day:
  1. Picks generated (with all strategies applied)
  2. Results fetched (hourly after races)
  3. Performance analyzed (what worked, what didn't)
  4. Insights generated (patterns identified)
  5. Adjustments calculated (improve future picks)
  6. Next picks better (learning applied)
  
Every Week:
  1. Review quality metrics
  2. Assess training phase progress
  3. Refine strategy priorities
  4. Celebrate improvements
  
Every Month:
  1. Major strategy review
  2. ROI trend analysis
  3. Course mastery assessment
  4. GREEN pick percentage growth
```

---

## The Bottom Line

**This system combines:**
1. ✅ AI analysis (Claude 4.5 Sonnet)
2. ✅ Real Betfair odds (live market data)
3. ✅ Historical learning (what actually works)
4. ✅ 67% rule exploitation (value in non-favorites)
5. ✅ Form hiding detection (avoid trainer traps)
6. ✅ Elite race emphasis (trust when everyone tries)
7. ✅ Progressive training (daily improvement)
8. ✅ Quality metrics (path to GREEN picks)

**To achieve:**
- 🎯 GREEN picks (75%+ confidence, 20%+ ROI)
- 💰 Consistent profitability (20-25%+ ROI)
- 📈 Daily improvement (learning from every bet)
- 🏆 Elite race success (where value meets certainty)
- ✅ Long-term sustainability (no gambling, just value)

**When the top of the card turns GREEN:**
You've found exceptional value, high probability, and the system's highest confidence. This is what we train for every single day! 🟢

---

## Related Documentation

- [DAILY_TRAINING_SYSTEM.md](DAILY_TRAINING_SYSTEM.md) - 7-week training progression
- [FAVORITE_VS_NON_FAVORITE_STRATEGY.md](FAVORITE_VS_NON_FAVORITE_STRATEGY.md) - 67% rule exploitation  
- [FORM_HIDING_DETECTION.md](FORM_HIDING_DETECTION.md) - Strategic behavior tracking
- [ELITE_RACE_STRATEGY.md](ELITE_RACE_STRATEGY.md) - Group 1/2/3 and major meetings
- [TRAINING_QUICK_START.md](TRAINING_QUICK_START.md) - Quick user guide
- [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) - Technical architecture

**Last Updated:** January 8, 2026
**System Version:** 2.0 - Complete Strategy Implementation
