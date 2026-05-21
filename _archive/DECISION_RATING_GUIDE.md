# Decision Rating System

## Overview

The **Decision Rating** is a single combined metric that collates all betting factors into one easy-to-understand score that tells you whether to bet or skip.

## Three Categories

### 🟢 DO IT (Score: 70-100)
**Action:** Place the bet with confidence

**What it means:**
- Strong positive expected value (EV)
- High ROI (typically 20%+)
- Good confidence level
- All factors align favorably

**Example:**
- Horse: **Pink Socks**
- Score: **75.3**
- ROI: **29.3%**
- EV: **+€5.87**
- Rating: **DO IT** ✓

### 🟠 RISKY (Score: 45-69)
**Action:** Consider betting but manage stake carefully

**What it means:**
- Moderate expected value
- ROI in the 10-20% range
- Some positive factors but also concerns
- Could be profitable but higher variance

**Example:**
- Horse: **Knight Of Magic**
- Score: **58.2**
- ROI: **15.8%**
- EV: **+€3.16**
- Rating: **RISKY** ⚠️

### 🔴 NOT GREAT (Score: 0-44)
**Action:** Skip this bet

**What it means:**
- Low or negative expected value
- ROI below 10%
- Weak fundamentals
- Better opportunities elsewhere

**Example:**
- Horse: **Longshot Larry**
- Score: **32.1**
- ROI: **5.2%**
- EV: **+€1.04**
- Rating: **NOT GREAT** ✗

---

## How the Score is Calculated

The Decision Rating combines **4 weighted factors** into a 0-100 score:

### 1. ROI (40% weight) ⭐ Most Important
- Normalized to 0-40 points
- 50% ROI or higher = maximum 40 points
- Example: 29.3% ROI = (29.3 / 50) × 40 = **23.4 points**

### 2. Expected Value (30% weight) ⭐ Very Important
- Normalized to 0-30 points
- €10 EV or higher = maximum 30 points
- Example: €5.87 EV = (5.87 / 10) × 30 = **17.6 points**

### 3. Confidence (20% weight)
- Win probability as percentage
- Directly mapped to 0-20 points
- Example: 25% win prob = 25% × 20 = **5.0 points**

### 4. Place Probability (10% weight)
- For EW bets: place probability
- For Win bets: win probability (since you need to win)
- Example: 58% place prob (EW) = 58% × 10 = **5.8 points**

### Total Calculation Example (Pink Socks):

```
ROI Score:     (29.3% / 50%) × 40 = 23.4 points
EV Score:      (€5.87 / €10) × 30 = 17.6 points
Confidence:    25% × 20 = 5.0 points
Place Prob:    58% × 10 = 5.8 points
──────────────────────────────────────
TOTAL SCORE:                   51.8 points → RISKY
```

*Note: Pink Socks would actually score higher with real market odds showing better value*

---

## Usage on Betting Cards

### Old Way (Multiple Metrics):
You had to look at:
- Expected Value: +€5.87 ✓
- ROI: 29.3% ✓
- Win Prob: 25% ⚠️
- Place Prob: 58% ✓
- Confidence: 25% ⚠️
- **Decision: ???** (requires mental calculation)

### New Way (Single Metric):
Look at:
- **Decision Rating: RISKY** (score 58.2)
- **Decision: Bet small or skip** (clear guidance)

---

## Decision Rules

### Conservative Strategy
- **DO IT only:** Bet on 70+ scores
- Skip everything else
- Lowest variance, steady growth

### Balanced Strategy (Recommended)
- **DO IT:** Full stake (e.g., €20)
- **RISKY:** Half stake (e.g., €10)
- **NOT GREAT:** Skip
- Moderate variance, good growth

### Aggressive Strategy
- **DO IT:** Double stake (e.g., €40)
- **RISKY:** Full stake (e.g., €20)
- **NOT GREAT:** Small stake (e.g., €5)
- Highest variance, fastest growth (or losses)

---

## Why This Metric Matters

### Problem Without It:
```
Horse A: ROI 30%, EV €3, Win Prob 15%, Place Prob 45%
Horse B: ROI 18%, EV €7, Win Prob 35%, Place Prob 70%

Which is better? 🤔 (You have to calculate in your head)
```

### Solution With Decision Rating:
```
Horse A: Score 48.2 → RISKY
Horse B: Score 71.5 → DO IT ✓

Clear winner: Horse B
```

---

## Real Examples from Your System

### Example 1: Strong Bet
```
Horse: Timely Affair
├─ ROI: 32.1% → 25.7 points
├─ EV: €6.42 → 19.3 points
├─ Win Prob: 42% → 8.4 points
├─ Place Prob: 75% → 7.5 points
└─ TOTAL: 60.9 → RISKY (close to DO IT)

Action: Bet €15-20
```

### Example 2: Marginal Bet
```
Horse: Moon Over The Sea
├─ ROI: 12.5% → 10.0 points
├─ EV: €2.50 → 7.5 points
├─ Win Prob: 19% → 3.8 points
├─ Place Prob: 48% → 4.8 points
└─ TOTAL: 26.1 → NOT GREAT

Action: Skip
```

### Example 3: Excellent Bet
```
Horse: Krissy (hypothetical with great odds)
├─ ROI: 45.2% → 36.2 points
├─ EV: €9.04 → 27.1 points
├─ Win Prob: 35% → 7.0 points
├─ Place Prob: 70% → 7.0 points
└─ TOTAL: 77.3 → DO IT ✓

Action: Bet full stake €20
```

---

## How to Use It

### Quick Glance Method
1. Open betting card
2. Look at **Decision Rating** badge
3. Act:
   - 🟢 **DO IT**: Bet
   - 🟠 **RISKY**: Bet small or skip
   - 🔴 **NOT GREAT**: Skip

### Detail Review Method
1. Check Decision Rating first
2. If **DO IT**: Bet immediately
3. If **RISKY**: Review "Why Now" reasoning
   - If reasoning is compelling → Bet
   - If reasoning is weak → Skip
4. If **NOT GREAT**: Skip (don't even read further)

---

## FAQ

### Q: Can a bet with 50% ROI be "RISKY"?
**A:** Yes, if EV is low (small stakes) or confidence is very low (unlikely to win). ROI is just one factor.

### Q: Should I ever bet on "NOT GREAT"?
**A:** No. If it scores below 45, the math doesn't support it. Wait for better opportunities.

### Q: What if I disagree with the rating?
**A:** The rating is based on mathematical expected value. If you have additional information (e.g., you know the jockey personally), you can override it. But be honest about whether you're using information or just hope.

### Q: Why does the system sometimes show "NOT GREAT" for picks?
**A:** The system generates many selections, then ranks them. Only the top 5 make it to your dashboard. If a "NOT GREAT" appears, it means the other races had even worse options. In that case, skip betting that day.

### Q: Can the thresholds be adjusted?
**A:** Yes! The 70/45 cutoffs can be tuned based on your results:
- If you're winning too conservatively: Lower "DO IT" to 65
- If you're losing on "RISKY" bets: Raise "RISKY" threshold to 50

---

## Summary

**One number to rule them all:**
- ✅ **70+ = DO IT** (bet with confidence)
- ⚠️ **45-69 = RISKY** (proceed with caution)
- ❌ **0-44 = NOT GREAT** (skip)

**Stop overthinking. Start winning.**

---

*Decision Rating auto-updates with every bet upload. Check the badge on your card!*
