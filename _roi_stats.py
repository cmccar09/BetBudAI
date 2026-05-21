import boto3
from boto3.dynamodb.conditions import Key
from datetime import date, timedelta, datetime
import re

db  = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

start = date(2026, 3, 22)
end   = date(2026, 3, 29)

all_picks = []
d = start
while d <= end:
    resp  = tbl.query(KeyConditionExpression=Key('bet_date').eq(str(d)))
    items = [i for i in resp['Items'] if i.get('show_in_ui')]
    seen = {}
    for p in items:
        k  = (p.get('horse',''), str(p.get('race_time','')))
        sc = float(p.get('comprehensive_score', p.get('score', 0)))
        if k not in seen or sc > float(seen[k].get('comprehensive_score', seen[k].get('score', 0))):
            seen[k] = p
    all_picks.extend(seen.values())
    d += timedelta(days=1)

def oc(p):
    return (p.get('result_emoji') or p.get('outcome','')).upper()

wins    = [p for p in all_picks if oc(p) in ('WIN','WON')]
losses  = [p for p in all_picks if oc(p) in ('LOSS','LOST')]
placed  = [p for p in all_picks if oc(p) == 'PLACED']
pending = [p for p in all_picks if oc(p) not in ('WIN','WON','LOSS','LOST','PLACED')]
settled = wins + losses + placed

total_stake  = len(settled) * 10
total_profit = sum(float(p.get('profit', 0)) for p in settled)
roi          = (total_profit / total_stake * 100) if total_stake else 0

print(f"Total UI picks: {len(all_picks)}")
print(f"Settled: {len(settled)}  Wins: {len(wins)}  Placed: {len(placed)}  Losses: {len(losses)}  Pending: {len(pending)}")
print(f"Win strike rate: {round(len(wins)/len(settled)*100,1) if settled else 0}%")
print(f"Win+Place rate:  {round((len(wins)+len(placed))/len(settled)*100,1) if settled else 0}%")
print(f"Total stake:  £{total_stake}")
print(f"Total profit: £{total_profit:.2f}")
print(f"ROI: {roi:.1f}%")
print()

by_day = {}
for p in settled:
    rt = p.get('race_time','')
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', rt)
    dn = f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}" if m else rt[:10]
    if dn not in by_day:
        by_day[dn] = {'w':0,'p':0,'l':0,'profit':0.0}
    o = oc(p)
    if o in ('WIN','WON'): by_day[dn]['w'] += 1
    elif o == 'PLACED':    by_day[dn]['p'] += 1
    else:                  by_day[dn]['l'] += 1
    by_day[dn]['profit'] += float(p.get('profit', 0))

print("By date:")
for dn in sorted(by_day):
    dr = by_day[dn]
    dow = datetime.strptime(dn, '%Y-%m-%d').strftime('%a')
    pnl = dr['profit']
    sign = '+' if pnl >= 0 else ''
    print(f"  {dn} {dow}  W:{dr['w']} P:{dr['p']} L:{dr['l']}  P&L: {sign}£{pnl:.2f}")

print()
for lbl, grp in [('WIN', wins), ('PLACED', placed), ('LOSS', losses)]:
    scores = [float(p.get('comprehensive_score',0)) for p in grp]
    avg = round(sum(scores)/len(scores),1) if scores else 'n/a'
    print(f"Avg score {lbl}: {avg}")

print()
print("Win odds:  ", sorted([float(p.get('odds',0)) for p in wins]))
print("Loss odds (first 10):", sorted([float(p.get('odds',0)) for p in losses])[:10])

# Per-day Saturday/Sunday breakdown
sat_picks = [p for p in settled if 'race_time' in p and
             datetime.strptime(
                 (lambda m, rt: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}" if m else rt[:10])(
                     re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', p.get('race_time','')),
                     p.get('race_time','')
                 ), '%Y-%m-%d').weekday() == 5]
sun_picks = [p for p in settled if 'race_time' in p and
             datetime.strptime(
                 (lambda m, rt: f"{m.group(3)}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}" if m else rt[:10])(
                     re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', p.get('race_time','')),
                     p.get('race_time','')
                 ), '%Y-%m-%d').weekday() == 6]

for lbl, grp in [('Saturday', sat_picks), ('Sunday', sun_picks)]:
    if not grp: continue
    gw = [p for p in grp if oc(p) in ('WIN','WON')]
    gp = [p for p in grp if oc(p) == 'PLACED']
    gl = [p for p in grp if oc(p) in ('LOSS','LOST')]
    gprofit = sum(float(p.get('profit',0)) for p in grp)
    wscores = [float(p.get('comprehensive_score',0)) for p in gw]
    lscores = [float(p.get('comprehensive_score',0)) for p in gl]
    print(f"\n{lbl}: W={len(gw)} P={len(gp)} L={len(gl)}  SR={round(len(gw)/len(grp)*100)}%  P&L=£{gprofit:+.2f}")
    print(f"  Avg winner score: {round(sum(wscores)/len(wscores),1) if wscores else 'n/a'}")
    print(f"  Avg loser  score: {round(sum(lscores)/len(lscores),1) if lscores else 'n/a'}")
