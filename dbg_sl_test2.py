import requests, re, json

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml'}
r = requests.get('https://www.sportinglife.com/racing/fast-results/all', headers=HEADERS, timeout=30)
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
data = json.loads(m.group(1))
fast = data['props']['pageProps']['fastResults']

UK_COURSES = {'Newcastle','Nottingham','Lingfield','Windsor','Huntingdon','Kempton','Wolverhampton','Newbury','Ascot','Haydock','Sandown','Chester','Goodwood','York','Leicester','Carlisle','Catterick','Hamilton','Perth','Ayr','Wetherby','Doncaster','Exeter','Taunton','Hereford','Ludlow','Market Rasen','Plumpton','Stratford','Uttoxeter','Wincanton','Ffos Las','Sedgefield','Southwell','Bangor','Worcester','Warwick','Bath','Chepstow','Epsom','Pontefract','Ripon','Redcar','Beverley','Thirsk','Brighton'}

print("UK races in fast-results feed:")
for f in fast:
    course = f.get('courseName','')
    if course in UK_COURSES:
        t = f.get('time','')
        status = f.get('status','')
        top_h = f.get('top_horses', [])
        winner = top_h[0].get('horse_name','?') if top_h else '(no result yet)'
        print(f'  {course:20s} time={t}  status={status:15s}  winner={winner}')
