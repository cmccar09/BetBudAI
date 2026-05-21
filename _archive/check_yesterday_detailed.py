import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': yesterday}
)

bets = resp['Items']

print(f'\n=== YESTERDAY ({yesterday}) RESULTS ===\n')
print(f'Total: {len(bets)} bets')

wins = [b for b in bets if b.get('result') == 'win']
losses = [b for b in bets if b.get('result') == 'loss']
pending = [b for b in bets if b.get('result') == 'pending']

print(f'Wins: {len(wins)}')
print(f'Losses: {len(losses)}')
print(f'Pending: {len(pending)}')

if bets:
    print(f'Win rate: {len(wins)/len(bets)*100:.1f}%')

if losses:
    print(f'\n=== LOSING BETS ({len(losses)}) ===')
    for b in sorted(losses, key=lambda x: x.get('combined_confidence', 0), reverse=True):
        conf = b.get('combined_confidence', 0)
        p_win = b.get('p_win', 0) * 100
        odds = b.get('odds', 0)
        reasoning = b.get('reasoning', '')[:100]
        print(f'\n  {b["horse_name"]} @ {b["venue"]}')
        print(f'    Confidence: {conf:.1f}, P_Win: {p_win:.0f}%, Odds: {odds:.2f}')
        print(f'    Type: {b.get("bet_type", "?")}')
        print(f'    Reason: {reasoning}...')

if wins:
    print(f'\n=== WINNING BETS ({len(wins)}) ===')
    for b in wins:
        conf = b.get('combined_confidence', 0)
        p_win = b.get('p_win', 0) * 100
        odds = b.get('odds', 0)
        print(f'  {b["horse_name"]} @ {b["venue"]} - Conf: {conf:.1f}, P_Win: {p_win:.0f}%, Odds: {odds:.2f}')

print(f'\n=== ANALYSIS ===')
if losses:
    avg_conf_losses = sum(b.get('combined_confidence', 0) for b in losses) / len(losses)
    avg_pwin_losses = sum(b.get('p_win', 0) for b in losses) / len(losses) * 100
    print(f'Average confidence (losses): {avg_conf_losses:.1f}')
    print(f'Average p_win (losses): {avg_pwin_losses:.1f}%')

if wins:
    avg_conf_wins = sum(b.get('combined_confidence', 0) for b in wins) / len(wins)
    avg_pwin_wins = sum(b.get('p_win', 0) for b in wins) / len(wins) * 100
    print(f'Average confidence (wins): {avg_conf_wins:.1f}')
    print(f'Average p_win (wins): {avg_pwin_wins:.1f}%')
