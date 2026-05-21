"""
Comprehensive Race Analyzer
Analyzes ALL horses in ALL UK/Ireland races (not just selected picks)
Saves complete pre-race data for later comparison with results
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# UK and Ireland racing venues
UK_IRELAND_VENUES = [
    # Major UK courses
    'Cheltenham', 'Aintree', 'Ascot', 'Newmarket', 'York', 'Doncaster',
    'Kempton', 'Sandown', 'Haydock', 'Newcastle', 'Goodwood', 'Epsom',
    'Chester', 'Newbury', 'Leicester', 'Nottingham', 'Warwick', 'Chepstow',
    'Ffos Las', 'Bangor', 'Carlisle', 'Cartmel', 'Catterick', 'Exeter',
    'Fakenham', 'Fontwell', 'Hamilton', 'Hereford', 'Hexham', 'Huntingdon',
    'Kelso', 'Lingfield', 'Ludlow', 'Market Rasen', 'Musselburgh', 'Newton Abbot',
    'Perth', 'Plumpton', 'Pontefract', 'Redcar', 'Ripon', 'Salisbury',
    'Sedgefield', 'Southwell', 'Stratford', 'Taunton', 'Thirsk', 'Towcester',
    'Uttoxeter', 'Wetherby', 'Wincanton', 'Windsor', 'Wolverhampton', 'Worcester',
    
    # Irish courses
    'Leopardstown', 'Fairyhouse', 'Punchestown', 'Navan', 'Gowran', 'Cork',
    'Naas', 'Tipperary', 'Dundalk', 'Galway', 'Killarney', 'Limerick',
    'Listowel', 'Tramore', 'Thurles', 'Sligo', 'Roscommon', 'Clonmel',
    'Ballinrobe', 'Bellewstown', 'Kilbeggan', 'Downpatrick', 'Down Royal',
    'Laytown'
]

def analyze_all_uk_ireland_races():
    """Analyze every horse in every UK/Ireland race"""
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE UK/IRELAND RACE ANALYSIS")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        with open('response_horses.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("ERROR: response_horses.json not found. Run betfair_odds_fetcher.py first.")
        return 0
    
    all_races = data.get('races', [])
    
    # Filter UK/Ireland races
    uk_ireland_races = []
    for race in all_races:
        venue = race.get('venue', '')
        if any(v.lower() in venue.lower() for v in UK_IRELAND_VENUES):
            uk_ireland_races.append(race)
    
    if not uk_ireland_races:
        print("INFO: No UK/Ireland races found in current data")
        return 0
    
    print(f"Found {len(uk_ireland_races)} UK/Ireland races")
    
    # Track statistics
    total_horses = 0
    new_analyses = 0
    existing_analyses = 0
    errors = 0
    good_bets_found = 0
    good_bets = []
    
    for race in uk_ireland_races:
        market_id = race.get('market_id', race.get('marketId', 'unknown'))
        venue = race.get('venue', 'Unknown')
        start_time = race.get('start_time', 'Unknown')
        market_name = race.get('market_name', race.get('marketName', 'Unknown'))
        runners = race.get('runners', [])
        
        # Check if race already analyzed
        existing = table.scan(
            FilterExpression='market_id = :mid AND analysis_type = :type',
            ExpressionAttributeValues={
                ':mid': market_id,
                ':type': 'PRE_RACE_COMPLETE'
            }
        )
        
        if existing.get('Items'):
            existing_analyses += len(existing['Items'])
            continue  # Skip if already analyzed
        
        print(f"\n{venue} - {start_time}")
        print(f"   {market_name} | {len(runners)} runners")
        
        saved_count = 0
        
        for runner in runners:
            try:
                analysis = create_comprehensive_analysis(race, runner)
                
                if analysis:
                    table.put_item(Item=analysis)
                    saved_count += 1
                    new_analyses += 1
                    total_horses += 1
                    
                    # Check if this is a good bet
                    if analysis.get('is_good_bet'):
                        good_bets_found += 1
                        good_bets.append({
                            'horse': analysis['horse'],
                            'venue': analysis['venue'],
                            'race_time': analysis['race_time'],
                            'odds': analysis['odds'],
                            'edge': analysis.get('edge_percentage', 0)
                        })
                        save_as_pick(analysis)  # Save to database as an actual pick
                    
            except Exception as e:
                errors += 1
                print(f"   ERROR analyzing {runner.get('name', 'Unknown')}: {str(e)}")
        
        print(f"   Saved {saved_count}/{len(runners)} horses")
    
    # Summary - ONLY show if there are good bets
    if good_bets:
        print(f"\n{'='*80}")
        print(f"TODAY'S PICKS - VALUE BETS IDENTIFIED")
        print(f"{'='*80}")
        for bet in good_bets:
            print(f"  {bet['venue']} {bet['race_time']}")
            print(f"    Horse: {bet['horse']}")
            print(f"    Odds:  {bet['odds']} | Edge: {bet['edge']}%")
            print()
        print(f"{'='*80}")
        print(f"Total picks: {good_bets_found}")
        print(f"{'='*80}\n")
        
        # Save to CSV for UI
        save_picks_to_csv(good_bets)
    else:
        # Silent background learning - only show brief message
        print(f"Background analysis: {len(uk_ireland_races)} races, {total_horses} horses analyzed for learning")
        if new_analyses > 0:
            print(f"  {new_analyses} new analyses saved for training")
    
    return new_analyses

def get_horse_history(horse_name):
    """Check if horse has been analyzed/picked before and get outcomes"""
    try:
        # Search for previous picks/analyses with this horse
        response = table.scan(
            FilterExpression='horse = :name',
            ExpressionAttributeValues={
                ':name': horse_name
            }
        )
        
        previous_records = response.get('Items', [])
        
        if not previous_records:
            return {
                'has_history': False,
                'total_picks': 0,
                'wins': 0,
                'losses': 0,
                'pending': 0,
                'win_rate': 0,
                'last_outcome': None,
                'last_picked_date': None,
                'avg_odds_when_picked': 0
            }
        
        # Calculate statistics
        wins = sum(1 for r in previous_records if r.get('outcome') == 'win')
        losses = sum(1 for r in previous_records if r.get('outcome') == 'loss')
        pending = sum(1 for r in previous_records if r.get('outcome') in ['pending', None])
        
        # Sort by date to get most recent
        dated_records = [r for r in previous_records if r.get('bet_date') or r.get('analyzed_at')]
        if dated_records:
            dated_records.sort(key=lambda x: x.get('bet_date') or x.get('analyzed_at', ''), reverse=True)
            last_record = dated_records[0]
            last_outcome = last_record.get('outcome', 'unknown')
            last_date = last_record.get('bet_date') or last_record.get('analyzed_at', '')[:10]
        else:
            last_outcome = None
            last_date = None
        
        # Calculate average odds when picked
        odds_records = [float(r.get('odds', 0)) if isinstance(r.get('odds'), (int, float, str)) else 0 
                        for r in previous_records if r.get('odds')]
        avg_odds = sum(odds_records) / len(odds_records) if odds_records else 0
        
        # Calculate win rate
        total_completed = wins + losses
        win_rate = (wins / total_completed * 100) if total_completed > 0 else 0
        
        return {
            'has_history': True,
            'total_picks': len(previous_records),
            'wins': wins,
            'losses': losses,
            'pending': pending,
            'win_rate': to_decimal(round(win_rate, 1)),
            'last_outcome': last_outcome,
            'last_picked_date': last_date,
            'avg_odds_when_picked': to_decimal(round(avg_odds, 2))
        }
        
    except Exception as e:
        print(f"   Warning: Could not retrieve history for {horse_name}: {str(e)}")
        return {
            'has_history': False,
            'total_picks': 0,
            'wins': 0,
            'losses': 0,
            'pending': 0,
            'win_rate': to_decimal(0),
            'last_outcome': None,
            'last_picked_date': None,
            'avg_odds_when_picked': to_decimal(0)
        }

def create_comprehensive_analysis(race, runner):
    """Create detailed analysis for a single horse"""
    
    horse_name = runner.get('name', runner.get('runnerName', 'Unknown'))
    selection_id = runner.get('selectionId', 0)
    market_id = race.get('marketId', 'unknown')
    
    # Check horse history FIRST
    history = get_horse_history(horse_name)
    
    # Build comprehensive analysis
    analysis = {
        # Primary keys
        'bet_id': f'ANALYSIS_{market_id}_{selection_id}',
        'bet_date': datetime.now().strftime('%Y-%m-%d'),
        
        # Analysis metadata
        'analysis_type': 'PRE_RACE_COMPLETE',
        'analysis_purpose': 'CONTINUOUS_LEARNING',
        'analyzed_at': datetime.now().isoformat(),
        
        # Race information
        'venue': race.get('venue', 'Unknown'),
        'course': race.get('venue', 'Unknown'),  # Add course field for API compatibility
        'race_time': race.get('start_time', 'Unknown'),
        'market_id': market_id,
        'market_name': race.get('marketName', 'Unknown'),
        'race_type': race.get('marketType', 'Unknown'),
        'distance': str(race.get('distance', 'Unknown')),
        'going': race.get('going', 'Unknown'),
        'race_class': str(race.get('raceClass', 'Unknown')),
        
        # Horse information
        'horse': horse_name,
        'selection_id': str(selection_id),
        
        # Odds and market data
        'odds': to_decimal(runner.get('odds', 0)),
        'implied_probability': to_decimal(runner.get('implied_probability', 0)),
        'total_matched': to_decimal(runner.get('total_matched', 0)),
        'back_price': to_decimal(runner.get('back_price', 0)) if runner.get('back_price') else to_decimal(0),
        'lay_price': to_decimal(runner.get('lay_price', 0)) if runner.get('lay_price') else to_decimal(0),
        
        # Form and connections
        'form': str(runner.get('form', 'Unknown')),
        'trainer': get_string_value(runner.get('trainer', 'Unknown')),
        'jockey': get_string_value(runner.get('jockey', 'Unknown')),
        'weight': str(runner.get('weight', 'Unknown')),
        'age': str(runner.get('age', 'Unknown')),
        'days_since_run': str(runner.get('days_since_last_run', 'Unknown')),
        
        # Race-specific
        'trap': str(runner.get('trap', runner.get('clothNumber', 'Unknown'))),
        'draw': str(runner.get('stall', 'Unknown')),
        
        # Horse History (from previous picks/analyses)
        'horse_history': history,
        'has_history': history['has_history'],
        'previous_picks': history['total_picks'],
        'history_wins': history['wins'],
        'history_losses': history['losses'],
        'history_win_rate': history['win_rate'],
        'last_outcome': str(history['last_outcome']) if history['last_outcome'] else 'Unknown',
        'last_picked_date': str(history['last_picked_date']) if history['last_picked_date'] else 'Unknown',
        
        # Enhanced analysis (if available)
        'value_score': 0,
        'form_score': 0,
        'class_score': 0,
        'edge_percentage': to_decimal(0),
        'trend': 'Unknown'
    }
    
    # Add enhanced analysis if available
    if 'enhanced_analysis' in runner:
        ea = runner['enhanced_analysis']
        analysis['value_score'] = ea.get('value_score', 0)
        analysis['form_score'] = ea.get('form_score', 0)
        analysis['class_score'] = ea.get('class_score', 0)
        analysis['edge_percentage'] = to_decimal(ea.get('edge_percentage', 0))
        analysis['trend'] = ea.get('trend', 'Unknown')
        analysis['reasoning'] = ea.get('reasoning', '')
    
    # Log history if found
    if history['has_history']:
        print(f"      HISTORY: {horse_name} - {history['total_picks']} picks, {history['wins']}W-{history['losses']}L ({history['win_rate']}%), Last: {history['last_outcome']} on {history['last_picked_date']}")
    
    # Calculate simple metrics with robust form parsing
    form_str = str(analysis['form']) if analysis['form'] else ''
    if form_str and form_str != 'Unknown':
        # Clean form string - remove special characters but keep digits
        # Form can be like: "231-426", "132-111", "1/P82-92", "8P-0557"
        # We only care about digits, where 1 = win
        cleaned_form = ''.join(c for c in form_str if c.isdigit())
        
        # Count recent wins (count all '1's in the cleaned form)
        analysis['recent_wins'] = cleaned_form.count('1')
        
        # Check for LTO win (first character is '1')
        analysis['lto_winner'] = (len(cleaned_form) > 0 and cleaned_form[0] == '1')
        
        # Check for win in last 3 runs (any '1' in first 3 characters)
        analysis['win_in_last_3'] = ('1' in cleaned_form[:3])
    else:
        # Set defaults if no form
        analysis['recent_wins'] = 0
        analysis['lto_winner'] = False
        analysis['win_in_last_3'] = False
    
    # Categorize odds
    odds_val = float(analysis['odds']) if analysis['odds'] else 0
    if odds_val > 0:
        if odds_val < 3.0:
            analysis['odds_category'] = 'FAVORITE'
        elif odds_val <= 9.0:
            analysis['odds_category'] = 'SWEET_SPOT'
        elif odds_val <= 15.0:
            analysis['odds_category'] = 'OUTSIDER'
        else:
            analysis['odds_category'] = 'LONGSHOT'
    else:
        analysis['odds_category'] = 'UNKNOWN'
    
    # Check if this is a GOOD BET based on current criteria
    is_good_bet = evaluate_as_pick(analysis, odds_val)
    analysis['is_good_bet'] = is_good_bet
    
    return analysis

def evaluate_as_pick(analysis, odds_val):
    """Evaluate if this horse meets our selection criteria for a pick"""
    
    # NEW MANDATORY REJECTION RULES
    
    # 1. Negative edge = automatic rejection
    edge = float(analysis.get('edge_percentage', 0))
    if edge < 0:
        return False
    
    # Get going condition for dynamic odds ranges
    going = str(analysis.get('going', '')).lower()
    venue = str(analysis.get('venue', '')).lower()
    trainer = str(analysis.get('trainer', '')).lower()
    
    # Determine if this is heavy going
    is_heavy = 'heavy' in going
    is_soft = 'soft' in going and not is_heavy
    is_normal = not is_heavy and not is_soft  # Good, Good to Soft, etc.
    
    # Determine if this is Elliott at Leopardstown
    is_elliott_leopardstown = ('elliott' in trainer and 'leopardstown' in venue)
    
    # 2. GOING-SPECIFIC ODDS VALIDATION
    if odds_val <= 0:
        return False
    
    # Heavy going with top trainer at home course: extend to 25.0
    if is_heavy and is_elliott_leopardstown:
        if odds_val > 25.0:
            return False
    # Heavy going generally: extend to 20.0
    elif is_heavy:
        if odds_val > 20.0:
            return False
    # Normal going: stick to sweet spot range
    else:
        if odds_val > 15.0:
            return False
    
    # 3. Must have form data
    form_str = analysis.get('form', '')
    if not form_str or form_str == 'Unknown':
        return False
    
    # POSITIVE SELECTION CRITERIA WITH GOING-SPECIFIC ADJUSTMENTS
    
    score = 0
    
    # ODDS SCORING - GOING DEPENDENT
    if is_heavy:
        # Heavy going: wider range, longshots more viable
        if 10.0 <= odds_val <= 20.0:
            score += 30  # Longshots sweet spot in heavy
        elif 5.0 <= odds_val < 10.0:
            score += 25  # Mid-range good
        elif 3.0 <= odds_val < 5.0:
            score += 15  # Short odds less reliable
        else:
            score += 5
    elif is_soft:
        # Soft going: traditional sweet spot
        if 3.0 <= odds_val <= 9.0:
            score += 30  # Classic sweet spot
        elif (2.5 <= odds_val < 3.0) or (9.0 < odds_val <= 12.0):
            score += 15  # Near sweet spot
        else:
            score += 5
    else:
        # Normal going (Good to Soft): favor favorites
        if 2.5 <= odds_val <= 6.0:
            score += 35  # Favorites and near-favorites excel
        elif 6.0 < odds_val <= 9.0:
            score += 25  # Sweet spot upper range
        elif (9.0 < odds_val <= 12.0):
            score += 10  # Outsiders less reliable
        else:
            score += 5
    
    # FORM SCORING
    if analysis.get('lto_winner'):
        score += 25  # Won last race
    elif analysis.get('win_in_last_3'):
        score += 15  # Win in last 3
    
    # Multiple recent wins
    recent_wins = analysis.get('recent_wins', 0)
    if recent_wins >= 3:
        score += 15  # 3+ wins
    elif recent_wins >= 2:
        score += 10  # 2 wins
    
    # TRAINER MULTIPLIERS
    # Gordon Elliott at Leopardstown in soft/heavy = 2x boost
    if is_elliott_leopardstown and (is_soft or is_heavy):
        trainer_boost = int(score * 0.5)  # 50% boost
        score += trainer_boost
    
    # EDGE PERCENTAGE SCORING
    if edge > 20:
        score += 20
    elif edge > 10:
        score += 10
    elif edge > 0:
        score += 5
    
    # HORSE HISTORY ADJUSTMENTS
    history = analysis.get('horse_history', {})
    if history.get('has_history'):
        total_picks = history.get('total_picks', 0)
        win_rate = history.get('win_rate', 0)
        last_outcome = history.get('last_outcome')
        
        # Boost for horses with good track record when picked
        if total_picks >= 3:  # At least 3 previous picks
            if win_rate >= 50:
                score += 15  # 50%+ win rate = strong boost
            elif win_rate >= 33:
                score += 10  # 33-50% win rate = moderate boost
            elif win_rate < 20:
                score -= 10  # <20% win rate = penalty
        
        # Recent outcome matters
        if last_outcome == 'win':
            score += 5  # Last time we picked them, they won
        elif last_outcome == 'loss' and total_picks == 1:
            score -= 5  # Only picked once and lost = caution
    
    # GOING-SPECIFIC MINIMUM THRESHOLDS
    if is_heavy:
        # Lower threshold for heavy going (more variance)
        return score >= 35
    else:
        # Standard threshold for normal/soft going
        return score >= 40

def to_decimal(value):
    """Convert to Decimal for DynamoDB"""
    try:
        if value is None:
            return Decimal('0')
        return Decimal(str(value))
    except:
        return Decimal('0')

def get_string_value(value):
    """Extract string from various formats"""
    if isinstance(value, str):
        return value
    elif isinstance(value, dict):
        return value.get('name', 'Unknown')
    else:
        return 'Unknown'

def save_as_pick(analysis):
    """Save good bet as an actual pick in the database"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')
        
        # Create pick entry
        pick = {
            'bet_id': f"PICK_{analysis['market_id']}_{analysis['selection_id']}",
            'bet_date': analysis['bet_date'],
            'bet_type': 'WIN',
            'horse': analysis['horse'],
            'venue': analysis['venue'],
            'race_time': analysis['race_time'],
            'odds': analysis['odds'],
            'confidence': 'MEDIUM',  # Can be enhanced based on score
            'status': 'PENDING',
            'created_at': datetime.now().isoformat(),
            'market_id': analysis['market_id'],
            'selection_id': analysis['selection_id'],
            'form': analysis.get('form', 'Unknown'),
            'trainer': analysis.get('trainer', 'Unknown'),
            'jockey': analysis.get('jockey', 'Unknown'),
            'is_learning_pick': True,
            'edge_percentage': to_decimal(analysis.get('edge_percentage', 0))
        }
        
        table.put_item(Item=pick)
        
    except Exception as e:
        print(f"   Warning: Could not save pick: {str(e)}")

def save_picks_to_csv(good_bets):
    """Save picks to CSV for UI display"""
    try:
        import csv
        from pathlib import Path
        
        csv_file = Path('today_picks.csv')
        
        # Read existing picks if file exists
        existing_picks = []
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                existing_picks = list(reader)
        
        # Add new picks (avoid duplicates)
        fieldnames = ['venue', 'race_time', 'horse', 'odds', 'edge', 'confidence', 'bet_type']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write existing
            for pick in existing_picks:
                writer.writerow(pick)
            
            # Write new
            for bet in good_bets:
                # Check if already exists
                if not any(p.get('horse') == bet['horse'] and p.get('race_time') == bet['race_time'] 
                          for p in existing_picks):
                    writer.writerow({
                        'venue': bet['venue'],
                        'race_time': bet['race_time'],
                        'horse': bet['horse'],
                        'odds': str(bet['odds']),
                        'edge': f"{bet['edge']}%",
                        'confidence': 'MEDIUM',
                        'bet_type': 'WIN'
                    })
        
        print(f"Picks saved to {csv_file}")
        
    except Exception as e:
        print(f"Warning: Could not save to CSV: {str(e)}")

def main():
    """Main execution"""
    new_analyses = analyze_all_uk_ireland_races()
    
    if new_analyses == 0:
        print("INFO: No new races to analyze (all current races already analyzed)")
    
    return new_analyses

if __name__ == "__main__":
    main()
