import sys
sys.path.insert(0, 'c:/Users/charl/OneDrive/futuregenAI/Betting')
from barrys.surebet_intel import build_all_picks

picks = build_all_picks()
print("Keys:", list(picks.keys()))
for day_key, day_picks in picks.items():
    day_picks = picks.get(day_key, [])
    print(f'{day_key}: {len(day_picks)} picks')
    for p in day_picks:
        rn = p.get('race_name', '')[:35]
        tier = p.get('tier', '')
        bt = p.get('bet_tier', 'N/A')
        rec = p.get('recommendation', 'N/A')
        score = p.get('score', 0)
        print(f"  {rn:35}  score={score}  tier={tier}  bet_tier={bt}  recommendation={rec}")
