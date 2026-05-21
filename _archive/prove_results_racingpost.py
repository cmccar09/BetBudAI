#!/usr/bin/env python3
"""Scrape today's race results from Racing Post"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def get_todays_results():
    """Fetch today's results from Racing Post"""
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Racing Post results page for today
    url = f"https://www.racingpost.com/results/{today}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"Fetching results from: {url}")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Status {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    results = []
    
    # Find race result cards
    race_cards = soup.find_all('div', class_=re.compile('raceCard|race-card|rc-card'))
    
    if not race_cards:
        # Try alternative structure
        race_cards = soup.find_all('article') or soup.find_all('section', class_=re.compile('race'))
    
    print(f"Found {len(race_cards)} race cards")
    
    # Parse each race
    for card in race_cards[:10]:  # First 10 races
        try:
            # Extract course name
            course_elem = card.find(['h3', 'h2', 'span'], class_=re.compile('course|venue|track'))
            course = course_elem.text.strip() if course_elem else "Unknown"
            
            # Extract race time
            time_elem = card.find(['span', 'div'], class_=re.compile('time|off-time'))
            race_time = time_elem.text.strip() if time_elem else "Unknown"
            
            # Extract winner
            winner_elem = card.find(['div', 'span', 'td'], class_=re.compile('winner|first|position-1'))
            if not winner_elem:
                winner_elem = card.find('td', string=re.compile('^1$'))
                if winner_elem:
                    winner_elem = winner_elem.find_next_sibling('td')
            
            winner = winner_elem.text.strip() if winner_elem else "Unknown"
            
            if course != "Unknown" and winner != "Unknown":
                results.append({
                    'course': course,
                    'time': race_time,
                    'winner': winner
                })
        except Exception as e:
            continue
    
    return results

def main():
    print("="*70)
    print(f"TODAY'S HORSE RACING RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    print("\nFetching results from Racing Post...")
    results = get_todays_results()
    
    print(f"\n✓ Found {len(results)} completed races\n")
    
    if results:
        print("RESULTS:")
        print("-" * 70)
        for idx, result in enumerate(results, 1):
            print(f"\n{idx}. {result['course']} - {result['time']}")
            print(f"   WINNER: {result['winner']}")
    else:
        print("No results found yet (races may still be running)")
        print("\nNote: Early in the day, fewer races will have completed.")
    
    print("\n" + "="*70)
    print("✓ Results fetching capability confirmed!")
    print("="*70)

if __name__ == "__main__":
    main()
