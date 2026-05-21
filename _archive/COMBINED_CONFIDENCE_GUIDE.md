# Combined Confidence Rating System

## Overview

The **Combined Confidence Rating** is a unified 0-100 metric that consolidates ALL confidence signals into one clear indicator. Unlike the Decision Rating (which tells you **whether to bet**), this tells you **how confident we are in the prediction**.

---

## What Makes This Different?

### Decision Rating vs Combined Confidence

| Metric | Purpose | What It Measures |
|--------|---------|------------------|
| **Decision Rating** | Bet quality | Should you bet? (ROI, EV, value) |
| **Combined Confidence** | Prediction strength | How sure are we? (probability accuracy) |

**Example:**
- Horse A: Decision Rating 75 (DO IT), Combined Confidence 45 (MODERATE)
  - *Good value bet, but moderate certainty - bet smaller*
- Horse B: Decision Rating 55 (RISKY), Combined Confidence 82 (VERY HIGH)  
  - *Not great value, but we're very sure of the outcome - skip or small bet*

---

## The Four Components (100-Point Scale)

### 1. Win Probability (40% weight) ⭐⭐⭐
**Most Important Component**

- Direct measure of how likely we think the horse will win
- Based on AI analysis, form, class, conditions
- **Calculation:** `p_win × 40`
- **Example:** 35% win probability = 14 points

**Why 40%?** This is our core prediction - everything else supports it.

---

### 2. Place Probability (20% weight) ⭐⭐
**Safety Net Component**

- Even if doesn't win, how likely to place (top 3-4)?
- Reduces risk for Each-Way bets
- **Calculation:** `p_place × 20`
- **Example:** 65% place probability = 13 points

**Why 20%?** Provides downside protection and consistency check.

---

### 3. Value Edge (20% weight) ⭐⭐
**Market Validation Component**

- How much better is our probability vs market odds?
- Confirms we've found genuine value, not just hope
- **Calculation:** 
  ```
  market_prob = 1 / odds
  edge = p_win - market_prob
  edge_score = min(20, (edge / 0.15) × 20)
  ```
- **Example:** 
  - Market odds 5.0 = 20% implied probability
  - Our p_win = 28%
  - Edge = 8% → Score = 10.7 points

**Why 20%?** Market disagreement validates our analysis.

---

### 4. Consistency Score (20% weight) ⭐⭐
**Internal Agreement Component**

- How well do our different signals align?
- Checks for contradictions in the data
- Signals checked:
  - p_win vs p_place (place should be higher)
  - p_win vs research confidence (should align)
  - Signal variance (low variance = high consistency)
- **Calculation:**
  ```
  variance = sum((signal - mean)² for each signal) / count
  consistency = max(0, 1 - (variance × 5))
  score = consistency × 20
  ```
- **Example:** All signals agree within 5% = 18+ points

**Why 20%?** Contradictory signals indicate uncertainty.

---

## Grade Thresholds

### 🟢 VERY HIGH (70-100)
**Meaning:** Multiple strong signals all pointing same direction

**Characteristics:**
- High win probability (30%+)
- Strong place probability (60%+)  
- Significant market edge (10%+ overlay)
- All signals agree (low variance)

**Action:** High conviction - can bet with confidence

**Example:**
```
Win Component:      35% × 40 = 14.0 points
Place Component:    68% × 20 = 13.6 points
Edge Component:     12% edge = 16.0 points
Consistency:        0.92 × 20 = 18.4 points
─────────────────────────────────────────
TOTAL:                        72.0 → VERY HIGH ✓
```

---

### 🟢 HIGH (50-69)
**Meaning:** Good signals with reasonable consistency

**Characteristics:**
- Decent win probability (20-30%)
- Good place probability (50-60%)
- Some market edge (5-10% overlay)
- Signals mostly agree

**Action:** Solid bet - normal stake

**Example:**
```
Win Component:      25% × 40 = 10.0 points
Place Component:    55% × 20 = 11.0 points
Edge Component:     7% edge = 9.3 points
Consistency:        0.85 × 20 = 17.0 points
─────────────────────────────────────────
TOTAL:                        47.3 → HIGH
```

---

### 🟠 MODERATE (35-49)
**Meaning:** Mixed signals - proceed with caution

**Characteristics:**
- Lower win probability (15-20%)
- Moderate place probability (40-50%)
- Small edge or no edge (0-5%)
- Some signal disagreement

**Action:** Risky territory - reduce stake or skip

**Example:**
```
Win Component:      18% × 40 = 7.2 points
Place Component:    45% × 20 = 9.0 points
Edge Component:     3% edge = 4.0 points
Consistency:        0.70 × 20 = 14.0 points
─────────────────────────────────────────
TOTAL:                        34.2 → MODERATE ⚠️
```

---

### 🔴 LOW (0-34)
**Meaning:** Weak or conflicting signals - avoid

**Characteristics:**
- Low win probability (<15%)
- Low place probability (<40%)
- No edge or negative edge
- Signals contradict each other

**Action:** Skip this bet

**Example:**
```
Win Component:      12% × 40 = 4.8 points
Place Component:    35% × 20 = 7.0 points
Edge Component:     -2% edge = 0.0 points
Consistency:        0.45 × 20 = 9.0 points
─────────────────────────────────────────
TOTAL:                        20.8 → LOW ❌
```

---

## How to Use Both Ratings Together

### The 2×2 Decision Matrix

|  | **High Confidence** (70+) | **Low Confidence** (<50) |
|---|---|---|
| **DO IT** (Decision 70+) | 💎 **PREMIUM BET** - Full stake | ⚠️ **VALUE GAMBLE** - Small stake |
| **RISKY** (Decision 45-69) | 💰 **SAFE BET** - Normal stake | ❌ **SKIP** - Too uncertain |

### Real Examples:

#### 💎 Premium Bet (Best Scenario)
```
Horse: Pink Socks
Decision Rating: 75 (DO IT)
Combined Confidence: 82 (VERY HIGH)
→ Strong value + high certainty = FULL STAKE €30
```

#### 💰 Safe Bet (Good Scenario)
```
Horse: Night Runner  
Decision Rating: 58 (RISKY)
Combined Confidence: 78 (VERY HIGH)
→ Moderate value but very certain = NORMAL STAKE €20
```

#### ⚠️ Value Gamble (Careful Scenario)
```
Horse: Lucky Strike
Decision Rating: 72 (DO IT)
Combined Confidence: 38 (MODERATE)
→ Good value but uncertain = SMALL STAKE €10
```

#### ❌ Skip (Avoid Scenario)
```
Horse: Wild Card
Decision Rating: 52 (RISKY)
Combined Confidence: 32 (LOW)
→ Poor value + low confidence = SKIP
```

---

## Why This Matters

### Before (Confusion):
```
Horse: Midnight Star
Win Prob: 28%
Place Prob: 62%
Research Confidence: 75
Market Edge: 8%
Odds: 4.5

Decision: ??? (need to calculate everything mentally)
```

### After (Clarity):
```
Horse: Midnight Star
Combined Confidence: 71.2 (VERY HIGH)
Decision Rating: 68 (RISKY)

Decision: Good confidence, moderate value → Bet €15-20
```

---

## Confidence Breakdown (Transparency)

Each bet shows detailed component scores for full transparency:

```json
{
  "combined_confidence": 71.2,
  "confidence_grade": "VERY HIGH",
  "confidence_breakdown": {
    "win_component": 14.0,      // 35% × 40
    "place_component": 13.6,    // 68% × 20
    "edge_component": 16.0,     // 12% edge
    "consistency_component": 18.4, // 92% consistency
    "raw_signals": {
      "p_win": 0.35,
      "p_place": 0.68,
      "market_edge": 0.12,
      "consistency_score": 0.92
    }
  }
}
```

This lets you see exactly where the confidence comes from!

---

## FAQ

### Q: Can a bet have high Decision Rating but low Combined Confidence?
**A:** Yes! This means good value but uncertain outcome. Bet smaller or skip.

### Q: What if Combined Confidence is high but Decision Rating is low?
**A:** We're confident in the prediction, but there's no value in the odds. Skip.

### Q: Should I always bet on VERY HIGH confidence?
**A:** No! Check Decision Rating too. High confidence + poor value = no bet.

### Q: What's a perfect bet?
**A:** Decision Rating 70+ AND Combined Confidence 70+ = Premium bet!

### Q: How often will I see VERY HIGH confidence?
**A:** Roughly 20-30% of picks if the system is working correctly.

---

## Technical Details

### Signal Consistency Calculation

```python
def calculate_consistency(signals):
    mean = sum(signals) / len(signals)
    variance = sum((s - mean) ** 2 for s in signals) / len(signals)
    consistency = max(0, 1 - (variance * 5))
    return consistency
```

**Example:**
```
Signals: [0.35, 0.38, 0.33]  # p_win, normalized_place, normalized_research
Mean: 0.353
Variance: 0.00043
Consistency: 1 - (0.00043 × 5) = 0.998 → Excellent!
```

### Edge Normalization

```python
def normalize_edge(edge):
    # 15% edge or more = maximum 20 points
    return min(20, (edge / 0.15) * 20)
```

**Example:**
```
Edge = 8%
Score = (0.08 / 0.15) × 20 = 10.67 points
```

---

## Summary

**Combined Confidence tells you:**
- ✅ How sure we are in the prediction
- ✅ Whether our signals agree
- ✅ If we have market validation
- ✅ Overall prediction strength

**Use it with Decision Rating to make informed betting decisions:**
- Both HIGH = Premium bet (full stake)
- Confidence HIGH, Decision MODERATE = Safe bet (normal stake)  
- Decision HIGH, Confidence MODERATE = Value gamble (small stake)
- Both LOW = Skip

**One number. Clear guidance. Better decisions.**

---

*Combined Confidence auto-calculates for every bet. Check the blue badge on your betting card!*
