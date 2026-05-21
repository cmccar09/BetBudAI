import requests, sys, re, boto3
from decimal import Decimal
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Try Sporting Life results page
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

urls_to_try = [
    'https://www.sportinglife.com/racing/results/2026-03-20/musselburgh',
    'https://www.racingpost.com/racecards/musselburgh/2026-03-20/results',
]

for url in urls_to_try:
    try:
        print(f"\nTrying: {url}")
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            text = r.text
            # Look for Light Fandango or 15:22
            if 'Light Fandango' in text or '15:22' in text or '3:22' in text:
                print("  Found relevant text!")
                # Extract context around Light Fandango
                idx = text.find('Light Fandango')
                if idx >= 0:
                    print(f"  Context: ...{text[max(0,idx-200):idx+300]}...")
            else:
                # Look for Musselburgh 15:22 results another way
                print(f"  Text length: {len(text)}, contains 'Musselburgh': {'Musselburgh' in text}")
        elif r.status_code in [403, 429]:
            print(f"  Blocked")
    except Exception as e:
        print(f"  Error: {e}")
