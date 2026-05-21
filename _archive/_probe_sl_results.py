"""Try SL results pages for historical dates to get horse IDs."""
import requests, re, json, time

SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Referer': 'https://www.sportinglife.com/',
    'Upgrade-Insecure-Requests': '1',
}
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)

def get_html(url):
    r = requests.get(url, headers=SL_HEADERS, timeout=15)
    print(f"  {url} -> {r.status_code}")
    return r.text if r.status_code == 200 else None

# Try different SL results URL patterns
test_date = '2026-03-29'
urls_to_try = [
    f'https://www.sportinglife.com/racing/results/{test_date}',
    f'https://www.sportinglife.com/racing/results/date/{test_date}',
    f'https://www.sportinglife.com/racing/{test_date}/results',
    f'https://www.sportinglife.com/racing/results',
]

for url in urls_to_try:
    html = get_html(url)
    if html:
        # Look for race result URLs
        result_urls = re.findall(r'/racing/results/(\d{4}-\d{2}-\d{2})/([^"/\s]+)/race/(\d+)/[^"?\s]+', html)
        print(f"  Result URLs found: {len(result_urls)}")
        if result_urls:
            print(f"  Sample: {result_urls[:3]}")
        
        # Look for horse IDs in HTML
        horse_ids = re.findall(r'/racing/profiles/horse/(\d+)', html)
        print(f"  Horse profile links found: {len(horse_ids)}")
        
        # Check NEXT_DATA
        m = NEXT_DATA_RE.search(html)
        if m:
            try:
                nd = json.loads(m.group(1))
                props = nd.get('props', {}).get('pageProps', {})
                print(f"  NEXT_DATA pageProps keys: {list(props.keys())[:10]}")
            except:
                pass
    print()
    time.sleep(0.5)
