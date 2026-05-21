"""
Test Weight Auto-Tuning System
===============================
Comprehensive tests for decision engine, validator, and deployer.

Usage:
    python backend/learning/test_weight_system.py
"""

import sys
import json
from datetime import datetime
from weight_decision_engine import WeightDecisionEngine, WeightChange
from weight_validator import WeightValidator
from weight_deployer import WeightDeployer

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_decision_engine():
    """Test decision engine with various scenarios."""
    print("\n" + "="*70)
    print("TEST 1: DECISION ENGINE")
    print("="*70)

    engine = WeightDecisionEngine()

    # Test Case 1: High confidence (2/2 races)
    print("\nTest Case 1: High Confidence (2/2 races)")
    print("-" * 70)

    data_high_conf = {
        "date": "2026-05-20",
        "total_races": 2,
        "losses": 2,
        "wins": 0,
        "patterns": {
            "consistent_placer_bias": {
                "count": 2,
                "confidence": 1.0,
                "votes_for": {
                    "consistency": True,
                    "form_velocity_bonus": True
                }
            }
        },
        "weight_recommendations": {
            "consistency": {
                "current": 12,
                "suggested": 8,
                "votes": 2,
                "historical_matches": 5
            },
            "form_velocity_bonus": {
                "current": 18,
                "suggested": 12,
                "votes": 2,
                "historical_matches": 4
            }
        }
    }

    decision = engine.analyze_aggregated_findings(data_high_conf)

    print(f"Strike Rate: {decision.strike_rate*100:.0f}%")
    print(f"Immediate Changes: {len(decision.immediate_changes)}")
    print(f"Confidence Met: {decision.confidence_threshold_met}")
    print(f"Recommendation: {decision.recommendation}")

    if decision.immediate_changes:
        for change in decision.immediate_changes:
            print(f"\n  {change.weight_name}:")
            print(f"    {change.current_value} → {change.suggested_value} ({change.change:+.0f}pts)")
            print(f"    Confidence: {change.confidence*100:.0f}%")
            print(f"    Urgency: {change.deployment_urgency}")

    assert decision.confidence_threshold_met, "High confidence should trigger deployment"
    assert len(decision.immediate_changes) > 0, "Should have immediate changes"

    # Test Case 2: Medium confidence (3/5 races)
    print("\n\nTest Case 2: Medium Confidence (3/5 races)")
    print("-" * 70)

    data_med_conf = {
        "date": "2026-05-20",
        "total_races": 5,
        "losses": 3,
        "wins": 2,
        "patterns": {
            "class_advantage_missed": {
                "count": 3,
                "confidence": 0.60,
                "votes_for": {
                    "class_drop_bonus": True
                }
            }
        },
        "weight_recommendations": {
            "class_drop_bonus": {
                "current": 24,
                "suggested": 30,
                "votes": 3,
                "historical_matches": 8
            }
        }
    }

    decision = engine.analyze_aggregated_findings(data_med_conf)

    print(f"Strike Rate: {decision.strike_rate*100:.0f}%")
    print(f"Immediate Changes: {len(decision.immediate_changes)}")
    print(f"Pending Changes: {len(decision.pending_changes)}")
    print(f"Recommendation: {decision.recommendation}")

    # Test Case 3: Low confidence (1/5 races)
    print("\n\nTest Case 3: Low Confidence (1/5 races)")
    print("-" * 70)

    data_low_conf = {
        "date": "2026-05-20",
        "total_races": 5,
        "losses": 1,
        "wins": 4,
        "patterns": {
            "pace_mismatch": {
                "count": 1,
                "confidence": 0.20,
                "votes_for": {
                    "going_suitability": True
                }
            }
        },
        "weight_recommendations": {
            "going_suitability": {
                "current": 16,
                "suggested": 20,
                "votes": 1,
                "historical_matches": 2
            }
        }
    }

    decision = engine.analyze_aggregated_findings(data_low_conf)

    print(f"Strike Rate: {decision.strike_rate*100:.0f}%")
    print(f"Monitor Only: {len(decision.monitor_only)}")
    print(f"Recommendation: {decision.recommendation}")

    assert not decision.confidence_threshold_met, "Low confidence should not trigger deployment"

    print("\n✓ Decision Engine Tests Passed")


def test_validator():
    """Test validator with various scenarios."""
    print("\n" + "="*70)
    print("TEST 2: VALIDATOR")
    print("="*70)

    validator = WeightValidator()

    # Test Case 1: Valid changes
    print("\nTest Case 1: Valid Changes")
    print("-" * 70)

    valid_changes = {
        'consistency': (12, 8),
        'form_velocity_bonus': (18, 12),
        'class_drop_bonus': (24, 28)
    }

    summary = validator.validate_all_changes(valid_changes)

    print(f"All Passed: {summary.all_passed}")
    print(f"Checks: {summary.passed_checks}/{summary.total_checks}")
    print(f"Safe to Deploy: {summary.safe_to_deploy}")

    for result in summary.results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.weight_name}: {result.recommendation}")

    assert summary.all_passed, "Valid changes should pass"

    # Test Case 2: Out of bounds
    print("\n\nTest Case 2: Out of Bounds")
    print("-" * 70)

    invalid_changes = {
        'consistency': (12, -5),  # Below minimum
    }

    summary = validator.validate_all_changes(invalid_changes)

    print(f"All Passed: {summary.all_passed}")
    print(f"Safe to Deploy: {summary.safe_to_deploy}")

    for result in summary.results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.weight_name}: {result.recommendation}")
        if result.failed_checks:
            print(f"    Failed: {', '.join(result.failed_checks)}")

    assert not summary.all_passed, "Out of bounds should fail"

    # Test Case 3: Conflicting changes
    print("\n\nTest Case 3: Conflicting Changes")
    print("-" * 70)

    conflicting_changes = {
        'consistency': (12, 8),           # Decrease
        'recent_win': (14, 18),            # Increase
        'form_velocity_bonus': (18, 12)   # Decrease
    }

    summary = validator.validate_all_changes(conflicting_changes)

    print(f"All Passed: {summary.all_passed}")
    print(f"Recommendation: {summary.overall_recommendation}")

    # Test Case 4: Large score impact
    print("\n\nTest Case 4: Large Score Impact")
    print("-" * 70)

    large_changes = {
        'consistency': (12, 45),  # Above maximum
    }

    summary = validator.validate_all_changes(large_changes)

    print(f"All Passed: {summary.all_passed}")
    for result in summary.results:
        status = "✓" if result.passed else "✗"
        print(f"  {status} {result.weight_name}: {result.recommendation}")

    assert not summary.all_passed, "Large impact should fail"

    print("\n✓ Validator Tests Passed")


def test_deployer_simulation():
    """Test deployer (simulation only, no actual deployment)."""
    print("\n" + "="*70)
    print("TEST 3: DEPLOYER (SIMULATION)")
    print("="*70)

    deployer = WeightDeployer(created_by='test_suite')

    # Test Case 1: Get current weights
    print("\nTest Case 1: Get Current Weights")
    print("-" * 70)

    try:
        current_weights, current_version = deployer.get_current_weights()
        print(f"Current Version: {current_version}")
        print(f"Weights Loaded: {len(current_weights)}")
    except Exception as e:
        print(f"Note: DynamoDB not accessible in test environment: {e}")
        print("Using mock data for testing")
        current_weights = {
            'consistency': 12,
            'form_velocity_bonus': 18,
            'class_drop_bonus': 24
        }
        current_version = 1

    # Test Case 2: Simulate deployment (don't actually deploy)
    print("\n\nTest Case 2: Simulate Deployment")
    print("-" * 70)

    new_weights = current_weights.copy()
    changes = {
        'consistency': {'old': 12, 'new': 8, 'change': -4},
        'form_velocity_bonus': {'old': 18, 'new': 12, 'change': -6}
    }

    for wname, change_data in changes.items():
        new_weights[wname] = change_data['new']

    print("Changes to deploy:")
    for wname, change_data in changes.items():
        print(f"  {wname}: {change_data['old']} → {change_data['new']} "
              f"({change_data['change']:+.0f})")

    print("\nNote: Actual deployment skipped in test mode")

    # Test Case 3: Check rollback triggers
    print("\n\nTest Case 3: Rollback Trigger Check")
    print("-" * 70)

    test_stats = {
        'strike_rate': 0.12,
        'baseline_strike_rate': 0.20,
        'wins': 3,
        'baseline_wins_7day_avg': 6,
        'manual_rollback_flag': False
    }

    should_rollback, triggers = deployer.check_rollback_triggers(test_stats)

    print(f"Should Rollback: {should_rollback}")
    for trigger in triggers:
        status = "TRIGGERED" if trigger.triggered else "OK"
        print(f"  [{status}] {trigger.name}")
        if trigger.current_value is not None:
            print(f"    Current: {trigger.current_value:.2f}, Threshold: {trigger.threshold:.2f}")

    assert should_rollback, "Strike rate drop should trigger rollback"

    print("\n✓ Deployer Tests Passed")


def test_integrated_flow():
    """Test complete flow: decision -> validation -> deployment simulation."""
    print("\n" + "="*70)
    print("TEST 4: INTEGRATED FLOW")
    print("="*70)

    # Step 1: Decision Engine
    print("\nStep 1: Decision Engine")
    print("-" * 70)

    engine = WeightDecisionEngine()

    aggregated_data = {
        "date": "2026-05-20",
        "total_races": 2,
        "losses": 2,
        "wins": 0,
        "patterns": {
            "consistent_placer_bias": {
                "count": 2,
                "confidence": 1.0,
                "votes_for": {
                    "consistency": True,
                    "form_velocity_bonus": True
                }
            }
        },
        "weight_recommendations": {
            "consistency": {
                "current": 12,
                "suggested": 8,
                "votes": 2,
                "historical_matches": 5
            },
            "form_velocity_bonus": {
                "current": 18,
                "suggested": 12,
                "votes": 2,
                "historical_matches": 4
            }
        }
    }

    decision = engine.analyze_aggregated_findings(aggregated_data)

    print(f"Immediate Changes: {len(decision.immediate_changes)}")
    for change in decision.immediate_changes:
        print(f"  {change.weight_name}: {change.current_value} → {change.suggested_value}")

    # Step 2: Validation
    print("\nStep 2: Validation")
    print("-" * 70)

    validator = WeightValidator()

    changes_for_validation = {}
    for change in decision.immediate_changes:
        changes_for_validation[change.weight_name] = (
            change.current_value,
            change.suggested_value
        )

    validation = validator.validate_all_changes(changes_for_validation)

    print(f"Validation Result: {'PASS' if validation.all_passed else 'FAIL'}")
    print(f"Safe to Deploy: {validation.safe_to_deploy}")

    # Step 3: Deployment Simulation
    if validation.safe_to_deploy:
        print("\nStep 3: Deployment (Simulated)")
        print("-" * 70)

        deployer = WeightDeployer(created_by='test_integrated_flow')

        print("Changes would be deployed:")
        for wname, (current, new) in changes_for_validation.items():
            print(f"  {wname}: {current} → {new} ({new-current:+.0f})")

        print("\nNote: Actual deployment skipped in test mode")
        print("✓ Integrated flow would succeed")

    else:
        print("\n✗ Validation failed - deployment blocked")

    print("\n✓ Integrated Flow Test Complete")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("WEIGHT AUTO-TUNING SYSTEM - COMPREHENSIVE TESTS")
    print("="*70)

    try:
        test_decision_engine()
        test_validator()
        test_deployer_simulation()
        test_integrated_flow()

        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        print("\nWeight auto-tuning system is ready for deployment.")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        raise


if __name__ == '__main__':
    main()
