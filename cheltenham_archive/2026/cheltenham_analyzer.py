"""
CHELTENHAM FESTIVAL 2026 - COMPREHENSIVE RACE ANALYZER
Advanced analysis tool for daily refinement of betting picks
Analyzes form, trainer stats, going preferences, and generates detailed reports
"""

import boto3
from datetime import datetime
from decimal import Decimal
from collections import defaultdict
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
cheltenham_table = dynamodb.Table('CheltenhamFestival2026')

# UPDATED BASED ON 5-YEAR HISTORICAL ANALYSIS (2021-2025)
# Championship race wins and specialties identified from actual results

TRAINER_STATS = {
    'Willie Mullins': {
        'festival_wins': 95, 
        'win_rate': 0.32,  # Updated: 32% in Championship races
        'grade1_wins': 45,
        'championship_wins': 7,  # 2021-2025 Championship races
        'specialties': ['Supreme Novices', 'Queen Mother Champion Chase', 'Gold Cup'],
        'weight_multiplier': 1.5,  # CRITICAL: Mullins gets priority
        'irish_trained': True
    },
    'Nicky Henderson': {
        'festival_wins': 72, 
        'win_rate': 0.28,  # Updated: Strong at Festival
        'grade1_wins': 38,
        'championship_wins': 3,  # Champion Hurdle specialist
        'specialties': ['Champion Hurdle', 'Arkle Challenge Trophy'],
        'weight_multiplier': 1.3,  # Champion Hurdle master
        'irish_trained': False
    },
    'Gordon Elliott': {
        'festival_wins': 38, 
        'win_rate': 0.26,  # Updated
        'grade1_wins': 18,
        'championship_wins': 3,  # Gold Cup & Stayers
        'specialties': ['Gold Cup', 'Stayers Hurdle'],
        'weight_multiplier': 1.3,
        'irish_trained': True
    },
    'Henry de Bromhead': {
        'festival_wins': 15, 
        'win_rate': 0.22,  # Updated: 2021-2022 dominance
        'grade1_wins': 8,
        'championship_wins': 6,  # Blackmore partnership magic
        'specialties': ['Champion Hurdle', 'Gold Cup'],
        'weight_multiplier': 1.2,
        'irish_trained': True
    },
    'Paul Nicholls': {
        'festival_wins': 48, 
        'win_rate': 0.18, 
        'grade1_wins': 22,
        'championship_wins': 0,  # Less successful in recent years
        'specialties': ['Gold Cup'],
        'weight_multiplier': 1.0,
        'irish_trained': False
    },
    'Gavin Cromwell': {
        'festival_wins': 8,
        'win_rate': 0.14,
        'grade1_wins': 3,
        'championship_wins': 3,  # Flooring Porter 3x Stayers winner
        'specialties': ['Stayers Hurdle'],
        'weight_multiplier': 1.1,
        'irish_trained': True
    }
}

JOCKEY_STATS = {
    'Paul Townend': {
        'festival_wins': 42, 
        'win_rate': 0.30,  # Updated: LETHAL with Mullins
        'champion_hurdle': 3,
        'championship_wins': 7,  # Matches Mullins - deadly combo
        'pairs_with': 'Willie Mullins',
        'combo_bonus': 10  # Extra points for Mullins/Townend
    },
    'Nico de Boinville': {
        'festival_wins': 28, 
        'win_rate': 0.25,  # Updated: Henderson partnership
        'queen_mother': 2,
        'championship_wins': 3,  # Champion Hurdle specialist
        'pairs_with': 'Nicky Henderson',
        'combo_bonus': 8
    },
    'Rachael Blackmore': {
        'festival_wins': 18, 
        'win_rate': 0.22,  # Historic 2021-2022
        'gold_cup': 1,
        'championship_wins': 5,  # 2021-2022 dominance
        'pairs_with': 'Henry de Bromhead',
        'combo_bonus': 8
    },
    'Mark Walsh': {
        'festival_wins': 15, 
        'win_rate': 0.17, 
        'grade1_wins': 8,
        'championship_wins': 0,
        'pairs_with': 'Willie Mullins',
        'combo_bonus': 5
    },
    'Jack Kennedy': {
        'festival_wins': 12, 
        'win_rate': 0.18,  # Updated
        'grade1_wins': 6,
        'championship_wins': 2,  # Elliott partnership
        'pairs_with': 'Gordon Elliott',
        'combo_bonus': 6
    },
    'Davy Russell': {
        'festival_wins': 9,
        'win_rate': 0.15,
        'championship_wins': 1,
        'pairs_with': 'Gordon Elliott',
        'combo_bonus': 5
    }
}

# Going preferences (how horses perform on different ground)
GOING_IMPACT = {
    'GOOD_TO_FIRM': 'Fast ground specialist',
    'GOOD': 'Versatile performer',
    'GOOD_TO_SOFT': 'Acts on any ground',
    'SOFT': 'Stays well in testing conditions',
    'HEAVY': 'Loves heavy ground',
}


def analyze_form_string(form, previous_festival_winner=False):
    """Detailed form analysis with Championship patterns
    
    Historical analysis shows:
    - '111' or '1111' form = STRONG indicator
    - Previous Festival winners = 27.3% of Championship winners
    - Consistent Grade 1 form crucial
    """
    
    if not form or form == 'N/A':
        return {
            'score': 50,
            'analysis': 'No form data available',
            'consistency': 'Unknown'
        }
    
    form = form.replace('-', '')
    score = 50
    
    # CRITICAL: Historical pattern - winning streaks matter at Cheltenham
    # Recent wins (last 5 runs)
    recent = form[:5]
    wins = recent.count('1')
    places = recent.count('2') + recent.count('3')
    poor = recent.count('0') + recent.count('P') + recent.count('F')
    
    # Scoring with Championship weights
    score += wins * 12
    score += places * 6
    score -= poor * 8
    
    # CRITICAL: Previous Festival winner bonus (27.3% historical edge)
    if previous_festival_winner:
        score += 20
        analysis_prefix = "🏆 PREVIOUS FESTIVAL WINNER - "
    else:
        analysis_prefix = ""
    
    # Consistency check
    if len(recent) >= 3:
        if '1' in recent[:3]:
            score += 5  # Recent win bonus
        if recent[:3].count('1') + recent[:3].count('2') >= 2:
            consistency = 'Consistent'
            score += 3
        elif poor >= 2:
            consistency = 'Inconsistent'
            score -= 5
        else:
            consistency = 'Moderate'
    else:
        consistency = 'Insufficient data'
    
    # CRITICAL: Historical analysis shows '111' or '1111' patterns win
    if recent.startswith('1111'):
        score += 18
        analysis = analysis_prefix + 'EXCEPTIONAL FORM - 4 straight wins (Championship pattern)'
    elif recent.startswith('111'):
        score += 15
        analysis = analysis_prefix + 'ELITE FORM - 3 straight wins (Championship pattern)'
    elif recent.startswith('11'):
        score += 10
        analysis = analysis_prefix + 'Excellent recent form - on a winning streak'
    elif '1' in recent and places >= 1:
        analysis = analysis_prefix + 'Good form - competitive'
    elif wins >= 2:
        analysis = analysis_prefix + 'Capable winner but not consistent'
    elif places >= 2:
        analysis = analysis_prefix + 'Regularly places but lacks wins'
    elif poor >= 2:
        analysis = analysis_prefix + 'Poor recent form - concerning'
    else:
        analysis = analysis_prefix + 'Mixed form - unpredictable'
    
    score = max(0, min(100, score))
    
    return {
        'score': score,
        'analysis': analysis,
        'consistency': consistency,
        'wins': wins,
        'places': places,
        'poor_runs': poor,
        'festival_winner_bonus': previous_festival_winner
    }


def analyze_trainer_jockey(trainer, jockey, race_grade, race_name=''):
    """Analyze trainer/jockey suitability for Cheltenham with Championship focus"""
    
    score = 50
    notes = []
    
    # CRITICAL: Historical analysis shows trainer importance at Cheltenham
    # 72.7% of Championship winners are Irish trained
    # Willie Mullins: 32% strike rate in Championship races
    
    # Trainer analysis
    if trainer in TRAINER_STATS:
        stats = TRAINER_STATS[trainer]
        
        # Base festival experience score
        score += min(20, stats['festival_wins'] // 5)
        
        # Apply Championship-specific weight multiplier
        championship_bonus = int((stats.get('weight_multiplier', 1.0) - 1.0) * 20)
        score += championship_bonus
        
        # Championship race wins are CRITICAL
        championship_wins = stats.get('championship_wins', 0)
        if championship_wins >= 5:
            notes.append(f"🏆 {trainer} - ELITE Championship record ({championship_wins} Championship wins)")
            score += 15
        elif championship_wins >= 3:
            notes.append(f"⭐ {trainer} - Strong Championship record ({championship_wins} wins)")
            score += 10
        elif championship_wins >= 1:
            notes.append(f"✅ {trainer} - Championship winner ({championship_wins} wins)")
            score += 5
        
        # Irish trained bonus (72.7% historical edge)
        if stats.get('irish_trained', False):
            score += 8
            notes.append(f"🇮🇪 Irish trained - 73% of Championship winners")
        
        # Race specialty matching
        specialties = stats.get('specialties', [])
        if race_name and any(specialty.lower() in race_name.lower() for specialty in specialties):
            score += 12
            notes.append(f"🎯 {trainer} specialist in this race type")
        
        # Win rate indicator
        if stats['win_rate'] >= 0.30:
            notes.append(f"⭐⭐ Elite win rate: {int(stats['win_rate']*100)}%")
            score += 8
        elif stats['win_rate'] >= 0.20:
            notes.append(f"⭐ Strong win rate: {int(stats['win_rate']*100)}%")
            score += 4
        
        # Grade 1 experience
        if race_grade == 'Grade 1' and stats['grade1_wins'] >= 10:
            score += 6
            notes.append(f"  Grade 1 proven ({stats['grade1_wins']} G1 wins)")
    else:
        notes.append(f"⚠️ {trainer} - No Championship record")
        score -= 8  # Increased penalty - history matters
    
    # Jockey analysis
    if jockey in JOCKEY_STATS:
        stats = JOCKEY_STATS[jockey]
        score += min(15, stats['festival_wins'] // 3)
        
        # Championship wins matter
        championship_wins = stats.get('championship_wins', 0)
        if championship_wins >= 5:
            notes.append(f"🏆 {jockey} - ELITE Championship jockey ({championship_wins} wins)")
            score += 12
        elif championship_wins >= 3:
            notes.append(f"⭐ {jockey} - Championship winner ({championship_wins} wins)")
            score += 8
        elif championship_wins >= 1:
            notes.append(f"✅ {jockey} - Championship experience")
            score += 4
        
        # Trainer-Jockey combination bonus (historical partnerships)
        pairs_with = stats.get('pairs_with', '')
        combo_bonus = stats.get('combo_bonus', 0)
        if pairs_with and pairs_with.lower() in trainer.lower():
            score += combo_bonus
            notes.append(f"🤝 PROVEN PARTNERSHIP: {trainer} & {jockey} (+{combo_bonus} pts)")
        
        # Experience level
        if stats['win_rate'] >= 0.25:
            notes.append(f"⭐⭐ Top jockey: {int(stats['win_rate']*100)}% win rate")
        elif stats['win_rate'] >= 0.15:
            notes.append(f"⭐ Experienced: {int(stats['win_rate']*100)}% win rate")
    else:
        notes.append(f"⚠️ {jockey} - Limited Championship experience")
        score -= 5
    
    score = max(0, min(100, score))
    
    return {
        'score': score,
        'notes': notes
    }


def calculate_odds_value(odds_string, confidence):
    """Calculate if odds represent value based on confidence
    
    Historical analysis: 40.9% of Championship favorites win
    DON'T FEAR SHORT PRICES at Cheltenham - favorites perform well
    """
    
    if not odds_string or odds_string == 'N/A':
        return {
            'value_rating': 'Unknown',
            'implied_probability': 0,
            'our_probability': confidence,
            'analysis': 'No odds available'
        }
    
    # Convert odds to decimal
    try:
        if '/' in odds_string:
            parts = odds_string.split('/')
            decimal_odds = (float(parts[0]) / float(parts[1])) + 1
        else:
            decimal_odds = float(odds_string)
    except:
        return {'value_rating': 'Error', 'analysis': 'Invalid odds format'}
    
    # Calculate implied probability
    implied_prob = (1 / decimal_odds) * 100
    our_prob = confidence
    
    # CRITICAL: Cheltenham-specific logic
    # Favorites win 40.9% of Championship races - don't be afraid of short prices
    is_favorite = implied_prob >= 35  # Roughly 2/1 or shorter
    
    # Value calculation
    value_diff = our_prob - implied_prob
    
    # Adjusted value ratings for Cheltenham
    if is_favorite and our_prob >= 75:
        # Don't penalize good favorites at Cheltenham
        if value_diff >= -5:
            value_rating = '🏆 FAVORITE - BACK IT'
            analysis = f'Strong favorite. We rate {our_prob:.0f}% vs {implied_prob:.0f}% implied. Historical: 41% of favorites win.'
        elif value_diff >= -15:
            value_rating = '✅ FAVORITE - FAIR PRICE'
            analysis = f'Fair favorite price. {our_prob:.0f}% vs {implied_prob:.0f}%. Favorites win 41% at Cheltenham.'
        else:
            value_rating = '⚠️ FAVORITE - SLIGHTLY SHORT'
            analysis = f'Favorite but slightly short at {implied_prob:.0f}% vs our {our_prob:.0f}%'
    elif value_diff >= 20:
        value_rating = '🔥 EXCELLENT VALUE'
        analysis = f'Massive value! We rate {our_prob:.0f}% but odds imply {implied_prob:.0f}%'
    elif value_diff >= 10:
        value_rating = '✅ GOOD VALUE'
        analysis = f'Good value bet. We rate {our_prob:.0f}% vs {implied_prob:.0f}% implied'
    elif value_diff >= 0:
        value_rating = '👍 FAIR VALUE'
        analysis = f'Fair odds. Our {our_prob:.0f}% matches market {implied_prob:.0f}%'
    elif value_diff >= -10:
        value_rating = '⚠️ SLIGHT OVERPRICED'
        analysis = f'Slightly short. {implied_prob:.0f}% implied but we rate {our_prob:.0f}%'
    else:
        value_rating = '❌ POOR VALUE'
        analysis = f'Avoid. Odds too short ({implied_prob:.0f}% vs our {our_prob:.0f}%)'
    
    return {
        'value_rating': value_rating,
        'implied_probability': round(implied_prob, 1),
        'our_probability': round(our_prob, 1),
        'value_difference': round(value_diff, 1),
        'analysis': analysis,
        'decimal_odds': round(decimal_odds, 2),
        'is_favorite': is_favorite
    }


def generate_comprehensive_horse_analysis(horse_data, race_name=''):
    """Generate complete analysis for a single horse with Championship patterns"""
    
    print("\n" + "="*80)
    print(f"ANALYZING: {horse_data.get('horseName', 'Unknown')}")
    print("="*80)
    
    # Check for previous Festival winner (27.3% edge)
    previous_festival_winner = horse_data.get('previousFestivalWinner', False)
    notes = horse_data.get('notes', '')
    if not previous_festival_winner and notes:
        # Check notes for Festival history
        if 'festival win' in notes.lower() or 'cheltenham win' in notes.lower():
            previous_festival_winner = True
    
    # Form analysis with historical patterns
    form = horse_data.get('form', '')
    form_analysis = analyze_form_string(form, previous_festival_winner)
    
    print(f"\n📊 FORM ANALYSIS:")
    print(f"  Form: {form}")
    print(f"  Score: {form_analysis['score']}/100")
    print(f"  {form_analysis['analysis']}")
    print(f"  Consistency: {form_analysis['consistency']}")
    print(f"  Wins: {form_analysis.get('wins', 0)} | Places: {form_analysis.get('places', 0)}")
    if previous_festival_winner:
        print(f"  🏆 PREVIOUS FESTIVAL WINNER (+20 pts historical edge)")
    
    # Trainer/Jockey analysis with Championship focus
    trainer = horse_data.get('trainer', 'Unknown')
    jockey = horse_data.get('jockey', 'Unknown')
    race_grade = horse_data.get('raceGrade', 'Grade 1')
    
    tj_analysis = analyze_trainer_jockey(trainer, jockey, race_grade, race_name)
    
    print(f"\n👨‍🏫 TRAINER/JOCKEY ANALYSIS:")
    print(f"  Score: {tj_analysis['score']}/100")
    for note in tj_analysis['notes']:
        print(f"  {note}")
    
    # Calculate final confidence with Championship weights
    base_confidence = float(horse_data.get('confidenceRank', 50))
    
    # CRITICAL: Historical analysis weight distribution
    form_weight = 0.35      # Form patterns matter (111, 1111)
    tj_weight = 0.40        # Trainer/Jockey CRITICAL at Cheltenham
    base_weight = 0.25      # Base research
    
    final_confidence = (
        form_analysis['score'] * form_weight +
        tj_analysis['score'] * tj_weight +
        base_confidence * base_weight
    )
    
    # Odds value analysis (respecting 40.9% favorite win rate)
    odds = horse_data.get('currentOdds', 'N/A')
    value_analysis = calculate_odds_value(odds, final_confidence)
    
    print(f"\n💰 ODDS VALUE ANALYSIS:")
    print(f"  Current Odds: {odds}")
    print(f"  {value_analysis['value_rating']}")
    print(f"  {value_analysis['analysis']}")
    if value_analysis.get('decimal_odds'):
        print(f"  Decimal: {value_analysis['decimal_odds']}")
    
    # Final recommendation with Championship thresholds
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"  Confidence: {final_confidence:.1f}%")
    
    # Championship-specific recommendation thresholds
    if final_confidence >= 90:
        recommendation = "🏆 BANKER BET"
        bet_size = "4x stake (Championship banker)"
    elif final_confidence >= 80:
        recommendation = "🔥 STRONG BET"
        bet_size = "3x stake"
    elif final_confidence >= 70:
        recommendation = "✅ BET"
        bet_size = "2x stake"
    elif final_confidence >= 60:
        recommendation = "👀 WATCH"
        bet_size = "1x stake"
    elif final_confidence >= 50:
        recommendation = "⏸️ HOLD"
        bet_size = "Consider small stake"
    else:
        recommendation = "❌ AVOID"
        bet_size = "No bet"
    
    # Special override for favorites with good confidence (40.9% win rate)
    if value_analysis.get('is_favorite') and final_confidence >= 75:
        print(f"  ⚠️ FAVORITE ALERT: 40.9% historical Championship favorite win rate")
    
    print(f"  Recommendation: {recommendation}")
    print(f"  Suggested Stake: {bet_size}")
    
    return {
        'finalConfidence': final_confidence,
        'recommendation': recommendation,
        'formAnalysis': form_analysis,
        'trainerJockeyAnalysis': tj_analysis,
        'valueAnalysis': value_analysis,
        'previousFestivalWinner': previous_festival_winner
    }


def analyze_entire_race(race_id):
    """Analyze all horses in a race and rank them"""
    
    print("\n" + "="*100)
    print(f"RACE ANALYSIS: {race_id}")
    print("="*100)
    
    # Get all horses in race
    response = cheltenham_table.query(
        KeyConditionExpression='raceId = :raceId',
        ExpressionAttributeValues={':raceId': race_id}
    )
    
    items = response.get('Items', [])
    race_info = next((item for item in items if item.get('horseId') == 'RACE_INFO'), None)
    horses = [item for item in items if item.get('horseId') != 'RACE_INFO']
    
    if race_info:
        print(f"\n📅 {race_info.get('raceName', 'Unknown Race')}")
        print(f"   Time: {race_info.get('raceTime', 'TBC')}")
        print(f"   Grade: {race_info.get('raceGrade', 'N/A')}")
        print(f"   Distance: {race_info.get('raceDistance', 'N/A')}")
    
    if not horses:
        print("\n⚠️ No horses added to this race yet")
        return
    
    print(f"\n🐴 Found {len(horses)} horses to analyze\n")
    
    # Analyze each horse
    horse_analyses = []
    for horse in horses:
        analysis = generate_comprehensive_horse_analysis(horse)
        horse_analyses.append({
            'horse': horse,
            'analysis': analysis
        })
    
    # Sort by confidence
    horse_analyses.sort(key=lambda x: x['analysis']['finalConfidence'], reverse=True)
    
    # Print rankings
    print("\n" + "="*100)
    print("FINAL RANKINGS")
    print("="*100)
    
    print(f"\n{'Rank':<6}{'Horse':<25}{'Odds':<10}{'Confidence':<15}{'Recommendation':<20}{'Value':<15}")
    print("-"*100)
    
    for i, ha in enumerate(horse_analyses, 1):
        horse = ha['horse']
        analysis = ha['analysis']
        
        print(f"{i:<6}{horse.get('horseName', 'Unknown'):<25}"
              f"{horse.get('currentOdds', 'N/A'):<10}"
              f"{analysis['finalConfidence']:.1f}%{'':<10}"
              f"{analysis['recommendation']:<20}"
              f"{analysis['valueAnalysis'].get('value_rating', 'N/A'):<15}")
    
    # Top pick summary
    if horse_analyses:
        top_pick = horse_analyses[0]
        print("\n" + "="*100)
        print("🏆 TOP PICK")
        print("="*100)
        print(f"\nHorse: {top_pick['horse'].get('horseName')}")
        print(f"Confidence: {top_pick['analysis']['finalConfidence']:.1f}%")
        print(f"Odds: {top_pick['horse'].get('currentOdds')}")
        print(f"Recommendation: {top_pick['analysis']['recommendation']}")
        print(f"Value: {top_pick['analysis']['valueAnalysis']['value_rating']}")


def daily_refinement_report():
    """Generate daily report for all races with horses"""
    
    print("\n" + "="*100)
    print(f"CHELTENHAM FESTIVAL 2026 - DAILY REFINEMENT REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)
    
    # Get all races
    response = cheltenham_table.scan()
    items = response.get('Items', [])
    
    # Group by race
    races = {}
    for item in items:
        race_id = item.get('raceId')
        if race_id not in races:
            races[race_id] = []
        races[race_id].append(item)
    
    # Analyze races with horses
    analyzed_count = 0
    for race_id, race_items in sorted(races.items()):
        horses = [item for item in race_items if item.get('horseId') != 'RACE_INFO']
        
        if len(horses) > 0:
            analyze_entire_race(race_id)
            analyzed_count += 1
    
    print("\n" + "="*100)
    print(f"REPORT COMPLETE")
    print("="*100)
    print(f"\nAnalyzed {analyzed_count} races")
    print(f"Next refinement: Tomorrow at 08:00")
    print("\n" + "="*100)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # Analyze specific race
        race_id = sys.argv[1]
        analyze_entire_race(race_id)
    else:
        # Full daily report
        daily_refinement_report()
