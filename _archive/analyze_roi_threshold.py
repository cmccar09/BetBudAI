#!/usr/bin/env python3
"""Analyze realistic ROI thresholds for horse racing betting"""

print('='*80)
print('REALITY CHECK: What Win % Needed for +5% ROI at Common Odds')
print('='*80)

odds_ranges = [
    (1.5, 'Odds-on'),
    (2.0, 'Even'),
    (2.5, '6/4'),
    (3.0, '2/1'),
    (4.0, '3/1'),
    (5.0, '4/1'),
    (6.0, '5/1'),
    (8.0, '7/1'),
    (10.0, '9/1'),
    (15.0, '14/1')
]

print(f'\n{"Odds":<10} {"Market%":<10} {"Need +5%":<12} {"Edge Req":<12} {"Realistic?"}')
print('-'*80)

for odds, name in odds_ranges:
    market_prob = (1.0 / odds) * 100
    min_prob_for_roi = (1.05 / odds) * 100
    
    # Edge needed over market
    edge_needed = min_prob_for_roi - market_prob
    realistic = '✅ Possible' if edge_needed <= 5 else '⚠️ Hard' if edge_needed <= 10 else '❌ Unlikely'
    
    print(f'{name:<10} {market_prob:>8.1f}% {min_prob_for_roi:>8.1f}% {edge_needed:>10.1f}% {realistic:<15}')

print('\n' + '='*80)
print('ALTERNATIVE THRESHOLDS:')
print('='*80)

for threshold_pct in [0, 2.5, 5.0, 10.0]:
    print(f'\nAt {threshold_pct}% ROI minimum:')
    multiplier = 1 + (threshold_pct / 100)
    
    # Show a few key odds
    for odds in [3.0, 5.0, 8.0]:
        min_prob = (multiplier / odds) * 100
        market_prob = (1.0 / odds) * 100
        edge = min_prob - market_prob
        print(f'  {odds:.1f} odds: Need {min_prob:.1f}% (market {market_prob:.1f}%, edge {edge:.1f}%)')

print('\n' + '='*80)
print('RECOMMENDATION:')
print('  - 5% ROI: Very strict, expect 0-2 picks per day (when value exists)')
print('  - 2.5% ROI: Moderate, expect 2-5 picks per day')
print('  - 0% ROI: Breakeven, expect 5-10 picks per day')
print('  - Negative allowed: Educational only, will lose money long-term')
print('='*80)
