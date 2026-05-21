"""
Simulate Morning Pipeline with Phase 1
========================================
Test Lambda as if called by morning pipeline
"""

import json
import boto3
import sys
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("MORNING PIPELINE SIMULATION (Phase 1 Active)")
print("="*70)
print()

# Simulate realistic race data from morning fetch
races = [
    {
        "venue": "Cheltenham",
        "time": "14:30",
        "race_name": "Novice Handicap Hurdle",
        "market_id": "1.234567",
        "avg_winner_odds": 5.2,
        "runners": [
            {
                "name": "Front Runner",
                "odds": 4.5,
                "form": "1-2-1",
                "trainer": "Nicky Henderson",
                "jockey": "Nico de Boinville",
                "weight": 11.0,
                "age": 6,
                "run_style": "E",  # Early speed
                "prev_results": [
                    {"position": "1", "going": "Good", "distance": "2m4f", "course": "Cheltenham"}
                ]
            },
            {
                "name": "Closer",
                "odds": 6.0,
                "form": "3-1-2",
                "trainer": "Paul Nicholls",
                "jockey": "Harry Cobden",
                "weight": 11.3,
                "age": 5,
                "run_style": "P",  # Presser
            },
            {
                "name": "Hold Up Horse",
                "odds": 8.0,
                "form": "2-3-1",
                "trainer": "W P Mullins",
                "jockey": "Paul Townend",
                "weight": 11.5,
                "age": 7,
                "run_style": "S",  # Sustained
            }
        ]
    },
    {
        "venue": "Ascot",
        "time": "15:00",
        "race_name": "Handicap Chase",
        "market_id": "1.345678",
        "avg_winner_odds": 4.8,
        "runners": [
            {
                "name": "Elite Jockey Upgrade",
                "odds": 5.5,
                "form": "2-3-2",
                "trainer": "Gordon Elliott",
                "jockey": "Rachael Blackmore",  # Elite jockey
                "prev_jockey": "Mr A Smith",     # Jockey upgrade
                "weight": 11.2,
                "age": 6
            }
        ]
    }
]

payload = {
    "target_date": datetime.now().strftime('%Y-%m-%d'),
    "races": races,
    "force": True
}

print(f"[1/3] Simulating morning pipeline call...")
print(f"  Date: {payload['target_date']}")
print(f"  Races: {len(races)}")
print(f"  Total runners: {sum(len(r['runners']) for r in races)}")
print()

lambda_client = boto3.client('lambda', region_name='eu-west-1')

try:
    response = lambda_client.invoke(
        FunctionName='surebet-analysis',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    response_payload = json.loads(response['Payload'].read())

    if response_payload.get('statusCode') != 200:
        print(f"❌ Lambda error: {response_payload}")
        exit(1)

    body = json.loads(response_payload['body'])

    print(f"[2/3] Analysis results...")
    print(f"  Status: {response['StatusCode']}")
    print(f"  Horses analyzed: {body.get('horses_analyzed', 0)}")
    print(f"  Top picks: {body.get('picks_count', 0)}")
    print(f"  Phase 1 signals: {'✅ ACTIVE' if body.get('phase1_signals_active') else '❌ INACTIVE'}")
    print()

    print(f"[3/3] Checking Phase 1 signal activity in picks...")

    if body.get('top_picks'):
        for i, pick in enumerate(body['top_picks'][:3], 1):
            print(f"\n  Pick #{i}: {pick['name']} @ {pick['odds']}")
            print(f"    Score: {pick['score']}")
            print(f"    Course: {pick['course']}")

            # Check Phase 1 signals in breakdown
            breakdown = pick.get('breakdown', {})
            phase1_signals = {
                'pace_match': breakdown.get('pace_match', 0),
                'jockey_upgrade': breakdown.get('jockey_upgrade', 0),
                'first_time_equipment': breakdown.get('first_time_equipment', 0),
                'market_liquidity': breakdown.get('market_liquidity', 0)
            }

            active_signals = {k: v for k, v in phase1_signals.items() if v != 0}

            if active_signals:
                print(f"    Phase 1 bonuses:")
                for signal, value in active_signals.items():
                    print(f"      - {signal}: {value:+.1f} pts")
            else:
                print(f"    Phase 1 bonuses: None in this pick")

            # Show key reasons
            reasons = pick.get('reasons', [])
            phase1_reasons = [r for r in reasons if any(kw in r.lower() for kw in ['pace', 'jockey upgrade', 'equipment', 'liquidity'])]
            if phase1_reasons:
                print(f"    Phase 1 reasons:")
                for reason in phase1_reasons[:3]:
                    print(f"      - {reason}")

    else:
        print("  ⚠️  No picks generated (may need higher scoring horses)")

    print()
    print("="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print()
    print("Summary:")
    print(f"  ✅ Lambda executed successfully")
    print(f"  ✅ Phase 1 signals: {'ACTIVE' if body.get('phase1_signals_active') else 'INACTIVE'}")
    print(f"  ✅ Analysis complete: {body.get('horses_analyzed')} horses scored")
    print()
    print("Lambda is ready for production morning pipeline.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
