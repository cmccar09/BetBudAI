"""
CURRENT SYSTEM CONFIGURATION - February 3, 2026
=================================================

REALISTIC WIN PROBABILITY GRADING:
- EXCELLENT (85+): Mortgage bet - 40-50% win chance - 2.0x stake
- GOOD (70-84): Solid pick - 25-35% win chance - 1.5x stake
- FAIR (55-69): Risky - 15-25% win chance - 1.0x stake
- POOR (<55): Avoid - <15% win chance - 0.5x stake

UI PICK STRATEGY:
- TOP 10 horses across ALL races globally (not 1 per race)
- Minimum threshold: 55/100 (FAIR)
- Remaining horses kept for training/learning

COVERAGE ENFORCEMENT:
- Minimum: 90% of horses analyzed
- Target: 100% coverage
- Races below 90% are REJECTED from UI

SCORING COMPONENTS:
- Base score: 30 (must earn confidence)
- Form analysis: Weighted positions (LTO 50%, 2nd 30%, 3rd 15%)
- Sweet spot odds: 3-9 = +8 points
- Long-shot penalty: 10-15 odds = -5, >15 = -10
- Win bonuses: LTO +6-8, 2nd last +5, 3rd last +3
- Consistency: All top-3 in last 3 = +6
- Improvement pattern: 3+ improvements = +8
- Form surge: Recent better than older = +5

DAILY WORKFLOW (9:00 AM):
1. Fetch yesterday's results
2. Store all races for learning
3. Auto-adjust weights
4. Learn from winners
5. Fetch today's races
6. Analyze all horses
7. Calculate confidence scores
8. Set TOP 10 UI picks
9. Clear old data

LEARNING MECHANISMS:
- auto_adjust_weights.py: Updates scoring weights based on results
- complete_race_learning.py: Learns from all race winners
- Runs automatically in daily workflow

RESULTS TRACKING:
- Harbour Vision WON @ 8.6 (+€150)
- No Return LOST @ 14.5 (-€30)
- Net: +€120

CURRENT TOP PICKS:
1. Getaway With You: 81/100 GOOD
2. Huit Reflets: 78/100 GOOD
3. Fiddlers Green: 75/100 GOOD
4. Barton Snow: 74/100 GOOD
5. Haarar: 74/100 GOOD
6. Grey Horizon: 72/100 GOOD
7. Rodney: 70/100 GOOD
8. Medieval Gold: 70/100 GOOD
9. Yorkshire Glory: 69/100 FAIR
10. Toothless: 69/100 FAIR

EXCELLENT PICKS: 0 (correct - should be very rare!)
GOOD PICKS: 8 (25-35% win chance)
FAIR PICKS: 2 (15-25% win chance)
"""
