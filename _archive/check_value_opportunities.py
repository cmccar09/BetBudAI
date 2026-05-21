#!/usr/bin/env python3
"""Check for potential value betting opportunities in current market"""

import json

with open('response_live.json') as f:
    data = json.load(f)

print('='*80)
print('POTENTIAL VALUE OPPORTUNITIES ANALYSIS')
print('='*80)

for race in data.get('races', []):
    market_name = race.get('marketName', 'Unknown')
    venue = race.get('venue', 'Unknown')
    
    print(f'\n{venue} - {market_name}')
    print('-' * 80)
    
    runners = race.get('runners', [])
    
    # Look for horses at decent odds (3.0+) where we might find value
    value_candidates = []
    for r in runners:
        try:
            odds = float(r.get('odds', 999))
            if odds < 3.0:  # Too short, unlikely to have value
                continue
            if odds > 15.0:  # Too long, low probability
                continue
                
            name = r.get('runnerName', 'Unknown')
            
            # For +5% ROI at these odds, we need:
            # ROI = (odds × p_win - 1) × 100 >= 5
            # odds × p_win >= 1.05
            # p_win >= 1.05 / odds
            min_p_win_for_roi = 1.05 / odds
            
            # Fair odds breakeven
            fair_p_win = 1.0 / odds
            
            # For value, our prediction needs to be HIGHER than market implies
            # E.g., if odds = 5.0 (implies 20%), we need to predict > 20%
            # For 5% ROI at 5.0 odds: need p_win >= 21%
            
            value_candidates.append({
                'name': name,
                'odds': odds,
                'market_prob': fair_p_win * 100,
                'min_p_win_pct': min_p_win_for_roi * 100
            })
        except:
            pass
    
    if value_candidates:
        print(f'{"Horse":<30} {"Odds":>6} {"Market%":>8} {"Need%":>8} (for +5% ROI)')
        for v in sorted(value_candidates, key=lambda x: x['odds'])[:12]:
            print(f'{v["name"]:<30} {v["odds"]:6.2f} {v["market_prob"]:7.1f}% {v["min_p_win_pct"]:7.1f}%')
    else:
        print('No suitable candidates found (all < 3.0 or > 15.0 odds)')

print('\n' + '='*80)
print('SUMMARY: To get +5% ROI, you need to find horses where:')
print('  - Your predicted win probability > "Need%" shown above')
print('  - Market odds are higher than your fair value assessment')
print('  - E.g., Horse at 6.0 odds (16.7% implied) with 20% true chance = +20% ROI')
print('='*80)
