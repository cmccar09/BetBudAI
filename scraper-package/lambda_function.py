"""
Racing Post Results Scraper
Fetches race results from racingpost.com and updates DynamoDB
Alternative to Betfair API for getting actual race outcomes
"""

import requests
from bs4 import BeautifulSoup
import boto3
from datetime import datetime, timedelta
import re
import time

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def get_racing_post_results(date_str=None):
    """
    Fetch race results from Racing Post for a specific date
    Args:
        date_str: Date in YYYY-MM-DD format (defaults to today)
    Returns:
        List of race results with winners
    """
    if not date_str:
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Racing Post results URL format
    url = f"https://www.racingpost.com/results/{date_str}"
    
    print(f"Fetching results from: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        # If 406 and date is 2026, try 2025 (system clock issue)
        if response.status_code == 406 and '2026-' in date_str:
            fallback_date = date_str.replace('2026-', '2025-')
            print(f"⚠️ 406 error with {date_str}, trying {fallback_date}...")
            url = f"https://www.racingpost.com/results/{fallback_date}"
            response = requests.get(url, headers=headers, timeout=30)
            date_str = fallback_date
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse results - Racing Post structure
        results = []
        
        # Find all race cards/results
        race_cards = soup.find_all('div', class_=re.compile('rp-raceCard|rc-card'))
        
        if not race_cards:
            # Try alternative structure
            race_cards = soup.find_all('article', class_=re.compile('race'))
        
        print(f"Found {len(race_cards)} race cards")
        
        for card in race_cards:
            try:
                # Extract course name
                course_elem = card.find('span', class_=re.compile('course|venue')) or card.find('a', class_=re.compile('course'))
                course = course_elem.text.strip() if course_elem else None
                
                # Extract race time
                time_elem = card.find('span', class_=re.compile('time|off-time')) or card.find('time')
                race_time = time_elem.text.strip() if time_elem else None
                
                # Extract winner (usually first in results table)
                winner_elem = card.find('div', class_=re.compile('winner|first-place')) or card.find('td', class_='horse')
                if not winner_elem:
                    # Look for results table
                    results_table = card.find('table', class_=re.compile('results'))
                    if results_table:
                        first_row = results_table.find('tr', class_=re.compile('first|winner'))
                        if first_row:
                            winner_elem = first_row.find('td', class_=re.compile('horse|name'))
                
                winner = winner_elem.text.strip() if winner_elem else None
                
                # Clean up winner name (remove jockey info, etc)
                if winner:
                    winner = re.sub(r'\([^)]*\)', '', winner).strip()
                    winner = winner.split('\n')[0].strip()
                
                if course and winner:
                    results.append({
                        'course': normalize_course_name(course),
                        'race_time': race_time,
                        'winner': winner,
                        'raw_html': str(card)[:500]  # For debugging
                    })
                    print(f"  ✓ {course} {race_time}: {winner}")
            
            except Exception as e:
                print(f"  ✗ Error parsing race card: {e}")
                continue
        
        return results
    
    except Exception as e:
        print(f"Error fetching Racing Post results: {e}")
        return []

def normalize_course_name(course):
    """Normalize course names to match between sources"""
    course = course.strip().lower()
    
    # Common variations
    replacements = {
        'newmarket (july)': 'newmarket',
        'newmarket (rowley)': 'newmarket',
        'leopardstown (a.w)': 'leopardstown',
        'kempton (a.w)': 'kempton',
        'kempton park (a.w)': 'kempton park',
        'cheltenham (old)': 'cheltenham',
    }
    
    for old, new in replacements.items():
        if old in course:
            return new
    
    return course

def get_pending_bets():
    """Get bets from DynamoDB that don't have results yet"""
    try:
        response = table.scan(
            FilterExpression='attribute_not_exists(actual_result)'
        )
        
        bets = response.get('Items', [])
        print(f"Found {len(bets)} bets pending results")
        return bets
    
    except Exception as e:
        print(f"Error fetching pending bets: {e}")
        return []

def match_bet_to_result(bet, results):
    """
    Match a bet to a race result
    Returns: (matched, winner_name) or (False, None)
    """
    bet_course = bet.get('course', '').lower().strip()
    bet_time = bet.get('race_time', '')
    bet_horse = bet.get('horse', '').lower().strip()
    
    # Parse bet time to get just HH:MM
    try:
        if 'T' in bet_time:
            bet_dt = datetime.fromisoformat(bet_time.replace('Z', '+00:00'))
            bet_time_str = bet_dt.strftime('%H:%M')
        else:
            bet_time_str = bet_time
    except:
        bet_time_str = bet_time
    
    # Try to match course and approximate time
    for result in results:
        result_course = result['course'].lower().strip()
        result_time = result['race_time'] or ''
        result_winner = result['winner']
        
        # Flexible course matching
        course_match = (
            result_course == bet_course or
            result_course in bet_course or
            bet_course in result_course
        )
        
        # Flexible time matching (within 10 minutes)
        time_match = False
        if result_time and bet_time_str:
            try:
                # Extract HH:MM from result time
                time_parts = re.search(r'(\d{1,2}):(\d{2})', result_time)
                if time_parts:
                    result_time_str = f"{time_parts.group(1).zfill(2)}:{time_parts.group(2)}"
                    
                    result_dt = datetime.strptime(result_time_str, '%H:%M')
                    bet_dt = datetime.strptime(bet_time_str, '%H:%M')
                    
                    time_diff = abs((result_dt - bet_dt).total_seconds())
                    time_match = time_diff < 600  # Within 10 minutes
            except:
                pass
        
        if course_match and time_match:
            # Check if our horse won
            winner_lower = result_winner.lower().strip()
            did_win = (
                winner_lower == bet_horse or
                bet_horse in winner_lower or
                winner_lower in bet_horse
            )
            
            return True, result_winner, did_win
    
    return False, None, False

def update_bet_result(bet, winner_name, did_win):
    """Update bet in DynamoDB with race result"""
    try:
        bet_date = bet['bet_date']
        bet_id = bet['bet_id']
        
        update_data = {
            'actual_result': 'WIN' if did_win else 'LOSS',
            'race_winner': winner_name,
            'result_captured_at': datetime.utcnow().isoformat()
        }
        
        # Calculate profit/loss
        if did_win:
            stake = float(bet.get('stake', 10))
            odds = float(bet.get('odds', 0))
            profit = stake * (odds - 1)
            update_data['profit'] = profit
        else:
            update_data['profit'] = -float(bet.get('stake', 10))
        
        # Update DynamoDB
        table.update_item(
            Key={
                'bet_date': bet_date,
                'bet_id': bet_id
            },
            UpdateExpression='SET actual_result = :res, race_winner = :win, result_captured_at = :time, profit = :profit',
            ExpressionAttributeValues={
                ':res': update_data['actual_result'],
                ':win': update_data['race_winner'],
                ':time': update_data['result_captured_at'],
                ':profit': update_data['profit']
            }
        )
        
        result_symbol = "✅" if did_win else "❌"
        print(f"  {result_symbol} Updated: {bet['horse']} - {update_data['actual_result']} (Winner: {winner_name})")
        return True
    
    except Exception as e:
        print(f"  ✗ Error updating bet: {e}")
        return False

def process_results(date_str=None):
    """Main function to fetch results and update database"""
    print("\n=== Racing Post Results Scraper ===\n")
    
    # Get race results
    results = get_racing_post_results(date_str)
    
    if not results:
        print("⚠️  No results found")
        return 0
    
    print(f"\n✓ Scraped {len(results)} race results")
    
    # Get pending bets
    pending_bets = get_pending_bets()
    
    if not pending_bets:
        print("No pending bets to update")
        return 0
    
    # Match and update
    print("\nMatching bets to results...")
    updated = 0
    
    for bet in pending_bets:
        matched, winner, did_win = match_bet_to_result(bet, results)
        
        if matched:
            if update_bet_result(bet, winner, did_win):
                updated += 1
        else:
            print(f"  ⊘ No match: {bet['horse']} at {bet['course']}")
    
    print(f"\n✅ Updated {updated}/{len(pending_bets)} bets")
    return updated

def lambda_handler(event, context):
    """AWS Lambda handler"""
    # Allow specifying date in event
    date_str = event.get('date') if event else None
    
    updated = process_results(date_str)
    
    return {
        'statusCode': 200,
        'body': {
            'message': 'Results processed',
            'updated': updated
        }
    }

if __name__ == '__main__':
    # Run locally
    import sys
    
    # Allow passing date as argument
    date = sys.argv[1] if len(sys.argv) > 1 else None
    
    updated = process_results(date)
    
    print(f"\n{'='*50}")
    print(f"Results scraping complete: {updated} bets updated")
    print(f"{'='*50}\n")
