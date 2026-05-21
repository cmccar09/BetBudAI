"""
Complete Race Learning System
Stores ALL races, tracks winners, compares with our analysis, and learns
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')


def store_all_races_for_learning():
    """Store ALL horses from ALL UK/Ireland races for later comparison"""
    
    print("="*80)
    print("STORING ALL RACES FOR LEARNING")
    print("="*80)
    print()
    
    try:
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No race data found - run betfair_odds_fetcher.py first")
        return
    
    races = data.get('races', [])
    today = datetime.now().strftime('%Y-%m-%d')
    
    stored_count = 0
    
    for race in races:
        market_id = race.get('marketId', '')
        venue = race.get('venue', 'Unknown')
        start_time = race.get('start_time', '')
        runners = race.get('runners', [])
        
        # Check if already stored
        existing = table.query(
            KeyConditionExpression='bet_date = :date',
            FilterExpression='market_id = :mid AND is_learning_pick = :learning',
            ExpressionAttributeValues={
                ':date': today,
                ':mid': market_id,
                ':learning': True
            }
        )
        
        if existing.get('Items'):
            continue  # Already stored
        
        print(f"Storing: {venue} {start_time} ({len(runners)} runners)")
        
        # Store each horse for learning
        for runner in runners:
            horse_name = runner.get('name', runner.get('runnerName', 'Unknown'))
            selection_id = runner.get('selectionId', 0)
            odds = float(runner.get('odds', 0))
            
            item = {
                'bet_id': f'{start_time}_{venue}_{horse_name}'.replace(' ', '_').replace(':', ''),
                'bet_date': today,
                'horse': horse_name,
                'course': venue,
                'race_time': start_time,
                'odds': Decimal(str(odds)),
                'selection_id': str(selection_id),
                'market_id': market_id,
                'sport': 'Horse Racing',
                
                # Learning metadata
                'is_learning_pick': True,
                'show_in_ui': False,
                'analysis_type': 'ALL_HORSES_LEARNING',
                
                # Store form data
                'form': str(runner.get('form', '')),
                'trainer': str(runner.get('trainer', {}).get('name', '') if isinstance(runner.get('trainer'), dict) else runner.get('trainer', '')),
                'jockey': str(runner.get('jockey', {}).get('name', '') if isinstance(runner.get('jockey'), dict) else runner.get('jockey', '')),
                
                # Metadata
                'created_at': datetime.now().isoformat(),
                'purpose': 'LEARNING_DATA'
            }
            
            table.put_item(Item=item)
            stored_count += 1
    
    print()
    print(f"✓ Stored {stored_count} horses for learning")
    print(f"✓ These will be compared with actual winners later")
    print()


def check_winners_and_learn():
    """Fetch actual winners and compare with our stored data"""
    
    print("="*80)
    print("CHECKING WINNERS AND LEARNING")
    print("="*80)
    print()
    
    # This would fetch results from Betfair
    # For now, we'll check database for items with outcomes
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get all learning picks from today
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='is_learning_pick = :learning',
        ExpressionAttributeValues={
            ':date': today,
            ':learning': True
        }
    )
    
    learning_picks = response.get('Items', [])
    
    print(f"Found {len(learning_picks)} learning records for today")
    
    # Group by race (market_id)
    races = defaultdict(list)
    for pick in learning_picks:
        market_id = pick.get('market_id', 'unknown')
        races[market_id].append(pick)
    
    print(f"Across {len(races)} different races")
    print()
    
    # Analyze completed races
    wins_analyzed = 0
    patterns_found = defaultdict(int)
    
    for market_id, horses in races.items():
        # Check if we have a winner recorded
        winners = [h for h in horses if h.get('outcome') == 'win']
        
        if not winners:
            continue  # Race not complete yet
        
        winner = winners[0]
        wins_analyzed += 1
        
        # Analyze winner characteristics
        winner_odds = float(winner.get('odds', 0))
        winner_form = winner.get('form', '')
        
        print(f"Winner: {winner.get('horse')} @ {winner_odds}")
        print(f"  Form: {winner_form}")
        
        # Pattern 1: Sweet spot winner?
        if 3.0 <= winner_odds <= 9.0:
            patterns_found['sweet_spot_wins'] += 1
            print(f"  ✓ Sweet spot win (3-9 range)")
        else:
            patterns_found['outside_sweet_spot_wins'] += 1
            print(f"  ✗ Outside sweet spot")
        
        # Pattern 2: Recent form winner?
        if '1' in winner_form[:3]:  # Win in last 3 races
            patterns_found['good_form_wins'] += 1
            print(f"  ✓ Had recent win in form")
        else:
            patterns_found['poor_form_wins'] += 1
            print(f"  ! Won without recent form")
        
        # Pattern 3: Optimal odds range?
        if 3.0 <= winner_odds <= 6.0:
            patterns_found['optimal_odds_wins'] += 1
            print(f"  ✓ Optimal odds range (3-6)")
        
        # Compare with ALL horses in the race
        horses_by_odds = sorted(horses, key=lambda x: float(x.get('odds', 999)))
        
        # Was the winner the favorite?
        favorite = horses_by_odds[0] if horses_by_odds else None
        if favorite and favorite.get('horse') == winner.get('horse'):
            patterns_found['favorite_wins'] += 1
            print(f"  ✓ Favorite won")
        else:
            print(f"  ! Upset - favorite was {favorite.get('horse') if favorite else 'unknown'} @ {favorite.get('odds') if favorite else '?'}")
        
        # What would we have picked?
        our_pick = None
        for horse in horses:
            h_odds = float(horse.get('odds', 0))
            h_form = horse.get('form', '')
            
            # Simple logic: sweet spot + recent win
            if 3.0 <= h_odds <= 9.0 and '1' in h_form[:3]:
                our_pick = horse
                break
        
        if our_pick:
            if our_pick.get('horse') == winner.get('horse'):
                patterns_found['we_picked_winner'] += 1
                print(f"  ✓✓ WE WOULD HAVE PICKED THE WINNER!")
            else:
                patterns_found['we_missed_winner'] += 1
                print(f"  ✗✗ We would have picked: {our_pick.get('horse')} @ {our_pick.get('odds')}")
        else:
            patterns_found['no_pick_in_race'] += 1
            print(f"  - No pick met our criteria in this race")
        
        print()
    
    # Summary
    print("="*80)
    print("LEARNING SUMMARY")
    print("="*80)
    
    if wins_analyzed > 0:
        print(f"\nRaces analyzed: {wins_analyzed}")
        print(f"\nPatterns found:")
        for pattern, count in patterns_found.items():
            pct = (count / wins_analyzed) * 100
            print(f"  {pattern}: {count}/{wins_analyzed} ({pct:.1f}%)")
        
        # Store learning insights
        learning_record = {
            'bet_id': f'LEARNING_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'bet_date': today,
            'learning_type': 'WINNER_ANALYSIS',
            'races_analyzed': wins_analyzed,
            'patterns': {k: Decimal(str(v)) for k, v in patterns_found.items()},
            'analyzed_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=learning_record)
        print(f"\n✓ Learning insights saved to DynamoDB")
        
        # Key learnings
        print("\n" + "="*80)
        print("KEY LEARNINGS:")
        print("="*80)
        
        sweet_spot_rate = patterns_found.get('sweet_spot_wins', 0) / wins_analyzed
        poor_form_rate = patterns_found.get('poor_form_wins', 0) / wins_analyzed
        we_picked_rate = patterns_found.get('we_picked_winner', 0) / wins_analyzed
        
        if sweet_spot_rate < 0.5:
            print(f"⚠ Sweet spot only {sweet_spot_rate*100:.0f}% effective - consider widening range")
        else:
            print(f"✓ Sweet spot {sweet_spot_rate*100:.0f}% effective - keep current range")
        
        if poor_form_rate > 0.3:
            print(f"⚠ {poor_form_rate*100:.0f}% winners had poor form - reduce form weight")
        else:
            print(f"✓ Form analysis working well ({poor_form_rate*100:.0f}% poor form wins)")
        
        if we_picked_rate > 0:
            print(f"✓ We would have picked {we_picked_rate*100:.0f}% of winners with current logic")
        
        print("="*80)
    else:
        print("No completed races found yet")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "store":
        store_all_races_for_learning()
    elif len(sys.argv) > 1 and sys.argv[1] == "learn":
        check_winners_and_learn()
    else:
        print("Usage:")
        print("  python complete_race_learning.py store  - Store all races for learning")
        print("  python complete_race_learning.py learn  - Check winners and learn")
