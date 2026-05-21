import boto3
from datetime import datetime
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-02'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']

# Group by course
by_course = defaultdict(list)
for item in items:
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    by_course[course].append({
        'time': race_time,
        'horse': item.get('horse', 'Unknown'),
        'outcome': item.get('outcome', 'pending'),
        'odds': item.get('odds', 0),
        'is_learning': item.get('is_learning_pick', False),
        'analysis_type': item.get('analysis_type'),
        'learning_type': item.get('learning_type'),
        'bet_id': item.get('bet_id', '')
    })

print('\n' + '='*80)
print('TODAY\'S RACES BY COURSE')
print('='*80)

for course in sorted(by_course.keys()):
    races = by_course[course]
    print(f'\n{course.upper()} ({len(races)} items)')
    print('-'*80)
    
    # Group by race time
    by_time = defaultdict(list)
    for race in races:
        by_time[race['time']].append(race)
    
    for time in sorted(by_time.keys()):
        items_at_time = by_time[time]
        print(f'\n  {time}:')
        for item in items_at_time:
            item_type = 'ANALYSIS' if item['analysis_type'] else ('LEARNING' if item['learning_type'] else ('TRAINING' if item['is_learning'] else 'PICK'))
            print(f'    [{item_type}] {item["horse"]} @ {item["odds"]:.1f} - {item["outcome"]}')

print('\n' + '='*80)
print('WOLVERHAMPTON RACES SUMMARY')
print('='*80)
if 'Wolverhampton' in by_course:
    wolv_times = sorted(set([r['time'] for r in by_course['Wolverhampton']]))
    print(f'Total race times: {len(wolv_times)}')
    print(f'Times: {", ".join(wolv_times)}')
    
    print('\n' + '='*80)
    print('WOLVERHAMPTON DETAILED BREAKDOWN')
    print('='*80)
    for time in wolv_times:
        items = [r for r in by_course['Wolverhampton'] if r['time'] == time]
        picks = [r for r in items if not r['analysis_type'] and not r['learning_type'] and not r['is_learning']]
        learnings = [r for r in items if r['learning_type']]
        analyses = [r for r in items if r['analysis_type']]
        
        print(f'\n{time}:')
        print(f'  Picks: {len(picks)}')
        print(f'  Learnings: {len(learnings)}')
        print(f'  Analyses: {len(analyses)}')
        
        if learnings:
            print(f'  ✓ Learning recorded')
        else:
            print(f'  ✗ NO LEARNING RECORDED')
else:
    print('No Wolverhampton races found in database')

# Check what analysis scripts exist
import os
import glob

print('\n' + '='*80)
print('WOLVERHAMPTON ANALYSIS SCRIPTS')
print('='*80)

scripts = glob.glob('analyze_wolverhampton*.py')
if scripts:
    for script in sorted(scripts):
        print(f'  ✓ {script}')
else:
    print('  No Wolverhampton analysis scripts found')

print('\n' + '='*80)
print('ALL RACE RESULT ANALYSIS SCRIPTS')
print('='*80)

all_scripts = glob.glob('analyze_*_result.py') + glob.glob('analyze_*_handicap.py')
if all_scripts:
    by_course_scripts = defaultdict(list)
    for script in sorted(all_scripts):
        # Extract course name
        parts = script.replace('.py', '').split('_')
        if len(parts) >= 2:
            course = parts[1]
            by_course_scripts[course].append(script)
    
    for course in sorted(by_course_scripts.keys()):
        scripts = by_course_scripts[course]
        print(f'\n{course.upper()}: {len(scripts)} scripts')
        for script in sorted(scripts):
            print(f'  - {script}')
else:
    print('  No analysis scripts found')
