"""
Deep Saturday vs Sunday analysis - compare race types, field sizes, 
market efficiency, score factors, winners vs losers
"""
import boto3, re, json
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from datetime import date, timedelta

db  = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

# Pull every Saturday and Sunday we have picks for
all_sat, all_sun = [], []

start = date(2026, 3, 14)
end   = date(2026, 3, 29)
d = start
while d <= end:
    resp  = tbl.query(KeyConditionExpression=Key('bet_date').eq(str(d)))
    items = resp['Items']
    # Deduplicate
    seen = {}
    for p in items:
        k  = (p.get('horse',''), str(p.get('race_time','')))
        sc = float(p.get('comprehensive_score', p.get('score', 0)))
        if k not in seen or sc > float(seen[k].get('comprehensive_score', seen[k].get('score', 0))):
            seen[k] = p
    picks = [p for p in seen.values()
             if p.get('outcome') or p.get('result_emoji')]  # settled only

    dow = d.strftime('%A')
    if dow == 'Saturday':
        all_sat.extend(picks)
    elif dow == 'Sunday':
        all_sun.extend(picks)
    d += timedelta(days=1)

def analyse(picks, label):
    wins   = [p for p in picks if (p.get('result_emoji') or p.get('outcome','')).upper() in ('WIN','WON')]
    losses = [p for p in picks if (p.get('result_emoji') or p.get('outcome','')).upper() in ('LOSS','LOST')]
    placed = [p for p in picks if (p.get('result_emoji') or p.get('outcome','')).upper() == 'PLACED']
    settled = len(wins)+len(losses)+len(placed)

    # Field sizes
    field_sizes = []
    for p in picks:
        m = re.search(r'of (\d+)', p.get('result_analysis','') or '')
        if m: field_sizes.append(int(m.group(1)))

    # Average score of winners vs losers
    win_scores  = [float(p.get('comprehensive_score', p.get('score', 0))) for p in wins]
    loss_scores = [float(p.get('comprehensive_score', p.get('score', 0))) for p in losses]

    # Score factor activity (what % had each factor > 0)
    factors = ['jockey_quality','database_history','cd_bonus','course_performance',
               'deep_form','meeting_focus','going_suitability','recent_win','total_wins',
               'consistency','market_leader','unknown_trainer_penalty']
    factor_activity = {f: 0 for f in factors}
    for p in picks:
        sb = p.get('score_breakdown') or {}
        for f in factors:
            if abs(float(sb.get(f, 0))) > 0:
                factor_activity[f] += 1

    # Courses
    courses = {}
    for p in picks:
        c = p.get('course','Unknown')
        courses[c] = courses.get(c, 0) + 1

    # Winner market rank (were they favourite?)
    # compare winner odds to our pick odds
    upset_count = 0  # winner had higher odds than our pick
    for p in losses + placed:
        our_odds  = float(p.get('odds', 0))
        winner_wa = p.get('winner_analysis') or {}
        # try to get winner rank from all_horses
        wname = (p.get('result_winner_name') or '').lower()
        field = [(h.get('horse',''), float(h.get('odds',0))) for h in (p.get('all_horses') or [])]
        wmatch = [o for (n,o) in field if n.lower() == wname]
        if wmatch and wmatch[0] > our_odds:
            upset_count += 1

    print(f"\n{'='*55}")
    print(f"  {label}  ({settled} settled picks)")
    print(f"{'='*55}")
    print(f"  W={len(wins)} P={len(placed)} L={len(losses)}  Strike={round(len(wins)/settled*100) if settled else 0}%")
    if field_sizes:
        print(f"  Avg field: {round(sum(field_sizes)/len(field_sizes),1)}  Max: {max(field_sizes)}  Min: {min(field_sizes)}")
    if win_scores:
        print(f"  Avg score winners : {round(sum(win_scores)/len(win_scores),1)}")
    if loss_scores:
        print(f"  Avg score losers  : {round(sum(loss_scores)/len(loss_scores),1)}")
    print(f"  Upset count (winner had longer odds than our pick): {upset_count}/{len(losses)+len(placed)}")
    print(f"\n  Factor activity (% of picks where factor scored >0):")
    for f, cnt in sorted(factor_activity.items(), key=lambda x: -x[1]):
        pct = round(cnt/len(picks)*100) if picks else 0
        bar = '█' * (pct // 5)
        print(f"    {f:<30} {pct:>3}%  {bar}")
    print(f"\n  Courses: {dict(sorted(courses.items(), key=lambda x: -x[1]))}")

analyse(all_sat, "SATURDAY")
analyse(all_sun, "SUNDAY")

# Head to head odds distribution
print("\n\nODDS DISTRIBUTION")
print("-"*40)
sat_odds = [float(p.get('odds',0)) for p in all_sat if p.get('odds')]
sun_odds = [float(p.get('odds',0)) for p in all_sun if p.get('odds')]
buckets = [(1,2,'Odds-on/Evs'),(2,3.5,'6/4 - 5/2'),(3.5,6,'11/4 - 4/1'),(6,10,'5/1 - 8/1'),(10,99,'9/1+')]
print(f"{'Range':<16} {'SAT picks':>10} {'SUN picks':>10}")
for lo,hi,lbl in buckets:
    sc = sum(1 for o in sat_odds if lo <= o < hi)
    su = sum(1 for o in sun_odds if lo <= o < hi)
    print(f"  {lbl:<14} {sc:>10} {su:>10}")
