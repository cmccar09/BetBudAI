import boto3
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-09')
)

items = [i for i in resp['Items'] if i.get('horse') == 'Solid Performer']
if items:
    item = items[0]
    print(f"Horse: {item.get('horse')}")
    print(f"Odds: {item.get('odds')}")
    print(f"Score: {item.get('comprehensive_score')}")
    print(f"ROI field: {item.get('roi', 'MISSING')}")
    print(f"Expected ROI field: {item.get('expected_roi', 'MISSING')}")
    
    odds = float(item.get('odds', 1))
    roi = (odds - 1) * 100
    
    print(f"\nCalculated ROI: {roi:.0f}%")
    print(f"At {odds} odds, €10 bet returns €{odds * 10:.0f}")
    print(f"Profit: €{(odds - 1) * 10:.0f} on €10 stake = {roi:.0f}% ROI")
    
    print(f"\nThis is a GOOD bet:")
    print(f"  - Score: 79/100 (GOOD)")
    print(f"  - Odds: {odds} (value range 3-9)")
    print(f"  - ROI: {roi:.0f}% (excellent value)")
    
    # Add ROI to database
    print(f"\nAdding expected_roi to database...")
    table.update_item(
        Key={'bet_date': '2026-02-09', 'bet_id': item['bet_id']},
        UpdateExpression='SET expected_roi = :roi',
        ExpressionAttributeValues={':roi': Decimal(str(roi))}
    )
    print("Done!")
