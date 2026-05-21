# Learning from Fairyhouse 16:40 (February 3, 2026)

## Race Result
**Fairyhouse 16:40 - Soft Ground | 7 Runners**

| Position | Horse | Odds | Trainer | Notes |
|----------|-------|------|---------|-------|
| 1st | **Outofafrika** | **5/1** | Gavin Patrick Cromwell | WON |
| 2nd | Green Hint | 4/7 FAV | W. P. Mullins | 6 lengths behind |
| 3rd | Lemmy Caution | 6/1 | Gordon Elliott | 10 lengths behind |

## System Status
**NOT IN DATABASE** - Race was not fetched or analyzed by our system.

## Key Learning Points

### 1. **Favorite Lost** - Green Hint (4/7)
- **Willie Mullins trained** - Usually very strong
- **Peter Mullins riding** (amateur, but from the famous family)
- **Beaten 6 lengths** by a 5/1 shot
- **Learning:** Even hot favorites (4/7) from top yards can be beaten in soft ground races

### 2. **Winner: Outofafrika (5/1)**
- **Gavin Patrick Cromwell trained** - Good trainer, especially on soft
- **Amateur jockey** (Mr D. G. Lavery)
- **5/1 odds** - Not an outsider, but not favored
- **Learning:** Mid-range prices (5/1) in soft ground races can represent value when from in-form yards

### 3. **Soft Ground Impact**
- Soft ground can be a great leveler
- Form on good/firm might not translate
- Horses proven on soft have significant advantage
- **Learning:** Our scoring should heavily weight:
  - Recent soft/heavy ground performances
  - Trainer's soft ground strike rate
  - Course/distance winners on similar going

### 4. **Small Field Dynamics (7 Runners)**
- With only 7 runners, favorite should theoretically have better chance
- Yet favorite still beaten
- **Learning:** Small fields don't guarantee favorite wins, especially on soft ground

### 5. **Amateur Jockeys**
- Both 1st (Outofafrika) and 3rd (Lemmy Caution) ridden by amateur jockeys (Mr.)
- Favorite ridden by amateur too (P. W. Mullins)
- **Learning:** In amateur races, form and going are MORE important than jockey prestige

## System Implications

### Why We Likely Would Have Struggled
If we HAD analyzed this race, our system would have faced challenges:

1. **Favorite Bias:** Might have picked Green Hint (4/7, Willie Mullins)
2. **Form Reading:** Would need to check if recent form was on soft ground
3. **Going Adjustment:** Critical - soft ground specialists vs good ground horses

### What Our Scoring SHOULD Do

#### Already Doing Well:
✓ Conservative scoring (wouldn't blindly back 4/7 favorite)
✓ Form position weighting (recent runs matter most)
✓ LTO (Last Time Out) bonus for winners

#### Need to Enhance:
⚠️ **Going-specific form analysis**
   - Weight soft/heavy ground performances higher
   - Penalize horses with no soft ground form
   - Bonus for proven soft ground winners

⚠️ **Trainer soft ground statistics**
   - Track trainers' soft ground strike rates
   - Cromwell is strong on soft - should be weighted

⚠️ **Going change detection**
   - If race going changed from forecast, adjust confidence
   - Soft ground is a major form reversal factor

### Recommended Scoring Adjustments

```python
# In calculate_confidence_score():

# 1. Going-specific form bonus
if going in ['Soft', 'Heavy']:
    if has_recent_soft_win:
        score += 15  # Major bonus for proven soft winner
    elif has_soft_form:
        score += 8   # Good bonus for soft ground form
    elif no_soft_experience:
        score -= 10  # Penalty for unproven on soft

# 2. Trainer going statistics
trainer_soft_strike_rate = get_trainer_soft_stats(trainer)
if going in ['Soft', 'Heavy'] and trainer_soft_strike_rate > 0.20:
    score += 10  # Trainer excels on soft

# 3. Favorite reliability check
if odds < 2.0 and going in ['Soft', 'Heavy']:
    score -= 5   # Short favorites less reliable on soft
```

## Validation Against Our Current System

### Current Thresholds (NEW):
- EXCELLENT: 75+ (would bet 2.0x)
- GOOD: 60-74 (would bet 1.5x)
- FAIR: 45-59 (would bet 1.0x)
- POOR: <45 (skip or 0.5x)

### How This Race Would Score (Estimated):

**Green Hint (4/7 FAV):**
- Base: 30
- Recent form: +15 (if recent wins)
- Willie Mullins: +10 (top trainer)
- Favorite penalty on soft: -5
- **Estimated: 50/100 = FAIR**
- Would bet 1.0x base stake
- **LOST** (2nd place)

**Outofafrika (5/1 WINNER):**
- Base: 30
- Recent form: +10 (moderate)
- Cromwell on soft: +10 (if we tracked this)
- Going-specific bonus: +15 (if proven on soft)
- **Estimated: 65/100 = GOOD**
- Would bet 1.5x base stake
- **WON** ✓

### Conclusion
If we had the going-specific enhancements, we MIGHT have:
1. ✓ Not overconfident on Green Hint (50 vs 65)
2. ✓ Identified Outofafrika as better value (65 GOOD)
3. ✓ Made profit on 5/1 winner at 1.5x stake

**BUT** - Race wasn't in database, so we need to ensure betfair_odds_fetcher.py captures ALL UK/Ireland races.

## Action Items

### Immediate:
1. ✓ Race not in database - ensure odds fetcher gets all races
2. Add going-specific form analysis to scoring
3. Add trainer going statistics to database

### Medium-Term:
1. Build going-specific form database
2. Track which horses have proven soft/heavy form
3. Weight recent soft wins heavily in scoring

### Long-Term:
1. Machine learning on going-specific patterns
2. Trainer/going combination analysis
3. Course/going specialist detection

## Quote for System
> "Soft ground is the great leveler. Favorites mean less, form on the wrong ground means nothing, and specialists reign supreme."

## Tags
`#soft_ground` `#going_analysis` `#favorite_beaten` `#amateur_race` `#fairyhouse` `#cromwell` `#learning`
