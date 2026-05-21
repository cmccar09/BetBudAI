import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get all learning entries
response = table.scan(
    FilterExpression='begins_with(bet_id, :prefix)',
    ExpressionAttributeValues={':prefix': 'LEARNING_'}
)

learnings = response['Items']

print(f'\nLEARNINGS FOUND: {len(learnings)}\n')
print('='*100)

for learning in learnings:
    print(f"\nLearning ID: {learning.get('bet_id')}")
    print(f"Venue: {learning.get('venue', 'Unknown')} - {learning.get('race_time', 'Unknown')}")
    print(f"Date: {learning.get('bet_date')}")
    
    if 'winner' in learning:
        winner_odds = learning.get('winner_odds', 'N/A')
        print(f"\nWINNER: {learning.get('winner')} at {winner_odds}")
    
    if 'our_pick' in learning:
        our_odds = learning.get('our_pick_odds', 'N/A')
        print(f"OUR PICK: {learning.get('our_pick')} at {our_odds}")
        print(f"RESULT: {'LOST' if 'winner' in learning and learning.get('winner') != learning.get('our_pick') else 'Unknown'}")
    
    # Show key insights
    if 'key_insights' in learning:
        print(f"\nKEY INSIGHTS:")
        insights = learning.get('key_insights', {})
        if isinstance(insights, dict):
            for key, value in insights.items():
                print(f"  • {key}: {value}")
    
    # Show top learnings
    if 'learnings' in learning:
        print(f"\nTOP LEARNINGS:")
        learnings_data = learning.get('learnings')
        if isinstance(learnings_data, list):
            for idx, item in enumerate(learnings_data[:5], 1):  # Show first 5
                print(f"  {idx}. {item}")
    
    print('='*100)

# Also check for race result analyses
print("\n\nCHECKING RACE RESULT ANALYSES...")
print('='*100)

response2 = table.scan(
    FilterExpression='analysis_type = :type',
    ExpressionAttributeValues={':type': 'RACE_RESULT_ANALYSIS'}
)

result_analyses = response2['Items']
print(f"RACE RESULT ANALYSES FOUND: {len(result_analyses)}\n")

for analysis in result_analyses[:10]:  # Show first 10
    print(f"Race: {analysis.get('venue')} - {analysis.get('race_time')}")
    print(f"Winner: {analysis.get('winner_horse', 'Unknown')} at {analysis.get('winner_odds', 'N/A')}")
    print(f"Winner was: {analysis.get('winner_analysis', {}).get('odds_category', 'Unknown')} in betting")
    print()
