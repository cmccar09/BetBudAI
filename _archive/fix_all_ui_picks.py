"""
Fix all UI picks to include combined_confidence, roi, and edge_percentage
"""
import boto3
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all UI picks for today
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui') == True]

print(f"Found {len(ui_picks)} UI picks to fix\n")

for pick in ui_picks:
    horse = pick.get('horse', 'Unknown')
    confidence = float(pick.get('confidence', 0))
    odds = float(pick.get('odds', 0))
    
    # Check if already has the fields
    has_combined = pick.get('combined_confidence') is not None
    has_roi = pick.get('roi') is not None
    has_edge = pick.get('edge_percentage') is not None
    
    if has_combined and has_roi and has_edge:
        print(f"✓ {horse} - already has all fields")
        continue
    
    # Calculate missing fields
    market_prob = 1 / odds if odds > 0 else 0
    implied_prob = confidence / 100.0
    edge = max(0, implied_prob - market_prob)
    expected_roi = edge * (odds - 1) if edge > 0 else 0.05
    
    # Update the pick
    update_expr = "SET combined_confidence = :cc, roi = :roi, edge_percentage = :edge, expected_roi = :eroi"
    
    table.update_item(
        Key={
            'bet_date': pick['bet_date'],
            'bet_id': pick['bet_id']
        },
        UpdateExpression=update_expr,
        ExpressionAttributeValues={
            ':cc': Decimal(str(confidence)),
            ':roi': Decimal(str(round(expected_roi, 4))),
            ':edge': Decimal(str(round(edge * 100, 2))),
            ':eroi': Decimal(str(round(expected_roi, 4)))
        }
    )
    
    print(f"✓ Fixed {horse}")
    print(f"  Confidence: {confidence}")
    print(f"  ROI: {expected_roi*100:.1f}%")
    print(f"  Edge: {edge*100:.1f}%\n")

print(f"\n✓ All {len(ui_picks)} UI picks updated!")
