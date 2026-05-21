import boto3
from datetime import datetime
from decimal import Decimal

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's picks
today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
print(f"Total picks for {today}: {len(items)}\n")

print("=" * 100)
for item in sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    horse = item.get('horse', 'Unknown')
    score = float(item.get('comprehensive_score', 0))
    show_ui = item.get('show_in_ui', False)
    recommended = item.get('recommended_bet', False)
    components = item.get('component_scores', {})
    analysis = item.get('analysis_summary', '')
    
    print(f"Horse: {horse}")
    print(f"  Score: {score:.0f}/100")
    print(f"  Show in UI: {show_ui}")
    print(f"  Recommended: {recommended}")
    print(f"  Has Components: {bool(components)}")
    print(f"  Has Analysis: {bool(analysis)}")
    
    if components:
        print(f"  Component Scores:")
        for key, value in sorted(components.items()):
            print(f"    - {key}: {float(value):.1f}")
    
    if analysis:
        print(f"  Analysis: {analysis[:200]}...")
    
    print("=" * 100)
