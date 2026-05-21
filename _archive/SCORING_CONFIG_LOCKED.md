# Betting System Scoring Configuration - LOCKED IN
**Date Locked:** February 3, 2026  
**Last Commit:** 3aa39d9

## Scoring System
**Conservative Scoring - Maximum Score: ~50 points**

### Point Distribution
- **Sweet Spot Base** (3-9 odds): 15 points
- **Recent Win** (in last 2 races): 12 points
- **Has Won Before**: 6 points  
- **2+ Place Finishes**: 8 points
- **1 Place Finish**: 4 points
- **Consistency** (5+ runs, no 0s/Ps): 5 points
- **Optimal Odds Range** (4.0-6.0): 10 points
- **Good Odds Range** (3.0-7.0): 5 points

**Maximum Possible Score:** 50 points (15+12+8+5+10)

### UI Threshold
- **Minimum score to show on UI:** 40 points

## Display Thresholds

| Score Range | Rating | Multiplier | Color | Description |
|------------|--------|------------|-------|-------------|
| 50+ | EXCELLENT | 2.0x | Green | Very Good |
| 40-49 | GOOD | 1.3x | Light Amber | Good |
| 30-39 | FAIR | 1.0x | Dark Amber | Fair |
| 20-29 | POOR | 0.5x | Red | Bad |
| <20 | POOR | 0.5x | Red | Very Bad |

## ROI Multipliers
- **150%+ ROI:** 1.5x stake multiplier
- **100-149% ROI:** 1.25x stake multiplier
- **50-99% ROI:** 1.0x stake multiplier
- **<50% ROI:** 0.75x stake multiplier

## Budget Configuration
- **Daily Budget:** €100
- **Max Picks Per Day:** 10
- **Base Stake Per Pick:** €10

**Final stake = Base × Confidence Multiplier × ROI Multiplier**

## Workflow Schedule
- **Trading Hours:** 11:00 AM - 7:00 PM
- **Update Frequency:** Every 30 minutes
- **Dual Workflows:**
  1. **Background Learning** (show_in_ui=False) - Analyzes all races for learning
  2. **Value Betting** (show_in_ui=True) - Generates UI picks with score ≥40

## Key Files
- `generate_ui_picks.py` - Scoring logic and pick generation
- `frontend/src/App.js` - UI display thresholds (lines 817-842)
- `value_betting_workflow.py` - 30-min cycle value betting
- `background_learning_workflow.py` - 30-min cycle learning

## Philosophy
These scores are **relative quality rankings**, NOT win probabilities. A 50/100 score means "very good value bet candidate for 4-6 odds range", not "50% chance to win".

Conservative scoring ensures honest assessment - even the best picks max out at 50/100, preventing false confidence in what are fundamentally value bets, not certainties.
