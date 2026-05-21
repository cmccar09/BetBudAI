"""
Show today's track-specific insights
What patterns are winning at each venue today?
"""
from track_daily_insights import load_todays_insights, print_track_insights

def main():
    insights_data = load_todays_insights()
    
    print("\n" + "="*80)
    print(f"TRACK INSIGHTS FOR {insights_data.get('date', 'TODAY')}")
    print("="*80)
    print("\nWhat's working at each track today?\n")
    
    tracks = insights_data.get('tracks', {})
    
    if not tracks:
        print("No track insights captured yet.")
        print("\nInsights are captured automatically after each race result is matched.")
        print("Run the coordinated_learning_workflow.py to capture insights.")
        return
    
    for course in sorted(tracks.keys()):
        print_track_insights(course)
    
    # Summary
    total_races = sum(t.get('races_analyzed', 0) for t in tracks.values())
    print("\n" + "="*80)
    print(f"SUMMARY: {len(tracks)} tracks analyzed, {total_races} races learned from")
    print("="*80)
    
    # Overall patterns
    all_patterns = {}
    for track_data in tracks.values():
        for pattern, count in track_data.get('patterns', {}).items():
            all_patterns[pattern] = all_patterns.get(pattern, 0) + count
    
    if all_patterns:
        print("\nOverall pattern frequency today:")
        total_pattern_count = sum(all_patterns.values())
        for pattern, count in sorted(all_patterns.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_pattern_count) * 100
            print(f"  {pattern:20s}: {count:2d} races ({pct:.0f}%)")
    
    print("\n" + "="*80)
    print("These insights automatically boost scores for upcoming races at each track.")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
