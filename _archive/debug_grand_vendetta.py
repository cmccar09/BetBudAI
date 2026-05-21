"""
Deep dive into Grand Vendetta analysis to see why it got 0/100
"""
import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("GRAND VENDETTA - WHY 0/100?")
print("="*80)

# Get all entries for Grand Vendetta
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={
        ':date': '2026-02-03'
    }
)

items = response.get('Items', [])
grand_vendetta_items = [item for item in items if 'Grand Vendetta' in item.get('horse', '')]

print(f"\nFound {len(grand_vendetta_items)} database entries for Grand Vendetta\n")

for idx, item in enumerate(grand_vendetta_items, 1):
    print(f"Entry #{idx}:")
    print(f"  bet_id: {item.get('bet_id', 'N/A')}")
    print(f"  horse: {item.get('horse', 'N/A')}")
    print(f"  course: {item.get('course', 'N/A')}")
    print(f"  race_time: {item.get('race_time', 'N/A')}")
    print(f"  confidence: {item.get('confidence', 'N/A')}")
    print(f"  combined_confidence: {item.get('combined_confidence', 'N/A')}")
    print(f"  form: {item.get('form', 'N/A')}")
    print(f"  odds: {item.get('odds', 'N/A')}")
    print(f"  trainer: {item.get('trainer', 'N/A')}")
    print(f"  jockey: {item.get('jockey', 'N/A')}")
    print(f"  analysis_type: {item.get('analysis_type', 'N/A')}")
    print(f"  show_in_ui: {item.get('show_in_ui', 'N/A')}")
    
    # Check if there's any scoring data
    print(f"\n  Scoring fields:")
    print(f"    value_score: {item.get('value_score', 'N/A')}")
    print(f"    form_score: {item.get('form_score', 'N/A')}")
    print(f"    class_score: {item.get('class_score', 'N/A')}")
    print(f"    edge_percentage: {item.get('edge_percentage', 'N/A')}")
    print(f"    comprehensive_score: {item.get('comprehensive_score', 'N/A')}")
    
    # Check form analysis
    print(f"\n  Form analysis:")
    print(f"    recent_wins: {item.get('recent_wins', 'N/A')}")
    print(f"    lto_winner: {item.get('lto_winner', 'N/A')}")
    print(f"    win_in_last_3: {item.get('win_in_last_3', 'N/A')}")
    
    print("\n" + "-"*80)

print("\nANALYSIS:")
print("-"*80)

if grand_vendetta_items:
    item = grand_vendetta_items[0]
    form = item.get('form', '')
    confidence = item.get('confidence', 0)
    
    print(f"\nForm string: '{form}'")
    print(f"Confidence: {confidence}")
    
    if form == '2':
        print("\nForm Analysis:")
        print("  Last run: 2nd place")
        print("  This is GOOD form - should score well!")
        print("  LTO winner: No (would need '1')")
        print("  Recent place: Yes (2nd = 60 points in position scoring)")
    
    if confidence == 0 or confidence == '0':
        print("\n❌ PROBLEM: Confidence is 0")
        print("   analyze_all_races_comprehensive.py stores horses but doesn't calculate")
        print("   confidence scores. It just populates basic data.")
        print("\n   The confidence/score calculation needs to happen in a separate step")
        print("   or be added to analyze_all_races_comprehensive.py")
    
    analysis_type = item.get('analysis_type', '')
    if analysis_type == 'PRE_RACE_COMPLETE':
        print("\n   This was stored by analyze_all_races_comprehensive.py")
        print("   which focuses on DATA STORAGE, not SCORING")
        print("   The scoring logic needs to be integrated!")

print("="*80)
