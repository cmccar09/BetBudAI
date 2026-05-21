"""Quick summary of today's going conditions"""
from weather_going_inference import check_all_tracks_going

tracks = [
    'Carlisle', 'Taunton', 'Fairyhouse', 'Kempton', 'Punchestown', 
    'Ludlow', 'Newcastle', 'Sedgefield', 'Ffos Las', 'Exeter', 
    'Warwick', 'Chepstow', 'Lingfield', 'Dundalk', 'Southwell', 'Wolverhampton'
]

going_data = check_all_tracks_going(tracks)

print("\n" + "="*80)
print("TODAY'S GOING CONDITIONS SUMMARY - February 21, 2026")
print("="*80)
print()

turf_tracks = []
aw_tracks = []

for track, data in going_data.items():
    if data.get('surface') == 'all-weather':
        aw_tracks.append((track, data))
    else:
        turf_tracks.append((track, data))

print("TURF TRACKS (Heavy going widely expected):")
print("-" * 80)
for track, data in sorted(turf_tracks):
    rainfall = data.get('rainfall_mm', 0)
    going = data['going']
    rain_icon = "🌧️" if rainfall >= 10 else "☁️" if rainfall > 2 else "☀️"
    print(f"  {rain_icon} {track:20} -> {going:30} ({rainfall:.1f}mm rainfall)")

print("\nALL-WEATHER TRACKS (Standard surface):")
print("-" * 80)
for track, data in sorted(aw_tracks):
    rainfall = data.get('rainfall_mm', 0)
    going = data['going']
    print(f"  🏁 {track:20} -> {going:30} ({rainfall:.1f}mm rainfall)")

print("\n" + "="*80)
print("Updated Heavy going threshold: 10mm+ (down from 15mm)")
print("Analysis now factors in Heavy going for horse form assessment")
print("="*80)
