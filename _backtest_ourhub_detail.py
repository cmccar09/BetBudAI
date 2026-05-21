"""Backtest: What would OurHub data have changed for past week's picks?"""
import boto3, json, requests
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime

API_BASE = 'https://api.ourhub.site/api'
API_KEY = 'oh_dfxqN2ufYVjFvLiK8-FHMnKO3svNbbkP'
HEADERS = {'X-API-Key': API_KEY}

db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('SureBetBets')

dates = ['2026-04-07','2026-04-08','2026-04-09','2026-04-10','2026-04-11','2026-04-12','2026-04-13']

def fetch_perf(date):
    try:
        r = requests.get(f'{API_BASE}/performance-stats/{date}', headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}

# Gather all picks first
all_picks = []
for d in dates:
    resp = t.query(KeyConditionExpression=Key('bet_date').eq(d))
    items = [i for i in resp['Items'] if i.get('show_in_ui')]
    for i in items:
        hn = i.get('horse_name', '?')
        if hn == '?':
            bid = str(i.get('bet_id', ''))
            if '_' in bid:
                hn = bid.split('_')[-1]
        bd = i.get('score_breakdown', {})
        all_picks.append({
            'date': d,
            'horse': hn,
            'course': str(i.get('course', '?')),
            'odds': float(i.get('odds', 0)),
            'outcome': str(i.get('outcome', '?')).lower(),
            'trainer': str(i.get('trainer', '?')),
            'jockey': str(i.get('jockey', '?')),
            'trainer_pts': float(bd.get('trainer_reputation', 0)),
            'unknown_tp': float(bd.get('unknown_trainer_penalty', 0)),
            'jockey_pts': float(bd.get('jockey_quality', 0)),
            'going_pts': float(bd.get('going_suitability', 0)),
            'score': float(i.get('score', 0)),
        })

# Now fetch OurHub data for each date
print("=" * 120)
print("OURHUB BACKTEST: What would have changed for each pick?")
print("=" * 120)

total_score_delta = 0
picks_affected = 0

for d in sorted(set(p['date'] for p in all_picks)):
    print(f"\n--- {d} ---")
    perf = fetch_perf(d)
    
    # Build lookup: horse_name -> stats
    horse_stats = {}
    for race_key, runners in perf.items():
        if isinstance(runners, list):
            for r in runners:
                hn = r.get('horse_name', '').strip().lower()
                horse_stats[hn] = r.get('stats', {})
    
    day_picks = [p for p in all_picks if p['date'] == d]
    for p in day_picks:
        horse_lower = p['horse'].strip().lower()
        # Try partial match since our horse names may be truncated
        matched_stats = None
        for hn_key, stats in horse_stats.items():
            if horse_lower in hn_key or hn_key in horse_lower:
                matched_stats = stats
                break
        
        trainer_wr = matched_stats.get('trainer_win_rate', 0) if matched_stats else 0
        trainer_runs = matched_stats.get('trainer_runs', 0) if matched_stats else 0
        jockey_wr = matched_stats.get('jockey_win_rate', 0) if matched_stats else 0
        jockey_runs = matched_stats.get('jockey_runs', 0) if matched_stats else 0
        trainer_wr = trainer_wr or 0
        trainer_runs = trainer_runs or 0
        jockey_wr = jockey_wr or 0
        jockey_runs = jockey_runs or 0
        
        # Calculate what would have changed
        delta = 0
        notes = []
        
        # Unknown trainer penalty impact
        if p['unknown_tp'] < 0:  # Currently penalised -8
            if trainer_wr >= 20 and trainer_runs >= 10:
                # Would have got +8 instead of -8 = +16 swing
                delta += 16  # from -8 to +8
                notes.append(f"trainer {trainer_wr:.0f}% WR ({trainer_runs} runs): -8 -> +8 = +16pts")
            elif trainer_wr >= 12 and trainer_runs >= 10:
                delta += 8  # from -8 to 0
                notes.append(f"trainer {trainer_wr:.0f}% WR ({trainer_runs} runs): -8 -> 0 = +8pts")
            elif trainer_runs >= 10:
                notes.append(f"trainer {trainer_wr:.0f}% WR ({trainer_runs} runs): still -8pts (low WR)")
            else:
                notes.append(f"trainer data: {trainer_runs} runs (too few, still -8pts)")
        
        # Jockey quality for non-elite
        if p['jockey_pts'] == 0 and p['jockey'] != '?':
            if jockey_wr >= 18 and jockey_runs >= 10:
                delta += 6
                notes.append(f"jockey {jockey_wr:.0f}% WR ({jockey_runs} runs): 0 -> +6pts")
            elif jockey_wr >= 10 and jockey_runs >= 10:
                delta += 3
                notes.append(f"jockey {jockey_wr:.0f}% WR ({jockey_runs} runs): 0 -> +3pts")
            elif jockey_runs >= 10:
                notes.append(f"jockey {jockey_wr:.0f}% WR ({jockey_runs} runs): still 0 (low WR)")
        
        outcome_icon = {'win': '✅', 'won': '✅', 'loss': '❌', 'lost': '❌', 'placed': '🔸'}.get(p['outcome'], '❓')
        
        if delta != 0:
            total_score_delta += delta
            picks_affected += 1
        
        status = f"{'⬆️ +' + str(delta) + 'pts' if delta > 0 else '→ no change'}"
        print(f"  {outcome_icon} {p['horse']:22s} | {p['course']:15s} | odds={p['odds']:5.2f} | trainer={p['trainer']:25s} | {status}")
        for n in notes:
            print(f"      {n}")

print(f"\n{'=' * 120}")
print(f"SUMMARY: {picks_affected} of {len(all_picks)} picks would have had score changes")
print(f"Total score points added: +{total_score_delta}")
print(f"\nROI IMPACT ANALYSIS:")

# Calculate actual ROI
wins = [p for p in all_picks if p['outcome'] in ('win', 'won')]
losses = [p for p in all_picks if p['outcome'] in ('loss', 'lost')]
placed = [p for p in all_picks if p['outcome'] == 'placed']
pending = [p for p in all_picks if p['outcome'] not in ('win', 'won', 'loss', 'lost', 'placed')]
settled = [p for p in all_picks if p['outcome'] in ('win', 'won', 'loss', 'lost')]

total_staked = len(settled)
total_return = sum(p['odds'] for p in wins)
roi = ((total_return - total_staked) / total_staked * 100) if total_staked else 0

print(f"  Settled picks: {len(settled)} (W={len(wins)}, L={len(losses)}+placed={len(placed)}, pending={len(pending)})")
print(f"  Win-only ROI (£1 stakes): staked £{total_staked}, returned £{total_return:.2f}, ROI = {roi:+.1f}%")

# Identify the picks with unknown_tp that LOST - they might not have been picked with OurHub
unknown_tp_losers = [p for p in all_picks if p['unknown_tp'] < 0 and p['outcome'] in ('loss', 'lost')]
print(f"\n  Picks with unknown trainer penalty that LOST: {len(unknown_tp_losers)}")
for p in unknown_tp_losers:
    print(f"    ❌ {p['horse']} ({p['course']}) odds={p['odds']} trainer={p['trainer']}")
