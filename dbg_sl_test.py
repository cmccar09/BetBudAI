import requests, re, json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
}

r = requests.get('https://www.sportinglife.com/racing/fast-results/all', headers=HEADERS, timeout=30)
print(f'Status: {r.status_code}, Size: {len(r.text)} chars')

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if m:
    print(f'__NEXT_DATA__ found, length: {len(m.group(1))}')
    data = json.loads(m.group(1))
    fast = data.get('props', {}).get('pageProps', {}).get('fastResults', None)
    if fast is None:
        pp = data.get('props', {}).get('pageProps', {})
        print(f'pageProps keys: {list(pp.keys())[:20]}')
        # Check if data is nested differently
        props = data.get('props', {})
        print(f'props keys: {list(props.keys())}')
    else:
        print(f'fastResults found: {len(fast)} entries')
        if fast:
            print(f'First entry keys: {list(fast[0].keys())}')
            print(f'First entry sample: {json.dumps(fast[0], indent=2)[:600]}')
else:
    print('__NEXT_DATA__ NOT FOUND in response')
    # Look for any script tags
    scripts = re.findall(r'<script[^>]*id="([^"]*)"', r.text)
    print(f'Script ids found: {scripts[:10]}')
    print(f'First 1000 chars: {r.text[:1000]}')
