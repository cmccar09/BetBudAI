import sys
sys.path.insert(0, '.')
from weather_going_inference import check_all_tracks_going

# Check all track going including Ffos Las
going_data = check_all_tracks_going(use_official=True)

print('\nAll Tracks Going Today:')
print('='*60)

for track, info in going_data.items():
    print(f"\n{track}:")
    print(f"  Going: {info.get('going', 'Unknown')}")
    print(f"  Adjustment: {info.get('adjustment', 0)}")
    print(f"  Surface: {info.get('surface', 'Unknown')}")

if 'Ffos Las' in going_data:
    print('\n' + '='*60)
    print('FFOS LAS SPECIFIC:')
    print('='*60)
    ffos = going_data['Ffos Las']
    print(f"Going: {ffos.get('going')}")
    print(f"Adjustment: {ffos.get('adjustment')}")
    print(f"Rainfall: {ffos.get('rainfall', 'N/A')}mm (last 3 days)")
else:
    print('\n⚠️ Ffos Las not found in tracked locations')
    print('   System may not have specific weather data for this track')
