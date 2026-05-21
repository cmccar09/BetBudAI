"""
Betfair Sports Analysis - Easiest to Integrate
Based on API structure similarity to existing horse racing system
"""

# Current System Uses:
# - Horse Racing (Event Type ID: 7)
# - Market structure: venue, race time, runners with odds
# - Results: WIN/PLACED/LOST status per runner

EASIEST_TO_INTEGRATE = {
    
    "1. GREYHOUND RACING": {
        "event_type_id": "4339",
        "market_count": 594,
        "difficulty": "VERY EASY",
        "similarity_to_horses": "95%",
        "reasons": [
            "Identical API structure (venue, race time, runners)",
            "Same market types (Win, Place, Forecast)",
            "Same result structure (WINNER/LOSER/PLACED)",
            "Can reuse ALL existing code with minimal changes",
            "Similar race dynamics (form, track conditions)",
            "Results available immediately after race"
        ],
        "code_changes": [
            "Add event_type_id filter option: '4339' or '7'",
            "Prompt.txt: Add greyhound-specific factors (trap, distance)",
            "UI: Change 'horse' to 'runner' or 'selection'",
            "Estimated effort: 2-4 hours"
        ],
        "data_available": [
            "Live odds for 594 markets",
            "Recent form (via Betfair)",
            "Track/distance data",
            "Trap positions",
            "Immediate race results"
        ]
    },
    
    "2. TENNIS": {
        "event_type_id": "2",
        "market_count": 3952,
        "difficulty": "EASY",
        "similarity_to_horses": "70%",
        "reasons": [
            "Simple structure: only 2 players (vs 8-20 horses)",
            "Match Odds market similar to Win market",
            "Clear WIN/LOSS outcomes (no places)",
            "Huge liquidity (3952 markets available)",
            "Results settle quickly",
            "Head-to-head format easier to analyze"
        ],
        "code_changes": [
            "Simpler runner structure (2 players not 8-20)",
            "No EW betting (just match winner)",
            "Prompt.txt: Tennis-specific factors (surface, H2H, ranking)",
            "Results: binary WIN/LOSS only",
            "Estimated effort: 4-8 hours"
        ],
        "data_available": [
            "Live odds for 3952 markets",
            "Player names and rankings",
            "Tournament/surface info",
            "Quick result settlement"
        ],
        "challenges": [
            "Need different analysis factors (not form/going)",
            "Would need external data for player stats/rankings",
            "Market moves differently (2-way vs multi-way)"
        ]
    },
    
    "3. SOCCER": {
        "event_type_id": "1",
        "market_count": 10848,
        "difficulty": "MEDIUM",
        "similarity_to_horses": "60%",
        "reasons": [
            "MASSIVE market count (10,848 - most liquidity)",
            "Match Odds: 3-way (Home/Draw/Away)",
            "Clear match outcomes",
            "Multiple markets per game (goals, corners, cards)",
            "Results available quickly"
        ],
        "code_changes": [
            "3-way market instead of multi-runner",
            "Prompt.txt: Soccer-specific (league, form table, H2H)",
            "Multiple market types to choose from",
            "Results: HOME_WIN/DRAW/AWAY_WIN",
            "Estimated effort: 6-12 hours"
        ],
        "data_available": [
            "Live odds for 10,848 markets",
            "Team names, competitions",
            "Match times",
            "Result data available"
        ],
        "challenges": [
            "Need league tables, team form data",
            "3-way market different from current system",
            "Draws complicate profitability",
            "Would benefit from external stats APIs"
        ]
    }
}

RECOMMENDATIONS = """
RECOMMENDED INTEGRATION ORDER:

1. GREYHOUND RACING (IMMEDIATE - 2-4 hours)
   ✓ Use EXACT same code as horse racing
   ✓ Just add event_type_id: '4339' filter
   ✓ 594 markets available right now
   ✓ Similar betting dynamics
   ✓ NO external data needed
   ✓ Can run alongside horses immediately
   
   QUICK WIN: Could be live TODAY with these changes:
   - generate_todays_picks.ps1: Add --sport greyhounds option
   - betfair_delayed_snapshots.py: Accept event_type_id parameter
   - prompt.txt: Section for greyhound factors (copy from horses, adjust)
   - UI: Show sport icon 🐕 vs 🐴

2. TENNIS (NEXT - 4-8 hours)
   ✓ Simpler than horses (2 players not 20)
   ✓ HUGE liquidity (3,952 markets)
   ✓ Clear binary outcomes
   ✓ Different analysis but Betfair data sufficient
   ✓ Good for diversification
   
   Benefits:
   - Less complex than horse racing
   - More frequent events
   - International coverage 24/7
   - Quick turnaround on results

3. SOCCER (LATER - 6-12 hours)
   ✓ Biggest market (10,848 available)
   ✓ Most mainstream appeal
   ✓ Would need external stats (league tables, H2H)
   ✓ More complex analysis
   
   Would benefit from:
   - Football-Data.org API (free tier)
   - League table data
   - Team form analysis

LOWEST HANGING FRUIT:
→ Greyhounds can be added THIS AFTERNOON
→ Code is 95% reusable
→ Just change event type filter
→ Doubles your market coverage instantly
"""

print(RECOMMENDATIONS)

for sport, details in EASIEST_TO_INTEGRATE.items():
    print(f"\n{'='*70}")
    print(f"{sport}")
    print(f"{'='*70}")
    print(f"Event Type ID: {details['event_type_id']}")
    print(f"Markets Available: {details['market_count']:,}")
    print(f"Difficulty: {details['difficulty']}")
    print(f"Similarity: {details['similarity_to_horses']}")
    print(f"\nReasons:")
    for reason in details['reasons']:
        print(f"  ✓ {reason}")
    print(f"\nCode Changes:")
    for change in details['code_changes']:
        print(f"  • {change}")
