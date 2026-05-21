#!/usr/bin/env python3
"""
fetch_gbgb_dog_form.py
Scrapes greyhound form data from GBGB (Greyhound Board of Great Britain)
Covers UK tracks: Towcester, Hove, Sheffield, Oxford, Brighton, etc.
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
import re
from datetime import datetime
import time

def search_gbgb_dog(dog_name):
    """
    Search for a greyhound on GBGB and return the profile URL
    
    Args:
        dog_name: Name of the greyhound
    
    Returns:
        greyhound_id or None
    """
    try:
        # GBGB search endpoint (may need adjustment)
        search_url = "https://www.gbgb.org.uk/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9',
        }
        
        # Try to search - GBGB might have an API or search parameter
        # For now, we'll need to construct the profile URL pattern
        # Pattern: https://www.gbgb.org.uk/greyhound-profile/?greyhoundId=XXXXXX
        
        # Alternative: scrape from race results or meetings
        # This is a placeholder - actual implementation may need different approach
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Search failed: {e}", file=sys.stderr)
        return None


def fetch_gbgb_dog_form(dog_name, greyhound_id=None):
    """
    Fetch dog form from GBGB
    
    Args:
        dog_name: Name of the greyhound
        greyhound_id: Optional GBGB greyhound ID (if known)
    
    Returns:
        Dictionary with dog statistics
    """
    dog_stats = {
        'name': dog_name,
        'greyhound_id': greyhound_id,
        'trainer': None,
        'last_races': [],
        'avg_time': None,
        'win_percentage': 0,
        'place_percentage': 0,
        'preferred_trap': None,
        'best_time': None,
        'total_races': 0,
        'wins': 0,
        'places': 0
    }
    
    # If we don't have ID, try to search
    if not greyhound_id:
        greyhound_id = search_gbgb_dog(dog_name)
    
    if not greyhound_id:
        print(f"[NO DATA] Could not find GBGB ID for {dog_name}", file=sys.stderr)
        return dog_stats
    
    try:
        url = f"https://www.gbgb.org.uk/greyhound-profile/?greyhoundId={greyhound_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code} for {dog_name}", file=sys.stderr)
            return dog_stats
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract trainer
        trainer_elem = soup.find(text=re.compile(r'TRAINER:'))
        if trainer_elem:
            dog_stats['trainer'] = trainer_elem.parent.text.replace('TRAINER:', '').strip()
        
        # Parse race history from the page content
        # The race data appears to be in a structured format
        races = parse_gbgb_race_history(soup)
        
        if races:
            dog_stats['last_races'] = races[:20]  # Keep last 20 races
            dog_stats['total_races'] = len(races)
            
            # Calculate statistics
            dog_stats = calculate_gbgb_statistics(dog_stats)
        
        return dog_stats
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error fetching {dog_name}: {e}", file=sys.stderr)
        return dog_stats
    except Exception as e:
        print(f"[ERROR] Parse error for {dog_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return dog_stats


def parse_gbgb_race_history(soup):
    """
    Parse race history from GBGB profile page
    
    The format appears to be in table rows or divs
    """
    races = []
    
    try:
        # Try to find race data in tables
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                
                row_text = row.get_text(' ', strip=True)
                
                # Look for date pattern at start
                date_match = re.match(r'(\d{2}/\d{2}/\d{2})', row_text)
                if not date_match:
                    continue
                
                # Extract fields using regex patterns
                date_str = date_match.group(1)
                
                # Track name (after date)
                track_match = re.search(r'\d{2}/\d{2}/\d{2}\s+([A-Za-z\s&]+?)\s+[A-Z0-9]+', row_text)
                track = track_match.group(1).strip() if track_match else ''
                
                # Distance
                dist_match = re.search(r'\|\s*(\d{3,4})\s*\|', row_text)
                distance = int(dist_match.group(1)) if dist_match else None
                
                # Position
                pos_match = re.search(r'Pos:(\d+)', row_text)
                position = int(pos_match.group(1)) if pos_match else None
                
                # Beaten distance
                beaten_match = re.search(r'Dis:([\d\s/]+)', row_text)
                beaten_dist = beaten_match.group(1).strip() if beaten_match else ''
                
                # Win time
                time_match = re.search(r'WinTime:([\d.]+)', row_text)
                win_time = float(time_match.group(1)) if time_match else None
                
                # Calc time
                calc_match = re.search(r'CalcTm:([\d.]+)', row_text)
                calc_time = float(calc_match.group(1)) if calc_match else None
                
                # SP (Starting Price)
                sp_match = re.search(r'SP:([\d/]+[FJ]?)', row_text)
                sp = sp_match.group(1) if sp_match else ''
                
                # Trap - look for trap number
                trap_match = re.search(r'(?:Trap|T)(\d)', row_text)
                trap = int(trap_match.group(1)) if trap_match else None
                
                # Race class
                class_match = re.search(r'\s([A-Z]+\d*)\s*\|', row_text)
                race_class = class_match.group(1) if class_match else ''
                
                if date_str and (position or win_time or calc_time):
                    races.append({
                        'date': date_str,
                        'track': track,
                        'race_class': race_class,
                        'distance': distance,
                        'trap': trap,
                        'position': position,
                        'beaten_distance': beaten_dist,
                        'win_time': win_time,
                        'calc_time': calc_time,
                        'sp': sp
                    })
        
        # If no table data found, try text parsing
        if not races:
            page_text = soup.get_text('\n')
            lines = page_text.split('\n')
            
            for line in lines:
                # Look for lines with date pattern
                if not re.match(r'\d{2}/\d{2}/\d{2}', line.strip()):
                    continue
                
                # Similar extraction as above
                date_match = re.match(r'(\d{2}/\d{2}/\d{2})', line)
                if not date_match:
                    continue
                
                date_str = date_match.group(1)
                
                pos_match = re.search(r'Pos:(\d+)', line)
                position = int(pos_match.group(1)) if pos_match else None
                
                time_match = re.search(r'WinTime:([\d.]+)', line)
                win_time = float(time_match.group(1)) if time_match else None
                
                calc_match = re.search(r'CalcTm:([\d.]+)', line)
                calc_time = float(calc_match.group(1)) if calc_match else None
                
                if date_str and (position or calc_time):
                    races.append({
                        'date': date_str,
                        'position': position,
                        'win_time': win_time,
                        'calc_time': calc_time
                    })
        
    except Exception as e:
        print(f"[ERROR] Error parsing race history: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    return races


def calculate_gbgb_statistics(dog_stats):
    """Calculate statistics from race history"""
    
    races = dog_stats['last_races']
    if not races:
        return dog_stats
    
    # Count wins and places
    wins = 0
    places = 0  # 1st, 2nd, or 3rd
    trap_counts = {}
    times = []
    
    for race in races:
        pos = race.get('position')
        trap = race.get('trap')
        calc_time = race.get('calc_time')
        
        if pos:
            if pos == 1:
                wins += 1
                places += 1
            elif pos in [2, 3]:
                places += 1
        
        if trap:
            trap_counts[trap] = trap_counts.get(trap, 0) + 1
        
        if calc_time:
            times.append(calc_time)
    
    total_races = len(races)
    dog_stats['wins'] = wins
    dog_stats['places'] = places
    dog_stats['win_percentage'] = round((wins / total_races * 100), 1) if total_races > 0 else 0
    dog_stats['place_percentage'] = round((places / total_races * 100), 1) if total_races > 0 else 0
    
    # Preferred trap (most common)
    if trap_counts:
        dog_stats['preferred_trap'] = max(trap_counts, key=trap_counts.get)
    
    # Average and best times
    if times:
        dog_stats['avg_time'] = round(sum(times) / len(times), 2)
        dog_stats['best_time'] = round(min(times), 2)
    
    # Recent form (last 5)
    recent_form = []
    for race in races[:5]:
        pos = race.get('position')
        if pos:
            recent_form.append(str(pos))
    dog_stats['last_5_form'] = '-'.join(recent_form) if recent_form else ''
    
    return dog_stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch GBGB greyhound form data")
    parser.add_argument('--dog', required=True, help="Dog name")
    parser.add_argument('--id', help="GBGB greyhound ID (if known)")
    parser.add_argument('--out', help="Output JSON file")
    
    args = parser.parse_args()
    
    print(f"Fetching GBGB data for: {args.dog}")
    
    result = fetch_gbgb_dog_form(args.dog, args.id)
    
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[OK] Saved to {args.out}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
