"""
Step 2: Test Individual Factors
Test each scoring factor independently to see which actually predicts wins
"""
import json
from collections import defaultdict

print("="*80)
print("INDIVIDUAL FACTOR BACKTESTING")
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

def test_factor(races, factor_name, factor_getter, thresholds=[50, 60, 70, 80, 85, 90]):
    """Test a single factor at different thresholds"""
    
    print(f"\n{'='*80}")
    print(f"TESTING FACTOR: {factor_name}")
    print('='*80)
    
    results = {}
    
    for threshold in thresholds:
        # Select races above threshold
        selected = [r for r in races if factor_getter(r) >= threshold]
        
        if len(selected) == 0:
            continue
        
        # Calculate performance
        wins = sum(1 for r in selected if r['outcome'] in ['WON', 'WIN'])
        total = len(selected)
        strike_rate = (wins / total * 100) if total > 0 else 0
        
        # Calculate profitability (£2 stake)
        stake_per_bet = 2.0
        total_staked = total * stake_per_bet
        total_returned = sum(r['odds'] * stake_per_bet for r in selected if r['outcome'] in ['WON', 'WIN'])
        profit = total_returned - total_staked
        roi = (profit / total_staked * 100) if total_staked > 0 else 0
        
        # Average odds
        avg_odds = sum(r['odds'] for r in selected) / total if total > 0 else 0
        
        results[threshold] = {
            'picks': total,
            'wins': wins,
            'strike_rate': strike_rate,
            'profit': profit,
            'roi': roi,
            'avg_odds': avg_odds
        }
        
        print(f"\nThreshold {threshold}+:")
        print(f"  Picks: {total}")
        print(f"  Wins: {wins} / Strike Rate: {strike_rate:.1f}%")
        print(f"  Avg Odds: {avg_odds:.2f}")
        print(f"  P&L: £{profit:.2f} | ROI: {roi:.1f}%")
        
        # Highlight profitable thresholds
        if roi > 5:
            print(f"  ✓✓✓ PROFITABLE!")
        elif roi > 0:
            print(f"  ✓ Slightly profitable")
        else:
            print(f"  ✗ Loss-making")
    
    return results

# Test each factor independently
print("\n" + "="*80)
print("FACTOR 1: COMPREHENSIVE SCORE")
print("="*80)
comprehensive_results = test_factor(
    data,
    "Comprehensive Score",
    lambda r: r['comprehensive_score'],
    thresholds=[60, 70, 75, 80, 85, 90, 95, 100]
)

print("\n" + "="*80)
print("FACTOR 2: FORM SCORE")
print("="*80)
form_results = test_factor(
    data,
    "Form Score",
    lambda r: r['factors'].get('form_score', 0),
    thresholds=[5, 7, 8, 9, 10]
)

print("\n" + "="*80)
print("FACTOR 3: TRAINER SCORE")
print("="*80)
trainer_results = test_factor(
    data,
    "Trainer Score",
    lambda r: r['factors'].get('trainer_score', 0),
    thresholds=[5, 7, 8, 9, 10]
)

print("\n" + "="*80)
print("FACTOR 4: GOING SUITABILITY SCORE")
print("="*80)
going_results = test_factor(
    data,
    "Going Score",
    lambda r: r['factors'].get('going_score', 0),
    thresholds=[5, 7, 8, 9, 10]
)

print("\n" + "="*80)
print("FACTOR 5: ODDS SCORE (Sweet Spot)")
print("="*80)
odds_results = test_factor(
    data,
    "Odds Score",
    lambda r: r['factors'].get('odds_score', 0),
    thresholds=[15, 20, 25]
)

print("\n" + "="*80)
print("FACTOR 6: ODDS RANGE TEST (Direct)")
print("="*80)
print("Testing if 3-9 odds range is actually a 'sweet spot'\n")

# Test different odds ranges
odds_ranges = [
    ("1.5-2.5 (Strong favorites)", 1.5, 2.5),
    ("2.5-3.5 (Favorites)", 2.5, 3.5),
    ("3.0-5.0 (Sweet spot start)", 3.0, 5.0),
    ("3.0-9.0 (Full sweet spot)", 3.0, 9.0),
    ("5.0-10.0 (Mid odds)", 5.0, 10.0),
    ("10.0-20.0 (Outsiders)", 10.0, 20.0),
]

for name, min_odds, max_odds in odds_ranges:
    selected = [r for r in data if min_odds <= r['odds'] <= max_odds]
    
    if len(selected) == 0:
        continue
    
    wins = sum(1 for r in selected if r['outcome'] in ['WON', 'WIN'])
    total = len(selected)
    strike_rate = (wins / total * 100) if total > 0 else 0
    
    stake_per_bet = 2.0
    total_staked = total * stake_per_bet
    total_returned = sum(r['odds'] * stake_per_bet for r in selected if r['outcome'] in ['WON', 'WIN'])
    profit = total_returned - total_staked
    roi = (profit / total_staked * 100) if total_staked > 0 else 0
    
    print(f"\n{name}:")
    print(f"  Picks: {total}")
    print(f"  Strike Rate: {strike_rate:.1f}%")
    print(f"  P&L: £{profit:.2f} | ROI: {roi:.1f}%")
    
    if roi > 5:
        print(f"  ✓✓✓ HIGHLY PROFITABLE")
    elif roi > 0:
        print(f"  ✓ Profitable")

print("\n" + "="*80)
print("SUMMARY: BEST PERFORMING FACTORS")
print("="*80)
print()

# Collect best results for each factor
all_results = {
    'Comprehensive Score': comprehensive_results,
    'Form Score': form_results,
    'Trainer Score': trainer_results,
    'Going Score': going_results,
    'Odds Score': odds_results
}

best_configs = []

for factor_name, results in all_results.items():
    if not results:
        continue
    
    # Find most profitable threshold
    best_threshold = max(results.items(), key=lambda x: x[1]['roi'])
    
    if best_threshold[1]['picks'] >= 20:  # Must have at least 20 picks
        best_configs.append({
            'factor': factor_name,
            'threshold': best_threshold[0],
            'roi': best_threshold[1]['roi'],
            'strike_rate': best_threshold[1]['strike_rate'],
            'picks': best_threshold[1]['picks']
        })

# Sort by ROI
best_configs.sort(key=lambda x: x['roi'], reverse=True)

print("Top Performing Configurations:")
print()
for i, config in enumerate(best_configs[:5], 1):
    print(f"{i}. {config['factor']} (threshold {config['threshold']}+)")
    print(f"   ROI: {config['roi']:.1f}% | Strike Rate: {config['strike_rate']:.1f}% | {config['picks']} picks")
    print()

# Save results
with open('individual_factor_results.json', 'w') as f:
    json.dump({
        'all_results': {k: {str(tk): tv for tk, tv in v.items()} for k, v in all_results.items()},
        'best_configs': best_configs
    }, f, indent=2)

print("✓ Results saved to individual_factor_results.json")
print()
print("="*80)
print("KEY FINDINGS:")
print("="*80)

if best_configs and best_configs[0]['roi'] > 10:
    print(f"✓ Found profitable factor: {best_configs[0]['factor']}")
    print(f"  ROI: {best_configs[0]['roi']:.1f}%")
elif best_configs and best_configs[0]['roi'] > 0:
    print(f"⚠️ Marginally profitable: {best_configs[0]['factor']}")
    print(f"  ROI: {best_configs[0]['roi']:.1f}%")
else:
    print("❌ NO PROFITABLE FACTORS FOUND")
    print("All factors tested are loss-making")

print()
print("NEXT: Run python backtest_baseline_strategies.py")
print("="*80)
