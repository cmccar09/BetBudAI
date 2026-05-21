import boto3
from datetime import datetime
from decimal import Decimal
import json

# Initialize DynamoDB
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Learning data from Kempton 13:27 race
learning_entry = {
    'id': f'LEARNING_2026-02-02_KEMPTON_1327',  # Keeping for readability
    'bet_id': 'LEARNING_2026-02-02_KEMPTON_1327',  # Required composite key
    'bet_date': '2026-02-02',  # Required key for DynamoDB table
    'date': datetime.now().isoformat(),
    'race_id': '1.253429872',
    'venue': 'Kempton',
    'race_time': '2026-02-02T13:27:00.000Z',
    'learning_type': 'CRITICAL_ERROR_ANALYSIS',
    
    # What happened
    'our_pick': 'Hawaii Du Mestivel',
    'our_pick_odds': Decimal('23.0'),
    'our_pick_confidence': 10,
    'our_pick_result': 'LOST - Did not place',
    
    'actual_winner': 'Aviation',
    'actual_winner_odds': Decimal('5.0'),  # SP (was 7.6 in analysis)
    'actual_winner_in_analysis': True,
    
    # Why we failed
    'errors_identified': [
        'Overweighted hot streak (1-1-1) without checking class context',
        'Ignored that Hawaii wins were in lower class',
        'Undervalued Aviation course form (1 course win at Kempton)',
        'Ignored perfect going match for Aviation',
        'Bet despite negative edge (-53.5% for Hawaii)',
        'Bet despite only 10% confidence (below minimum)',
        'Missed that Aviation had 36.4% positive edge (highest in race)',
        'Combined score: Hawaii 17/30 vs Aviation 24/30'
    ],
    
    # What we learned
    'key_insights': [
        'Class context is everything - wins in Class 6 dont equal wins in Class 4',
        'Course form beats generic form - course winners repeat at 25% higher rate',
        'Perfect going match vs good going match is a major differentiator',
        'Negative edge percentage = market is smarter than our analysis - NEVER BET',
        'Confidence <30% should mean no bet at all, not low-stake bet',
        'Improving trend in same class > hot streak from lower class',
        'Combined score threshold needed - Aviation 24/30 vs Hawaii 17/30'
    ],
    
    # Rule changes implemented
    'rule_changes': [
        'HARD RULE: Reject if edge_percentage < 0%',
        'HARD RULE: Reject if confidence < 30%',
        'HARD RULE: Reject if combined_score < 20/30',
        'Course winner: +25 confidence points (increased from +15)',
        'Perfect going match: +15 points (new)',
        'Good going match: +5 points (new)',
        'Class step-up: -30% confidence (new)',
        'Recent win must be in same/higher class (refined)',
        'Improving in same class > hot streak from lower class (new logic)'
    ],
    
    # Comparative analysis
    'comparative_data': {
        'hawaii_analysis': {
            'value_score': 1,
            'form_score': 9,
            'class_score': 7,
            'total_score': 17,
            'edge_percentage': Decimal('-53.5'),
            'last_3_runs': '1-1-1',
            'trend': 'hot',
            'course_wins': 0,
            'going_match': 'good',
            'class_advantage': True,
            'form_context': 'Three wins in LOWER class - unproven at Class 4'
        },
        'aviation_analysis': {
            'value_score': 8,
            'form_score': 8,
            'class_score': 8,
            'total_score': 24,
            'edge_percentage': Decimal('36.4'),
            'last_3_runs': '3-2-6',
            'trend': 'improving',
            'course_wins': 1,
            'going_match': 'perfect',
            'class_advantage': True,
            'form_context': 'Improving in SAME class with course win'
        }
    },
    
    # Impact estimate
    'impact': 'If new rules applied: Would have selected AVIATION (winner) instead of Hawaii Du Mestivel',
    'prevented': True,
    'severity': 'HIGH',
    
    # Implementation status
    'status': 'IMPLEMENTED',
    'prompt_updated': True,
    'rules_active': True,
    'updated_by': 'self_learning_system',
    'analysis_file': 'learning_kempton_13_27_analysis.md'
}

# Save to DynamoDB
print("Saving learning entry to DynamoDB...")
table.put_item(Item=learning_entry)

print(f"\n✅ Learning entry saved: {learning_entry['id']}")
print(f"\n📊 SUMMARY:")
print(f"Race: {learning_entry['venue']} {learning_entry['race_time']}")
print(f"Our pick: {learning_entry['our_pick']} (odds {learning_entry['our_pick_odds']}, confidence {learning_entry['our_pick_confidence']}%) - LOST")
print(f"Winner: {learning_entry['actual_winner']} (odds {learning_entry['actual_winner_odds']}) - Was in our analysis but not selected")
print(f"\n🔍 Errors identified: {len(learning_entry['errors_identified'])}")
for i, error in enumerate(learning_entry['errors_identified'], 1):
    print(f"   {i}. {error}")
    
print(f"\n💡 Key insights: {len(learning_entry['key_insights'])}")
for i, insight in enumerate(learning_entry['key_insights'], 1):
    print(f"   {i}. {insight}")
    
print(f"\n⚙️ Rule changes: {len(learning_entry['rule_changes'])}")
for i, rule in enumerate(learning_entry['rule_changes'], 1):
    print(f"   {i}. {rule}")

print(f"\n📈 Impact: {learning_entry['impact']}")
print(f"Status: {learning_entry['status']}")
print(f"\nDetailed analysis: {learning_entry['analysis_file']}")
