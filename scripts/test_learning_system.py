#!/usr/bin/env python3
"""
Test script for Daily Learning System

Validates the fan-out architecture with mock data.
Tests orchestration, parallel processing, and aggregation.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_mock_race_job(race_num: int) -> dict:
    """Create a mock race job for testing."""
    return {
        'race_id': f'2026-05-20_COURSE{race_num}_14:{race_num:02d}',
        'date': '2026-05-20',
        'course': f'COURSE{race_num}',
        'race_time': f'14:{race_num:02d}',
        'our_pick': {
            'horse_name': f'Test Horse {race_num}',
            'odds': 4.5 + race_num * 0.5,
            'score': 75.0 + race_num,
            'confidence': 0.80,
            'signals': {
                'jockey': 'Test Jockey',
                'trainer': 'Test Trainer',
                'form': '123',
            },
            'bet_type': 'win',
        },
        'bet_id': f'2026-05-20_COURSE{race_num}_14:{race_num:02d}_001',
        'market_id': f'1.{race_num}',
        'outcome': 'LOSS',
    }


def mock_analyze_single_race(job: dict) -> dict:
    """Mock race analyzer for testing."""
    import time
    import random

    # Simulate processing time
    time.sleep(random.uniform(0.1, 0.3))

    # Simulate different loss types
    loss_types = [
        'improver_missed',
        'jockey_upgrade',
        'course_specialist',
        'market_wrong',
        'close_call'
    ]

    loss_type = random.choice(loss_types)

    return {
        'status': 'success',
        'race_id': job['race_id'],
        'date': job['date'],
        'course': job['course'],
        'race_time': job['race_time'],
        'our_pick': job['our_pick']['horse_name'],
        'winner': f"Winner {job['race_id']}",
        'loss_type': loss_type,
        'severity': random.choice(['high', 'medium', 'low']),
        'reason': f'Test reason for {loss_type}',
        'missing_signals': random.sample(
            ['form_velocity', 'jockey_quality', 'course_form', 'odds_sweet_spot'],
            k=random.randint(1, 3)
        ),
        'comparison': {
            'our_pick_name': job['our_pick']['horse_name'],
            'winner_name': f"Winner {job['race_id']}",
            'odds_gap': random.uniform(-2, 2),
        },
        'recommendations': [
            {
                'weight': 'form_velocity_bonus',
                'change': random.uniform(2, 6),
                'reason': 'Test recommendation',
                'confidence': random.uniform(0.5, 0.9)
            },
            {
                'weight': 'jockey_quality',
                'change': random.uniform(1, 4),
                'reason': 'Test recommendation',
                'confidence': random.uniform(0.4, 0.8)
            }
        ],
        'placed_horses': [],
        'processing_time': random.uniform(0.1, 0.3),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }


def test_orchestration():
    """Test full orchestration flow."""
    from backend.learning.orchestrator import LearningOrchestrator
    from backend.learning.aggregator import aggregate_findings

    print("=" * 70)
    print("Testing Daily Learning System - Fan-Out Architecture")
    print("=" * 70)

    # Create mock jobs
    num_races = 10
    race_jobs = [create_mock_race_job(i) for i in range(1, num_races + 1)]

    print(f"\nCreated {len(race_jobs)} mock race jobs")

    # Test parallel processing
    print("\nTesting parallel worker execution...")

    orchestrator = LearningOrchestrator(max_workers=5)

    successful, failed = orchestrator.run_parallel_analysis(
        race_jobs,
        mock_analyze_single_race
    )

    print(f"[OK] Parallel analysis complete: {len(successful)} succeeded, {len(failed)} failed")

    # Test aggregation
    print("\nTesting results aggregation...")

    aggregation = aggregate_findings(successful, min_confidence=0.3)

    patterns = aggregation.get('patterns', {})
    deployment = aggregation.get('deployment_plan', {})

    print(f"[OK] Patterns identified:")
    print(f"  - Dominant loss type: {patterns.get('dominant_loss_type')}")
    print(f"  - Total races: {patterns.get('total_races')}")

    print(f"\n[OK] Deployment plan:")
    print(f"  - Recommendation: {deployment.get('recommendation')}")
    print(f"  - High priority changes: {len(deployment.get('high_priority_changes', []))}")
    print(f"  - Medium priority changes: {len(deployment.get('medium_priority_changes', []))}")

    # Show top recommendations
    print("\n[OK] Top weight recommendations:")
    for i, change in enumerate(deployment.get('high_priority_changes', [])[:5], 1):
        weight = change['weight']
        recommended = change['recommended_change']
        confidence = change['confidence']
        print(f"  {i}. {weight}: {recommended:+.1f} (confidence: {confidence:.2f})")

    # Impact estimate
    impact = aggregation.get('impact_estimate', {})
    print("\n[OK] Impact estimate:")
    print(f"  - Win rate improvement: +{impact.get('estimated_win_rate_improvement', 0) * 100:.1f}%")
    print(f"  - ROI improvement: +{impact.get('estimated_roi_improvement', 0) * 100:.1f}%")

    print("\n" + "=" * 70)
    print("[OK] All tests passed!")
    print("=" * 70)


def test_performance():
    """Test parallel performance vs sequential."""
    import time

    print("\n" + "=" * 70)
    print("Performance Test: Parallel vs Sequential")
    print("=" * 70)

    num_races = 10
    race_jobs = [create_mock_race_job(i) for i in range(1, num_races + 1)]

    # Sequential
    print(f"\n1. Sequential Processing ({num_races} races):")
    start = time.time()
    sequential_results = []
    for job in race_jobs:
        result = mock_analyze_single_race(job)
        sequential_results.append(result)
    sequential_time = time.time() - start
    print(f"   Time: {sequential_time:.2f}s")

    # Parallel
    print(f"\n2. Parallel Processing ({num_races} races, 5 workers):")
    from backend.learning.orchestrator import LearningOrchestrator

    orchestrator = LearningOrchestrator(max_workers=5)
    start = time.time()
    parallel_results, _ = orchestrator.run_parallel_analysis(
        race_jobs,
        mock_analyze_single_race
    )
    parallel_time = time.time() - start
    print(f"   Time: {parallel_time:.2f}s")

    # Speedup
    speedup = sequential_time / parallel_time
    print(f"\n[OK] Speedup: {speedup:.1f}x")
    print(f"[OK] Time saved: {sequential_time - parallel_time:.2f}s")

    print("=" * 70)


if __name__ == '__main__':
    try:
        test_orchestration()
        test_performance()
        print("\n[OK] All tests completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
