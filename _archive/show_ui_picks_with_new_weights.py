import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

items = table.scan().get('Items', [])

# Get all UI picks
ui_picks = [i for i in items if i.get('show_in_ui') == True]
ui_today = [i for i in ui_picks if '2026-02-04' in i.get('race_time', '')]

print(f"\n{'='*80}")
print(f"CURRENT UI PICKS - WITH NEW WEIGHTS")
print(f"{'='*80}\n")

print(f"Total UI picks today: {len(ui_today)}\n")

for pick in sorted(ui_today, key=lambda x: x.get('race_time', '')):
    time = pick.get('race_time', '').split('T')[1][:5] if 'T' in pick.get('race_time', '') else 'Unknown'
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    score = float(pick.get('combined_confidence', 0))
    outcome = pick.get('outcome', 'PENDING')
    odds = pick.get('odds', 'N/A')
    
    status = ''
    if outcome == 'WON':
        status = ' 🏆 WON'
    elif outcome == 'PLACED':
        status = ' ✓ PLACED'
    elif outcome == 'LOST':
        status = ' ✗ LOST'
    else:
        # Check if race has started
        race_time_str = pick.get('race_time', '')
        if race_time_str:
            try:
                race_dt = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
                now_aware = datetime.now(race_dt.tzinfo)
                if race_dt < now_aware:
                    status = ' ⏳ AWAITING RESULT'
                else:
                    status = ' 🎯 UPCOMING'
            except:
                status = ''
        else:
            status = ''
    
    tier = 'EXCEPTIONAL' if score >= 95 else 'EXCELLENT' if score >= 85 else 'VERY GOOD' if score >= 75 else 'GOOD'
    
    print(f"{time} {course:<15} {horse:<30} {score:5.0f}/100 ({tier}){status}")

# Show top scorers from upcoming races
print(f"\n{'='*80}")
print(f"TOP SCORERS FROM UPCOMING RACES (85+)")
print(f"{'='*80}\n")

now = datetime.now().astimezone()
upcoming = [i for i in items 
            if '2026-02-04' in i.get('race_time', '') 
            and i.get('race_time')]

upcoming_filtered = []
for i in upcoming:
    try:
        race_dt = datetime.fromisoformat(i.get('race_time', '').replace('Z', '+00:00'))
        if race_dt > now:
            upcoming_filtered.append(i)
    except:
        pass

upcoming = upcoming_filtered

# Group by race and get top scorer
races = {}
for item in upcoming:
    race_key = f"{item.get('course')}_{item.get('race_time')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(item)

high_scorers = []
for race_key, horses in races.items():
    top = max(horses, key=lambda x: float(x.get('combined_confidence', 0)))
    score = float(top.get('combined_confidence', 0))
    
    if score >= 85:
        high_scorers.append(top)

if high_scorers:
    for pick in sorted(high_scorers, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
        time = pick.get('race_time', '').split('T')[1][:5] if 'T' in pick.get('race_time', '') else 'Unknown'
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', 'Unknown')
        score = float(pick.get('combined_confidence', 0))
        odds = pick.get('odds', 'N/A')
        is_ui = pick.get('show_in_ui', False)
        
        ui_status = ' [ALREADY UI PICK]' if is_ui else ' [SHOULD BE UI PICK]'
        
        print(f"{time} {course:<15} {horse:<30} {score:5.0f}/100 @{odds}{ui_status}")
else:
    print("No horses scored 85+ in upcoming races")
    
    # Show top 10 scorers
    print(f"\nTop 10 scorers in upcoming races:")
    all_upcoming = []
    for race_key, horses in races.items():
        all_upcoming.extend(horses)
    
    all_upcoming.sort(key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)
    
    for i, pick in enumerate(all_upcoming[:10], 1):
        time = pick.get('race_time', '').split('T')[1][:5] if 'T' in pick.get('race_time', '') else 'Unknown'
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', 'Unknown')
        score = float(pick.get('combined_confidence', 0))
        odds = pick.get('odds', 'N/A')
        
        print(f"{i:2}. {time} {course:<15} {horse:<30} {score:5.0f}/100 @{odds}")

print(f"\n{'='*80}\n")
