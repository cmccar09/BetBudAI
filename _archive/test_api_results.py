"""
Quick test: Check if API results endpoint returns separated horse/greyhound data
"""

import requests
import json

API_URL = "https://e5na6ldp35.execute-api.eu-west-1.amazonaws.com/prod"

print("\nTesting /results endpoint...")
print("="*80)

try:
    response = requests.get(f"{API_URL}/results", timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nFull response:")
        print(json.dumps(data, indent=2))
        
        print(f"\nSuccess: {data.get('success')}")
        print(f"Date: {data.get('date')}")
        
        if 'horses' in data and data['horses'].get('summary'):
            h_sum = data['horses']['summary']
            print(f"\n🏇 HORSES:")
            print(f"  Total: {h_sum.get('total_picks')}")
            print(f"  W/L: {h_sum.get('wins')}/{h_sum.get('losses')}")
            print(f"  P/L: €{h_sum.get('profit')}")
            print(f"  ROI: {h_sum.get('roi')}%")
        
        if 'greyhounds' in data and data['greyhounds'].get('summary'):
            g_sum = data['greyhounds']['summary']
            print(f"\n🐕 GREYHOUNDS:")
            print(f"  Total: {g_sum.get('total_picks')}")
            print(f"  W/L: {g_sum.get('wins')}/{g_sum.get('losses')}")
            print(f"  P/L: €{g_sum.get('profit')}")
            print(f"  ROI: {g_sum.get('roi')}%")
        
        if 'summary' in data:
            overall = data['summary']
            print(f"\n📊 OVERALL:")
            print(f"  Total: {overall.get('total_picks')}")
            print(f"  W/L: {overall.get('wins')}/{overall.get('losses')}")
            print(f"  P/L: €{overall.get('profit')}")
            print(f"  ROI: {overall.get('roi')}%")
    else:
        print(f"Error response: {response.text}")
        
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*80 + "\n")
