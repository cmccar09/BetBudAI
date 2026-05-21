import json

with open('/tmp/featured_response.json') as f:
    data = json.load(f)

print("Featured Meeting Picks and Outcomes:\n")
for race in data['races'][:5]:
    time = race['time_user']
    if race['runners']:
        top_pick = race['runners'][0]
        horse = top_pick['horse']
        outcome = top_pick.get('outcome', 'MISSING')
        print(f"{time} - {horse}: outcome={outcome}")
