"""
Fetch ground conditions for today's racing
"""
import sys
sys.path.append('.')
from enhanced_racing_data_fetcher import EnhancedRacingDataFetcher
from datetime import datetime

tracks = ['Carlisle', 'Taunton', 'Fairyhouse', 'Wolverhampton']
today = datetime.now().strftime('%Y-%m-%d')

print(f"\n{'='*80}")
print(f"GROUND CONDITIONS - {today}")
print(f"{'='*80}\n")

fetcher = EnhancedRacingDataFetcher()

for track in tracks:
    print(f"Fetching {track}...")
    going = fetcher.fetch_going_data(track, today)
    
    if going:
        print(f"  ✓ {track:20} Going: {going}")
    else:
        print(f"  ✗ {track:20} Unable to fetch going data")
    print()

print(f"{'='*80}\n")
