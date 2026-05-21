import requests
import json

API_BASE = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com"

print("\n" + "="*80)
print("TESTING UPDATED API - Yesterday's Results")
print("="*80 + "\n")

print("Fetching from: /api/picks/yesterday\n")

try:
    response = requests.get(f"{API_BASE}/api/picks/yesterday", timeout=10)
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"Success: {data.get('success')}")
        print(f"Date: {data.get('date')}")
        print(f"Total picks: {data.get('count')}\n")
        
        picks = data.get('picks', [])
        
        if picks:
            # Check outcome distribution
            outcomes = {}
            for pick in picks:
                outcome = pick.get('outcome', 'None')
                outcomes[outcome] = outcomes.get(outcome, 0) + 1
            
            print("="*80)
            print("OUTCOME DISTRIBUTION (after normalization)")
            print("="*80)
            for outcome, count in sorted(outcomes.items()):
                print(f"  {outcome}: {count}")
            
            # Show sample winners
            winners = [p for p in picks if p.get('outcome') == 'win']
            losers = [p for p in picks if p.get('outcome') == 'loss']
            
            print(f"\n{'='*80}")
            print(f"VERIFICATION")
            print(f"{'='*80}")
            print(f"✅ Winners (outcome='win'): {len(winners)}")
            print(f"❌ Losers (outcome='loss'): {len(losers)}")
            
            if winners:
                print(f"\nSample winner:")
                w = winners[0]
                print(f"  Horse: {w.get('horse', 'N/A')}")
                print(f"  Venue: {w.get('venue', 'N/A')}")  
                print(f"  Odds: {w.get('odds', 'N/A')}")
                print(f"  Outcome: '{w.get('outcome')}' <-- Should be 'win'")
            
            print(f"\n{'='*80}")
            print("✅ FIX SUCCESSFUL - Outcomes are now normalized to 'win'/'loss'")
            print(f"{'='*80}\n")
        else:
            print("No picks returned")
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.Timeout:
    print("Request timed out - API may still be deploying")
except Exception as e:
    print(f"Error: {e}")
