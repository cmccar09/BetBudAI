"""
Test Sporting Life Results Scraper
===================================
Check if we can fetch today's results from Sporting Life
"""

import requests
import json
import re
from datetime import datetime

print("="*70)
print("TESTING SPORTING LIFE RESULTS SCRAPER")
print("="*70)
print()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}

# Test 1: Fast Results Page
print("[TEST 1] Fetching fast-results page...")
url = 'https://www.sportinglife.com/racing/fast-results/all'

try:
    response = requests.get(url, headers=HEADERS, timeout=30)
    print(f"  Status: {response.status_code}")
    print(f"  Content length: {len(response.text)} bytes")

    if response.status_code == 200:
        # Check for __NEXT_DATA__ tag
        if '__NEXT_DATA__' in response.text:
            print(f"  [SUCCESS] Found __NEXT_DATA__ tag")

            # Extract JSON
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', response.text, re.DOTALL)
            if match:
                json_str = match.group(1)
                print(f"  [SUCCESS] Extracted JSON ({len(json_str)} bytes)")

                try:
                    data = json.loads(json_str)
                    print(f"  [SUCCESS] Parsed JSON")

                    # Check structure
                    if 'props' in data:
                        print(f"  [SUCCESS] Found 'props' key")
                        if 'pageProps' in data['props']:
                            print(f"  [SUCCESS] Found 'pageProps' key")

                            page_props = data['props']['pageProps']

                            # Check for fastResults
                            if 'fastResults' in page_props:
                                results = page_props['fastResults']
                                print(f"  [SUCCESS] Found 'fastResults' array with {len(results)} races")

                                # Show sample race
                                if results:
                                    print(f"\n  Sample race data:")
                                    sample = results[0]
                                    print(f"    Keys: {list(sample.keys())[:10]}")
                                    if 'courseName' in sample:
                                        print(f"    Course: {sample['courseName']}")
                                    if 'time' in sample:
                                        print(f"    Time: {sample['time']}")
                                    if 'top_horses' in sample:
                                        print(f"    Top horses: {len(sample['top_horses'])} horses")
                                        if sample['top_horses']:
                                            winner = sample['top_horses'][0]
                                            print(f"      Winner: {winner.get('horse_name', 'N/A')}")
                                else:
                                    print(f"  [INFO] No races in fastResults yet (may be too early)")
                            else:
                                print(f"  [ERROR] No 'fastResults' key in pageProps")
                                print(f"  Available keys: {list(page_props.keys())}")
                        else:
                            print(f"  [ERROR] No 'pageProps' in props")
                            print(f"  Available keys: {list(data['props'].keys())}")
                    else:
                        print(f"  [ERROR] No 'props' key in JSON")
                        print(f"  Available keys: {list(data.keys())}")

                except json.JSONDecodeError as e:
                    print(f"  [ERROR] Failed to parse JSON: {e}")
            else:
                print(f"  [ERROR] Could not extract JSON from __NEXT_DATA__ tag")
        else:
            print(f"  [ERROR] __NEXT_DATA__ tag not found in page")
            print(f"  Page may have changed structure or requires JavaScript")

            # Check for Cloudflare
            if 'cf-browser-verification' in response.text or 'Cloudflare' in response.text:
                print(f"  [WARNING] Cloudflare protection detected")
    else:
        print(f"  [ERROR] HTTP {response.status_code}")

except requests.Timeout:
    print(f"  [ERROR] Request timed out after 30 seconds")
except Exception as e:
    print(f"  [ERROR] Request failed: {e}")

# Test 2: Results Index Page
print(f"\n[TEST 2] Checking results index page...")
today = datetime.now().strftime('%Y-%m-%d')
index_url = f'https://www.sportinglife.com/racing/results/{today}/'

try:
    response = requests.get(index_url, headers=HEADERS, timeout=30)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        # Look for race links
        race_links = re.findall(r'href="(/racing/results/' + re.escape(today) + r'/[^"]+)"', response.text)
        print(f"  [INFO] Found {len(race_links)} race result links")

        if race_links:
            print(f"  Sample link: {race_links[0]}")
    else:
        print(f"  [ERROR] HTTP {response.status_code}")

except Exception as e:
    print(f"  [ERROR] Request failed: {e}")

print()
print("="*70)
print("TEST COMPLETE")
print("="*70)
print()
print("Summary:")
print("  - If __NEXT_DATA__ found: Scraper structure OK")
print("  - If fastResults empty: Too early (races not finished yet)")
print("  - If __NEXT_DATA__ missing: Sporting Life changed structure")
print("  - If Cloudflare detected: Need to add anti-bot measures")
