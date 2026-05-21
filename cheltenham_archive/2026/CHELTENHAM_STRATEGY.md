# Cheltenham Festival Strategy 2026

##CONTINUOUS MONITORING SYSTEM ✅ ACTIVE

### Daily Cheltenham Analysis (NEW - Feb 23, 2026)
**Automated continuous tracking of ALL potential Festival horses**

**System**: `continuous_cheltenham_monitoring.py`
- Runs daily after `daily_automated_workflow.py`
- Analyzes ALL horses in Grade 1/2/3 races
- Tracks elite trainer/jockey combinations  
- Applies Cheltenham-specific bonuses
- Uses validated **75+ threshold** (45.4% ROI)

**Query Commands**:
```bash
# View all Festival candidates (75+)
python query_cheltenham_research.py

# Track specific horse progression
python query_cheltenham_research.py --horse "Horse Name"

# View trainer's horses  
python query_cheltenham_research.py --trainer "Mullins"

# Top scorers
python query_cheltenham_research.py --top 20
```

**Storage**: CheltenhamResearch DynamoDB table
- Tracks form progression over time
- Identifies horses peaking for Festival
- Flags 75+ scores for betting consideration

## Why Our Validated Logic THRIVES at Cheltenham

### Perfect Match for Our Strengths ✅

1. **Elite Connections Dominate**
   - Willie Mullins, Gordon Elliott, Nicky Henderson, Paul Nicholls
   - Our +40pts elite trainer/jockey bonus is IDEAL for Festival
   - Yesterday validated: Mullins/Townend 79pts → WON

2. **Grade 1/2 Championship Races**
   - NO novice penalties apply (these are championship races)
   - Our grade vs novice distinction = huge advantage
   - 28 races, mostly Grade 1/2 quality

3. **Form Horses with History**
   - Recent win bonus (+25pts) applies to festival specialists
   - Consistency scoring works with established horses
   - Our 50% strike rate on quality picks should excel here

4. **Heavy Going Expected**
   - March in Gloucestershire = soft/heavy typical
   - Our weather-based going analysis fully applies
   - Going specialists get proper weighting

## Dual Approach: Opinion on ALL, Bet on BEST

### Tier 1: BETTING PICKS (High Confidence 75+)
**Criteria for actual bets:**
- Score ≥ 75 points (EXCELLENT tier)
- Elite connections (Mullins/Elliott/Henderson/Nicholls)
- Recent Grade 1/2 form
- Course/Festival form bonus
- Odds 2.0-8.0 (sweet spot)

**Expected**: 8-12 betting picks across 4 days (2-3 per day)

### Tier 2: STRONG INTEREST (60-74 points)
**Watch list / smaller stakes:**
- Score 60-74 (GOOD tier)
- Good connections but not elite
- Solid recent form
- Monitor for odds movement

**Expected**: 15-20 picks total

### Tier 3: LEARNING DATA (All other races)
**Full analysis but no bet:**
- Score < 60
- Analyze for learning/patterns
- Track actual winners vs predictions
- Build Cheltenham-specific insights

**Expected**: 60+ analyzed horses

## Cheltenham-Specific Scoring Enhancements

### Additional Bonuses (Add to validated weights)

```python
CHELTENHAM_BONUSES = {
    'festival_winner_history': 15,     # Previous Cheltenham winner
    'festival_placed_history': 8,       # Previous Cheltenham place
    'course_winner': 10,                # Won at Cheltenham before
    'graded_winner_this_season': 12,   # Grade 1/2 win this season
    'irish_raider_elite': 8,           # Mullins/Elliott at Festival
    'champion_jockey': 5,               # Walsh/Townend/Blackmore
}
```

### Race Type Weighting
- **Grade 1 Championship**: Base +10pts (Supreme, Champion Hurdle, Gold Cup, etc.)
- **Grade 1 Novice**: +5pts (still quality, but less predictable)
- **Grade 2/3**: Standard weights
- **Handicaps**: -5pts (more unpredictable)

## 4-Day Plan

### Day 1 (Tuesday) - Supreme & Arkle Focus
- **Supreme Novices' Hurdle** (Grade 1) - Festival opener, quality field
- **Arkle Chase** (Grade 1) - 2-mile championship
- **Ultima Handicap Chase** - Skip or small stake (handicap)
- **Champion Hurdle** (Grade 1) - PRIORITY BET if elite horse scores 75+
- **Mares' Hurdle** (Grade 1) - Willie Mullins dominates historically
- **Boodles Fred Winter** - Analyze but likely skip (handicap)
- **National Hunt Chase** - Amateur riders, lower confidence

**Expected Bets**: 2-3 picks (Champion Hurdle, Arkle, possibly Mares')

### Day 2 (Wednesday) - Queen Mother & Ballymore
- **Ballymore Novices' Hurdle** (Grade 1)
- **Brown Advisory Novices' Chase** (Grade 1)
- **Coral Cup** - Skip (handicap)
- **Queen Mother Champion Chase** (Grade 1) - PRIORITY BET, 2-mile championship
- **Glenfarclas Cross Country Chase** - Skip (specialist race)
- **Grand Annual** - Skip (handicap)
- **Champion Bumper** (Grade 1) - Mullins/Elliott dominate

**Expected Bets**: 2-3 picks (Queen Mother, Ballymore, Champion Bumper)

### Day 3 (Thursday) - Gold Cup Day
- **Turners Novices' Chase** (Grade 1)
- **Pertemps Final** - Skip (handicap)
- **Ryanair Chase** (Grade 1)
- **Cheltenham Gold Cup** (Grade 1) - THE RACE, PRIORITY BET if 75+
- **Mares' Novices' Hurdle** (Grade 2)
- **Kim Muir** - Skip (amateur riders)
- **Festival Trophy** - Skip (handicap)

**Expected Bets**: 2-4 picks (Gold Cup mandatory if quality pick, Ryanair, Turners)

### Day 4 (Friday) - Stayers' Hurdle
- **Triumph Hurdle** (Grade 1) - Juvenile championship
- **County Hurdle** - Skip (handicap)
- **Albert Bartlett** (Grade 1) - Staying novices
- **Stayers' Hurdle** (Grade 1) - PRIORITY BET, staying championship
- **Mares' Chase** (Grade 2)
- **Festival Plate** - Skip (handicap)
- **Martin Pipe** - Skip (handicap)

**Expected Bets**: 2-3 picks (Stayers' Hurdle, Triumph, Albert Bartlett)

## Betting Strategy

### Bankroll Management
- **Total Festival Budget**: Set fixed amount (e.g., £500)
- **Per Pick**: £5-£10 on 75+ confidence
- **Per Pick**: £2-£5 on 60-74 confidence
- **Max Daily Bets**: 3-4 actual bets per day
- **Reserve**: 20% for Day 4 if running well

### Staking Tiers
- **90+ points**: £10 (max confidence)
- **80-89 points**: £7.50
- **75-79 points**: £5
- **60-74 points**: £2-£3 (watch list only)

### When to Increase Stakes
- ✅ Running profit on Days 1-2
- ✅ Gold Cup day with 85+ pick
- ✅ Multiple factors align (elite connections + festival history + recent Grade 1 win)

### When to SKIP
- ❌ Handicaps (too unpredictable even with good analysis)
- ❌ Amateur rider races (form less reliable)
- ❌ Cross country/specialist races
- ❌ Any pick scoring < 60 regardless of odds
- ❌ Odds < 1.8 (not worth the risk even on favorites)

## Implementation Plan

### Before Festival (1 week out)
1. Create `cheltenham_comprehensive_analysis.py`
2. Add Cheltenham-specific bonuses to scoring
3. Scrape all 28 race cards
4. Run preliminary analysis
5. Identify top 10-15 betting targets

### Each Morning (Race Day)
1. Run fresh analysis with latest odds
2. Check for non-runners/ground changes
3. Generate "Opinion on ALL" report (28 races analyzed)
4. Flag "BET THESE" picks (75+ only)
5. Email/dashboard with recommendations

### Post-Race (Each Day)
1. Record all results immediately
2. Update learning database
3. Analyze what worked/didn't work
4. Adjust Day 2/3/4 if patterns emerge

## Expected Performance

### Conservative Estimate
- **Total Bets**: 10-12 across 4 days
- **Target Strike Rate**: 40% (4-5 winners)
- **Average Odds**: 4.0
- **Total Stake**: £60-£80
- **Target Profit**: £30-£50 (40-60% ROI)

### Optimistic (If Elite Connections Dominate)
- **Total Bets**: 12-15
- **Strike Rate**: 50% (6-8 winners)
- **Average Odds**: 4.5
- **Total Stake**: £80-£100
- **Target Profit**: £80-£120 (80-120% ROI)

## Key Success Factors

1. **Discipline**: Only bet 75+ scores, ignore temptation
2. **Elite Bias**: Mullins/Elliott/Henderson get full weight
3. **Grade Focus**: Prioritize Grade 1 championships over novices
4. **Form Recency**: Recent Grade 1/2 wins heavily weighted
5. **Going**: Soft/Heavy specialists get bonus
6. **Festival History**: Previous Cheltenham success = major factor

## Risk Management

### Red Flags to Avoid
- First-time Festival runners (no course form)
- Horses stepping up significantly in class
- Trainers with poor Festival record
- Ground concerns (Good/Firm specialists on Heavy)
- Odds drifting significantly pre-race

### When to Hedge
- If 90+ pick wins Day 1, consider laying small on Day 2
- If losing 3+ bets in a row, reduce stakes
- If ahead by Day 3, secure profit by reducing Day 4 stakes

---

## Summary

✅ **Analyze ALL 28 races** - Full comprehensive scoring for every horse  
✅ **Bet ONLY 75+ confidence** - Elite connections + championship races  
✅ **10-15 total bets** across 4 days (2-4 per day)  
✅ **Skip handicaps** - Not worth the risk even with analysis  
✅ **Target 40-50% strike rate** - Our validated system should excel here  
✅ **Document everything** - Festival = perfect learning opportunity  

**The validated Feb 14 logic (elite connections, grade distinction, recent form) is BUILT for Cheltenham. This is where it should shine brightest.**
