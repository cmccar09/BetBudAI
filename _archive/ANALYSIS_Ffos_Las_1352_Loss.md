# ANALYSIS: Ffos Las 13:52 - River Run Free Loss (Feb 20, 2026)

## Race Details
- **Course:** Ffos Las
- **Time:** 13:52
- **Class:** 5
- **Distance:** 3m Handicap Chase
- **Official Going:** HEAVY (Soft in places)
- **Runners:** 7

## Result
1. **River Voyage (IRE)** - 11/4 - J: Toby McCain-Mitchell(5) T: Rebecca Curtis
2. **Steal The Moves (IRE)** - 11/1 - (Dist: 1 length)
3. **River Run Free (IRE)** - 6/4 FAV - J: Jack Tudor T: David Pipe (Dist: 9.5 lengths behind winner)

## Our Analysis vs Reality

### Our Picks
| Horse | Our Score | Odds (Dec) | Result | Error |
|-------|-----------|------------|--------|-------|
| River Run Free | **93/100** | 3.2 (6/4) | 3rd | ❌ HIGH CONFIDENCE LOSS |
| River Voyage | **49/100** | 4.4 (11/4) | **1st** | ❌ WINNER DISMISSED |

### Critical Failures

#### 1. GOING MISCALCULATION
- **Our Prediction:** Soft (-5 adjustment)
- **Actual Conditions:** HEAVY (should be -8)
- **Weather Data:** 19.7mm rainfall over 3 days
- **Error:** Threshold too high - 19.7mm produced Heavy ground, not Soft

**Current Thresholds (weather_going_inference.py):**
```python
if rainfall > 15:  # Should be SOFT
    going = "Soft"
    adjustment = -5
```

**Analysis:**  
- 19.7mm in exposed Welsh location = HEAVY conditions
- Our system classified this as "Soft"
- Need regional adjustments for exposed/elevated tracks
- Ffos Las (Welsh valleys, exposed) holds water differently than sheltered tracks

#### 2. WINNER SCORING FAILURE
**River Voyage: 49/100 (below threshold)**
- Won at 11/4 (implied probability: 31%)
- 5lb claiming jockey advantage
- Trainer Rebecca Curtis (strong Ffos Las record?)
- **Our system completely missed this horse**

**Questions:**
1. Did we underweight claiming jockey advantage in Heavy ground?
2. Was Rebecca Curtis's course record considered?
3. Did River Voyage have proven Heavy ground form we missed?

#### 3. FAVORITE SELECTION ERROR
**River Run Free: 93/100 → 3rd, beaten 10.5 lengths**
- Market favorite (6/4)
- David Pipe trainer (high reputation = bonus points?)
- Jack Tudor jockey
- **Comprehensively beaten on Heavy ground**

**Why did we rate this so highly?**
- Likely overweighted: sweet spot odds (6/4 = optimal range)
- Trainer reputation bonus (David Pipe)
- Possibly good recent form
- **BUT:** Did NOT check Heavy ground suitability properly

## Root Causes

### Primary: Weather Classification Error
```
19.7mm rainfall → System said "Soft" → Actual was "HEAVY"
```
- This corrupted ALL going suitability scoring for this race
- Horses suited to Heavy were penalized
- Horses unsuited to Heavy got bonus points

### Secondary: Winner Evaluation Gap
- 49/100 score for the winner suggests missing factors:
  - Course specialist data?
  - Claiming jockey impact underweighted?
  - Trainer course record?
  - Heavy ground form not properly weighted?

### Tertiary: Favorite Bias
- 93/100 for 6/4 favorite suggests we overweight:
  - Optimal odds range (sweet spot scoring)
  - Trainer reputation
  - Recent form
- **Without sufficient penalty for wrong going**

## Recommended Fixes

### 1. Recalibrate Weather Thresholds (PRIORITY 1)
```python
# OLD (too lenient):
if rainfall > 25: going = "Heavy" 
if rainfall > 15: going = "Soft"

# NEW (proposed):
if rainfall > 15: going = "Heavy"  # More realistic
if rainfall > 10: going = "Soft"
if rainfall > 5: going = "Good to Soft"
```

### 2. Add Regional/Exposure Adjustments
```python
TRACK_CHARACTERISTICS = {
    'Ffos Las': {'exposure': 'HIGH', 'drainage': 'POOR', 'rainfall_multiplier': 1.3},
    'Carlisle': {'exposure': 'HIGH', 'drainage': 'MODERATE', 'rainfall_multiplier': 1.2},
    'Kempton': {'exposure': 'LOW', 'drainage': 'GOOD', 'rainfall_multiplier': 0.9},
}
```

### 3. Increase Going Weight in Heavy Conditions
- Current: going_suitability = 8 points
- **Proposed: In Heavy ground, increase to 15 points**
- Justification: Heavy ground is a MAJOR differentiator - unsuited horses have no chance

### 4. Add Claiming Jockey Bonus in Testing Conditions
- River Voyage won with 5lb claimer in Heavy ground
- **Proposed:** In Soft/Heavy, add +5 points for claiming allowance (reduced weight = advantage)

### 5. Course Specialist Detection
- Check if trainer/horse have won at course before
- Add +5 bonus for course winner
- Rebecca Curtis may have strong Ffos Las record

## Data to Collect

### For River Voyage (Winner)
- **Heavy ground record:** Previous Heavy/Soft runs and results
- **Rebecca Curtis Ffos Las record:** Strike rate and winners at this course
- **Distance suitability:** 3m form
- **Claiming jockey impact:** Toby McCain-Mitchell stats in testing ground

### For River Run Free (Our top pick - failed)
- **Heavy ground record:** Has this horse won on Heavy?
- **David Pipe Heavy ground stats:** Does stable struggle in extreme going?
- **Distance:** Was 3m the right trip in these conditions?

## Confidence Impact

| Metric | Before | After This Loss |
|--------|--------|-----------------|
| Going prediction accuracy | ~80%? | ❌ Major failure |
| High-score pick reliability (90+) | Strong | ⚠️ NOW QUESTIONED |
| Winner detection | ? | ❌ 49/100 = total miss |

## Financial Impact
- **If £10 stake:** -£10 loss
- **If followed favorite:** Lost at short odds (6/4)
- **If backed winner:** Would need to spot it despite 49/100 score

## Next Steps
1. ✅ Add Ffos Las to weather tracking (DONE)
2. ⏳ Recalibrate rainfall → going thresholds
3. ⏳ Add regional exposure multipliers
4. ⏳ Increase going weight in Heavy conditions
5. ⏳ Research Rebecca Curtis Ffos Las record
6. ⏳ Add claiming jockey bonus logic
7. ⏳ Pull River Voyage + River Run Free historical form

## Tags
`#HEAVY_GROUND` `#GOING_ERROR` `#HIGH_CONFIDENCE_LOSS` `#WINNER_MISSED` `#WEATHER_CLASSIFICATION` `#CLAIMING_JOCKEY` `#COURSE_SPECIALIST`

---
*Date: Feb 20, 2026*  
*Analysis Type: POST-RACE LOSS REVIEW*  
*Priority: CRITICAL - System scored winner at 49/100 and loser at 93/100*
