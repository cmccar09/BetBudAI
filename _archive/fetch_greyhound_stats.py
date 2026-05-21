#!/usr/bin/env python3
"""
fetch_greyhound_stats.py
Scrapes individual greyhound statistics and form data
Sources: Racing Post, IGB, and other public sources
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
import argparse
from datetime import datetime
import time

def fetch_racing_post_dog_form(dog_name, track=None):
    """
    Fetch dog form from Racing Post
    
    Args:
        dog_name: Name of the greyhound
        track: Optional track name to filter results
    
    Returns:
        Dictionary with dog statistics
    """
    dog_stats = {
        'name': dog_name,
        'last_races': [],
        'avg_time': None,
        'win_percentage': 0,
        'place_percentage': 0,
        'preferred_trap': None,
        'best_time': None
    }
    
    try:
        # Racing Post greyhound search
        # Note: This URL structure is an example - may need adjustment
        search_url = "https://www.racingpost.com/greyhounds/search"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Search for the dog
        params = {'q': dog_name}
        response = requests.get(search_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse dog profile page (structure depends on actual website)
            # This is a template - adjust based on actual HTML
            
            # Extract recent form
            form_table = soup.find('table', class_='form-table')
            if form_table:
                dog_stats['last_races'] = parse_form_table(form_table)
            
            # Calculate statistics
            if dog_stats['last_races']:
                dog_stats = calculate_dog_statistics(dog_stats)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Racing Post data: {e}", file=sys.stderr)
    
    return dog_stats

def parse_form_table(table):
    """Parse form table to extract recent race results"""
    races = []
    
    rows = table.find_all('tr')[1:]  # Skip header
    
    for row in rows[:10]:  # Last 10 races
        cells = row.find_all('td')
        if len(cells) >= 6:
            race = {
                'date': cells[0].text.strip(),
                'track': cells[1].text.strip(),
                'distance': cells[2].text.strip(),
                'trap': cells[3].text.strip(),
                'position': cells[4].text.strip(),
                'time': cells[5].text.strip()
            }
            races.append(race)
    
    return races

def calculate_dog_statistics(dog_stats):
    """Calculate statistics from recent races"""
    races = dog_stats['last_races']
    
    if not races:
        return dog_stats
    
    # Calculate win/place percentages
    wins = sum(1 for r in races if r['position'] == '1')
    places = sum(1 for r in races if r['position'] in ['1', '2', '3'])
    total = len(races)
    
    dog_stats['win_percentage'] = round((wins / total) * 100, 1) if total > 0 else 0
    dog_stats['place_percentage'] = round((places / total) * 100, 1) if total > 0 else 0
    
    # Find preferred trap (most common)
    from collections import Counter
    trap_counts = Counter(r['trap'] for r in races if r['trap'])
    if trap_counts:
        dog_stats['preferred_trap'] = trap_counts.most_common(1)[0][0]
    
    # Calculate average time (converting from string format like "28.50")
    times = []
    for race in races:
        try:
            time_str = race['time'].replace('s', '').strip()
            if time_str and time_str != 'N/A':
                times.append(float(time_str))
        except (ValueError, AttributeError):
            continue
    
    if times:
        dog_stats['avg_time'] = round(sum(times) / len(times), 2)
        dog_stats['best_time'] = round(min(times), 2)
    
    return dog_stats

def fetch_timeform_ratings(dog_name):
    """
    Fetch Timeform speed ratings for a dog
    Note: Timeform requires subscription for detailed data
    """
    # Placeholder for Timeform integration
    # Requires API key or premium access
    return {
        'speed_rating': None,
        'class': None,
        'form_comment': None
    }

def enrich_with_betfair_data(dog_stats, betfair_selection_id=None):
    """
    Enrich dog stats with Betfair historical data
    
    Args:
        dog_stats: Existing dog statistics
        betfair_selection_id: Betfair selection ID if known
    """
    # Can integrate with Betfair historical data API
    # Get past odds, market movements, etc.
    
    if betfair_selection_id:
        # Fetch historical odds for this selection
        pass
    
    return dog_stats

def fetch_multiple_dogs(dog_names, track=None):
    """Fetch stats for multiple dogs"""
    all_stats = []
    
    for i, dog_name in enumerate(dog_names):
        print(f"Fetching stats for {dog_name} ({i+1}/{len(dog_names)})...")
        
        stats = fetch_racing_post_dog_form(dog_name, track)
        all_stats.append(stats)
        
        # Be polite - add delay between requests
        if i < len(dog_names) - 1:
            time.sleep(1)
    
    return all_stats

def main():
    parser = argparse.ArgumentParser(description="Fetch greyhound statistics and form")
    parser.add_argument('--dog', type=str, help='Dog name to fetch stats for')
    parser.add_argument('--dogs-file', type=str, 
                        help='File with dog names (one per line)')
    parser.add_argument('--from-snapshot', type=str,
                        help='Extract dog names from Betfair snapshot JSON')
    parser.add_argument('--track', type=str, help='Filter by track')
    parser.add_argument('--out', type=str, default='greyhound_stats.json',
                        help='Output JSON file (default: greyhound_stats.json)')
    
    args = parser.parse_args()
    
    dog_names = []
    
    # Get dog names from various sources
    if args.dog:
        dog_names = [args.dog]
    elif args.dogs_file:
        with open(args.dogs_file, 'r') as f:
            dog_names = [line.strip() for line in f if line.strip()]
    elif args.from_snapshot:
        # Extract dog names from Betfair snapshot
        with open(args.from_snapshot, 'r') as f:
            snapshot = json.load(f)
            for race in snapshot.get('races', []):
                for runner in race.get('runners', []):
                    dog_names.append(runner['name'])
    else:
        print("Error: Must provide --dog, --dogs-file, or --from-snapshot")
        return 1
    
    if not dog_names:
        print("No dog names found")
        return 1
    
    print(f"Fetching stats for {len(dog_names)} greyhound(s)...")
    all_stats = fetch_multiple_dogs(dog_names, args.track)
    
    # Save results
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_dogs': len(all_stats),
        'track_filter': args.track,
        'dogs': all_stats
    }
    
    with open(args.out, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Statistics saved to {args.out}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    for stat in all_stats:
        print(f"\n{stat['name']}:")
        print(f"  Win Rate: {stat['win_percentage']}%")
        print(f"  Place Rate: {stat['place_percentage']}%")
        if stat['avg_time']:
            print(f"  Avg Time: {stat['avg_time']}s")
        if stat['best_time']:
            print(f"  Best Time: {stat['best_time']}s")
        if stat['preferred_trap']:
            print(f"  Preferred Trap: {stat['preferred_trap']}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
