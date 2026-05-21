"""
PHASE 1 ANALYSIS - LOCAL DEMONSTRATION
=======================================
Generate Phase 1 enhanced picks using synthetic race data to demonstrate
the new Run Style + Jockey Upgrade signals in action.

Since no real race data is available for 2026-05-20, this creates realistic
synthetic races that trigger Phase 1 signals to show the system working.
"""

import sys
import os
sys.path.insert(0, 'C:\\Users\\charl\\OneDrive\\futuregenAI\\BetBudAI')
os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'

from datetime import datetime
import json

print("=" * 80)
print("PHASE 1 ANALYSIS - DEMONSTRATION RUN")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("NOTE: Using synthetic race data to demonstrate Phase 1 signals")
print("      Real data unavailable for 2026-05-20")
print()

# Import scoring module with Phase 1
print("[1/5] Loading scoring module with Phase 1 signals...")
try:
    from backend.core.scoring import (
        get_comprehensive_pick,
        analyze_horse_comprehensive,
        get_dynamic_weights,
        DEFAULT_WEIGHTS
    )
    print("[SUCCESS] Scoring module loaded")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

# Check Phase 1 weights
print("\n[2/5] Verifying Phase 1 weights...")
weights = get_dynamic_weights()
phase1_signals = {
    'pace_match_bonus': weights.get('pace_match_bonus', 0),
    'jockey_upgrade_bonus': weights.get('jockey_upgrade_bonus', 0),
    'first_time_blinkers': weights.get('first_time_blinkers', 0),
    'market_liquidity_bonus': weights.get('market_liquidity_bonus', 0),
}

print("Phase 1 weights configured:")
for signal, value in phase1_signals.items():
    status = "ACTIVE" if value > 0 else "pending"
    print(f"  {signal}: {value} [{status}]")

# Create synthetic race data showcasing Phase 1 signals
print("\n[3/5] Creating synthetic race scenarios...")

synthetic_races = [
    # Race 1: PACE ADVANTAGE - Closer in contested pace
    {
        'venue': 'Ascot',
        'time': '14:30',
        'market_name': '2m Handicap Hurdle',
        'distance': '2m',
        'going': 'Good',
        'runners': [
            {
                'name': 'Night Vision',
                'odds': 5.0,
                'form': '1212',
                'jockey': 'Ryan Moore',  # Elite T1
                'trainer': 'Aidan O\'Brien',
                'weight': '10-7',
                'age': 6,
                'form_runs': [
                    {
                        'position': 1,
                        'comment': 'held up in rear, stayed on strongly final furlong, led close home',
                        'date': '2026-04-28',
                        'distance': '2m',
                        'going': 'Good',
                        'jockey': 'J. Smith (7)',  # Claimer previously
                    },
                    {
                        'position': 2,
                        'comment': 'settled towards rear, headway 2f out, kept on well',
                        'date': '2026-04-12',
                        'distance': '2m1f',
                        'going': 'Good to Firm',
                        'jockey': 'T. Jones',
                    },
                    {
                        'position': 1,
                        'comment': 'raced in rear, switched right and ran on final furlong',
                        'date': '2026-03-30',
                        'distance': '2m',
                        'going': 'Good',
                        'jockey': 'J. Smith (7)',
                    },
                ]
            },
            # Front runners to create contested pace
            {
                'name': 'Speed Demon',
                'odds': 4.5,
                'form': '1112',
                'jockey': 'William Buick',
                'trainer': 'Charlie Appleby',
                'form_runs': [
                    {'comment': 'led throughout, quickened clear 2f out', 'position': 1},
                    {'comment': 'prominent, disputed lead, headed final furlong', 'position': 1},
                    {'comment': 'made all, drew clear', 'position': 1},
                ]
            },
            {
                'name': 'Early Leader',
                'odds': 6.0,
                'form': '2111',
                'jockey': 'Frankie Dettori',
                'trainer': 'John Gosden',
                'form_runs': [
                    {'comment': 'led early, set strong pace, headed 1f out', 'position': 2},
                    {'comment': 'keen, led until weakened final furlong', 'position': 1},
                    {'comment': 'prominent throughout, led 3f out', 'position': 1},
                ]
            },
            {
                'name': 'Pace Maker',
                'odds': 8.0,
                'form': '3121',
                'jockey': 'Oisin Murphy',
                'trainer': 'Andrew Balding',
                'form_runs': [
                    {'comment': 'disputed lead, headed approaching final furlong', 'position': 3},
                    {'comment': 'raced keenly in front rank', 'position': 1},
                ]
            },
        ]
    },

    # Race 2: JOCKEY UPGRADE - Claimer to Elite
    {
        'venue': 'Newmarket',
        'time': '15:15',
        'market_name': '1m Maiden Stakes',
        'distance': '1m',
        'going': 'Good to Firm',
        'runners': [
            {
                'name': 'Rising Star',
                'odds': 3.5,
                'form': '233',
                'jockey': 'William Buick',  # Elite upgrade
                'trainer': 'Charlie Appleby',
                'weight': '9-5',
                'age': 3,
                'form_runs': [
                    {
                        'position': 2,
                        'comment': 'tracked leaders, kept on same pace final furlong',
                        'date': '2026-05-05',
                        'distance': '1m',
                        'going': 'Good',
                        'jockey': 'A. Kirby (7)',  # 7lb claimer
                    },
                    {
                        'position': 3,
                        'comment': 'held up, ran on inside final furlong',
                        'date': '2026-04-20',
                        'distance': '7f',
                        'going': 'Good to Firm',
                        'jockey': 'B. Robinson (5)',  # 5lb claimer
                    },
                    {
                        'position': 3,
                        'comment': 'mid-division, stayed on',
                        'date': '2026-04-08',
                        'distance': '1m',
                        'going': 'Good',
                        'jockey': 'A. Kirby (7)',
                    },
                ]
            },
            {
                'name': 'Steady Runner',
                'odds': 4.0,
                'form': '445',
                'jockey': 'Jim Crowley',
                'trainer': 'Roger Varian',
                'form_runs': [
                    {'comment': 'mid-division throughout', 'position': 4},
                ]
            },
        ]
    },

    # Race 3: COMBINED SIGNALS - Both pace and jockey upgrade
    {
        'venue': 'Cheltenham',
        'time': '16:00',
        'market_name': '2m4f Novice Hurdle',
        'distance': '2m4f',
        'going': 'Good',
        'runners': [
            {
                'name': 'Perfect Storm',
                'odds': 4.2,
                'form': '112',
                'jockey': 'Paul Townend',  # Elite T1
                'trainer': 'Willie Mullins',
                'weight': '11-0',
                'age': 5,
                'form_runs': [
                    {
                        'position': 1,
                        'comment': 'held up, made smooth progress 3 out, led last, stayed on',
                        'date': '2026-05-01',
                        'distance': '2m4f',
                        'going': 'Good',
                        'jockey': 'D. Murphy',  # Average jockey
                    },
                    {
                        'position': 1,
                        'comment': 'settled in rear, headway approaching 2 out, ran on strongly',
                        'date': '2026-04-15',
                        'distance': '2m',
                        'going': 'Good to Soft',
                        'jockey': 'J. Brown (5)',  # Claimer
                    },
                    {
                        'position': 2,
                        'comment': 'towards rear, progress from 3 out, kept on',
                        'date': '2026-03-28',
                        'distance': '2m3f',
                        'going': 'Good',
                        'jockey': 'D. Murphy',
                    },
                ]
            },
            # Multiple front runners
            {
                'name': 'Fast Starter',
                'odds': 3.8,
                'form': '1211',
                'jockey': 'Jack Kennedy',
                'trainer': 'Gordon Elliott',
                'form_runs': [
                    {'comment': 'led until headed last, kept on', 'position': 1},
                    {'comment': 'made running, clear 2 out', 'position': 2},
                    {'comment': 'prominent, led 3 out', 'position': 1},
                ]
            },
            {
                'name': 'Front Runner Pro',
                'odds': 5.5,
                'form': '1123',
                'jockey': 'Rachael Blackmore',
                'trainer': 'Henry de Bromhead',
                'form_runs': [
                    {'comment': 'set pace, headed last', 'position': 1},
                    {'comment': 'led until 2 out', 'position': 1},
                ]
            },
        ]
    },

    # Race 4: BASELINE (no Phase 1 triggers) - for comparison
    {
        'venue': 'Kempton',
        'time': '18:30',
        'market_name': '1m4f All Weather',
        'distance': '1m4f',
        'going': 'Standard',
        'runners': [
            {
                'name': 'Baseline Horse',
                'odds': 5.5,
                'form': '2134',
                'jockey': 'Tom Marquand',
                'trainer': 'Ralph Beckett',
                'weight': '9-7',
                'age': 4,
                'form_runs': [
                    {
                        'position': 2,
                        'comment': 'mid-division, ran on',
                        'date': '2026-05-10',
                        'jockey': 'Tom Marquand',  # Same jockey
                    },
                    {
                        'position': 1,
                        'comment': 'handy, led 2f out',
                        'date': '2026-04-25',
                        'jockey': 'Tom Marquand',
                    },
                ]
            },
            {
                'name': 'Regular Runner',
                'odds': 6.0,
                'form': '3456',
                'jockey': 'David Probert',
                'trainer': 'Michael Bell',
                'form_runs': [
                    {'comment': 'mid-division', 'position': 3},
                ]
            },
        ]
    },
]

print(f"[SUCCESS] Created {len(synthetic_races)} synthetic races")

# Analyze each race
print("\n[4/5] Running Phase 1 analysis on synthetic races...")
print()

results = []

for race_idx, race_data in enumerate(synthetic_races, 1):
    print(f"\n{'=' * 80}")
    print(f"RACE {race_idx}/{len(synthetic_races)}: {race_data['venue']} {race_data['time']}")
    print(f"{'=' * 80}")
    print(f"Distance: {race_data['distance']} | Going: {race_data['going']}")
    print(f"Runners: {len(race_data['runners'])}")
    print()

    try:
        # Get comprehensive pick with Phase 1
        pick = get_comprehensive_pick(race_data)

        if pick:
            horse = pick['horse']
            score = pick['score']
            breakdown = pick.get('breakdown', {})
            reasons = pick.get('reasons', [])

            # Extract Phase 1 signals
            phase1_detected = {
                'pace_match': breakdown.get('pace_match', 0),
                'jockey_upgrade': breakdown.get('jockey_upgrade', 0),
                'equipment': breakdown.get('first_time_equipment', 0),
            }

            phase1_total = sum(phase1_detected.values())
            phase1_active = phase1_total > 0

            # Store result
            result = {
                'race_number': race_idx,
                'venue': race_data['venue'],
                'time': race_data['time'],
                'distance': race_data['distance'],
                'horse': horse['name'],
                'odds': horse.get('odds', 0),
                'trainer': horse.get('trainer', 'Unknown'),
                'jockey': horse.get('jockey', 'Unknown'),
                'total_score': score,
                'phase1_active': phase1_active,
                'phase1_total': phase1_total,
                'phase1_signals': phase1_detected,
                'breakdown': breakdown,
                'reasons': reasons,
            }
            results.append(result)

            # Display result
            print(f"TOP PICK: {horse['name']}")
            print(f"  Odds: {horse.get('odds')}")
            print(f"  Trainer: {horse.get('trainer')}")
            print(f"  Jockey: {horse.get('jockey')}")
            print(f"  Total Score: {score:.1f}")

            if phase1_active:
                print(f"\n  [PHASE 1] SIGNALS TRIGGERED (+{phase1_total:.1f} pts):")
                if phase1_detected['pace_match'] > 0:
                    print(f"    - Pace Match: +{phase1_detected['pace_match']:.1f} pts")
                if phase1_detected['jockey_upgrade'] > 0:
                    print(f"    - Jockey Upgrade: +{phase1_detected['jockey_upgrade']:.1f} pts")
                if phase1_detected['equipment'] > 0:
                    print(f"    - Equipment Change: +{phase1_detected['equipment']:.1f} pts")
            else:
                print(f"\n  [BASELINE] No Phase 1 signals (standard scoring)")

            # Show Phase 1 reasons
            phase1_reasons = [r for r in reasons if '[PHASE1]' in str(r)]
            if phase1_reasons:
                print(f"\n  Phase 1 Reasons:")
                for reason in phase1_reasons[:3]:
                    print(f"    - {reason}")

            # Top score components
            print(f"\n  Top Score Components:")
            sorted_breakdown = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
            for component, value in sorted_breakdown[:5]:
                if value > 0:
                    print(f"    {component}: +{value:.1f}")
        else:
            print(f"[SKIPPED] Race did not meet selection criteria")

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()

# Generate summary report
print("\n\n")
print("=" * 80)
print("PHASE 1 ANALYSIS SUMMARY")
print("=" * 80)
print()

if results:
    # Count Phase 1 triggers
    phase1_triggered = [r for r in results if r['phase1_active']]
    baseline_picks = [r for r in results if not r['phase1_active']]

    print(f"Total Races Analyzed: {len(results)}")
    print(f"Phase 1 Triggered: {len(phase1_triggered)} races")
    print(f"Baseline Only: {len(baseline_picks)} races")
    print()

    if phase1_triggered:
        avg_phase1_boost = sum(r['phase1_total'] for r in phase1_triggered) / len(phase1_triggered)
        print(f"Average Phase 1 Boost: +{avg_phase1_boost:.1f} points")
        print()

        print("Phase 1 Enhanced Picks:")
        for r in phase1_triggered:
            print(f"  {r['race_number']}. {r['venue']} {r['time']} - {r['horse']}")
            print(f"     Score: {r['total_score']:.1f} (Phase 1: +{r['phase1_total']:.1f})")
            signals = []
            if r['phase1_signals']['pace_match'] > 0:
                signals.append('Pace Advantage')
            if r['phase1_signals']['jockey_upgrade'] > 0:
                signals.append('Jockey Upgrade')
            print(f"     Signals: {', '.join(signals)}")
            print()

    # Calculate average scores
    avg_score_phase1 = sum(r['total_score'] for r in phase1_triggered) / len(phase1_triggered) if phase1_triggered else 0
    avg_score_baseline = sum(r['total_score'] for r in baseline_picks) / len(baseline_picks) if baseline_picks else 0

    print(f"Average Score (Phase 1 picks): {avg_score_phase1:.1f}")
    print(f"Average Score (Baseline picks): {avg_score_baseline:.1f}")
    print()

    # Expected impact
    print("EXPECTED IMPACT:")
    print("  Phase 1 signals target specific edges:")
    print("    - Run Style Match: +5-8% strike rate")
    print("    - Jockey Upgrade: +2-4% strike rate")
    print("    - Combined: +7-12% potential improvement")
    print()
    print("  Baseline: 18.64% strike rate (11/59 wins)")
    print("  Target: 25-30% strike rate with Phase 1")

else:
    print("[WARNING] No results generated")

print()
print("=" * 80)
print("[5/5] ANALYSIS COMPLETE")
print("=" * 80)
print()

# Save results to JSON
output_data = {
    'analysis_date': datetime.now().isoformat(),
    'data_type': 'SYNTHETIC_DEMO',
    'phase1_status': 'ACTIVE',
    'races_analyzed': len(results),
    'phase1_triggered': len([r for r in results if r['phase1_active']]),
    'results': results,
}

output_file = 'C:/Users/charl/OneDrive/futuregenAI/BetBudAI/phase1_analysis_output.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"Results saved to: {output_file}")
print()
print("NOTE: This demonstration uses synthetic data to show Phase 1 working.")
print("      Real picks will be generated tomorrow (May 21) when pipeline runs.")
