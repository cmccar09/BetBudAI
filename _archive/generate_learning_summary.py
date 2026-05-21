"""
Generate Learning Summary
Analyzes all results and generates insights for improving selection logic
"""

import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import json

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

def generate_comprehensive_summary(days=7):
    """Generate learning summary for last N days"""
    
    print(f"\n{'='*80}")
    print(f"LEARNING SUMMARY - Last {days} Days")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Query all race results from last N days
    results = []
    for day_offset in range(days):
        date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d')
        
        response = table.scan(
            FilterExpression='learning_type = :type AND bet_date = :date',
            ExpressionAttributeValues={
                ':type': 'RACE_RESULT_ANALYSIS',
                ':date': date
            }
        )
        
        results.extend(response.get('Items', []))
    
    if not results:
        print("ℹ️  No race results found in the specified period")
        return None
    
    print(f"📊 Analyzing {len(results)} race results\n")
    
    # Initialize statistics
    stats = {
        'total_races': len(results),
        'by_odds_category': defaultdict(int),
        'by_position': defaultdict(int),
        'by_form': defaultdict(int),
        'by_venue': defaultdict(int),
        'favorites_won': 0,
        'sweet_spot_won': 0,
        'longshots_won': 0,
        'lto_winners': 0,
        'win_in_last_3': 0,
        'multiple_recent_wins': 0,
        'average_winner_odds': 0,
        'median_winner_odds': 0
    }
    
    winner_odds = []
    
    # Analyze each result
    for result in results:
        # Odds category
        category = result.get('winner_odds_category', 'UNKNOWN')
        stats['by_odds_category'][category] += 1
        
        if category == 'SWEET_SPOT':
            stats['sweet_spot_won'] += 1
        elif category == 'FAVORITE':
            stats['favorites_won'] += 1
        elif category == 'LONGSHOT':
            stats['longshots_won'] += 1
        
        # Position in betting
        position = result.get('winner_position_in_betting', 0)
        stats['by_position'][position] += 1
        
        # Venue
        venue = result.get('venue', 'Unknown')
        stats['by_venue'][venue] += 1
        
        # Form patterns
        insights = result.get('insights', [])
        if any('LTO winner' in i for i in insights):
            stats['lto_winners'] += 1
        if any('win in last 3' in i for i in insights):
            stats['win_in_last_3'] += 1
        if any('recent wins' in i for i in insights):
            stats['multiple_recent_wins'] += 1
        
        # Track odds
        odds = float(result.get('winner_odds', 0))
        if odds > 0:
            winner_odds.append(odds)
    
    # Calculate averages
    if winner_odds:
        stats['average_winner_odds'] = sum(winner_odds) / len(winner_odds)
        winner_odds.sort()
        mid = len(winner_odds) // 2
        stats['median_winner_odds'] = winner_odds[mid]
    
    # Print detailed summary
    print_summary(stats, days)
    
    # Generate recommendations
    recommendations = generate_recommendations(stats)
    
    # Save to database
    summary_entry = {
        'bet_id': f'SUMMARY_{datetime.now().strftime("%Y%m%d_%H%M")}',
        'bet_date': datetime.now().strftime('%Y-%m-%d'),
        'learning_type': 'LEARNING_SUMMARY',
        'period_days': days,
        'total_races': stats['total_races'],
        'sweet_spot_wins': stats['sweet_spot_won'],
        'sweet_spot_pct': to_decimal(100 * stats['sweet_spot_won'] / stats['total_races']),
        'favorites_won': stats['favorites_won'],
        'favorite_pct': to_decimal(100 * stats['favorites_won'] / stats['total_races']),
        'lto_winners': stats['lto_winners'],
        'lto_pct': to_decimal(100 * stats['lto_winners'] / stats['total_races']),
        'average_winner_odds': to_decimal(stats['average_winner_odds']),
        'median_winner_odds': to_decimal(stats['median_winner_odds']),
        'recommendations': recommendations,
        'analyzed_at': datetime.now().isoformat()
    }
    
    table.put_item(Item=summary_entry)
    
    print(f"\n✅ Summary saved to database\n")
    
    return stats

def print_summary(stats, days):
    """Print formatted summary"""
    
    total = stats['total_races']
    
    print(f"{'='*80}")
    print(f"ODDS ANALYSIS")
    print(f"{'='*80}")
    print(f"Sweet Spot (3-9 odds):  {stats['sweet_spot_won']:4d} / {total:4d} = {100*stats['sweet_spot_won']/total:5.1f}%")
    print(f"Favorites (< 3.0):      {stats['favorites_won']:4d} / {total:4d} = {100*stats['favorites_won']/total:5.1f}%")
    print(f"Longshots (> 15.0):     {stats['longshots_won']:4d} / {total:4d} = {100*stats['longshots_won']/total:5.1f}%")
    print(f"\nAverage winner odds:    {stats['average_winner_odds']:.2f}")
    print(f"Median winner odds:     {stats['median_winner_odds']:.2f}")
    
    print(f"\n{'='*80}")
    print(f"FORM ANALYSIS")
    print(f"{'='*80}")
    print(f"LTO winners:            {stats['lto_winners']:4d} / {total:4d} = {100*stats['lto_winners']/total:5.1f}%")
    print(f"Win in last 3 runs:     {stats['win_in_last_3']:4d} / {total:4d} = {100*stats['win_in_last_3']/total:5.1f}%")
    print(f"Multiple recent wins:   {stats['multiple_recent_wins']:4d} / {total:4d} = {100*stats['multiple_recent_wins']/total:5.1f}%")
    
    print(f"\n{'='*80}")
    print(f"BETTING POSITION")
    print(f"{'='*80}")
    positions_sorted = sorted(stats['by_position'].items())
    for pos, count in positions_sorted[:10]:  # Top 10 positions
        if pos > 0:
            print(f"{pos:2d}{'st' if pos==1 else 'nd' if pos==2 else 'rd' if pos==3 else 'th':2s} favorite:  {count:4d} / {total:4d} = {100*count/total:5.1f}%")
    
    print(f"\n{'='*80}")
    print(f"TOP VENUES (by wins)")
    print(f"{'='*80}")
    venues_sorted = sorted(stats['by_venue'].items(), key=lambda x: x[1], reverse=True)
    for venue, count in venues_sorted[:10]:
        print(f"{venue:20s} {count:4d} races")
    
    print(f"{'='*80}\n")

def generate_recommendations(stats):
    """Generate actionable recommendations based on data"""
    
    total = stats['total_races']
    recommendations = []
    
    # Sweet spot analysis
    sweet_spot_pct = 100 * stats['sweet_spot_won'] / total
    if sweet_spot_pct > 40:
        recommendations.append(f"STRONG: Sweet spot (3-9 odds) producing {sweet_spot_pct:.1f}% of winners - PRIORITIZE THIS RANGE")
    elif sweet_spot_pct > 30:
        recommendations.append(f"GOOD: Sweet spot producing {sweet_spot_pct:.1f}% of winners - maintain focus")
    else:
        recommendations.append(f"WEAK: Sweet spot only {sweet_spot_pct:.1f}% of winners - may need to adjust range")
    
    # Favorite analysis
    favorite_pct = 100 * stats['favorites_won'] / total
    if favorite_pct > 40:
        recommendations.append(f"WARNING: Favorites winning {favorite_pct:.1f}% - market very efficient, harder to find value")
    elif favorite_pct < 25:
        recommendations.append(f"OPPORTUNITY: Favorites only {favorite_pct:.1f}% - upsets common, good for value hunting")
    
    # LTO winner analysis
    lto_pct = 100 * stats['lto_winners'] / total
    if lto_pct > 30:
        recommendations.append(f"STRONG: LTO winners at {lto_pct:.1f}% - PRIORITIZE horses that won last race")
    elif lto_pct > 20:
        recommendations.append(f"GOOD: LTO winners at {lto_pct:.1f}% - factor in recent wins")
    
    # Form in last 3
    form_3_pct = 100 * stats['win_in_last_3'] / total
    if form_3_pct > 50:
        recommendations.append(f"CRITICAL: {form_3_pct:.1f}% had win in last 3 - this is ESSENTIAL criteria")
    
    # Odds range recommendation
    if stats['median_winner_odds'] < 5.0:
        recommendations.append("ADJUST: Median winner odds low - consider tightening to 3-6 range")
    elif stats['median_winner_odds'] > 8.0:
        recommendations.append("ADJUST: Median winner odds high - can extend upper range to 12")
    
    print(f"💡 RECOMMENDATIONS:\n")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return recommendations

def to_decimal(value):
    """Convert to Decimal"""
    try:
        return Decimal(str(value))
    except:
        return Decimal('0')

def main():
    """Generate summary for last 7 days"""
    stats = generate_comprehensive_summary(days=7)
    return stats

if __name__ == "__main__":
    main()
