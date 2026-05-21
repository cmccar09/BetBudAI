"""
Step 4: Comprehensive Backtesting Analysis
Final analysis and recommendations based on all tests
"""
import json
from datetime import datetime

print("="*80)
print("COMPREHENSIVE BACKTESTING ANALYSIS")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print()

# Load all results
try:
    with open('backtest_dataset.json', 'r') as f:
        dataset = json.load(f)
    with open('individual_factor_results.json', 'r') as f:
        factor_results = json.load(f)
    with open('baseline_comparison.json', 'r') as f:
        baseline_results = json.load(f)
except FileNotFoundError as e:
    print(f"ERROR: Missing required file: {e.filename}")
    print("\nRun these scripts in order:")
    print("1. python extract_historical_data.py")
    print("2. python backtest_individual_factors.py")
    print("3. python backtest_baseline_strategies.py")
    exit(1)

print("✓ All backtest results loaded")
print()

print("="*80)
print("DATASET OVERVIEW")
print("="*80)
print(f"Total races analyzed: {len(dataset)}")
wins = sum(1 for r in dataset if r['outcome'] in ['WON', 'WIN'])
print(f"Wins: {wins} ({wins/len(dataset)*100:.1f}%)")
print(f"Losses: {len(dataset) - wins} ({(len(dataset)-wins)/len(dataset)*100:.1f}%)")
print()

print("="*80)
print("FACTOR ANALYSIS SUMMARY")
print("="*80)
print()

best_factors = factor_results.get('best_configs', [])
if best_factors:
    print("Top 3 Best Performing Factors:")
    for i, factor in enumerate(best_factors[:3], 1):
        print(f"\n{i}. {factor['factor']} (threshold {factor['threshold']}+)")
        print(f"   Strike Rate: {factor['strike_rate']:.1f}%")
        print(f"   ROI: {factor['roi']:.1f}%")
        print(f"   Sample Size: {factor['picks']} picks")
        
        if factor['roi'] > 10:
            print("   ✓✓✓ HIGHLY PROFITABLE")
        elif factor['roi'] > 5:
            print("   ✓✓ PROFITABLE")
        elif factor['roi'] > 0:
            print("   ✓ Marginally profitable")
        else:
            print("   ✗ Loss-making")
else:
    print("❌ No profitable factors found")

print()
print("="*80)
print("BASELINE STRATEGY COMPARISON")
print("="*80)
print()

strategies = baseline_results.get('strategies', [])
best_baseline = baseline_results.get('best_strategy', {})
current_system = baseline_results.get('current_system', {})

if strategies:
    print(f"{'Strategy':<35} {'ROI%':<10} {'Strike Rate%':<15} {'Picks':<10}")
    print("-" * 75)
    
    for strategy in strategies:
        marker = "✓✓✓" if strategy['roi'] > 10 else "✓✓" if strategy['roi'] > 5 else "✓" if strategy['roi'] > 0 else "✗"
        print(f"{strategy['name']:<35} {strategy['roi']:<10.1f} {strategy['strike_rate']:<15.1f} {strategy['picks']:<10} {marker}")

print()
print("="*80)
print("CRITICAL FINDINGS")
print("="*80)
print()

# Determine system viability
findings = []

# 1. Is current system profitable?
if current_system:
    if current_system['roi'] > 5:
        findings.append("✓ Current system IS profitable (ROI: {:.1f}%)".format(current_system['roi']))
    elif current_system['roi'] > 0:
        findings.append("⚠️ Current system marginally profitable (ROI: {:.1f}%)".format(current_system['roi']))
    else:
        findings.append("❌ Current system LOSING MONEY (ROI: {:.1f}%)".format(current_system['roi']))

# 2. Is it beaten by baselines?
if best_baseline and current_system:
    if best_baseline['roi'] > current_system['roi']:
        findings.append(f"❌ Current system BEATEN by {best_baseline['name']} ({best_baseline['roi']:.1f}% vs {current_system['roi']:.1f}%)")
    else:
        findings.append(f"✓ Current system BEATS all baselines")

# 3. Are there better factors?
if best_factors:
    best_factor = best_factors[0]
    if current_system and best_factor['roi'] > current_system['roi']:
        findings.append(f"⚠️ Single factor ({best_factor['factor']}) outperforms current system ({best_factor['roi']:.1f}% vs {current_system['roi']:.1f}%)")

# 4. Is there any edge at all?
if best_baseline and best_baseline['roi'] < 0:
    findings.append("🚨 CRITICAL: Even BEST strategy loses money - NO EDGE DETECTED")
else:
    findings.append(f"✓ Edge exists: Best strategy achieves {best_baseline['roi']:.1f}% ROI")

# 5. Data sufficiency
if len(dataset) < 200:
    findings.append(f"⚠️ LIMITED DATA: Only {len(dataset)} races (recommended 500+)")
elif len(dataset) < 500:
    findings.append(f"⚠️ MODERATE DATA: {len(dataset)} races (recommended 500+)")
else:
    findings.append(f"✓ SUFFICIENT DATA: {len(dataset)} races")

for finding in findings:
    print(finding)
    print()

print("="*80)
print("RECOMMENDATIONS")
print("="*80)
print()

recommendations = []

# Recommendation 1: Stop or continue?
if current_system and current_system['roi'] < -5:
    recommendations.append({
        'priority': 'CRITICAL',
        'action': 'STOP ALL BETTING IMMEDIATELY',
        'reason': f"System losing {abs(current_system['roi']):.1f}% ROI - no edge",
        'steps': [
            'Disable all automated betting workflows',
            'Do not place any bets with current system',
            'Switch to best performing baseline if needed'
        ]
    })
elif current_system and current_system['roi'] < 0:
    recommendations.append({
        'priority': 'HIGH',
        'action': 'PAUSE BETTING - System not profitable',
        'reason': f"System losing {abs(current_system['roi']):.1f}% ROI",
        'steps': [
            'Temporarily halt automated betting',
            'Investigate why system underperforms baseline',
            'Consider switching to best baseline strategy'
        ]
    })

# Recommendation 2: Switch to better strategy?
if best_baseline and current_system and best_baseline['roi'] > current_system['roi'] + 5:
    recommendations.append({
        'priority': 'HIGH',
        'action': f'SWITCH TO: {best_baseline["name"]}',
        'reason': f"Improves ROI by {best_baseline['roi'] - current_system['roi']:.1f}% ({current_system['roi']:.1f}% → {best_baseline['roi']:.1f}%)",
        'steps': [
            f'Implement {best_baseline["name"]} strategy',
            'Paper trade for 1 week to validate',
            'Monitor performance against backtest expectations'
        ]
    })

# Recommendation 3: Simplify if single factor beats comprehensive
if best_factors:
    best_factor = best_factors[0]
    if current_system and best_factor['roi'] > current_system['roi']:
        recommendations.append({
            'priority': 'MEDIUM',
            'action': f'SIMPLIFY TO: {best_factor["factor"]} only',
            'reason': f"Single factor outperforms complex system ({best_factor['roi']:.1f}% vs {current_system['roi']:.1f}%)",
            'steps': [
                f'Use only {best_factor["factor"]} at threshold {best_factor["threshold"]}+',
                'Remove other 6 factors that add no value',
                'Simpler = more reliable and easier to maintain'
            ]
        })

# Recommendation 4: Collect more data if needed
if len(dataset) < 500:
    recommendations.append({
        'priority': 'MEDIUM',
        'action': 'COLLECT MORE HISTORICAL DATA',
        'reason': f'Only {len(dataset)} races - need 500+ for reliable conclusions',
        'steps': [
            'Import historical race data from Racing Post API',
            'Or wait to accumulate more results over time',
            'Re-run backtest with larger dataset'
        ]
    })

# Recommendation 5: No edge found?
if best_baseline and best_baseline['roi'] < 0:
    recommendations.append({
        'priority': 'CRITICAL',
        'action': 'FUNDAMENTAL SYSTEM REDESIGN REQUIRED',
        'reason': 'No strategy (including baselines) is profitable',
        'steps': [
            'Check data quality - are odds accurate?',
            'Consider that market may be too efficient',
            'Explore machine learning approaches (logistic regression, random forest)',
            'Look for niche markets (e.g., specific track types, conditions)',
            'May need to accept betting is not profitable with available data'
        ]
    })

# Print recommendations
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. [{rec['priority']}] {rec['action']}")
    print(f"   Reason: {rec['reason']}")
    print(f"   Steps:")
    for step in rec['steps']:
        print(f"     • {step}")
    print()

print("="*80)
print("NEXT ACTIONS")
print("="*80)
print()

if recommendations:
    top_rec = recommendations[0]
    print(f"IMMEDIATE ACTION: {top_rec['action']}")
    print()
    print("Steps:")
    for i, step in enumerate(top_rec['steps'], 1):
        print(f"  {i}. {step}")
else:
    print("✓ System performing acceptably")
    print("  Continue monitoring and collecting data")

print()
print("="*80)
print("REPORT COMPLETE")
print("="*80)
print()
print("All backtest results saved:")
print("  • backtest_dataset.json")
print("  • individual_factor_results.json")
print("  • baseline_comparison.json")
print()
print("Review these files for detailed analysis.")
print("="*80)

# Save comprehensive report
report = {
    'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'dataset_size': len(dataset),
    'findings': findings,
    'recommendations': recommendations,
    'best_baseline': best_baseline,
    'current_system': current_system,
    'best_factors': best_factors[:3] if best_factors else []
}

with open('comprehensive_backtest_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print()
print("✓ Comprehensive report saved to: comprehensive_backtest_report.json")
