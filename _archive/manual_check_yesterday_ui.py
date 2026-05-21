"""
Manually fetch results for yesterday's UI picks
Uses alternate date for Racing Post (2025 instead of 2026)
"""
import boto3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f'Fetching results for UI picks on {yesterday}')
print('=' * 80)

# Get UI picks without results
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

items = response.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui') == True]
pending = [i for i in ui_picks if not i.get('outcome') or i.get('outcome') == 'pending']

print(f'UI picks needing results: {len(pending)}')
print()

# Try with 2025 date for Racing Post
rp_date = yesterday.replace('2026-', '2025-')

for pick in pending:
    horse = pick.get('horse', '')
    course = pick.get('course', '')
    race_time = pick.get('race_time', '')
    
    print(f'Need result for: {horse} @ {course} at {race_time}')
    
    # Extract course and race time for Racing Post
    # Format race_time: "2026-02-24T14:50:00.000Z" -> "1450"
    if 'T' in str(race_time):
        time_part = str(race_time).split('T')[1][:5].replace(':', '')
    else:
        time_part = 'unknown'
    
    course_lower = course.lower().replace(' ', '-')
    
    # Try to fetch specific race from Racing Post
    url = f"https://www.racingpost.com/results/{rp_date}/{course_lower}/{time_part}"
    
    print(f'  Trying: {url}')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            # Look for winner
            # This is a simplified check - might need actual HTML structure analysis
            if horse.lower() in resp.text.lower():
                print(f'  ✓ Found race page, contains {horse}')
            else:
                print(f'  ⊘ Race page found but no mention of {horse}')
        else:
            print(f'  ⚠ HTTP {resp.status_code}')
    except Exception as e:
        print(f'  ✗ Error: {str(e)[:50]}')
    
    print()

print('=' * 80)
print('Manual verification needed for these results')
print('Check Racing Post website directly for accurate results')
