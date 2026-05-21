import requests
from datetime import datetime, timedelta

# Test different dates
dates_to_test = [
    '2025-01-07',  # Yesterday  
    '2025-01-06',  # 2 days ago
    '2024-12-20',  # A while back
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

for date in dates_to_test:
    url = f'https://www.racingpost.com/results/{date}'
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"{date}: Status {r.status_code}, Length {len(r.content)} bytes")
        if r.status_code == 200:
            print(f"  ✅ SUCCESS - Can fetch {date}")
            break
    except Exception as e:
        print(f"{date}: ERROR - {e}")
