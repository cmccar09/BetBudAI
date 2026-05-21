"""
Remove invalid UI picks that don't meet new validation requirements
"""
import boto3
from race_analysis_validator import validate_race_analysis

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("REMOVING INVALID UI PICKS - Feb 3, 2026")
print("="*80)

# Get all picks marked for UI display
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :show',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':show': True
    }
)

ui_picks = response.get('Items', [])

if not ui_picks:
    print("\nNo picks currently on UI")
else:
    print(f"\nFound {len(ui_picks)} picks on UI\n")
    
    # Group by race to validate
    races = {}
    for pick in ui_picks:
        race_key = f"{pick.get('course')} {pick.get('race_time', '')}"
        if race_key not in races:
            races[race_key] = {
                'course': pick.get('course'),
                'race_time': pick.get('race_time', ''),
                'picks': []
            }
        races[race_key]['picks'].append(pick)
    
    removed_count = 0
    
    for race_key, race_data in races.items():
        course = race_data['course']
        race_time = race_data['race_time']
        
        # Extract time part (HH:MM)
        if 'T' in race_time:
            time_part = race_time.split('T')[1].split(':')[0:2]
            time_str = ':'.join(time_part)
        else:
            time_str = race_time
        
        # Validate race completion
        is_valid, num_analyzed, total_horses, issues = validate_race_analysis(
            course, 
            time_str,
            '2026-02-03'
        )
        
        print(f"\n{race_key}")
        print(f"  Analysis: {num_analyzed}/{total_horses} ({num_analyzed/total_horses*100 if total_horses > 0 else 0:.0f}%)")
        print(f"  Valid: {is_valid}")
        
        if not is_valid:
            print(f"  Issues: {', '.join(issues)}")
            
            # Remove each pick from this race
            for pick in race_data['picks']:
                horse = pick.get('horse', '')
                bet_id = pick.get('bet_id', '')
                
                try:
                    # Update to hide from UI
                    table.update_item(
                        Key={
                            'bet_date': '2026-02-03',
                            'bet_id': bet_id
                        },
                        UpdateExpression='SET show_in_ui = :false',
                        ExpressionAttributeValues={
                            ':false': False
                        }
                    )
                    print(f"  [REMOVED] {horse} (incomplete race analysis)")
                    removed_count += 1
                except Exception as e:
                    print(f"  [ERROR] Failed to remove {horse}: {str(e)}")
        else:
            print(f"  [KEEPING] Race meets validation requirements")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Picks removed from UI: {removed_count}")
    print(f"Reason: Races with <75% analysis completion")
    print("\nUI now shows only validated picks (if any)")
