import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-09')
)

# Find Ferret Jeeter
ferret_items = [i for i in resp['Items'] if i.get('horse') == 'Ferret Jeeter' and 'Plumpton' in i.get('course', '')]
pachacuti_items = [i for i in resp['Items'] if i.get('horse') == 'Pachacuti']

print("="*80)
print("WINNER vs OUR PICK - DETAILED COMPARISON")
print("="*80)

print(f"\nFound {len(ferret_items)} Ferret Jeeter entries")
for idx, item in enumerate(ferret_items):
    print(f"\nFerret Jeeter Entry {idx+1}:")
    print(f"  Comprehensive Score: {float(item.get('comprehensive_score', 0)):.0f}/100")
    print(f"  Odds: {item.get('odds')}")
    print(f"  Form: {item.get('form', 'N/A')}")
    print(f"  Trainer: {item.get('trainer', 'N/A')}")
    print(f"  Component Scores:")
    print(f"    Form: {item.get('form_score', 'N/A')}/25")
    print(f"    Class: {item.get('class_score', 'N/A')}/15")
    print(f"    Trainer: {item.get('trainer_score', 'N/A')}/10")
    print(f"    Jockey: {item.get('jockey_score', 'N/A')}/10")
    print(f"    Value: {item.get('value_score', 'N/A')}/5")
    print(f"    Recent Perf: {item.get('recent_performance_score', 'N/A')}/10")

print(f"\n" + "="*80)
print("OUR LOSING PICK")
print("="*80)

if pachacuti_items:
    item = pachacuti_items[0]
    print(f"\nPachacuti:")
    print(f"  Comprehensive Score: {float(item.get('comprehensive_score', 0)):.0f}/100")
    print(f"  Odds: {item.get('odds')}")
    print(f"  Form: {item.get('form', 'N/A')}")
    print(f"  Trainer: {item.get('trainer', 'N/A')}")
    print(f"  Component Scores:")
    print(f"    Form: {item.get('form_score', 'N/A')}/25")
    print(f"    Class: {item.get('class_score', 'N/A')}/15")
    print(f"    Trainer: {item.get('trainer_score', 'N/A')}/10")
    print(f"    Jockey: {item.get('jockey_score', 'N/A')}/10")
    print(f"    Value: {item.get('value_score', 'N/A')}/5")
    print(f"    Recent Perf: {item.get('recent_performance_score', 'N/A')}/10")

print(f"\n" + "="*80)
print("ANALYSIS")
print("="*80)
print("\nThe system needs immediate recalibration.")
print("Racing results so far:")
print("  Race 1 (Catterick 14:00): 79/100 pick came 2nd (close)")
print("  Race 2 (Plumpton 14:15): 78/100 pick came 5th (disaster)")
print("\nPattern: High scores are NOT predicting winners")
