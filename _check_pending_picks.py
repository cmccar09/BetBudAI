"""Look up details of pending past picks so we know what results to record."""
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

pending_picks = [
    ('2026-03-26', '2026-03-26T15:50', 'Chepstow', 'River Voyage'),
    ('2026-04-04', '2026-04-04T14:42', 'Musselburgh', 'Tropical Storm'),
    ('2026-04-04', '2026-04-04T15:40', 'Carlisle', 'Guet Apens'),
    ('2026-04-04', '2026-04-04T16:05', 'Haydock', 'Major Fortune'),
    ('2026-04-05', '2026-04-05T14:23', 'Market Rasen', 'Ballynaheer'),
    ('2026-04-05', '2026-04-05T14:50', 'Fairyhouse', 'Oldschool Outlaw'),
    ('2026-04-05', '2026-04-05T15:15', 'Southwell', 'Marry The Night'),
    ('2026-04-05', '2026-04-05T16:00', 'Fairyhouse', "Jacob's Ladder"),
    ('2026-04-06', '2026-04-06T17:10', 'Fairyhouse', 'Poetisa'),
]

for bet_date, race_time_pfx, course, horse in pending_picks:
    kwargs = {
        'KeyConditionExpression': 'bet_date = :d',
        'ExpressionAttributeValues': {':d': bet_date}
    }
    # paginate
    items = []
    while True:
        resp = table.query(**kwargs)
        items.extend(resp.get('Items', []))
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek

    match = next((i for i in items
                  if str(i.get('race_time', ''))[:16] == race_time_pfx
                  and horse.lower()[:8] in str(i.get('horse', '')).lower()), None)
    if match:
        print(f"{bet_date} {race_time_pfx} | {match.get('course')} | {match.get('horse')} | "
              f"score={match.get('comprehensive_score')} | odds={match.get('odds')} | sp={match.get('sp_odds')} | "
              f"bet_id={match.get('bet_id')}")
    else:
        print(f"NOT FOUND: {bet_date} {horse}")
