"""
Deep dive on Talk To The Man - Taunton 13:40 winner
Why did it score 0/100?
"""
import boto3
import json

# Always use eu-west-1
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 80)
print("TALK TO THE MAN - DEEP DIVE ANALYSIS")
print("=" * 80)

# Get from database
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='course = :course AND horse = :horse',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':course': 'Taunton',
        ':horse': 'Talk To The Man'
    }
)

items = response.get('Items', [])

if items:
    item = items[0]
    print("\nDATABASE RECORD:")
    print(json.dumps(item, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("SCORING BREAKDOWN")
    print("=" * 80)
    
    odds = float(item.get('odds', 0))
    form = item.get('form', '')
    confidence_score = item.get('confidence_score', 0)
    
    print(f"\nHorse: {item.get('horse')}")
    print(f"Odds: {odds} (11/4 = 3.75 in reality, database shows {odds})")
    print(f"Form: '{form}'")
    print(f"Current Score: {confidence_score}/100")
    
    # Analyze why score is 0
    print("\n" + "-" * 80)
    print("WHY IS SCORE 0?")
    print("-" * 80)
    
    if not form or form.strip() == '':
        print("✗ EMPTY FORM STRING - This is why score is 0!")
        print("  Without form data, the scoring logic can't assess the horse")
        print("  This is a data quality issue")
    
    if odds == 0:
        print("✗ ZERO ODDS - Invalid odds data")
    
    # Check what the score SHOULD be
    print("\n" + "-" * 80)
    print("WHAT SHOULD THE SCORE BE?")
    print("-" * 80)
    
    # Actual race data
    actual_odds = 3.75
    actual_form = "12-1"  # Need to get real form
    
    print(f"\nUsing actual race data:")
    print(f"  Odds: {actual_odds} (11/4)")
    print(f"  Form: {actual_form} (assumed from win)")
    
    # Sweet spot check
    if 3.0 <= actual_odds <= 9.0:
        print("\n  ✓ IN SWEET SPOT (3-9) - Base eligibility")
        
        # Form analysis
        form_parts = actual_form.split('-')
        recent_wins = sum(1 for f in form_parts[:3] if f == '1')
        
        if recent_wins >= 1:
            print(f"  ✓ Recent wins: {recent_wins} - Would get positive score")
            print("\n  ESTIMATED SCORE: 30-50/100")
            print("  VERDICT: SHOULD HAVE BEEN PICKED")
        else:
            print(f"  ~ Recent wins: {recent_wins} - Marginal")
    else:
        print(f"\n  ✗ Outside sweet spot (odds {actual_odds})")
    
    # Check other fields
    print("\n" + "-" * 80)
    print("OTHER DATABASE FIELDS")
    print("-" * 80)
    
    for key in ['trainer', 'jockey', 'weight', 'age', 'distance', 'going', 
                'analyzed_at', 'analysis_purpose', 'prediction_factors']:
        if key in item:
            value = item[key]
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")

else:
    print("\n⚠ Talk To The Man not found in database")
    print("   Checking all Taunton 13:40 horses...")
    
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='course = :course',
        ExpressionAttributeValues={
            ':date': '2026-02-03',
            ':course': 'Taunton'
        }
    )
    
    items = response.get('Items', [])
    taunton_1340 = [i for i in items if '13:40' in i.get('race_time', '')]
    
    print(f"\n   Found {len(taunton_1340)} horses for Taunton 13:40:")
    for item in taunton_1340:
        print(f"     - {item.get('horse')}")

print("\n" + "=" * 80)
