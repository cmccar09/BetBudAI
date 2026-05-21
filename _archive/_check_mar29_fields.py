import boto3, json
from boto3.dynamodb.conditions import Key
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-29'))

horses = ['Jimmy Speaking', 'Fine Interview', 'Say What You See', 'Shazani']
for i in resp['Items']:
    if i.get('horse') in horses:
        # Show key fields
        fields = {k: i[k] for k in ['horse', 'bet_date', 'race_time', 'outcome', 'odds',
                                      'show_in_ui', 'profit_units', 'sp_decimal', 'comprehensive_score',
                                      'course', 'result_won'] if k in i}
        print(json.dumps(fields, cls=DecimalEncoder, indent=2))
        print()
