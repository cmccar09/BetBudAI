# BetBudAI Historical Analysis System

**Created**: 2026-05-20  
**Purpose**: Validate Weight V3 adjustments using 30 days of historical data  
**Status**: Ready for execution

---

## Overview

This system analyzes historical BetBudAI results to:
1. Extract patterns from wins and losses
2. Validate weight adjustments (Weight V3)
3. Categorize loss types
4. Backtest proposed changes
5. Generate actionable insights

## System Components

### 1. Primary Analysis Script (DynamoDB)
**File**: `scripts/analyze_historical_month.py`

**Purpose**: Full 30-day analysis from DynamoDB (April 20 - May 20, 2026)

**Features**:
- Queries DynamoDB for all settled picks
- Categorizes losses by pattern type
- Validates weight correlations (win vs loss)
- Backtests Weight V3 on historical data
- Generates comprehensive reports

**Usage**:
```bash
python scripts/analyze_historical_month.py
```

**Requirements**:
- AWS credentials configured
- DynamoDB table: `SureBetBets`
- Date range: 2026-04-20 to 2026-05-20
- Expected picks: ~150-200 races

**Output Files**:
- `HISTORICAL_ANALYSIS_30_DAYS.md` - Complete findings report
- `historical_patterns.json` - Pattern frequency data
- `weight_validation_report.json` - Weight correlation data
- `backtest_results.json` - V3 performance simulation

---

### 2. Alternative Analysis Script (JSON)
**File**: `scripts/analyze_historical_from_json.py`

**Purpose**: Analysis from existing JSON data files (when DynamoDB unavailable)

**Features**:
- Works with `last7_race_deep_analysis_fresh.json`
- Analyzes 284 races (May 12-18, 2026)
- Validates consistency placer bias pattern
- Backtests Weight V3
- Same report structure as primary script

**Usage**:
```bash
python scripts/analyze_historical_from_json.py
```

**Requirements**:
- `last7_race_deep_analysis_fresh.json` in root directory
- No AWS credentials needed
- Sample size: 284 races (7 days)

**Output Files**:
- Same as primary script
- Note: Report indicates 7-day sample size

---

## Loss Pattern Categories

### 1. Consistent Placer Bias
**Definition**: High consistency (≥12pts) + high form velocity (≥18pts) → 2nd/3rd finish

**Indicators**:
- Finish position: 2nd or 3rd
- Consistency signal: ≥12pts
- Form velocity signal: ≥18pts
- Horse profile: "Reliable placer, not winner"

**Weight V3 Response**:
- Consistency: 12pts → 8pts (-4pts)
- Form velocity: 18pts → 12pts (-6pts)

**Historical Frequency**: TBD (will be calculated by script)

---

### 2. Class Advantage Missed
**Definition**: Winner had class drop advantage we undervalued

**Indicators**:
- Our pick class_drop_bonus: <10pts
- Winner dropped in class
- Winner had class_drop_rebound pattern

**Weight V3 Response**:
- Class drop bonus: 24pts → 28pts (+4pts)

---

### 3. Pace Signal Missing
**Definition**: Winner matched race pace, we missed it (pre-Phase 1)

**Indicators**:
- No pace_match_bonus in our pick
- Winner likely had pace advantage
- Pre-Phase 1 deployment (before May 20)

**Response**:
- Phase 1 deployed May 20
- Run style + pace matching now active
- Expected +7-12% strike rate improvement

---

### 4. Jockey Upgrade Missing
**Definition**: Winner had elite jockey booking we missed (pre-Phase 1)

**Indicators**:
- No jockey_upgrade_bonus in our pick
- Winner had Dettori/Buick/Murphy/similar
- Elite jockey at secondary course

**Response**:
- Phase 1 deployed May 20
- Jockey upgrade detection now active
- +10-22pts bonus for elite upgrades

---

### 5. Market Surprise (Longshot)
**Definition**: Winner had odds >8.0 (double-digit)

**Indicators**:
- Winner SP: >8.0
- Ranked 6+ in pre-race betting
- Genuine upset/variance

**Response**:
- No weight change (acceptable variance)
- Monitor frequency
- Alert if >40% of losses

---

### 6. Recent Win Overweight
**Definition**: Our pick scored high on recent_win but lost

**Indicators**:
- Recent win signal: ≥14pts
- Finish position: 4th or worse
- Horse at performance ceiling

**Response**:
- Monitor pattern frequency
- Consider adding "recent_win_recency_multiplier"
- Win in last 7 days = 1.5x bonus

---

### 7. Form Velocity False Positive
**Definition**: Form velocity detected "improvement" but it was placing form, not winning form

**Indicators**:
- Form velocity: ≥18pts
- Finish position: 2nd/3rd
- Last 3 runs all places (no wins)

**Weight V3 Response**:
- Form velocity: 18pts → 12pts (-6pts)

---

### 8. Market Position Wrong
**Definition**: We trusted market, market was wrong

**Indicators**:
- Favorite correction: ≥5pts
- Pick odds: <4.0
- Winner was underdog

**Response**:
- Monitor pattern frequency
- Consider reducing favorite_correction if >30% of losses

---

## Weight Validation Methodology

### Correlation Analysis
For each weight signal:
1. Calculate average value in **WINS**
2. Calculate average value in **LOSSES**
3. Correlation = win_avg - loss_avg

**Positive correlation** (>2.0):
- Signal appears MORE in wins than losses
- Good predictor → consider INCREASING weight

**Negative correlation** (<-2.0):
- Signal appears MORE in losses than wins
- Bad predictor → consider REDUCING weight

**Neutral correlation** (-2.0 to 2.0):
- Balanced appearance → MAINTAIN current weight

### Recommendation Logic
```python
if correlation > 2.0:
    recommendation = "INCREASE by +4pts"
elif correlation < -2.0:
    recommendation = "REDUCE by -4pts"
elif loss_avg > win_avg * 1.5:
    recommendation = "REDUCE by -2pts (overweighted in losses)"
else:
    recommendation = "MAINTAIN (appropriate balance)"
```

---

## Backtest V3 Methodology

### Simulation Approach
1. For each historical pick:
   - Get original score and breakdown
   - Apply V3 weight changes:
     * Consistency: 12→8pts (-4pts)
     * Form velocity: 18→12pts (-6pts)
     * Class drop: 24→28pts (+4pts)
   - Calculate new V3 score
   - Determine if outcome would change

2. Track improvements:
   - Losses with score reduced by ≥5pts
   - Estimate rank position change
   - Project new strike rate

### Confidence Levels
- **HIGH**: ≥10 losses potentially avoided
- **MEDIUM**: 5-9 losses potentially avoided
- **LOW**: <5 losses potentially avoided

### Projected Strike Rate
```python
original_strike_rate = wins / total_picks * 100
avoided_losses = count(score_delta < -5 for losses)
improvement = avoided_losses / total_picks * 100
projected_strike_rate = min(original_strike_rate + improvement, 60)
```

---

## Output Report Structure

### HISTORICAL_ANALYSIS_30_DAYS.md

**Section 1: Executive Summary**
- Total picks, wins, losses
- Overall strike rate
- Top 3 loss patterns
- Weight V3 validation status

**Section 2: Loss Pattern Analysis**
- Frequency of each pattern
- Examples with horse names, dates, scores
- Percentage of total losses

**Section 3: Weight Validation**
- Top 10 positive correlations (increase candidates)
- Top 5 negative correlations (reduce candidates)
- Current weight vs recommended weight
- Win avg vs loss avg for each signal

**Section 4: Weight V3 Backtest**
- Original vs projected strike rate
- Losses potentially avoided
- Confidence level
- Validation status

**Section 5: Cost of Not Adjusting**
- Financial impact (£ lost)
- Monthly ROI improvement
- Strike rate gap to target (60%)

**Section 6: Recommendations**
- Immediate actions (completed)
- Next steps (monitoring)
- Future enhancements (V4 signals)

---

## Expected Results

### Current State (Weight V2)
- Strike Rate: ~24.65% (from last7_race_deep_analysis_fresh.json)
- Primary issue: Consistent placer bias
- Missing: Phase 1 signals (pace, jockey upgrade)

### With Weight V3
- Projected Strike Rate: 28-32%
- Consistency placer bias: Reduced by ~40%
- Class advantage detection: Improved

### With Phase 1 + V3
- Projected Strike Rate: 35-40%
- Pace matching: +5-8% improvement
- Jockey upgrade: +2-4% improvement

### Target (60%)
- Remaining gap: ~20-25%
- Future signals needed: Equipment change, win conversion rate, serial placer penalty
- Timeline: 4-8 weeks with iterative improvements

---

## Execution Instructions

### Step 1: Run Primary Analysis (Preferred)
```bash
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI
python scripts/analyze_historical_month.py
```

**If DynamoDB data incomplete**, proceed to Step 2.

### Step 2: Run Alternative Analysis (JSON)
```bash
cd /c/Users/charl/OneDrive/futuregenAI/BetBudAI
python scripts/analyze_historical_from_json.py
```

### Step 3: Review Reports
1. Open `HISTORICAL_ANALYSIS_30_DAYS.md`
2. Check `historical_patterns.json` for pattern breakdown
3. Review `weight_validation_report.json` for weight recommendations
4. Validate V3 with `backtest_results.json`

### Step 4: Take Action
- ✓ Weight V3 already deployed (2026-05-20)
- ✓ Phase 1 already active (2026-05-20)
- ⏳ Monitor May 21-27 strike rate
- ⏳ Alert if 2+ more 3rd place finishes

---

## Data Sources

### DynamoDB Table: SureBetBets
**Structure**:
```python
{
    'bet_date': '2026-05-20',  # Partition key
    'bet_id': 'unique-id',     # Sort key
    'race_time': '2026-05-20T13:12:00+00:00',
    'course': 'Ayr',
    'horse_name': 'Classy Clarets',
    'score': Decimal('98.5'),
    'score_breakdown': {
        'consistency': 12,
        'form_velocity_bonus': 18,
        'class_drop_bonus': 0,
        # ... all other signals
    },
    'outcome': 'loss',  # 'win', 'placed', 'loss'
    'finish_position': 3,
    'winner_name': 'Winner Horse',
    'winner_sp': '5.50',
    'odds': 3.65,
    'profit': -6.00
}
```

### JSON Data File: last7_race_deep_analysis_fresh.json
**Structure**:
```json
{
  "summary": {
    "date_range": ["2026-05-12", "2026-05-18"],
    "races_analyzed": 284,
    "hits": 70,
    "misses": 214,
    "hit_rate_pct": 24.65
  },
  "races": [
    {
      "race_time": "2026-05-12T13:20:00+00:00",
      "course": "bath",
      "winner": "Sovereign Glory",
      "hit": false,
      "our_pick": {
        "horse": "Our Pick Name",
        "score": 95.5,
        "score_breakdown": { ... },
        "finish_position": 3
      },
      "miss_causes": [
        "winner_double_digit_odds",
        "narrow_gap_10_or_less"
      ]
    }
  ]
}
```

---

## Integration with Existing Systems

### scripts/analyze_classy_clarets_loss.py
- Single-race analysis script
- Used for today's Ayr 13:12 loss
- **Superseded by**: Historical analysis system (multi-race)

### scripts/analyze_lion_loss.py
- Single-race analysis script
- Used for today's Ffos Las 13:50 loss
- **Superseded by**: Historical analysis system (multi-race)

### scripts/deploy_emergency_v3.py
- Weight V3 deployment script
- Deploys changes to DynamoDB
- **Validated by**: Historical analysis system

### backend/config/weights.py
- Weight configuration module
- `DEFAULT_WEIGHTS` dictionary
- Used by historical analysis for comparisons

---

## Future Enhancements

### V4 Signals (Planned)
1. **Serial Placer Penalty** (-10pts)
   - Detect: Last 3 finishes all 2nd/3rd
   - Action: Penalize "consistent placer" profile

2. **Win Conversion Rate** (±12pts)
   - Calculate: wins / total_runs
   - If win_rate > 30% → +12pts
   - If place_rate > 50% and win_rate < 20% → -12pts

3. **Equipment Change Detector** (+8pts)
   - Detect: First-time blinkers
   - Detect: Tongue-tie added
   - Requires: Equipment data extraction

4. **Recent Win Recency Multiplier**
   - Win in last 7 days: 1.5x bonus
   - Win 8-14 days: 1.2x bonus
   - Win 15+ days: 1.0x (standard)

5. **Enhanced Class Drop Rebound**
   - Class drop + bounce back: 28pts → 36pts
   - Class drop + improving form: Additional +8pts

---

## Troubleshooting

### "No picks found in date range"
**Cause**: DynamoDB table empty or date range incorrect

**Solutions**:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify table exists: `aws dynamodb describe-table --table-name SureBetBets`
3. Check date range (should be April 20 - May 20, 2026)
4. Use alternative script: `python scripts/analyze_historical_from_json.py`

### "JSON file not found"
**Cause**: `last7_race_deep_analysis_fresh.json` missing

**Solutions**:
1. Check file exists in root directory
2. Regenerate file with evening pipeline
3. Use primary script with DynamoDB instead

### "boto3 not installed"
**Cause**: Missing dependencies

**Solution**:
```bash
pip install boto3 requests
```

### "Permission denied"
**Cause**: AWS credentials not configured

**Solution**:
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (eu-west-1)
```

---

## Success Metrics

### Week 1 (May 21-27, 2026)
- **Target**: 30-35% strike rate
- **Monitor**: 3rd place finish frequency
- **Alert**: If ≥2 more 3rd place finishes → emergency review
- **Validation**: V3 + Phase 1 working as expected

### Week 4 (June 11-17, 2026)
- **Target**: 40-45% strike rate
- **Validation**: Win conversion rate > place rate
- **Proof**: More 1st places than 2nd/3rd places combined

### Week 12 (Target Achievement)
- **Target**: 50-60% strike rate
- **Status**: System optimized
- **Milestone**: Production-ready for user base scaling

---

## Maintenance

### Weekly Tasks
1. Run historical analysis on new data
2. Monitor pattern frequency changes
3. Update weight recommendations
4. Check backtest projections vs actual

### Monthly Tasks
1. Full 30-day analysis
2. Validate all weight correlations
3. Generate trend reports
4. Plan V4/V5 enhancements

### Quarterly Tasks
1. Complete system audit
2. Seasonal pattern analysis
3. Long-term strike rate trends
4. Major version planning (V5+)

---

## Contact & Support

**System Owner**: BetBudAI Development Team  
**Created**: 2026-05-20  
**Version**: 1.0  
**Status**: Production Ready

For questions or issues:
1. Check troubleshooting section above
2. Review existing analysis scripts in `scripts/`
3. Check DynamoDB table structure
4. Validate AWS credentials and permissions

---

**Document Last Updated**: 2026-05-20 15:45 UTC
