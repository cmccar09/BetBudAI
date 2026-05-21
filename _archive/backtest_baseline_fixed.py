"""
Step 3: Benchmark Against Baseline Strategies
Compare our system against simple baseline strategies
"""
import json
import random
from collections import defaultdict

print("="*80)
print("BASELINE STRATEGY BACKTESTING")
print("="*80)
print()

# Load dataset
try:
    with open('backtest_dataset.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print("ERROR: backtest_dataset.json not found")
    print("Run: python extract_historical_data.py first")
    exit(1)

print(f"Loaded {len(data)} races")
print()

# Group races by race (same date + time + course)
races_grouped = defaultdict(list)
for entry in data:
    race_key = f"{entry['bet_date']}_{entry['race_time']}_{entry['course']}"
    races_grouped[race_key].append(entry)

print(f"Grouped into {len(races_grouped)} unique races")
print()

stake_per_bet = 2.0

def evaluate_strategy(name, picks):
    """Evaluate a betting strategy"""
    
    if not picks:
        print(f"\n{name}: No picks")
        return None
    
    wins = sum(1 for p in picks if p['outcome'] in ['WON', 'WIN'])
    total = len(picks)
    strike_rate = (wins / total * 100) if total > 0 else 0
    
    total_staked = total * stake_per_bet
    total_returned = sum(p['odds'] * stake_per_bet for p in picks if p['outcome'] in ['WON', 'WIN'])
    profit = total_returned - total_staked
    roi = (profit / total_staked * 100) if total_staked > 0 else 0
    
    avg_odds = sum(p['odds'] for p in picks) / total if total > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"STRATEGY: {name}")
    print('='*80)
    print(f"Total Picks: {total}")
    print(f"Wins: {wins}")
    print(f"Strike Rate: {strike_rate:.1f}%")
    print(f"Average Odds: {avg_odds:.2f}")
    print(f"Total Staked: £{total_staked:.2f}")
    print(f"Total Returned: £{total_returned:.2f}")
    print(f"Profit/Loss: £{profit:.2f}")
    print(f"ROI: {roi:.1f}%")
    
    if roi > 10:
        print("SUCCESSSUCCESSSUCCESS HIGHLY PROFITABLE")
    elif roi > 5:
        print("SUCCESSSUCCESS PROFITABLE")
    elif roi > 0:
        print("SUCCESS Slightly profitable")
    elif roi > -10:
        print("WARNING Small loss")
    else:
        print("ERROR SIGNIFICANT LOSS")
    
    return {
        'name': name,
        'picks': total,
        'wins': wins,
        'strike_rate': strike_rate,
        'avg_odds': avg_odds,
        'profit': profit,
        'roi': roi
    }

# BASELINE 1: Always bet the favorite
print("\n" + "="*80)
print("BASELINE 1: ALWAYS BET THE FAVORITE")
print("="*80)
favorite_picks = []
for race_key, horses in races_grouped.items():
    if len(horses) > 1:
        # Favorite = lowest odds
        favorite = min(horses, key=lambda x: x['odds'])
        favorite_picks.append(favorite)

baseline1 = evaluate_strategy("Always Bet Favorite", favorite_picks)

# BASELINE 2: Random selection (one horse per race)
print("\n" + "="*80)
print("BASELINE 2: RANDOM SELECTION")
print("="*80)
random.seed(42)  # For reproducibility
random_picks = []
for race_key, horses in races_grouped.items():
    if horses:
        random_pick = random.choice(horses)
        random_picks.append(random_pick)

baseline2 = evaluate_strategy("Random Selection", random_picks)

# BASELINE 3: Always bet horses with odds between 3-5 (mid-range)
print("\n" + "="*80)
print("BASELINE 3: MID-RANGE ODDS (3.0-5.0)")
print("="*80)
mid_odds_all = [h for h in data if 3.0 <= h['odds'] <= 5.0]
baseline3 = evaluate_strategy("Mid-Range Odds (3.0-5.0)", mid_odds_all)

# BASELINE 4: Top 2 favorites per race
print("\n" + "="*80)
print("BASELINE 4: TOP 2 FAVORITES PER RACE")
print("="*80)
top2_picks = []
for race_key, horses in races_grouped.items():
    if len(horses) >= 2:
        # Sort by odds and take top 2
        sorted_horses = sorted(horses, key=lambda x: x['odds'])
        top2_picks.extend(sorted_horses[:2])

baseline4 = evaluate_strategy("Top 2 Favorites", top2_picks)

# BASELINE 5: Current system (85+ comprehensive score)
print("\n" + "="*80)
print("CURRENT SYSTEM: 85+ COMPREHENSIVE SCORE")
print("="*80)
current_system = [h for h in data if h['comprehensive_score'] >= 85]
current = evaluate_strategy("Current System (85+)", current_system)

# BASELINE 6: High form horses (form contains '1')
print("\n" + "="*80)
print("BASELINE 6: RECENT WIN IN FORM (contains '1')")
print("="*80)
form_winners = [h for h in data if '1' in h.get('form', '')]
baseline6 = evaluate_strategy("Recent Winner (form has '1')", form_winners)

# Compile all results
all_baselines = [baseline1, baseline2, baseline3, baseline4, current, baseline6]
all_baselines = [b for b in all_baselines if b is not None]

# Sort by ROI
all_baselines.sort(key=lambda x: x['roi'], reverse=True)

print("\n" + "="*80)
print("STRATEGY COMPARISON SUMMARY")
print("="*80)
print()
print(f"{'Strategy':<30} {'Picks':<8} {'SR%':<8} {'Avg Odds':<10} {'ROI%':<10}")
print("-" * 80)

for result in all_baselines:
    marker = "SUCCESSSUCCESSSUCCESS" if result['roi'] > 10 else "SUCCESSSUCCESS" if result['roi'] > 5 else "SUCCESS" if result['roi'] > 0 else "LOSS"
    print(f"{result['name']:<30} {result['picks']:<8} {result['strike_rate']:<8.1f} {result['avg_odds']:<10.2f} {result['roi']:<10.1f} {marker}")

print()
print("="*80)
print("KEY FINDINGS:")
print("="*80)
print()

# Find best baseline
best_baseline = all_baselines[0]
current_system_result = next((r for r in all_baselines if 'Current System' in r['name']), None)

if current_system_result:
    current_rank = all_baselines.index(current_system_result) + 1
    
    print(f"Current System Performance:")
    print(f"  Rank: #{current_rank} out of {len(all_baselines)}")
    print(f"  ROI: {current_system_result['roi']:.1f}%")
    print(f"  Strike Rate: {current_system_result['strike_rate']:.1f}%")
    print()
    
    if current_rank == 1:
        print("SUCCESSSUCCESSSUCCESS Current system BEATS all baselines!")
    elif current_system_result['roi'] > 0:
        print(f"WARNING Current system is profitable but beaten by: {best_baseline['name']}")
        print(f"   Best baseline ROI: {best_baseline['roi']:.1f}%")
    else:
        print(f"ERROR Current system is LOSING MONEY")
        print(f"   Best baseline ({best_baseline['name']}): ROI {best_baseline['roi']:.1f}%")
        print(f"   Current system: ROI {current_system_result['roi']:.1f}%")

print()
print("Best Overall Strategy:")
print(f"  {best_baseline['name']}")
print(f"  ROI: {best_baseline['roi']:.1f}%")
print(f"  Strike Rate: {best_baseline['strike_rate']:.1f}%")
print(f"  {best_baseline['picks']} picks")
print()

if best_baseline['roi'] < 0:
    print("CRITICAL CRITICAL: Even the BEST strategy is losing money!")
    print("This suggests:")
    print("  1. Data quality issues (odds not accurate?)")
    print("  2. Market efficiency - no edge available")
    print("  3. Need more sophisticated approach")
else:
    print(f"SUCCESS At least one strategy is profitable: {best_baseline['name']}")

# Save results
with open('baseline_comparison.json', 'w') as f:
    json.dump({
        'strategies': all_baselines,
        'best_strategy': best_baseline,
        'current_system': current_system_result
    }, f, indent=2)

print()
print("SUCCESS Results saved to baseline_comparison.json")
print()
print("="*80)
print("RECOMMENDATIONS:")
print("="*80)
print()

if best_baseline['roi'] > current_system_result['roi'] if current_system_result else 0:
    print(f"1. Consider switching to: {best_baseline['name']}")
    print(f"   Expected improvement: +{best_baseline['roi'] - (current_system_result['roi'] if current_system_result else 0):.1f}% ROI")
    print()

print("2. Run comprehensive analysis:")
print("   python backtest_comprehensive_analysis.py")
print()
print("="*80)
