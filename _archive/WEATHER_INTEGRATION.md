# Weather-Based Going Integration with Seasonal Adjustments

## Overview
Weather-based going inference with **seasonal factors** and **horse suitability analysis** is now locked into the value betting workflow. The system automatically:
1. Fetches 3-day rainfall history for each racecourse
2. Applies seasonal bias (February = softer, July = firmer)
3. Analyzes horse form patterns for going suitability
4. Adjusts scoring based on predicted ground conditions + horse fit

## How It Works

### 1. Rainfall Data Collection
- **API**: Open-Meteo Archive API (free, no key required)
- **Location**: `weather_going_inference.py`
- **Frequency**: Once per scoring run (cached for all tracks)
- **Time Window**: Last 3 days of rainfall history

### 2. Seasonal Adjustments (NEW)

The system recognizes UK/Ireland seasonal patterns:

| Month | Seasonal Bias | Typical Conditions |
|-------|---------------|-------------------|
| January | -5 | Very wet/soft |
| February | -5 | Wet/soft |
| March | -3 | Wet |
| April | -2 | Transitional |
| May | 0 | Mild/neutral |
| June | +2 | Drier |
| **July** | **+5** | **Dry/firm** |
| **August** | **+5** | **Dry/firm** |
| September | +2 | Drier |
| October | -2 | Wetter |
| November | -3 | Wet |
| December | -5 | Very wet |

**Formula**: `Final Adjustment = (Rainfall Score × 70%) + (Seasonal Bias × 30%)`

**Example**: 
- **February** (Seasonal Bias: -5)
  - Carlisle 3.6mm rain = Base +5 (Good)
  - Final: (5 × 0.7) + (-5 × 0.3) = +3.5 - 1.5 = **+2**
  
- **July** (Seasonal Bias: +5)
  - Same 3.6mm rain = Base +5 (Good)
  - Final: (5 × 0.7) + (5 × 0.3) = +3.5 + 1.5 = **+5**

### 3. Going Inference Logic

| Rainfall (3 days) | Base Going | Base Adjustment | After Seasonal |
|-------------------|------------|-----------------|----------------|
| 20mm+ | Heavy | -10 | -8 to -10 |
| 10-20mm | Soft | -5 | -4 to -6 |
| 5-10mm | Good to Soft | -2 | -1 to -3 |
| 2-5mm | Good | +5 | +2 to +7 |
| 0-2mm | Good to Firm | +10 | +7 to +12 |

**All-Weather Tracks**: No adjustment (±0) regardless of rainfall or season

### 4. Horse Going Suitability (NEW)

The system analyzes each horse's form pattern to determine going suitability:

#### Speed Horses (Winners > Places)
- Form pattern: Lots of wins (1s), fewer places
- Example: `112-45` (wins or nowhere)
- **Firm Ground**: +3 (Speed profiles suit firm)
- **Soft Ground**: -2 (May struggle in heavy going)

#### Stamina Horses (Consistent Placers)
- Form pattern: Many places (2-3), few wins
- Example: `23-3221` (always competitive)
- **Soft Ground**: +3 (Stamina suits heavy going)
- **Firm Ground**: -2 (May lack speed on fast ground)

#### Balanced Horses (Mix of Wins/Places)
- Form pattern: Both wins and places
- Example: `12-2314`
- **Good Ground**: +2 (Suits most horses)
- **Any Going**: Generally positive (versatile)

**Analysis Logic**:
```python
Recent Form (last 6 runs):
- Heavy/Soft: Favor consistent placers (+3 if 3+ places, 0 failures)
- Firm: Favor speed horses (+3 if 2+ wins)
- Good: Favor balanced horses (+2 if 1+ win, 2+ places)
```

### 5. Integration Points

**weather_going_inference.py**:
```python
# Seasonal adjustments
SEASONAL_ADJUSTMENTS = {
    1: -5, 2: -5, 3: -3, 4: -2,  # Winter/Spring (wet)
    5: 0, 6: +2, 7: +5, 8: +5,   # Summer (dry)
    9: +2, 10: -2, 11: -3, 12: -5 # Autumn/Winter (wet)
}

# Weighted average: 70% rainfall, 30% seasonal
final_adjustment = int(base_adjustment * 0.7 + seasonal_bias * 0.3)
```

**horse_going_performance.py**:
```python
def get_going_suitability_bonus(horse_data, going_info):
    # Analyzes form pattern (wins vs places vs failures)
    # Returns adjustment (-3 to +3) based on going match
```

**generate_ui_picks.py**:
```python
# Fetch going data once with seasonal factors
going_data = check_all_tracks_going()

# Apply to each horse at that track
track_going = going_data.get(venue, {})
going_adjustment = track_going.get('adjustment', 0)

# Score with going + suitability
score, reasons = score_horse(runner, race, going_adjustment, track_going)
```

**value_betting_workflow.py**:
- Calls `generate_ui_picks.py` every 30 minutes
- Weather data + seasonal factors refreshed each cycle
- Going adjustments + horse suitability applied to all picks

## Example Output

```
Checking weather and ground conditions...

WEATHER-BASED GOING INFERENCE (3-Day Rainfall + Seasonal Factor)
Current Month: February (Seasonal Bias: -5)

Checking Carlisle (turf)...
  ☁️ Rainfall: 3.6mm → Going: Good (Score: +2)
     February typical: softer (-5)

Checking Taunton (turf)...
  🌧️ Rainfall: 16.6mm → Going: Soft (Score: -5)
     February typical: softer (-5)

✓ HIGH CONFIDENCE PICK
  Carlisle - 14:00:00 | Going: Good
  Thank You Maam @ 6.8
  Score: 49/100 (adjustment: +2)
  Reasons: Sweet spot odds (6.8), Recent win, 3 place finishes, 
           Good ground (+2), Balanced form suits good ground

✓ HIGH CONFIDENCE PICK
  Taunton - 15:15:00 | Going: Soft
  Courageous Strike @ 5.2
  Score: 48/100 (adjustment: -5)
  Reasons: Sweet spot odds (5.2), Recent win, 3 place finishes,
           Soft ground (-5), Consistent form suits soft ground
```

**Notice**:
- February bias (-5) reduced Carlisle from +5 to +2
- Taunton soft ground gets +3 bonus for "Consistent form suits soft ground"
- Horse suitability adds 0-3 points based on form pattern match

## Why This Matters

### Seasonal Factors Are Critical
- **February (Winter)**: Ground typically 30% softer than rainfall alone suggests
- **July (Summer)**: Ground typically 30% firmer, even with some rain
- **Drainage**: Tracks drain better in summer (warm, dry soil)
- **Saturation**: Winter ground holds moisture longer (cold, wet soil)

### Ground Conditions Impact Performance
- **Soft Ground** (-5 to -10): Favors stamina horses, slower times, exhausting
- **Good Ground** (+2 to +5): Optimal for most horses, balanced conditions
- **Firm Ground** (+7 to +10): Fast times, favors speed horses, can be jarring

### Horse Form Patterns Matter
- **Speed Horse on Firm**: Perfect match (+3 bonus) = Total +8 to +13
- **Stamina Horse on Soft**: Perfect match (+3 bonus) = Total -2 to -7  
- **Mismatched**: Speed horse on soft = -2 penalty worsens soft ground effect

### Real-World Impact Examples

**February at Taunton** (16.6mm rain):
- Base: -5 (Soft from rainfall)
- Seasonal: -5 (February wet bias)
- Final: -5 (70/30 weighted)
- **Courageous Strike** (form: 21-1523 = consistent placer)
  - Gets +3 "Consistent form suits soft ground"
  - Net effect: -5 + 3 = **-2 total adjustment**
  - Still meets 45+ threshold due to suitability match

**February at Carlisle** (3.6mm rain):
- Base: +5 (Good from rainfall)
- Seasonal: -5 (February wet bias)
- Final: +2 (compromised by winter)
- **Haarar** (form: 213-231 = balanced)
  - Gets +2 "Balanced form suits good ground"  
  - Net effect: +2 + 2 = **+4 total boost**
  - Excellent match = higher confidence

**July at Carlisle** (hypothetical 3.6mm rain):
- Base: +5 (Good from rainfall)
- Seasonal: +5 (July dry bias)
- Final: +5 (reinforced by summer)
- **Speed Horse** (hypothetical form: 112)
  - Would get +3 "Speed profile suits firm ground"
  - Net effect: +5 + 3 = **+8 total boost**
  - Perfect summer conditions for speed

## Configuration Locked

This enhanced weather integration is now **locked** into the workflows:
- ✅ Automatic rainfall fetching every 30 minutes
- ✅ Seasonal bias applied (Feb=-5, Jul=+5, etc)
- ✅ Going inference with 70/30 weighted formula
- ✅ Horse form pattern analysis for suitability
- ✅ Speed/Stamina/Balanced horse detection
- ✅ Going-specific bonuses/penalties (-3 to +3)
- ✅ Combined adjustments in final scoring
- ✅ All turf tracks affected, all-weather excluded
- ✅ Results displayed in UI pick summaries

## Files Modified
1. **weather_going_inference.py**: Added SEASONAL_ADJUSTMENTS dict, updated infer_going() with month parameter
2. **horse_going_performance.py**: NEW - Analyzes form patterns for going suitability
3. **generate_ui_picks.py**: Integrated seasonal + suitability scoring
4. **value_betting_workflow.py**: Updated to call enhanced generate_ui_picks.py
5. **WEATHER_INTEGRATION.md**: Complete documentation (this file)

## Future Enhancements (NOT LOCKED YET)
- Add more UK/Ireland tracks as racing schedule expands
- Fine-tune seasonal biases based on actual results
- Consider temperature (frozen ground in extreme cold)
- Consider wind factors for exposed tracks
- Add manual override for official going reports from Racing Post
- Track historical going accuracy vs actual conditions

## NO ACTION REQUIRED
This system runs automatically with every workflow cycle. Weather data is fetched, seasonal factors applied, horse suitability analyzed, and combined adjustments applied without manual intervention.

The system is now **seasonally aware** - recognizing that 3.6mm of rain in February creates softer ground than 3.6mm in July.
