import boto3
import sys
import traceback

try:
    from comprehensive_pick_logic import get_going_conditions
except Exception as e:
    print(f"ERROR importing: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("GOING CONDITIONS DATA CHECK")
print("="*80)

going_data = get_going_conditions()

print(f"\nTotal tracks with going data: {len(going_data)}\n")

for track in sorted(going_data.keys()):
    info = going_data[track]
    going = info.get('going', 'Unknown')
    adjustment = info.get('adjustment', 0)
    print(f"{track:20} Going: {going:25} Adjustment: {adjustment:3}")

if 'Ffos Las' in going_data:
    print("\n✅ Ffos Las IS in going_data")
    print(f"   Details: {going_data['Ffos Las']}")
else:
    print("\n❌ Ffos Las NOT in going_data!")
    
print("\n" + "="*80)

# Now test the logic with River Voyage data
print("TESTING RIVER VOYAGE SCORING LOGIC")
print("="*80)

horse_data = {
    'name': 'River Voyage',
    'odds': 4.4,
    'form': '6211-3P',
    'trainer': 'Rebecca Curtis',
    'jockey': 'Toby McCain-Mitchell(5)'
}

form = horse_data['form']
wins = form.count('1')
recent_win = form.split('-')[-1] == '1' if '-' in form else False

print(f"\nForm: {form}")
print(f"Wins: {wins}")
print(f"Recent win: {recent_win}")
print(f"Recent win check: form.split('-')[-1] = '{form.split('-')[-1]}' == '1'? {form.split('-')[-1] == '1'}")

course = 'Ffos Las'
if course in going_data:
    going_info = going_data[course]
    going_adjustment = going_info.get('adjustment', 0)
    going_description = going_info.get('going', 'Unknown')
    
    print(f"\nGoing: {going_description}")
    print(f"Going adjustment: {going_adjustment}")
    print(f"abs(going_adjustment): {abs(going_adjustment)}")
    print(f"abs(going_adjustment) > 5: {abs(going_adjustment) > 5}")
    print(f"wins >= 2: {wins >= 2}")
    
    if going_adjustment != 0:
        if recent_win and abs(going_adjustment) <= 5:
            print("\n✅ Would get going bonus (branch 1: recent win in moderate conditions)")
        elif abs(going_adjustment) > 5:
            if wins >= 2:
                print(f"\n✅ Would get going bonus (branch 2: {wins} wins in extreme conditions)")
            else:
                print(f"\n❌ NO going bonus (branch 2 fail: only {wins} wins, needs >= 2)")
        else:
            print("\n❌ NO going bonus (no matching branch)")
    else:
        print("\n❌ NO going bonus (going_adjustment == 0)")
else:
    print(f"\n❌ {course} not in going_data")

# Check claiming jockey
jockey = horse_data['jockey']
claiming_allowance = 0
if '(' in jockey and ')' in jockey:
    try:
        claiming_str = jockey.split('(')[1].split(')')[0]
        claiming_allowance = int(claiming_str)
        print(f"\n✅ Claiming jockey detected: {claiming_allowance}lb allowance")
        
        if course in going_data:
            going_desc = going_data[course].get('going', 'Unknown')
            if 'Heavy' in going_desc or 'Soft' in going_desc:
                claiming_bonus = claiming_allowance * 2
                print(f"✅ Claiming bonus in {going_desc}: {claiming_bonus}pts")
            else:
                claiming_bonus = claiming_allowance
                print(f"✅ Claiming bonus in {going_desc}: {claiming_bonus}pts")
    except:
        print(f"\n❌ Failed to parse claiming allowance from: {jockey}")
else:
    print(f"\n❌ No claiming jockey (jockey: '{jockey}')")

print("\n" + "="*80)
