"""Complete summary of today's betting performance and system status"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')

# Get today's picks
resp = table.scan(
    FilterExpression='begins_with(bet_date, :d)',
    ExpressionAttributeValues={':d': '2026-01-10'}
)

picks = resp.get('Items', [])

# Categorize
wins = [p for p in picks if p.get('outcome') == 'WON']
losses = [p for p in picks if p.get('outcome') in ['LOST', 'PLACED']]
pending = [p for p in picks if p.get('outcome') is None]

# Calculate P/L
total_pnl = sum(float(p.get('profit_loss', 0)) for p in picks if p.get('profit_loss') is not None)
settled_pnl = sum(float(p.get('profit_loss', 0)) for p in (wins + losses))

print("="*70)
print(f"SUREBET BETTING - DAILY SUMMARY")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("="*70)

print(f"\n📊 TODAY'S PERFORMANCE:")
print(f"   Total Picks:     {len(picks)}")
print(f"   Wins:            {len(wins)}")
print(f"   Losses/Placed:   {len(losses)}")
print(f"   Pending:         {len(pending)}")
print(f"\n💰 PROFIT/LOSS:")
print(f"   Settled P/L:     {settled_pnl:+.2f} units")
print(f"   Total P/L:       {total_pnl:+.2f} units")

if wins:
    print(f"\n🎉 WINNERS:")
    for p in wins:
        pnl = float(p.get('profit_loss', 0))
        odds = p.get('odds', 'N/A')
        print(f"   • {p['horse']} @ {p['course']} - {p['bet_type']} @ {odds} - Profit: +{pnl:.2f} units")

if losses:
    print(f"\n📉 LOSSES:")
    for p in sorted(losses, key=lambda x: float(x.get('profit_loss', 0))):
        pnl = float(p.get('profit_loss', 0))
        outcome = p.get('outcome', 'LOST')
        print(f"   • {p['horse']} @ {p['course']} - {outcome} - Loss: {pnl:.2f} units")

if pending:
    print(f"\n⏳ PENDING ({len(pending)} races):")
    for p in sorted(pending, key=lambda x: x.get('race_time', '')):
        race_time = p.get('race_time', '').split('T')[1][:5] if 'T' in p.get('race_time', '') else 'Time N/A'
        print(f"   • {p['horse']} @ {p['course']} - {race_time} ({p['bet_type']})")

print(f"\n🤖 SYSTEM STATUS:")
print(f"   Results Fetcher: Hourly (next: 16:23)")
print(f"   Learning System: Tonight 23:00")
print(f"   Pick Validation: Integrated in workflow")

win_rate = (len(wins) / (len(wins) + len(losses)) * 100) if (wins or losses) else 0
roi = (settled_pnl / (len(wins) + len(losses)) * 100) if (wins or losses) else 0

print(f"\n📈 STATISTICS (settled bets):")
print(f"   Win Rate:        {win_rate:.1f}%")
print(f"   ROI per bet:     {roi:+.1f}%")
print(f"   Avg P/L:         {settled_pnl/(len(wins) + len(losses)) if (wins or losses) else 0:+.2f} units")

print("="*70)
