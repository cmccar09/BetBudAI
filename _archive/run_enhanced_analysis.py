#!/usr/bin/env python3
"""
run_enhanced_analysis.py - Use the new enhanced multi-pass analysis system
Drop-in replacement for run_saved_prompt.py with superior analysis
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from enhanced_analysis import EnhancedAnalyzer

def load_race_data(json_path: str) -> list:
    """Load race data from JSON snapshot"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different JSON formats
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Try different keys
        return data.get('races', data.get('result', data.get('markets', data.get('data', []))))
    else:
        print(f"ERROR: Unexpected JSON format", file=sys.stderr)
        return []

def save_selections_csv(selections: list, output_path: str):
    """Save selections to CSV format"""
    
    if not selections:
        print("No selections to save")
        return
    
    # Required columns - ADDED all_horses_analyzed for v2.3
    columns = [
        "runner_name", "selection_id", "market_id", "market_name", "venue",
        "start_time_dublin", "p_win", "p_place", "bet_type", "ew_places", "ew_fraction",
        "tags", "why_now", "all_horses_analyzed"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        
        for sel in selections:
            # Build row with defaults for missing fields
            row = {
                "runner_name": sel.get('runner_name', ''),
                "selection_id": sel.get('selection_id', ''),
                "market_id": sel.get('market_id', ''),
                "market_name": sel.get('market_name', ''),
                "venue": sel.get('venue', ''),
                "start_time_dublin": sel.get('start_time_dublin', ''),
                "p_win": sel.get('p_win', 0.0),
                "p_place": sel.get('p_place', 0.0),
                "bet_type": sel.get('bet_type', 'EW'),  # Default to EW if not specified
                "ew_places": sel.get('ew_places', 3),  # Default 3 places
                "ew_fraction": sel.get('ew_fraction', 0.2),  # Default 1/5 odds
                "tags": "enhanced_analysis," + sel.get('strengths', ''),
                "why_now": sel.get('why_now', sel.get('reasoning', '')),
                "all_horses_analyzed": json.dumps(sel.get('all_horses_analyzed', {}))  # V2.3: Store all horses data
            }
            writer.writerow(row)
    
    print(f"[OK] Saved {len(selections)} selections to: {output_path}")

def main(hours=1):
    """Main execution
    
    Args:
        hours: Time window in hours to analyze (default: 1)
    """
    
    # Use SNAPSHOT_FILE env var if set, otherwise default to response_live.json
    snapshot_path = os.environ.get('SNAPSHOT_FILE', os.path.join('.', 'response_live.json'))
    if not os.path.exists(snapshot_path):
        print(f"ERROR: Snapshot not found: {snapshot_path}", file=sys.stderr)
        sys.exit(1)
    
    # Load race data
    print(f"Loading market data from: {snapshot_path}")
    races = load_race_data(snapshot_path)
    
    if not races:
        print("ERROR: No races found in snapshot", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(races)} races")
    
    # Filter races to next X hours
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    time_ahead = now + timedelta(hours=hours)
    
    races_in_window = []
    past_races = 0
    for r in races:
        start_time_str = r.get('start_time', '')
        if start_time_str:
            try:
                # Parse ISO format timestamp
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                # Only include future races within time window
                if start_time < now:
                    past_races += 1
                    continue
                if start_time <= time_ahead:
                    races_in_window.append(r)
            except:
                # If parsing fails, include the race to be safe
                races_in_window.append(r)
        else:
            # No timestamp, include it
            races_in_window.append(r)
    
    print(f"Filtered to {len(races_in_window)} races in next {hours} hour(s) (excluded {past_races} past races)")
    
    # PROCESS ALL RACES - Detailed analysis for every race in the time window
    # Filter to horses only (skip greyhounds)
    greyhound_venues = ['Monmore', 'Central Park', 'Perry Barr', 'Romford', 'Crayford', 'Belle Vue', 
                        'Sheffield', 'Newcastle (Greyhounds)', 'Sunderland', 'Harlow', 'Henlow']
    
    races_to_process = []
    for r in races_in_window:
        venue = r.get('venue', 'Unknown')
        # Skip greyhound races
        if venue not in greyhound_venues:
            races_to_process.append(r)
    
    # Sort by start time
    races_to_process.sort(key=lambda x: x.get('start_time', ''))
    
    horse_count = len(races_to_process)
    greyhound_count = 0
    
    print(f"Processing ALL races in next {hours} hour(s): {len(races_to_process)} races (horses only)")
    print(f"  - {horse_count} horse races")
    print(f"  - {greyhound_count} greyhound races (skipped)")
    
    analyzer = EnhancedAnalyzer()
    
    all_selections = []
    for i, race in enumerate(races_to_process, 1):
        print(f"\n[{i}/{len(races_to_process)}] Processing: {race.get('market_name', 'Unknown')}")
        
        try:
            selections = analyzer.analyze_race_enhanced(race)
            all_selections.extend(selections)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue
    
    # Use ALL selections from every race (no top 5 filtering)
    top_selections = all_selections
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(all_selections)} selections generated from {len(races_to_process)} races")
    print(f"[OK] All picks:")
    for i, sel in enumerate(top_selections[:10], 1):  # Show first 10 for preview
        print(f"  {i}. {sel.get('runner_name', 'Unknown')} @ {sel.get('venue', 'Unknown')} (p_win: {sel.get('p_win', 0):.2f}, confidence: {sel.get('confidence', 0)})")
    if len(top_selections) > 10:
        print(f"  ... and {len(top_selections) - 10} more")
    
    # Save to history folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join('history', f'selections_{timestamp}.csv')
    
    # Ensure history directory exists
    os.makedirs('history', exist_ok=True)
    
    save_selections_csv(top_selections, output_path)
    
    # Also save as today_picks.csv for compatibility
    save_selections_csv(top_selections, 'today_picks.csv')
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {len(top_selections)} selections generated (one per race)")
    print(f"Output: {output_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run enhanced betting analysis')
    parser.add_argument('--hours', type=int, default=1, help='Time window in hours (default: 1)')
    args = parser.parse_args()
    
    # Pass hours to main
    main(hours=args.hours)
