runners = [
    {'name': 'Barefoot Beach',  'form': '1-'},
    {'name': 'Mehmas Engine',   'form': '3'},
    {'name': 'Yasalam',         'form': '4-'},
    {'name': 'Sizzling Seixas', 'form': '4'},
    {'name': 'Minnie Idol',     'form': '24'},
]
market_name = '6f Nov Stks'
our_form = '1-'
our_score = 85

debut_count = 0
for ru in runners:
    f = str(ru.get('form', '')).strip()
    run_chars = f.replace('-','').replace('/','').replace('P','').replace('F','').replace('U','').replace('0','')
    is_one = len(f) == 0 or f == '-' or len(run_chars) <= 1
    if is_one:
        debut_count += 1
    print(f"  {ru['name']:<22} form={f!r:<8} run_chars={run_chars!r:<6} debut_or_1run={is_one}")

ratio = debut_count / len(runners)
print()
print(f"Debut/one-run horses: {debut_count}/{len(runners)} = {ratio:.0%}")
is_nov = any(kw in market_name.lower() for kw in ['nov', 'novice', 'mdn', 'maiden', 'cond', 'nstks', 'nst'])
our_runs = len(our_form.replace('-', '').replace('/', ''))
print(f"Is novice race:  {is_nov}  ('{market_name}')")
print(f"Our pick runs:   {our_runs},  score: {our_score}")
print()
if ratio >= 0.60 and is_nov and not (our_runs >= 3 and our_score >= 88):
    print("RESULT: GATE-S7 WOULD REJECT -> novice stakes + debut-heavy field -> SKIPPED")
elif ratio >= 0.80 and not (our_runs >= 3 and our_score >= 88):
    print("RESULT: GATE-S7 WOULD REJECT -> 80%+ debut field")
else:
    print("RESULT: passes S7")
