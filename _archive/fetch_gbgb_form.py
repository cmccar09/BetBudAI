#!/usr/bin/env python3
"""
fetch_gbgb_form.py
Fetches greyhound form data from GBGB API (Greyhound Board of Great Britain)
Covers UK tracks: Towcester, Hove, Sheffield, Oxford, Brighton, etc.
"""

import requests
import json
import sys
from datetime import datetime
from collections import Counter

# GBGB API endpoint
GBGB_API = "https://api.gbgb.org.uk/api/results"


def search_gbgb_dog_id(dog_name, track=None):
    """
    Search for a greyhound on GBGB API and return the dog ID
    
    Args:
        dog_name: Name of the greyhound
        track: Optional track name to filter (e.g., "Towcester")
    
    Returns:
        (dog_id, trainer_name) tuple or (None, None)
    """
    try:
        params = {'dogName': dog_name}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(GBGB_API, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[ERROR] API returned {response.status_code} for {dog_name}", file=sys.stderr)
            return None, None
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            print(f"[NO DATA] No results found for {dog_name}", file=sys.stderr)
            return None, None
        
        # Get first result (most recent)
        first_result = items[0]
        dog_id = first_result.get('dogId')
        trainer = first_result.get('trainerName')
        
        return dog_id, trainer
        
    except Exception as e:
        print(f"[ERROR] Search failed for {dog_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None, None


def parse_race_results(races):
    """Convert API race results to simplified format"""
    parsed = []
    
    for race in races:
        try:
            parsed.append({
                'date': race.get('raceDate', ''),
                'track': race.get('trackName', ''),
                'race_class': race.get('raceClass', ''),
                'distance': race.get('raceDistance'),
                'trap': int(race['trapNumber']) if race.get('trapNumber') else None,
                'position': race.get('resultPosition'),
                'race_time': race.get('raceTime', '')
            })
        except Exception as e:
            continue
    
    return parsed


def calculate_statistics(dog_stats, races):
    """Calculate statistics from race results"""
    
    if not races:
        return dog_stats
    
    wins = 0
    places = 0  # 1st, 2nd, or 3rd
    trap_counts = Counter()
    
    for race in races:
        pos = race.get('resultPosition')
        trap = race.get('trapNumber')
        
        if pos == 1:
            wins += 1
            places += 1
        elif pos in [2, 3]:
            places += 1
        
        if trap:
            try:
                trap_counts[int(trap)] += 1
            except:
                pass
    
    total_races = len(races)
    dog_stats['wins'] = wins
    dog_stats['places'] = places
    dog_stats['win_percentage'] = round((wins / total_races * 100), 1) if total_races > 0 else 0
    dog_stats['place_percentage'] = round((places / total_races * 100), 1) if total_races > 0 else 0
    
    # Preferred trap (most common)
    if trap_counts:
        dog_stats['preferred_trap'] = trap_counts.most_common(1)[0][0]
    
    # Recent form (last 5)
    recent_form = []
    for race in races[:5]:
        pos = race.get('resultPosition')
        if pos:
            recent_form.append(str(pos))
    dog_stats['last_5_form'] = '-'.join(recent_form) if recent_form else ''
    
    return dog_stats


def fetch_gbgb_dog_form(dog_name, track=None):
    """
    Fetch dog form from GBGB API
    
    Args:
        dog_name: Name of the greyhound
        track: Optional track name for context
    
    Returns:
        Dictionary with dog statistics
    """
    dog_stats = {
        'name': dog_name,
        'greyhound_id': None,
        'trainer': None,
        'last_races': [],
        'avg_time': None,
        'win_percentage': 0,
        'place_percentage': 0,
        'preferred_trap': None,
        'best_time': None,
        'total_races': 0,
        'wins': 0,
        'places': 0,
        'last_5_form': ''
    }
    
    # Search for dog ID
    dog_id, trainer = search_gbgb_dog_id(dog_name, track)
    
    if not dog_id:
        return dog_stats
    
    dog_stats['greyhound_id'] = dog_id
    dog_stats['trainer'] = trainer
    
    try:
        # Fetch all results for this dog
        params = {'dogId': dog_id}
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(GBGB_API, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[ERROR] API returned {response.status_code} for dog ID {dog_id}", file=sys.stderr)
            return dog_stats
        
        data = response.json()
        races = data.get('items', [])
        
        if not races:
            print(f"[NO DATA] No race history for {dog_name}", file=sys.stderr)
            return dog_stats
        
        print(f"[OK] Found {len(races)} races for {dog_name} (ID: {dog_id})", file=sys.stderr)
        
        # Parse race results
        dog_stats['last_races'] = parse_race_results(races[:20])  # Keep last 20
        dog_stats['total_races'] = len(races)
        
        # Calculate statistics
        dog_stats = calculate_statistics(dog_stats, races)
        
        return dog_stats
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch history for {dog_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return dog_stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch GBGB greyhound form data")
    parser.add_argument('--dog', required=True, help="Dog name")
    parser.add_argument('--track', help="Track name (optional)")
    parser.add_argument('--out', help="Output JSON file")
    
    args = parser.parse_args()
    
    print(f"Fetching GBGB data for: {args.dog}")
    
    result = fetch_gbgb_dog_form(args.dog, args.track)
    
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[OK] Saved to {args.out}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
