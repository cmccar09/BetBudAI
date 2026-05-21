# Track-Specific Daily Learning

## Overview
The system now learns from each race result to improve predictions for **subsequent races at the same track on the same day**.

## How It Works

### 1. **After Each Race Result**
When a winner is identified, the system analyzes:
- Which scoring factors contributed most (recent_win, course_bonus, sweet_spot, etc.)
- What percentage of the winner's score came from each factor
- Identifies the dominant winning pattern

### 2. **Pattern Recognition**
Patterns identified include:
- **RECENT_FORM**: Horses with recent wins dominating
- **COURSE_SPECIALIST**: Course experience is key
- **DISTANCE_SUITED**: Distance-suited horses winning
- **PROVEN_WINNER**: Track record matters most
- **GOING_SPECIALIST**: Going conditions favoring specialists
- **VALUE_BET**: Longer odds finding success
- **BALANCED**: No clear pattern

### 3. **Same-Day Application**
For the **next race at that track**:
- System loads insights from earlier races
- If a dominant pattern emerges (60%+ of races), applies +10pt bonus
- If moderate pattern (40-60%), applies +5pt bonus
- Bonuses only apply to horses that already scored in that factor

### 4. **Example Flow**

**Kempton - Race 1 (12:50)**
- Winner: "Fast Freddie" - Score breakdown shows 35% from recent_win
- System records: "Recent form factor strong at Kempton"

**Kempton - Race 2 (13:20)**  
- Winner: "Quick Liz" - Score breakdown shows 40% from recent_win
- System identifies: "RECENT_FORM dominant at Kempton today (60% pattern strength)"

**Kempton - Race 3 (15:10)** ← Im Workin On It
- Analysis runs, horse has recent win
- Base recent_win score: +25pts
- **Track pattern bonus: +10pts** (matches RECENT_FORM pattern)
- New score: 57 → **67/100** (boosted by track learning)

## Files

### Core Logic
- **track_daily_insights.py**: Main learning engine
  - `analyze_winner_factors()`: Analyzes why winner won
  - `add_race_insight()`: Stores insight after each race
  - `get_track_insights()`: Retrieves insights for upcoming race
  - `print_track_insights()`: Shows patterns in readable format

### Integration Points
- **comprehensive_pick_logic.py**: 
  - Loads track insights before scoring
  - Applies track_pattern_bonus (+10pts max)
  - Factors in dominant patterns automatically

- **coordinated_learning_workflow.py**:
  - `capture_track_insights()`: Runs in Step 3 after matching results
  - Captures insights from all WON outcomes
  - Groups by track and displays patterns

### Utilities
- **show_track_insights.py**: View current insights
  - Shows patterns at each track
  - Displays recent winners
  - Summary of overall patterns today

### Data Storage
- **track_insights_today.json**: Daily insights file
  - Resets automatically each day
  - Stores per-track patterns and race history
  - Includes pattern strength percentages

## Viewing Insights

```powershell
# View all track insights
python show_track_insights.py

# View insights in learning workflow output
python coordinated_learning_workflow.py
```

## Example Output

```
============================================================
TRACK INSIGHTS: Kempton
============================================================
Races analyzed today: 3

Dominant pattern: RECENT_FORM (67% of races)
→ Horses with recent wins are dominating

Recommended score adjustments for next race:
  • recent_win: +10 points

Recent winners: Fast Freddie, Quick Liz, Im Workin On It
============================================================
```

## Benefits

1. **Intra-Day Adaptation**: System learns what's working TODAY, not just historical patterns
2. **Track-Specific**: Kempton patterns don't affect Ludlow predictions
3. **Evidence-Based**: Only applies bonuses when pattern strength is 40%+
4. **Conservative**: Max +10pt bonus prevents over-weighting
5. **Automatic**: No manual intervention needed - runs in learning workflow

## Integration with Existing System

This works **alongside** existing factors:
- Sweet spot scoring (30pts)
- Optimal odds (20pts)
- Recent win (25pts)
- Going suitability (8pts)
- Database history (15pts)
- Course bonus (10pts)
- **Track pattern bonus (NEW - 10pts)**

Total possible score: ~130pts before -35 adjustment

## Reset Behavior

- Insights reset daily (new date = fresh start)
- First race at each track has no insights (no data yet)
- Pattern strength builds as more races complete
- Stronger patterns (60%+) get higher bonuses than weak patterns (40-60%)

## Monitoring

Track insights are displayed:
1. After Step 3 in `coordinated_learning_workflow.py`
2. Via `show_track_insights.py` anytime
3. In scoring breakdown (track_pattern_bonus field)

## Future Enhancements

Potential improvements:
- Multi-day pattern persistence (weekly trends)
- Jockey/trainer pattern tracking per track
- Distance-specific patterns (sprints vs. staying races)
- Weather interaction patterns (track+going combinations)
