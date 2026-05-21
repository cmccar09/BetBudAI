import boto3
from boto3.dynamodb.conditions import Key

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = resp['Items']
picks = [it for it in items if it.get('show_in_ui')]

for p in sorted(picks, key=lambda x: str(x.get('race_time', ''))):
    horse = p.get('horse', '')
    course = p.get('race_course', '') or p.get('course', '')
    outcome = p.get('outcome', '') or 'PENDING'
    fp = p.get('finish_position', '') or '?'
    winner = p.get('winner_horse', '') or p.get('result_winner_name', '') or '?'
    rt = str(p.get('race_time', ''))[11:16]
    odds = p.get('odds', '')
    print(f"  {rt} {course:15s} {horse:25s} outcome={outcome:8s} fp={fp} winner={winner} odds={odds}")

print(f"\nTotal picks: {len(picks)}")
print(f"Settled: {sum(1 for p in picks if p.get('outcome'))}")
print(f"Pending: {sum(1 for p in picks if not p.get('outcome'))}")
