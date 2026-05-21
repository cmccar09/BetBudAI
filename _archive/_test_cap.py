from comprehensive_pick_logic import analyze_horse_comprehensive
t = {'horse':'X','form':'1-1-1-1-1-1-1-1','odds':3.9,'race_class':'5','race_name':'Class 5 Hcap','trainer':'Ian Williams','jockey':'Charles Bishop'}
s, bd, reasons = analyze_horse_comprehensive(t, 'Wolverhampton')
print(f'Final score: {s}')
print(f'class5_cap applied: {bd.get("class5_cap", 0)}')
print(f'aw_low_class_penalty: {bd.get("aw_low_class_penalty", 0)}')
cap_reasons = [r for r in reasons if 'capped' in r.lower() or 'Class 5/6' in r or 'AW Class' in r]
for r in cap_reasons:
    print(' ', r)
assert s <= 80, f'Cap failed! Score is {s}'
print('PASS: score capped at <= 80')
