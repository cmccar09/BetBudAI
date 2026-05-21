"""
Track-Specific Daily Learning
Learns patterns from race winners at each track to improve predictions for subsequent races
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any

INSIGHTS_FILE = 'track_insights_today.json'

def load_todays_insights() -> Dict[str, Any]:
    """Load today's track insights"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not os.path.exists(INSIGHTS_FILE):
        return {'date': today, 'tracks': {}}
    
    try:
        with open(INSIGHTS_FILE, 'r') as f:
            data = json.load(f)
            # Reset if it's a new day
            if data.get('date') != today:
                return {'date': today, 'tracks': {}}
            return data
    except:
        return {'date': today, 'tracks': {}}

def save_insights(insights: Dict[str, Any]):
    """Save insights to file"""
    with open(INSIGHTS_FILE, 'w') as f:
        json.dump(insights, f, indent=2)

def analyze_winner_factors(winner_data: Dict[str, Any], breakdown: Dict[str, int]) -> Dict[str, Any]:
    """
    Analyze what factors made the winner strong
    Returns insights about which scoring factors were dominant
    """
    insights = {
        'horse_name': winner_data.get('horse_name', 'Unknown'),
        'odds': winner_data.get('odds', 0),
        'score': winner_data.get('combined_confidence', 0),
        'dominant_factors': [],
        'winning_pattern': None
    }
    
    # Identify which factors contributed most
    total_score = sum(breakdown.values())
    if total_score > 0:
        factor_percentages = {k: (v/total_score)*100 for k, v in breakdown.items() if v > 0}
        
        # Find dominant factors (>25% of score)
        dominant = {k: v for k, v in factor_percentages.items() if v > 25}
        insights['dominant_factors'] = list(dominant.keys())
        
        # Determine winning pattern
        if 'recent_win' in dominant:
            insights['winning_pattern'] = 'RECENT_FORM'
        elif 'course_bonus' in dominant:
            insights['winning_pattern'] = 'COURSE_SPECIALIST'
        elif 'sweet_spot' in dominant:
            insights['winning_pattern'] = 'DISTANCE_SUITED'
        elif 'database_history' in dominant:
            insights['winning_pattern'] = 'PROVEN_WINNER'
        elif 'going_suitability' in dominant:
            insights['winning_pattern'] = 'GOING_SPECIALIST'
        elif 'optimal_odds' in dominant:
            insights['winning_pattern'] = 'VALUE_BET'
        else:
            insights['winning_pattern'] = 'BALANCED'
        
        insights['factor_breakdown'] = breakdown
        insights['factor_percentages'] = factor_percentages
    
    return insights

def add_race_insight(course: str, race_time: str, winner_data: Dict[str, Any], 
                     breakdown: Dict[str, int], race_distance: str = None):
    """
    Add insight from a race winner
    """
    insights_data = load_todays_insights()
    
    if course not in insights_data['tracks']:
        insights_data['tracks'][course] = {
            'races_analyzed': 0,
            'patterns': {},
            'race_history': []
        }
    
    track = insights_data['tracks'][course]
    
    # Analyze this winner
    winner_insights = analyze_winner_factors(winner_data, breakdown)
    winner_insights['race_time'] = race_time
    winner_insights['distance'] = race_distance
    
    # Add to history
    track['race_history'].append(winner_insights)
    track['races_analyzed'] += 1
    
    # Update pattern counts
    pattern = winner_insights['winning_pattern']
    if pattern:
        track['patterns'][pattern] = track['patterns'].get(pattern, 0) + 1
    
    # Identify dominant pattern for today
    if track['patterns']:
        dominant_pattern = max(track['patterns'].items(), key=lambda x: x[1])
        track['todays_dominant_pattern'] = dominant_pattern[0]
        track['pattern_strength'] = dominant_pattern[1] / track['races_analyzed']
    
    save_insights(insights_data)
    
    return winner_insights

def get_track_insights(course: str) -> Dict[str, Any]:
    """
    Get insights for a specific track
    Returns patterns learned from today's earlier races
    """
    insights_data = load_todays_insights()
    
    if course not in insights_data['tracks']:
        return {
            'has_data': False,
            'races_analyzed': 0,
            'suggested_boost': {}
        }
    
    track = insights_data['tracks'][course]
    
    # Determine what to boost based on patterns
    boost_recommendations = {}
    
    if 'todays_dominant_pattern' in track:
        pattern = track['todays_dominant_pattern']
        strength = track.get('pattern_strength', 0)
        
        # Strong pattern (60%+ of races)
        if strength >= 0.6:
            if pattern == 'RECENT_FORM':
                boost_recommendations['recent_win'] = 10
            elif pattern == 'COURSE_SPECIALIST':
                boost_recommendations['course_bonus'] = 8
            elif pattern == 'DISTANCE_SUITED':
                boost_recommendations['sweet_spot'] = 8
            elif pattern == 'PROVEN_WINNER':
                boost_recommendations['database_history'] = 8
            elif pattern == 'GOING_SPECIALIST':
                boost_recommendations['going_suitability'] = 6
        # Moderate pattern (40-60%)
        elif strength >= 0.4:
            if pattern == 'RECENT_FORM':
                boost_recommendations['recent_win'] = 5
            elif pattern == 'COURSE_SPECIALIST':
                boost_recommendations['course_bonus'] = 5
            elif pattern == 'DISTANCE_SUITED':
                boost_recommendations['sweet_spot'] = 5
    
    return {
        'has_data': True,
        'races_analyzed': track['races_analyzed'],
        'patterns': track['patterns'],
        'dominant_pattern': track.get('todays_dominant_pattern'),
        'pattern_strength': track.get('pattern_strength', 0),
        'suggested_boost': boost_recommendations,
        'recent_winners': [r['horse_name'] for r in track['race_history'][-3:]]
    }

def print_track_insights(course: str):
    """Print insights for a track in a readable format"""
    insights = get_track_insights(course)
    
    print(f"\n{'='*60}")
    print(f"TRACK INSIGHTS: {course}")
    print(f"{'='*60}")
    
    if not insights['has_data']:
        print("No data yet - first race at this track today")
        return
    
    print(f"Races analyzed today: {insights['races_analyzed']}")
    
    if insights.get('dominant_pattern'):
        pattern = insights['dominant_pattern']
        strength = insights['pattern_strength'] * 100
        print(f"\nDominant pattern: {pattern} ({strength:.0f}% of races)")
        
        pattern_names = {
            'RECENT_FORM': 'Horses with recent wins are dominating',
            'COURSE_SPECIALIST': 'Course experience is key',
            'DISTANCE_SUITED': 'Distance-suited horses winning',
            'PROVEN_WINNER': 'Proven track record matters most',
            'GOING_SPECIALIST': 'Going conditions favoring specialists',
            'VALUE_BET': 'Longer odds finding success',
            'BALANCED': 'No clear pattern - balanced factors'
        }
        print(f"→ {pattern_names.get(pattern, pattern)}")
    
    if insights['suggested_boost']:
        print(f"\nRecommended score adjustments for next race:")
        for factor, boost in insights['suggested_boost'].items():
            print(f"  • {factor}: +{boost} points")
    
    if insights.get('recent_winners'):
        print(f"\nRecent winners: {', '.join(insights['recent_winners'])}")
    
    print(f"{'='*60}\n")

if __name__ == '__main__':
    # Test - show insights for all tracks with data
    insights_data = load_todays_insights()
    
    if insights_data.get('tracks'):
        print(f"\nToday's Track Insights ({insights_data['date']})")
        print("="*60)
        
        for course in insights_data['tracks'].keys():
            print_track_insights(course)
    else:
        print("No track insights yet today")
