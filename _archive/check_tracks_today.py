import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui') == True]
tracks = set([p.get('course') for p in ui_picks])

print(f'\nTracks with UI picks today ({len(ui_picks)} picks):\n')
for track in sorted(tracks):
    track_picks = [p for p in ui_picks if p.get('course') == track]
    print(f'  {track}: {len(track_picks)} picks')

print(f'\nAll UI picks:')
for p in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    print(f"  {p.get('race_time', 'N/A')[:16]:18} {p.get('course', 'Unknown'):15} {p.get('horse', 'Unknown'):25} Score: {p.get('confidence', 0)}")
