import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

history = Path('./history')
dates = ['20251229', '20251230', '20260103', '20260104', '20260105']

print("\n" + "="*70)
print("LEARNING SYSTEM ANALYSIS - Historical Performance")
print("="*70)

total_bets = 0
total_wins = 0
total_places = 0
predicted_wins = []
actual_results = []

tag_stats = defaultdict(lambda: {'bets': 0, 'wins': 0, 'predicted': []})

for date in dates:
    sel_files = list(history.glob(f'selections_{date}*.csv'))
    if not sel_files:
        continue
        
    df = pd.read_csv(sel_files[-1])
    res_file = history / f'results_{date}.json'
    
    if not res_file.exists():
        print(f"\n{date}: No results yet")
        continue
    
    results = json.load(open(res_file))
    if not results:
        print(f"\n{date}: Empty results file")
        continue
        
    res_map = {(str(r['market_id']), str(r['selection_id'])): r for r in results}
    
    day_bets = 0
    day_wins = 0
    
    for _, row in df.iterrows():
        key = (str(row['market_id']), str(row['selection_id']))
        if key in res_map:
            r = res_map[key]
            total_bets += 1
            day_bets += 1
            
            p_win = float(row.get('p_win', 0))
            predicted_wins.append(p_win)
            
            is_winner = r.get('is_winner', False)
            is_placed = r.get('is_placed', False)
            
            if is_winner:
                total_wins += 1
                day_wins += 1
                actual_results.append(1)
            else:
                actual_results.append(0)
            
            if is_placed:
                total_places += 1
            
            # Track by tags
            tags = str(row.get('tags', '')).split(',')
            for tag in tags:
                tag = tag.strip()
                if tag:
                    tag_stats[tag]['bets'] += 1
                    tag_stats[tag]['predicted'].append(p_win)
                    if is_winner:
                        tag_stats[tag]['wins'] += 1
    
    if day_bets > 0:
        print(f"\n{date}: {day_bets} bets, {day_wins} wins ({day_wins/day_bets*100:.1f}%)")

print("\n" + "="*70)
print("OVERALL PERFORMANCE")
print("="*70)
print(f"Total bets tracked: {total_bets}")
print(f"Wins: {total_wins} ({total_wins/total_bets*100:.1f}%)")
print(f"Places: {total_places} ({total_places/total_bets*100:.1f}%)")
print(f"Average predicted win%: {sum(predicted_wins)/len(predicted_wins)*100:.1f}%")
print(f"\n⚠️  CALIBRATION ERROR: Predicted {sum(predicted_wins)/len(predicted_wins)*100:.1f}% but actual is {total_wins/total_bets*100:.1f}%")
print(f"   AI is overconfident by {(sum(predicted_wins)/len(predicted_wins) - total_wins/total_bets)*100:.1f} percentage points")

print("\n" + "="*70)
print("PATTERN ANALYSIS (What strategies work?)")
print("="*70)

for tag, stats in sorted(tag_stats.items(), key=lambda x: x[1]['wins']/x[1]['bets'] if x[1]['bets'] > 0 else 0, reverse=True):
    if stats['bets'] >= 3:  # Only show patterns with 3+ bets
        win_rate = stats['wins'] / stats['bets'] * 100
        expected_rate = sum(stats['predicted']) / len(stats['predicted']) * 100
        diff = win_rate - expected_rate
        
        status = "✓ GOOD" if diff > -5 else "⚠️  POOR"
        print(f"{status} {tag[:30]:30s}: {stats['wins']}/{stats['bets']} ({win_rate:5.1f}% vs {expected_rate:5.1f}% expected)")

print("\n" + "="*70)
