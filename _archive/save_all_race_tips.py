"""
Save Top Tips for All Races
Generates predictions for every race without showing on UI
Used for end-of-day performance reporting
"""
import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
bets_table = dynamodb.Table('SureBetBets')

def save_all_tips():
    """Save top tip for each race to file"""
    
    # Get all analyzed horses
    response = bets_table.scan()
    items = response.get('Items', [])
    
    # Group by race
    races = {}
    for item in items:
        course = item.get('course', '')
        race_time = item.get('race_time', '')
        
        if course and race_time:
            race_key = f"{course}_{race_time}"
            
            if race_key not in races:
                races[race_key] = {
                    'course': course,
                    'time': race_time,
                    'horses': []
                }
            
            races[race_key]['horses'].append({
                'name': item.get('horse', 'Unknown'),
                'odds': float(item.get('odds', 0)),
                'score': float(item.get('combined_confidence', 0)),
                'grade': item.get('confidence_grade', ''),
                'breakdown': {k: int(item.get(k, 0)) for k in ['sweet_spot', 'optimal_odds', 'recent_win', 
                                                                 'total_wins', 'consistency', 'course_bonus', 
                                                                 'database_history', 'going_suitability', 
                                                                 'track_pattern_bonus'] if k in item}
            })
    
    # Get top tip for each race
    tips = []
    
    for race_key, race_data in sorted(races.items()):
        horses = race_data['horses']
        
        if horses:
            # Sort by score
            sorted_horses = sorted(horses, key=lambda x: x['score'], reverse=True)
            top = sorted_horses[0]
            
            tips.append({
                'course': race_data['course'],
                'time': race_data['time'],
                'tip': top['name'],
                'odds': top['odds'],
                'score': top['score'],
                'grade': top['grade'],
                'runners': len(horses),
                'top_5': [{'name': h['name'], 'score': h['score'], 'odds': h['odds']} 
                         for h in sorted_horses[:5]],
                'breakdown': top['breakdown']
            })
    
    # Save to file
    today = datetime.now().strftime('%Y-%m-%d')
    filename = f'daily_tips_{today}.json'
    
    output = {
        'date': today,
        'generated_at': datetime.now().isoformat(),
        'total_races': len(tips),
        'tips': tips
    }
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved tips for {len(tips)} races to {filename}")
    print(f"\nSummary:")
    for tip in tips:
        print(f"  {tip['time']} {tip['course']:<15} → {tip['tip']:<25} {tip['score']:.0f}/100 @{tip['odds']}")
    
    return filename, tips

if __name__ == '__main__':
    save_all_tips()
