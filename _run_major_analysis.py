"""Run major race analysis now and display picks with odds."""
import boto3, json

client = boto3.client('lambda', region_name='eu-west-1')
payload = {
    'httpMethod': 'POST',
    'path': '/api/major-race-analysis/run',
    'headers': {},
    'body': '{}',
    'source': 'scheduled-major-analysis'
}
print('Invoking BettingPicksAPI for major race analysis...\n')
resp = client.invoke(
    FunctionName='BettingPicksAPI',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)
result = json.loads(resp['Payload'].read().decode())
body = json.loads(result.get('body', '{}'))
status = result.get('statusCode', '?')
print(f'Status: {status}')
print(f'Message: {body.get("message", "")}\n')

for a in body.get('analysed', []):
    race = a['race_name']
    meeting = a['meeting']
    race_date = a['race_date']
    grade = a['grade']
    rtype = a['type']
    days = a['days_to_race']
    total = a['total_horses']

    print(f'{"="*70}')
    print(f'  {race} ({meeting}, {race_date})')
    print(f'  Grade: {grade} | Type: {rtype} | Days to race: {days} | Runners found: {total}')
    print(f'{"="*70}')

    if a.get('top_pick'):
        pick_odds = a.get('top_pick_odds', 'N/A')
        top3 = a.get('top3', [])
        pick_dec = ''
        for h in top3:
            if h['name'] == a['top_pick'] and h.get('odds'):
                pick_dec = f' (decimal: {h["odds"]})'

        conf = a['confidence']
        score = a['top_pick_score']
        print(f'\n  >>> AI PICK: {a["top_pick"]} @ {pick_odds}{pick_dec}')
        print(f'      Score: {score}/100 | Confidence: {conf}')
        factors = a.get('top_pick_factors', [])
        if factors:
            print(f'      Factors:')
            for f in factors:
                print(f'        - {f}')

        print(f'\n  Top 3 Contenders:')
        for i, h in enumerate(top3, 1):
            odds_disp = h.get('odds_display', '') or 'N/A'
            dec_part = f' ({h["odds"]})' if h.get('odds') else ''
            trainer = f' [{h["trainer"]}]' if h.get('trainer') else ''
            print(f'    {i}. {h["name"]} @ {odds_disp}{dec_part} — Score: {h["score"]}/100{trainer}')
            if h.get('factors'):
                for fac in h['factors']:
                    print(f'       - {fac}')
    else:
        print(f'\n  No ante-post data available yet for this race.')

    print()

print(f'\nDone! {len(body.get("analysed", []))} races analysed.')
