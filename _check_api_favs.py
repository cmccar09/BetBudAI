import requests, json

r = requests.get('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/favs-run?date=2026-04-14')
d = r.json()
races = d.get('races', [])
wins = sum(1 for r in races if r.get('outcome') == 'win')
losses = sum(1 for r in races if r.get('outcome') == 'loss')
pending = sum(1 for r in races if not r.get('outcome'))
print(f"Races: {len(races)} | Fav Won: {wins} | Fav Lost (lay win): {losses} | Pending: {pending}")
summary = d.get('summary', {})
print(f"Summary: settled={summary.get('settled')} fav_lost={summary.get('fav_lost')} lay_win_pct={summary.get('lay_win_pct')}%")
print()
for race in sorted(races, key=lambda x: x.get('race_time', '')):
    oc = race.get('outcome') or 'PENDING'
    rt = (race.get('race_time') or '???')[11:16]
    course = race.get('course') or '?'
    fav = race.get('favourite') or '?'
    score = race.get('lay_score') or 0
    verdict = race.get('verdict') or '?'
    symbol = 'X FAV WON' if oc == 'win' else 'V FAV LOST' if oc == 'loss' else '? PENDING'
    print(f"  {rt} {course:15s} {fav:25s} {oc:7s} score={score:2d} {verdict:20s} {symbol}")
