"""
Test the updated betfair_odds_fetcher with interactive login
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from betfair_odds_fetcher import get_live_betfair_races
import json

print("=" * 60)
print("Testing Betfair Odds Fetcher with Interactive Login")
print("=" * 60)

try:
    print("\nFetching live horse racing odds...")
    races = get_live_betfair_races()
    
    print(f"\n✓ SUCCESS! Found {len(races)} races with odds")
    
    if races:
        print("\nFirst 3 races:")
        for i, race in enumerate(races[:3], 1):
            print(f"\n  Race {i}:")
            print(f"    Course: {race['course']}")
            print(f"    Time: {race['race_time']}")
            print(f"    Runners: {len(race['runners'])}")
            
            if race['runners']:
                print(f"    Sample odds:")
                for runner in race['runners'][:3]:
                    print(f"      {runner['name']}: {runner['odds']}")
        
        # Save to file
        with open('live_races_test.json', 'w') as f:
            json.dump(races[:5], f, indent=2, default=str)
        
        print(f"\n✓ First 5 races saved to: live_races_test.json")
    else:
        print("\n⚠ No races found in betting window (15 mins - 24 hours)")
        print("  This is normal if there are no upcoming races")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
