"""
Add The Dark Baron pick to database with comprehensive analysis
"""
import boto3
from datetime import datetime
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# The Dark Baron @ 5.1 - comprehensive analysis winner
pick = {
    'bet_id': '2026-02-02T190000.000Z_Wolverhampton_The_Dark_Baron',
    'bet_date': '2026-02-02',
    'course': 'Wolverhampton',
    'horse': 'The Dark Baron',
    'odds': Decimal('5.1'),
    'race_time': '2026-02-02T19:00:00.000Z',
    'sport': 'Horse Racing',
    'race_type': '1m1f Hcap',
    'confidence': Decimal('85'),
    'show_in_ui': True,
    
    # Comprehensive analysis details
    'analysis_method': 'COMPREHENSIVE',
    'analysis_score': Decimal('73'),
    'form': '41332-3',
    'trainer': 'Kathy Turner',
    'selection_id': '72592572',
    
    'reasoning': 'Comprehensive analysis (73pts): Optimal odds position (5.1 vs avg 4.65), consistent form (1W-4P), fits Wolverhampton 4/4 pattern today',
    
    'why_selected': [
        'Sweet spot validated (10/10 today = 100%)',
        'Optimal odds: 5.1 (only 0.45 from average winner 4.65)',
        'Wolverhampton perfect: 4/4 today (4.0, 4.0, 5.0, 6.0)',
        'Consistent form: 41332-3 (1 win, 4 places)',
        'Beats Magic Runner by 21pts in comprehensive scoring'
    ],
    
    'analysis_breakdown': {
        'sweet_spot_bonus': 30,
        'total_wins': 5,
        'consistency_places': 8,
        'optimal_odds_bonus': 20,
        'wolverhampton_bonus': 10,
        'total_score': 73
    },
    
    'tags': [
        'comprehensive_analysis',
        'optimal_odds',
        'wolverhampton_validated',
        'sweet_spot',
        'consistent_placer'
    ],
    
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat(),
    'source': 'comprehensive_learnings'
}

print("\nAdding The Dark Baron @ 5.1 to database...")
print(f"Analysis Score: 73 (highest of 5 sweet spot horses)")
print(f"Form: 41332-3 (1 win, 4 places = very consistent)")
print(f"Odds Quality: 5.1 (optimal - only 0.45 from 4.65 average)")
print(f"Wolverhampton: Fits 4/4 pattern (4.0, 4.0, 5.0, 6.0)")

table.put_item(Item=pick)

print("\n✓ The Dark Baron added to database")
print("✓ show_in_ui = True (will appear in UI)")
print("\nComprehensive analysis factors:")
print("  • Sweet spot validation: 10/10 (100%)")
print("  • Optimal odds position: Near 4.65 average")
print("  • Wolverhampton performance: 4/4 today")
print("  • Form consistency: 4 places in 6 races")
print("  • Database history: Checked (none found)")
print("  • Total score: 73/100")

# Verify
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

visible = [item for item in response['Items'] 
           if not item.get('analysis_type') 
           and not item.get('learning_type')
           and item.get('show_in_ui') == True]

print(f"\n✓ Total visible picks in database: {len(visible)}")
for p in sorted(visible, key=lambda x: x.get('race_time', '')):
    print(f"  • {p.get('horse')} @ {p.get('odds')} - {p.get('race_time', 'Unknown')[:16]}")
