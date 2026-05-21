import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get all UI picks with results
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :ui AND attribute_exists(outcome)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':ui': True
    }
)

print("\n" + "="*80)
print("TODAY'S BETTING RESULTS - FEBRUARY 3, 2026")
print("="*80)

total_profit = 0
wins = 0
losses = 0
results_list = []

for item in sorted(response['Items'], key=lambda x: x.get('race_time', '')):
    outcome = item.get('outcome', 'pending')
    if outcome == 'pending':
        continue
        
    profit = float(item.get('profit_loss', 0))
    total_profit += profit
    
    if outcome == 'win':
        wins += 1
        status = "WIN "
    else:
        losses += 1
        status = "LOSS"
    
    # Parse bet_id for horse name
    bet_id = item.get('bet_id', '')
    if 'Haarar' in bet_id:
        horse = 'Haarar'
    elif 'Medieval' in bet_id:
        horse = 'Medieval Gold'
    else:
        parts = bet_id.split('_')
        horse = parts[3] if len(parts) > 3 else 'Unknown'
    
    race_time = item.get('race_time', '').split('T')[1][:5] if 'T' in item.get('race_time', '') else 'N/A'
    course = item.get('course', 'N/A')
    score = int(item.get('comprehensive_score', 0) or 0)
    grade = item.get('confidence_grade', 'N/A')
    winner = item.get('actual_winner', 'N/A')
    
    results_list.append({
        'time': race_time,
        'course': course,
        'horse': horse,
        'status': status,
        'score': score,
        'grade': grade,
        'profit': profit,
        'winner': winner
    })
    
    print(f"{race_time} {course:15} {horse:20} {status} {score:3}/100 {grade:10} {profit:+7.0f} EUR")

total_bets = wins + losses
total_staked = total_bets * 30
roi = (total_profit / total_staked) * 100

print("="*80)
print(f"PERFORMANCE SUMMARY:")
print(f"  Total Bets: {total_bets}")
print(f"  Wins: {wins} ({wins/total_bets*100:.1f}%) | Losses: {losses} ({losses/total_bets*100:.1f}%)")
print(f"  Total Staked: {total_staked} EUR (30 EUR per bet)")
print(f"  Net Profit: {total_profit:+.2f} EUR")
print(f"  ROI: {roi:+.2f}%")
print("="*80)
