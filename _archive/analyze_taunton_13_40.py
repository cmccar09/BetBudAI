"""
Analyze Taunton 13:40 race result (Feb 3, 2026)
Winner: Talk To The Man (11/4 = 3.75)
2nd: Kings Champion (10/11 = 1.91 favorite)
"""
import json
import boto3
from datetime import datetime

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 80)
print("TAUNTON 13:40 RACE ANALYSIS - Feb 3, 2026")
print("=" * 80)
print("\nActual Result:")
print("  1st: Talk To The Man (11/4 = 3.75 odds)")
print("  2nd: Kings Champion (10/11 = 1.91 odds - FAVORITE)")
print()

# First, check response_horses.json for Taunton data
print("\n" + "=" * 80)
print("CHECKING RESPONSE_HORSES.JSON")
print("=" * 80)

try:
    with open('response_horses.json') as f:
        data = json.load(f)
    
    races = data.get('races', [])
    print(f"Total races in file: {len(races)}")
    
    # Find all Taunton races
    taunton_races = []
    for race in races:
        if race.get('venue') == 'Taunton' or race.get('course') == 'Taunton':
            start_time = race.get('start_time', '')
            market_name = race.get('market_name', '')
            runners = race.get('runners', [])
            taunton_races.append({
                'start_time': start_time,
                'market_name': market_name,
                'num_runners': len(runners),
                'race': race
            })
    
    print(f"\nTaunton races found: {len(taunton_races)}")
    
    if taunton_races:
        print("\nAll Taunton races:")
        for tr in taunton_races:
            print(f"  {tr['start_time']} - {tr['market_name']} ({tr['num_runners']} runners)")
        
        # Find the 13:40 race (might be stored as 13:40 or 14:40 depending on timezone)
        target_race = None
        for tr in taunton_races:
            st = tr['start_time']
            # Check for 13:40 or 14:40 (timezone differences)
            if 'T13:40' in st or 'T14:40' in st:
                target_race = tr['race']
                print(f"\n✓ Found Taunton 13:40 race: {tr['market_name']}")
                break
        
        if not target_race and taunton_races:
            # Use first Taunton race if time doesn't match
            print("\n⚠ Could not find exact 13:40 time, using first Taunton race")
            target_race = taunton_races[0]['race']
        
        if target_race:
            runners = target_race.get('runners', [])
            print(f"\nRunners in race: {len(runners)}")
            
            # Find our key horses
            talk_to_the_man = None
            kings_champion = None
            
            print("\nAll runners:")
            for runner in sorted(runners, key=lambda x: x.get('odds', 999)):
                name = runner.get('name', '')
                odds = runner.get('odds', 0)
                form = runner.get('form', '')
                
                if 'Talk To The Man' in name:
                    talk_to_the_man = runner
                    print(f"  ★ {name:<30} Odds: {odds:6.2f}  Form: {form}")
                elif 'Kings Champion' in name:
                    kings_champion = runner
                    print(f"  ★ {name:<30} Odds: {odds:6.2f}  Form: {form}")
                else:
                    print(f"    {name:<30} Odds: {odds:6.2f}  Form: {form}")
            
            # Analyze our logic
            print("\n" + "=" * 80)
            print("SCORING ANALYSIS")
            print("=" * 80)
            
            if talk_to_the_man:
                print("\n1. TALK TO THE MAN (WINNER)")
                print(f"   Odds: {talk_to_the_man.get('odds')} (11/4 = 3.75)")
                print(f"   Form: {talk_to_the_man.get('form')}")
                print(f"   Trainer: {talk_to_the_man.get('trainer')}")
                
                odds = talk_to_the_man.get('odds', 0)
                form = talk_to_the_man.get('form', '')
                
                # Check if in sweet spot (3-9)
                if 3.0 <= odds <= 9.0:
                    print("   ✓ IN SWEET SPOT (3-9 odds)")
                else:
                    print(f"   ✗ Outside sweet spot (odds {odds})")
                
                # Check form
                form_parts = form.split('-') if form else []
                recent_wins = sum(1 for f in form_parts[:3] if f == '1')
                recent_places = sum(1 for f in form_parts[:3] if f in ['2', '3'])
                
                print(f"   Recent form: {recent_wins} wins, {recent_places} places in last 3 runs")
                
                # Would our logic pick it?
                if 3.0 <= odds <= 9.0 and recent_wins >= 1:
                    print("   ✓✓ SHOULD BE PICKED - Sweet spot with recent win")
                elif recent_wins >= 1:
                    print("   ~ Might be picked - Has recent win but odds outside sweet spot")
                else:
                    print("   ? Marginal - In sweet spot but no recent wins")
            
            if kings_champion:
                print("\n2. KINGS CHAMPION (2ND - FAVORITE)")
                print(f"   Odds: {kings_champion.get('odds')} (10/11 = 1.91)")
                print(f"   Form: {kings_champion.get('form')}")
                print(f"   Trainer: {kings_champion.get('trainer')}")
                
                odds = kings_champion.get('odds', 0)
                form = kings_champion.get('form', '')
                
                # Check if quality favorite
                if 1.5 <= odds <= 3.0:
                    print("   ✓ IN QUALITY FAVORITE RANGE (1.5-3.0)")
                    
                    form_parts = form.split('-') if form else []
                    if len(form_parts) > 0 and form_parts[0] == '1':
                        print("   ✓ LTO WINNER - Gets +20 bonus")
                        print("   ✓✓ SHOULD BE PICKED AS QUALITY FAVORITE")
                    else:
                        wins = sum(1 for f in form_parts if f == '1')
                        places = sum(1 for f in form_parts if f in ['2', '3'])
                        print(f"   Form analysis: {wins} wins, {places} places")
                        
                        if wins >= 2 and places >= 3:
                            print("   ✓ Strong record - Gets +20 bonus")
                            print("   ✓✓ SHOULD BE PICKED AS QUALITY FAVORITE")
                        else:
                            print("   ✗ Form not strong enough for quality favorite bonus")
                else:
                    print(f"   ✗ Not in quality favorite range (odds {odds})")
    
    else:
        print("\n⚠ No Taunton races found in response_horses.json")

except Exception as e:
    print(f"Error reading response_horses.json: {e}")

# Now check database (using eu-west-1)
print("\n" + "=" * 80)
print("CHECKING DATABASE (eu-west-1)")
print("=" * 80)

try:
    # Query for today's data
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='course = :course',
        ExpressionAttributeValues={
            ':date': '2026-02-03',
            ':course': 'Taunton'
        }
    )
    
    items = response.get('Items', [])
    print(f"\nTaunton items in database: {len(items)}")
    
    if items:
        # Find 13:40 race
        race_1340 = [item for item in items if '13:40' in item.get('race_time', '')]
        
        print(f"Taunton 13:40 horses in database: {len(race_1340)}")
        
        if race_1340:
            print("\nDatabase horses for Taunton 13:40:")
            for item in sorted(race_1340, key=lambda x: x.get('confidence_score', 0), reverse=True):
                horse = item.get('horse', '')
                score = item.get('confidence_score', 0)
                odds = item.get('odds', 0)
                form = item.get('form', '')
                
                marker = "★" if 'Talk To The Man' in horse or 'Kings Champion' in horse else " "
                print(f"  {marker} {horse:<30} Score: {score:3}/100  Odds: {odds:6.2f}  Form: {form[:15]}")

except Exception as e:
    print(f"Database error: {e}")

print("\n" + "=" * 80)
