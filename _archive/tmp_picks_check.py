import boto3, json
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')
resp = table.scan()
# Get unique picks (highest score per race_name)
picks = {}
for item in resp['Items']:
    rn = item.get('race_name','')
    sc = float(item.get('score', 0))
    if rn not in picks or sc > float(picks[rn].get('score', 0)):
        picks[rn] = item

# Sort by time (approximate via known order)
race_order = [
    "Sky Bet Supreme Novices' Hurdle",
    "Arkle Challenge Trophy Chase",
    "Fred Winter Handicap Hurdle",
    "Ultima Handicap Chase",
    "Unibet Champion Hurdle",
    "Cheltenham Plate Chase",
    "Challenge Cup Chase",
    "Turner's Novices' Hurdle",
    "Brown Advisory Novices' Chase",
    "BetMGM Cup Hurdle",
    "Glenfarclas Cross Country Chase",
    "Queen Mother Champion Chase",
    "Grand Annual Handicap Chase",
    "Champion Bumper",
    "Ryanair Mares' Novices' Hurdle",
    "Jack Richards Novices' Chase",
]
done = {"Sky Bet Supreme Novices' Hurdle", "Arkle Challenge Trophy Chase", "Fred Winter Handicap Hurdle", "Ultima Handicap Chase"}

print("REMAINING PICKS — trainer/jockey to cross-check:")
print("="*80)
for rn in race_order:
    if rn in done: continue
    item = picks.get(rn)
    if not item: continue
    trainer = item.get('trainer', '?')
    jockey  = item.get('jockey', '?')
    horse   = item.get('horse', '?')
    tips    = item.get('tips', [])
    if isinstance(tips, str): tips = json.loads(tips)
    trainer_tip = next((t for t in tips if 'Trainer' in t), '')
    jockey_tip  = next((t for t in tips if 'Jockey' in t), '')
    print(f"{rn}")
    print(f"  PICK: {horse}")
    print(f"  trainer={trainer}  jockey={jockey}")
    print(f"  tips: {trainer_tip} | {jockey_tip}")
    print()

# Also show any remaining not in ordered list
for rn, item in sorted(picks.items(), key=lambda x: x[0]):
    if rn in done or rn in race_order: continue
    trainer = item.get('trainer', '?')
    jockey  = item.get('jockey', '?')
    horse   = item.get('horse', '?')
    print(f"{rn}")
    print(f"  PICK: {horse}  trainer={trainer}  jockey={jockey}")
    print()
