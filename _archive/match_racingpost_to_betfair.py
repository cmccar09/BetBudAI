#!/usr/bin/env python3
"""
MATCH RACINGPOST DATA WITH BETFAIR PICKS
Matches Racing Post race data/results with Betfair-based picks for learning
"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import re

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
racingpost_table = dynamodb.Table('RacingPostRaces')
bets_table = dynamodb.Table('SureBetBets')

def normalize_course_name(name):
    """Normalize course names for matching"""
    name = name.lower().strip()
    # Remove common suffixes
    name = name.replace('-aw', '').replace(' aw', '')
    name = name.replace('(aw)', '').replace('(a.w.)', '')
    name = name.replace(' ', '').replace('-', '')
    return name

def normalize_horse_name(name):
    """Normalize horse names for matching"""
    name = name.lower().strip()
    # Remove extra spaces
    name = ' '.join(name.split())
    return name

def parse_time(time_str):
    """Parse race time to comparable format"""
    if not time_str or time_str == 'unknown':
        return None
    
    # Handle formats like "14:35", "2:35pm", etc.
    time_str = time_str.lower().replace('pm', '').replace('am', '').strip()
    
    try:
        if ':' in time_str:
            return time_str.split(':')[0].zfill(2) + time_str.split(':')[1][:2]
        return None
    except:
        return None

def match_and_update_picks(date_str=None):
    """Match Racing Post data with Betfair picks and update outcomes"""
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*80}")
    print(f"MATCHING RACINGPOST DATA WITH BETFAIR PICKS")
    print(f"{'='*80}")
    print(f"Date: {date_str}\n")
    
    # Get Racing Post races for this date
    print("1. Fetching Racing Post data...")
    rp_response = racingpost_table.query(
        IndexName='DateIndex',
        KeyConditionExpression='raceDate = :date',
        ExpressionAttributeValues={':date': date_str}
    )
    
    rp_races = rp_response.get('Items', [])
    
    # Filter to only races with results
    rp_races_with_results = [r for r in rp_races if r.get('hasResults')]
    
    print(f"   Found {len(rp_races)} Racing Post races")
    print(f"   {len(rp_races_with_results)} have results\n")
    
    if not rp_races_with_results:
        print("No results available yet")
        return 0
    
    # Get Betfair picks for this date
    print("2. Fetching Betfair picks...")
    bets_response = bets_table.scan(
        FilterExpression='contains(#raceId, :date)',
        ExpressionAttributeNames={'#raceId': 'raceId'},
        ExpressionAttributeValues={':date': date_str.replace('-', '')}
    )
    
    picks = bets_response.get('Items', [])
    print(f"   Found {len(picks)} Betfair picks\n")
    
    if not picks:
        print("No picks to match")
        return 0
    
    # Match picks with results
    print("3. Matching picks with results...")
    matched = 0
    updated = 0
    
    for pick in picks:
        try:
            # Extract pick details
            pick_race_id = pick.get('raceId', '')
            pick_horse = normalize_horse_name(pick.get('horseName', ''))
            
            # Try to extract course and time from raceId
            # Format examples: "carlisle_20260203_1330", "8_1330_20260203"
            pick_course = None
            pick_time = None
            
            # Try pattern: course_date_time
            match = re.match(r'([a-z-]+)_\d{8}_(\d{4})', pick_race_id.lower())
            if match:
                pick_course = normalize_course_name(match.group(1))
                pick_time = match.group(2)
            else:
                # Try pattern: id_time_date
                match = re.match(r'\d+_(\d{4})_\d{8}', pick_race_id)
                if match:
                    pick_time = match.group(1)
            
            # Try to match with Racing Post races
            best_match = None
            best_match_score = 0
            
            for rp_race in rp_races_with_results:
                score = 0
                
                rp_course = normalize_course_name(rp_race.get('courseName', ''))
                rp_time = parse_time(rp_race.get('raceTime', ''))
                
                # Course match
                if pick_course and rp_course:
                    if pick_course == rp_course:
                        score += 10
                    elif pick_course in rp_course or rp_course in pick_course:
                        score += 5
                
                # Time match
                if pick_time and rp_time:
                    if pick_time == rp_time:
                        score += 10
                    elif abs(int(pick_time) - int(rp_time)) <= 5:  # Within 5 minutes
                        score += 5
                
                # Horse name match in runners
                for runner in rp_race.get('runners', []):
                    rp_horse = normalize_horse_name(runner.get('horse_name', ''))
                    
                    if pick_horse == rp_horse:
                        score += 20  # Exact match
                        
                        if score > best_match_score:
                            best_match_score = score
                            best_match = {
                                'race': rp_race,
                                'runner': runner
                            }
                        break
            
            # If we have a good match, update the pick
            if best_match and best_match_score >= 20:  # At least horse name must match
                matched += 1
                
                runner = best_match['runner']
                position = runner.get('position')
                
                # Determine outcome
                outcome = 'won' if position == '1' else 'lost'
                
                # Calculate profit/loss
                odds = pick.get('odds', 0)
                stake = pick.get('stake', 10)
                
                if outcome == 'won':
                    profit_loss = (Decimal(str(odds)) - 1) * Decimal(str(stake))
                else:
                    profit_loss = -Decimal(str(stake))
                
                # Update in database
                try:
                    bets_table.update_item(
                        Key={
                            'raceId': pick['raceId'],
                            'timestamp': pick['timestamp']
                        },
                        UpdateExpression='SET outcome = :outcome, actual_position = :pos, '
                                       'profit_loss = :profit, result_source = :source, '
                                       'result_updated = :updated',
                        ExpressionAttributeValues={
                            ':outcome': outcome,
                            ':pos': position,
                            ':profit': profit_loss,
                            ':source': 'racingpost',
                            ':updated': datetime.now().isoformat()
                        }
                    )
                    
                    updated += 1
                    
                    status = "WIN" if outcome == 'won' else "LOSS"
                    print(f"   ✓ {pick.get('horseName', 'Unknown'):20} pos {position} = {status} ({profit_loss:+.2f} EUR)")
                
                except Exception as e:
                    print(f"   ✗ Error updating {pick.get('horseName')}: {e}")
        
        except Exception as e:
            print(f"   ✗ Error processing pick: {e}")
            continue
    
    print(f"\n{'='*80}")
    print(f"MATCHING COMPLETE")
    print(f"{'='*80}")
    print(f"Total picks: {len(picks)}")
    print(f"Matched: {matched}")
    print(f"Updated: {updated}")
    print(f"{'='*80}\n")
    
    return updated

def main():
    """Main execution"""
    import sys
    
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        updated = match_and_update_picks(date_str)
        
        # Log result
        with open('matching_log.txt', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Matched and updated {updated} picks\n")
        
        return 0
    
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
