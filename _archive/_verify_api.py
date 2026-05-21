import urllib.request, json
url = "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today"
with urllib.request.urlopen(url) as r:
    d = json.loads(r.read())
picks = d.get('picks', [])
print(f'Live API picks: {len(picks)}')
for p in picks:
    horse = p.get('horse','?')
    course = p.get('course','?')
    rt = p.get('race_time','?')
    odds = p.get('odds','?')
    score = p.get('comprehensive_score','?')
    gap = p.get('score_gap','?')
    all_h = len(p.get('all_horses', []))
    print(f"  {rt[11:16] if len(rt)>11 else rt} {course} | {horse} @ {odds} | score={score} gap=+{gap} | allHorses={all_h}")
