# Confidence Grading Standard

**Last Updated:** 2026-02-03  
**Status:** LOCKED - Production Standard

## 4-Tier Grading System

All confidence scores use this universal grading scale across the entire system:

| Grade | Range | Color | Stake Multiplier | Description |
|-------|-------|-------|------------------|-------------|
| **EXCELLENT** | 70-100 | Green (#10b981) | 2.0x | Strong conviction bets - multiple signals align |
| **GOOD** | 55-69 | Light Amber (#FFB84D) | 1.5x | Solid picks - good value with reasonable confidence |
| **FAIR** | 40-54 | Dark Amber (#FF8C00) | 1.0x | Marginal bets - proceed with caution |
| **POOR** | 0-39 | Red (#ef4444) | 0.5x | Weak signals - minimal stake or avoid |

## Scoring Logic

**Base Score:** Starts at 30 (must EARN confidence)

**Form Scoring (Most Important):**
- Weighted positions: 50% last run, 30% 2nd-last, 15% 3rd-last, 3% 4th, 2% 5th
- Position scores: 1st=+30, 2nd=+20, 3rd=+10, 4th=+5, 5th=0, 6th=-5, 7th=-10, worse=-15 to -25
- No form = -10 penalty

**Consistency Bonus:**
- All top-3 finishes in last 3 runs: +10
- All top-5 finishes in last 3 runs: +5
- Any zeros/unplaced: -8

**LTO (Last Time Out) Winner Bonus:**
- Won last time + 2nd last run in top-3: +12 (consistent performer)
- Won last time but inconsistent before: +8

**Odds Adjustment:**
- 3-7 range (value zone): +8
- 2-3 range: +5
- <2 (favorites): +3
- >15 (longshots): -8

**Trainer Bonus:**
- Elite trainers (Nicholls, Mullins, Elliott, Henderson): +3

## UI Display Thresholds

**Normal Fields (6+ runners):** 45+ minimum to show on UI  
**Small Fields (<6 runners):** 55+ minimum to show on UI

## Validation Requirements

Before ANY pick appears on UI:
- ✅ >=75% of horses in race must be analyzed
- ✅ 100% of LTO (Last Time Out) winners must be analyzed
- ✅ >=90% analyzed for small fields (<6 runners)

## Files Implementing This Standard

### Backend (Python)
- `calculate_all_confidence_scores.py` - Calculates scores for all horses
- `set_ui_picks_from_validated.py` - Generates UI picks with validation
- `save_selections_to_dynamodb.py` - Base grading logic
- `race_analysis_validator.py` - Ensures >=75% completion
- `weighted_form_analyzer.py` - Form analysis with 50/30/20 weighting

### Workflows
- `value_betting_workflow.py` - 4-step process: analyze → score → validate → generate
- `background_learning_workflow.py` - 6-step process including confidence scoring

### Frontend (JavaScript)
- `frontend/src/App.js` - UI display with 4-tier colors and labels

## Database Fields

Each horse entry includes:
- `confidence` (Decimal 0-100) - Raw confidence score
- `combined_confidence` (Decimal 0-100) - Same as confidence
- `confidence_level` (String) - HIGH (70+), MEDIUM (55+), or LOW (<55)
- `confidence_grade` (String) - EXCELLENT, GOOD, FAIR, or POOR
- `confidence_color` (String) - Hex color code for UI display
- `show_in_ui` (Boolean) - True only if validated and meets threshold

## Historical Context

**Problem:** Previous system had inflated scores with 100/100 common
- Old thresholds: EXCELLENT 60+, GOOD 40+, FAIR 25+
- Base score started at 50
- Position scores too generous (1st=+100, 2nd=+60)

**Solution:** Conservative scoring where 100/100 is RARE
- New thresholds: EXCELLENT 70+, GOOD 55+, FAIR 40+, POOR <40
- Base score starts at 30
- Position scores balanced (1st=+30, 2nd=+20)
- Must EARN high confidence through multiple signals

## Examples

**Oldschool Outlaw (Fairyhouse 14:25 Winner):**
- Form: 27-11
- Score: 48/100 → FAIR (1.0x stake)
- System correctly identified but prioritized for value

**First Confession (Carlisle 14:00 Winner):**
- Form: 1P-335F (LTO winner)
- Score: 76/100 → EXCELLENT (2.0x stake)
- Correctly identified as top pick

**Divas Doyen:**
- Form: 13-7432
- Score: 51/100 → FAIR (1.0x stake)
- Previously showed as EXCELLENT (bug) - now FIXED

## Integration Checklist

When this standard is applied to ALL future races:
- [x] Backend scoring logic updated
- [x] UI pick generation updated
- [x] Frontend display updated
- [x] Workflows configured to use calculate_all_confidence_scores.py
- [x] Database entries include all confidence fields
- [x] Validation ensures >=75% race completion
- [x] Small field threshold enforced (55+ vs 45+)

## Maintenance

**DO NOT change these thresholds without:**
1. Testing on historical race data
2. Validating against actual winners
3. Updating ALL 8 files listed above
4. Rebuilding frontend production build
5. Deploying to Amplify
6. Updating this document

**Version Control:**
All changes to this grading system must be committed to git with clear documentation of the reason for change.
