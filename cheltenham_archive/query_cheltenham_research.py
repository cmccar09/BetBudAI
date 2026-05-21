"""
Query and analyze Cheltenham research data
View trends, top improvers, and Festival candidate insights

Usage:
    python query_cheltenham_research.py --today
    python query_cheltenham_research.py --horse "Stede Bonnet"
    python query_cheltenham_research.py --improving
    python query_cheltenham_research.py --top-candidates
"""

import boto3
import argparse
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
research_table = dynamodb.Table('CheltenhamResearch')

def query_today():
    """Show all Cheltenham candidates tracked today"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"\n{'='*80}")
    print(f"CHELTENHAM CANDIDATES - {today}")
    print(f"{'='*80}\n")
    
    try:
        response = research_table.query(
            IndexName='ResearchDateIndex',
            KeyConditionExpression=Key('research_date').eq(today)
        )
        
        entries = response.get('Items', [])
        
        if not entries:
            print("No Cheltenham candidates tracked today yet.")
            print("Run: python daily_cheltenham_research.py")
            return
        
        # Group by trend
        by_trend = defaultdict(list)
        for entry in entries:
            trend = entry.get('form_trend', 'unknown')
            by_trend[trend].append(entry)
        
        # Show improving first
        if by_trend['improving']:
            print("🔥 IMPROVING FORM:")
            for e in sorted(by_trend['improving'], key=lambda x: float(x.get('trend_score', 0)), reverse=True):
                score = float(e.get('score', 0))
                trend = float(e.get('trend_score', 0))
                print(f"  {e['horse_name']:25s} {score:3.0f}pts (+{trend:.1f}) - {e.get('trainer', '')}")
        
        if by_trend['stable']:
            print(f"\n📊 STABLE FORM ({len(by_trend['stable'])}):")
            for e in sorted(by_trend['stable'], key=lambda x: float(x.get('score', 0)), reverse=True)[:5]:
                score = float(e.get('score', 0))
                print(f"  {e['horse_name']:25s} {score:3.0f}pts - {e.get('race_name', '')}")
        
        print(f"\nTotal tracked today: {len(entries)}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Ensure CheltenhamResearch table and ResearchDateIndex exist")

def query_horse(horse_name):
    """Show historical tracking for a specific horse"""
    print(f"\n{'='*80}")
    print(f"CHELTENHAM RESEARCH - {horse_name}")
    print(f"{'='*80}\n")
    
    try:
        response = research_table.query(
            KeyConditionExpression=Key('horse_name').eq(horse_name),
            ScanIndexForward=False  # Most recent first
        )
        
        entries = response.get('Items', [])
        
        if not entries:
            print(f"No tracking data found for {horse_name}")
            return
        
        print(f"Tracked runs: {len(entries)}\n")
        
        print("DATE       | SCORE | TREND    | RACE                    | COURSE")
        print("-" * 80)
        
        for entry in entries[:10]:  # Last 10 runs
            date = entry.get('research_date', '')
            score = float(entry.get('score', 0))
            trend = entry.get('form_trend', 'unknown')
            trend_score = float(entry.get('trend_score', 0))
            race = entry.get('race_name', 'Unknown')[:23]
            course = entry.get('course', 'Unknown')
            
            trend_str = f"{trend} ({trend_score:+.1f})" if trend != 'unknown' else trend
            
            print(f"{date} | {score:3.0f}  | {trend_str:12s} | {race:23s} | {course}")
        
        # Calculate overall trend
        if len(entries) >= 3:
            recent = [float(e.get('score', 0)) for e in entries[:3]]
            older = [float(e.get('score', 0)) for e in entries[3:6]] if len(entries) > 3 else recent
            
            recent_avg = sum(recent) / len(recent)
            older_avg = sum(older) / len(older)
            overall_trend = recent_avg - older_avg
            
            print(f"\nOVERALL TREND: {overall_trend:+.1f} points")
            
            if overall_trend > 10:
                print("✅ IMPROVING - Strong Cheltenham candidate")
            elif overall_trend > 5:
                print("📈 Slight improvement - Monitor closely")
            elif overall_trend < -10:
                print("⚠️  DECLINING - Form concerns")
            else:
                print("📊 STABLE - Consistent performer")
        
    except Exception as e:
        print(f"Error: {e}")

def query_improving():
    """Show all horses with improving form trends"""
    print(f"\n{'='*80}")
    print(f"IMPROVING FORM - CHELTENHAM WATCH LIST")
    print(f"{'='*80}\n")
    
    # Get last 7 days
    improving_horses = defaultdict(list)
    
    for days_ago in range(7):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        try:
            response = research_table.query(
                IndexName='ResearchDateIndex',
                KeyConditionExpression=Key('research_date').eq(date)
            )
            
            for entry in response.get('Items', []):
                if entry.get('form_trend') == 'improving':
                    horse_name = entry['horse_name']
                    score = float(entry.get('score', 0))
                    trend = float(entry.get('trend_score', 0))
                    
                    improving_horses[horse_name].append({
                        'date': date,
                        'score': score,
                        'trend': trend,
                        'trainer': entry.get('trainer', ''),
                        'race': entry.get('race_name', '')
                    })
        except:
            continue
    
    if not improving_horses:
        print("No improving horses found in last 7 days")
        return
    
    # Show horses that improved multiple times
    print("CONSISTENT IMPROVERS (Multiple improving runs):")
    print("-" * 80)
    
    for horse, runs in sorted(improving_horses.items(), key=lambda x: len(x[1]), reverse=True):
        if len(runs) >= 2:
            latest = runs[0]
            avg_trend = sum(r['trend'] for r in runs) / len(runs)
            print(f"\n{horse} ({len(runs)} improving runs)")
            print(f"  Latest: {latest['score']:.0f}pts (+{latest['trend']:.1f}) - {latest['date']}")
            print(f"  Trainer: {latest['trainer']}")
            print(f"  Avg trend: +{avg_trend:.1f} pts")

def query_top_candidates():
    """Show top Cheltenham candidates by score and trend"""
    print(f"\n{'='*80}")
    print(f"TOP CHELTENHAM FESTIVAL CANDIDATES")
    print(f"{'='*80}\n")
    
    # Get last 14 days of data
    all_horses = defaultdict(list)
    
    for days_ago in range(14):
        date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        try:
            response = research_table.query(
                IndexName='ResearchDateIndex',
                KeyConditionExpression=Key('research_date').eq(date)
            )
            
            for entry in response.get('Items', []):
                horse_name = entry['horse_name']
                all_horses[horse_name].append(entry)
        except:
            continue
    
    # Score each horse
    candidates = []
    
    for horse, entries in all_horses.items():
        if not entries:
            continue
        
        latest = entries[0]
        latest_score = float(latest.get('score', 0))
        
        # Count improving runs
        improving_count = sum(1 for e in entries if e.get('form_trend') == 'improving')
        
        # Average score
        avg_score = sum(float(e.get('score', 0)) for e in entries) / len(entries)
        
        # Cheltenham readiness score
        readiness = latest_score + (improving_count * 5)
        
        candidates.append({
            'horse': horse,
            'latest_score': latest_score,
            'avg_score': avg_score,
            'improving_runs': improving_count,
            'total_runs': len(entries),
            'readiness': readiness,
            'trainer': latest.get('trainer', ''),
            'latest_race': latest.get('race_name', '')
        })
    
    # Sort by readiness
    candidates.sort(key=lambda x: x['readiness'], reverse=True)
    
    print("TOP 20 CHELTENHAM CANDIDATES (by readiness score):")
    print("-" * 80)
    print(f"{'HORSE':25s} | SCORE | AVG  | TREND | RUNS | TRAINER")
    print("-" * 80)
    
    for c in candidates[:20]:
        horse = c['horse'][:24]
        score = c['latest_score']
        avg = c['avg_score']
        improving = c['improving_runs']
        runs = c['total_runs']
        trainer = c['trainer'][:20]
        
        print(f"{horse:25s} | {score:3.0f}  | {avg:4.1f} | {improving}/{runs:2d}    | {runs:2d}   | {trainer}")
    
    print(f"\n{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(description='Query Cheltenham Research Data')
    parser.add_argument('--today', action='store_true', help='Show todays candidates')
    parser.add_argument('--horse', type=str, help='Show history for specific horse')
    parser.add_argument('--improving', action='store_true', help='Show all improving horses')
    parser.add_argument('--top-candidates', action='store_true', help='Show top Festival candidates')
    
    args = parser.parse_args()
    
    if args.today:
        query_today()
    elif args.horse:
        query_horse(args.horse)
    elif args.improving:
        query_improving()
    elif args.top_candidates:
        query_top_candidates()
    else:
        print("\nCheltenham Research Query Tool\n")
        print("Usage:")
        print("  python query_cheltenham_research.py --today")
        print("  python query_cheltenham_research.py --horse 'Stede Bonnet'")
        print("  python query_cheltenham_research.py --improving")
        print("  python query_cheltenham_research.py --top-candidates")

if __name__ == '__main__':
    main()
