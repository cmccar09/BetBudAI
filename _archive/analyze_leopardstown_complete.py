"""
Comprehensive Leopardstown Race Analysis
Analyzes ALL horses in ALL Leopardstown races for learning purposes
Saves complete analysis to DynamoDB for later comparison with actual results
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal
import sys

# Initialize DynamoDB
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

def convert_to_decimal(obj):
    """Recursively convert floats to Decimal for DynamoDB"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_decimal(item) for item in obj]
    else:
        return obj

def analyze_leopardstown_races():
    """Load and analyze all Leopardstown races"""
    
    print("=" * 80)
    print("LEOPARDSTOWN COMPLETE RACE ANALYSIS - 2026-02-02")
    print("=" * 80)
    
    # Load race data
    with open('response_horses.json', 'r') as f:
        data = json.load(f)
    
    # Filter Leopardstown races
    leopardstown_races = [r for r in data['races'] if r.get('venue') == 'Leopardstown']
    
    print(f"\n📊 Found {len(leopardstown_races)} Leopardstown races")
    print(f"Total horses to analyze: {sum(len(r.get('runners', [])) for r in leopardstown_races)}\n")
    
    all_analyses = []
    race_count = 0
    
    for race in leopardstown_races:
        race_count += 1
        market_id = race.get('marketId', 'unknown')
        market_name = race.get('marketName', 'Unknown Race')
        start_time = race.get('start_time', 'Unknown')
        runners = race.get('runners', [])
        
        print(f"\n{'='*80}")
        print(f"RACE {race_count}: {market_name}")
        print(f"Time: {start_time} | Market ID: {market_id}")
        print(f"Runners: {len(runners)}")
        print(f"{'='*80}\n")
        
        # Analyze each horse
        for idx, runner in enumerate(runners, 1):
            horse_name = runner.get('name', runner.get('runnerName', 'Unknown'))
            selection_id = runner.get('selectionId', 0)
            
            # Extract all available data
            analysis = {
                # Identity
                'bet_id': f'ANALYSIS_{market_id}_{selection_id}',
                'bet_date': '2026-02-02',
                'analysis_type': 'PRE_RACE_COMPLETE',
                'venue': 'Leopardstown',
                'race_time': start_time,
                'market_id': market_id,
                'market_name': market_name,
                'horse': horse_name,
                'selection_id': str(selection_id),
                'runner_number': idx,
                
                # Odds data
                'odds': convert_to_decimal(runner.get('odds', 0)),
                'implied_probability': convert_to_decimal(runner.get('implied_probability', 0)),
                
                # Form data (if available)
                'jockey': runner.get('jockey', 'Unknown') if isinstance(runner.get('jockey'), str) else runner.get('jockey', {}).get('name', 'Unknown'),
                'trainer': runner.get('trainer', 'Unknown') if isinstance(runner.get('trainer'), str) else runner.get('trainer', {}).get('name', 'Unknown'),
                'weight': str(runner.get('weight', 'Unknown')),
                'age': str(runner.get('age', 'Unknown')),
                'form': str(runner.get('form', 'Unknown')),
                'days_since_last_run': str(runner.get('days_since_last_run', 'Unknown')),
                'trap': str(runner.get('trap', 'Unknown')),
                
                # Additional metadata
                'cloth_number': str(runner.get('clothNumber', runner.get('trap', 'Unknown'))),
                'total_matched': convert_to_decimal(runner.get('total_matched', 0)),
                
                # Analysis metadata
                'analyzed_at': datetime.now().isoformat(),
                'analysis_purpose': 'LEARNING_BASELINE',
                'notes': 'Pre-race analysis for learning comparison with actual results'
            }
            
            # Add any enhanced analysis data if it exists
            if 'enhanced_analysis' in runner:
                ea = runner['enhanced_analysis']
                analysis['value_score'] = ea.get('value_score', 0)
                analysis['form_score'] = ea.get('form_score', 0)
                analysis['class_score'] = ea.get('class_score', 0)
                analysis['edge_percentage'] = convert_to_decimal(ea.get('edge_percentage', 0))
                analysis['trend'] = ea.get('trend', 'Unknown')
                analysis['reasoning'] = ea.get('reasoning', 'No enhanced analysis')
            
            all_analyses.append(analysis)
            
            # Print summary
            odds_str = f"{analysis['odds']}" if analysis['odds'] else "N/A"
            print(f"  {idx:2d}. {horse_name:30s} | Odds: {odds_str:>6s} | J: {analysis['jockey'][:20]:20s} | Form: {analysis['form']}")
    
    return all_analyses

def save_analyses_to_db(analyses):
    """Save all analyses to DynamoDB"""
    
    print(f"\n{'='*80}")
    print(f"SAVING {len(analyses)} HORSE ANALYSES TO DATABASE")
    print(f"{'='*80}\n")
    
    saved_count = 0
    failed_count = 0
    
    for analysis in analyses:
        try:
            table.put_item(Item=analysis)
            saved_count += 1
            if saved_count % 10 == 0:
                print(f"  ✓ Saved {saved_count}/{len(analyses)} analyses...")
        except Exception as e:
            failed_count += 1
            print(f"  ✗ Failed to save {analysis['horse']}: {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"SAVE COMPLETE")
    print(f"  ✓ Successfully saved: {saved_count}")
    print(f"  ✗ Failed: {failed_count}")
    print(f"  Total: {len(analyses)}")
    print(f"{'='*80}\n")
    
    return saved_count, failed_count

def generate_summary(analyses):
    """Generate summary statistics"""
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS SUMMARY")
    print(f"{'='*80}\n")
    
    # Group by race
    races = {}
    for a in analyses:
        race_key = f"{a['race_time']} - {a['market_name']}"
        if race_key not in races:
            races[race_key] = []
        races[race_key].append(a)
    
    print(f"📊 LEOPARDSTOWN RACES ANALYZED: {len(races)}")
    print(f"🐴 TOTAL HORSES ANALYZED: {len(analyses)}\n")
    
    for race_key, horses in races.items():
        print(f"\n{race_key}")
        print(f"  Runners: {len(horses)}")
        
        # Find favorite and longshot
        horses_with_odds = [h for h in horses if h['odds'] and h['odds'] > 0]
        if horses_with_odds:
            favorite = min(horses_with_odds, key=lambda x: x['odds'])
            longshot = max(horses_with_odds, key=lambda x: x['odds'])
            print(f"  Favorite: {favorite['horse']} ({favorite['odds']})")
            print(f"  Longshot: {longshot['horse']} ({longshot['odds']})")
    
    print(f"\n{'='*80}")
    print(f"READY FOR RESULTS COMPARISON")
    print(f"{'='*80}")
    print(f"\n💡 When race results come in, run comparison analysis to learn:")
    print(f"   - Which factors predicted the winner")
    print(f"   - What we missed in our analysis")
    print(f"   - How to improve future selections\n")

def main():
    """Main execution"""
    try:
        # Analyze all Leopardstown races
        analyses = analyze_leopardstown_races()
        
        if not analyses:
            print("⚠️  No Leopardstown races found in data")
            return
        
        # Save to database
        saved, failed = save_analyses_to_db(analyses)
        
        # Generate summary
        generate_summary(analyses)
        
        # Save local copy for reference
        output_file = 'leopardstown_analysis_2026_02_02.json'
        with open(output_file, 'w') as f:
            # Convert Decimal back to float for JSON
            json_safe = json.loads(json.dumps(analyses, default=str))
            json.dump(json_safe, f, indent=2)
        
        print(f"✅ Analysis also saved to: {output_file}")
        
        return analyses
        
    except FileNotFoundError:
        print("❌ Error: response_horses.json not found")
        print("   Run the workflow first to fetch race data")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
