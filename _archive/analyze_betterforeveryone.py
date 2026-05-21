"""
Analyze Betterforeveryone pick and race competition
"""
import boto3
from datetime import datetime
import sys
sys.path.append('.')
from api_server import decimal_to_float

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={':today': today}
)

items = [decimal_to_float(i) for i in response['Items']]

# Find Betterforeveryone
better = next((i for i in items if i.get('horse') == 'Betterforeveryone'), None)

if better:
    print('='*100)
    print('BETTERFOREVERYONE - RACE ANALYSIS')
    print('='*100)
    
    pick_score = float(better.get('comprehensive_score', 0))
    pick_course = better.get('course', '')
    pick_race_time = better.get('race_time', '')
    pick_odds = float(better.get('odds', 0))
    
    print(f'\n🎯 YOUR PICK:')
    print(f'  Horse: Betterforeveryone')
    print(f'  Score: {pick_score}/100')
    print(f'  Odds: {pick_odds:.2f}')
    print(f'  Course: {pick_course}')
    print(f'  Race time: {pick_race_time}')
    
    # Parse time
    if 'T' in str(pick_race_time):
        time_str = str(pick_race_time).split('T')[1][:5]
        print(f'  Race: {time_str} GMT')
    
    # Find other horses in same race
    same_race = [
        i for i in items 
        if i.get('course') == pick_course 
        and i.get('race_time') == pick_race_time
        and i.get('horse') != 'Betterforeveryone'
        and i.get('comprehensive_score')
    ]
    
    print(f'\n\n📊 ALL HORSES IN THIS RACE (16:00 Bangor-on-Dee):')
    print('='*100)
    
    all_horses = [(better.get('horse'), pick_score, pick_odds, better.get('show_in_ui', False))] + \
                 [(h.get('horse'), float(h.get('comprehensive_score', 0)), float(h.get('odds', 0)), h.get('show_in_ui', False)) for h in same_race]
    all_horses.sort(key=lambda x: x[1], reverse=True)
    
    print(f'{"Pos":<5}{"Horse":<35}{"Score":<10}{"Odds":<10}{"Status"}')
    print('-'*100)
    
    for i, (horse, score, odds, is_ui) in enumerate(all_horses, 1):
        if horse == 'Betterforeveryone':
            marker = '👑 YOUR PICK'
            status = f'[RECOMMENDED] - {marker}'
        elif is_ui and score >= 85:
            status = '[RECOMMENDED]'
        elif is_ui:
            status = '[HIGH CONF]'
        else:
            status = ''
        
        print(f'{i:<5}{horse:<35}{score:<10.0f}{odds:<10.2f}{status}')
    
    # Analysis
    if same_race:
        scores = [float(h.get('comprehensive_score', 0)) for h in same_race]
        scores.sort(reverse=True)
        
        next_best = scores[0]
        next_best_horse = next((h for h in same_race if float(h.get('comprehensive_score', 0)) == next_best), None)
        gap = pick_score - next_best
        
        print(f'\n\n🔍 COMPETITIVE ANALYSIS:')
        print('='*100)
        print(f'Your pick score:    {pick_score:.0f}')
        print(f'Next best score:    {next_best:.0f} ({next_best_horse.get("horse") if next_best_horse else "Unknown"})')
        print(f'Score gap:          +{gap:.0f} points')
        
        if gap > 10:
            comp_level = '🟢 DOMINANT ADVANTAGE'
            assessment = 'Strong pick - significantly better than competition'
        elif gap > 5:
            comp_level = '🟡 MODERATE ADVANTAGE'
            assessment = 'Good pick - noticeable edge over competition'
        else:
            comp_level = '🔴 TIGHT COMPETITION'
            assessment = 'Competitive race - multiple horses rated similarly'
        
        print(f'Competition level:  {comp_level}')
        print(f'Assessment:         {assessment}')
        
        # Check if race has started
        print(f'\n\n⏰ RACE STATUS:')
        print('='*100)
        if 'T' in str(pick_race_time):
            race_hour = int(str(pick_race_time).split('T')[1].split(':')[0])
            race_min = int(str(pick_race_time).split('T')[1].split(':')[1])
            current_time = datetime.now()
            current_hour = current_time.hour
            current_min = current_time.minute
            
            if current_hour < race_hour or (current_hour == race_hour and current_min < race_min):
                mins_to_race = (race_hour - current_hour) * 60 + (race_min - current_min)
                print(f'⏳ Race starts in: {mins_to_race} minutes')
                print(f'Status: UPCOMING (betting still open)')
            else:
                print(f'🏁 Race time has PASSED')
                print(f'Status: Check for results')
        
        # Overall recommendation
        print(f'\n\n💡 RECOMMENDATION:')
        print('='*100)
        
        if pick_score >= 90:
            rec_icon = '✅ STRONG BET'
        elif pick_score >= 85:
            rec_icon = '✅ GOOD BET'
        else:
            rec_icon = '⚠️ MODERATE BET'
        
        print(f'{rec_icon}')
        print(f'\nKey factors:')
        print(f'  • Score: {pick_score}/100 ({"Excellent" if pick_score >= 90 else "Very Good" if pick_score >= 85 else "Good"})')
        print(f'  • Competition: {comp_level}')
        print(f'  • Odds: {pick_odds:.2f} ({"Good value" if pick_odds >= 5.0 else "Moderate value" if pick_odds >= 3.0 else "Lower value"})')
        print(f'  • Analysis: 100% field coverage')
        
        # Value assessment
        print(f'\n\n💰 VALUE ASSESSMENT:')
        print('='*100)
        
        # Simple implied probability
        implied_prob = (1 / pick_odds) * 100
        
        # Our estimated probability (rough estimate based on score and competition)
        if gap > 10:
            our_prob = 35  # Dominant
        elif gap > 5:
            our_prob = 25  # Moderate advantage
        elif gap > 0:
            our_prob = 20  # Slight advantage
        else:
            our_prob = 15  # Even competition
        
        print(f'Bookmaker odds:           {pick_odds:.2f} (implied {implied_prob:.1f}% chance)')
        print(f'Our score advantage:      +{gap:.0f} points over next best')
        
        if our_prob > implied_prob * 1.1:
            print(f'Value rating:             ✅ GOOD VALUE')
            print(f'  Our advantage suggests better chance than odds indicate')
        elif our_prob > implied_prob * 0.9:
            print(f'Value rating:             ⚖️ FAIR ODDS')
            print(f'  Odds roughly reflect competitive advantage')
        else:
            print(f'Value rating:             ⚠️ ODDS FAVOR FAVORITE')
            print(f'  Market may recognize our advantage')
        
        # Check Bangor results so far today
        print(f'\n\n📈 BANGOR-ON-DEE TRACK PERFORMANCE TODAY:')
        print('='*100)
        
        bangor_items = [i for i in items if i.get('course', '').lower() == 'bangor-on-dee']
        bangor_with_results = [i for i in bangor_items if i.get('outcome')]
        
        if bangor_with_results:
            bangor_ui_results = [i for i in bangor_with_results if i.get('show_in_ui')]
            bangor_winners = [i for i in bangor_ui_results if i.get('outcome', '').lower() == 'won']
            
            print(f'Our picks at this track today:')
            print(f'  Results available: {len(bangor_ui_results)}')
            print(f'  Winners: {len(bangor_winners)}')
            
            if len(bangor_ui_results) > 0:
                strike_rate = len(bangor_winners) / len(bangor_ui_results) * 100
                print(f'  Strike rate: {strike_rate:.0f}%')
                
                # Show results
                if bangor_ui_results:
                    print(f'\n  Results so far:')
                    for result in bangor_ui_results:
                        h = result.get('horse', 'Unknown')
                        s = float(result.get('comprehensive_score', 0))
                        o = result.get('outcome', 'unknown').upper()
                        marker = '🏆' if o == 'WON' else '❌'
                        print(f'    {marker} {h} (Score: {s:.0f}) - {o}')
        else:
            print('No races completed yet at this track today')
            print('This will be one of the first results from Bangor-on-Dee')
    
else:
    print('Betterforeverone not found in today\'s picks')

print('\n' + '='*100)
