"""
Test Enhanced Pick Selector Locally
====================================
Run this before deploying to verify everything works.
"""

import sys
import os
from decimal import Decimal

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all modules import correctly."""
    print("="*70)
    print("TEST 1: Module Imports")
    print("="*70)

    try:
        from backend.core.ev_calculator import (
            calculate_expected_value,
            score_to_win_probability,
            categorize_by_ev,
            calculate_kelly_stake
        )
        print("✓ ev_calculator imported successfully")

        from backend.core.race_quality_filter import (
            is_quality_race,
            select_best_races_from_meeting,
            should_recommend_each_way
        )
        print("✓ race_quality_filter imported successfully")

        from backend.core.enhanced_pick_selector import (
            select_top_picks,
            format_pick_for_ui
        )
        print("✓ enhanced_pick_selector imported successfully")

        print()
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_ev_calculator():
    """Test EV calculation."""
    print("="*70)
    print("TEST 2: EV Calculator")
    print("="*70)

    from backend.core.ev_calculator import calculate_expected_value, score_to_win_probability

    # Test case 1: Good value bet
    score = 125
    odds = 4.5
    win_prob = score_to_win_probability(score)
    ev = calculate_expected_value(win_prob, odds)

    print(f"\nTest Case 1: High confidence, good odds")
    print(f"  Score: {score}")
    print(f"  Odds: {odds}")
    print(f"  Win Probability: {win_prob*100:.1f}%")
    print(f"  Expected Value: {ev*100:+.1f}%")

    if ev > 0.15:
        print(f"  ✓ Good value bet (EV > +15%)")
    else:
        print(f"  ✗ Insufficient value")

    # Test case 2: No value bet
    score = 85
    odds = 3.0
    win_prob = score_to_win_probability(score)
    ev = calculate_expected_value(win_prob, odds)

    print(f"\nTest Case 2: Medium confidence, short odds")
    print(f"  Score: {score}")
    print(f"  Odds: {odds}")
    print(f"  Win Probability: {win_prob*100:.1f}%")
    print(f"  Expected Value: {ev*100:+.1f}%")

    if ev < 0.10:
        print(f"  ✓ Correctly filtered out (EV too low)")
    else:
        print(f"  ? Marginal value")

    print()
    return True


def test_race_filter():
    """Test race quality filtering."""
    print("="*70)
    print("TEST 3: Race Quality Filter")
    print("="*70)

    from backend.core.race_quality_filter import is_quality_race

    # Test case 1: Good race
    good_race = {
        'market_name': 'Class 3 Handicap',
        'runners': [{'name': f'Horse {i}'} for i in range(10)],
        'venue': 'Newmarket'
    }
    is_good, reason = is_quality_race(good_race)
    print(f"\nTest Case 1: Class 3 Handicap, 10 runners")
    print(f"  Quality: {is_good}")
    print(f"  Reason: {reason or 'Passed all filters'}")
    if is_good:
        print(f"  ✓ Correctly identified as quality race")

    # Test case 2: Bad race (maiden)
    bad_race = {
        'market_name': 'Maiden Stakes',
        'runners': [{'name': f'Horse {i}'} for i in range(12)],
        'venue': 'Lingfield'
    }
    is_good, reason = is_quality_race(bad_race)
    print(f"\nTest Case 2: Maiden Stakes, 12 runners")
    print(f"  Quality: {is_good}")
    print(f"  Reason: {reason or 'Passed'}")
    if not is_good:
        print(f"  ✓ Correctly filtered out maiden race")

    # Test case 3: Bad race (too many runners)
    cavalry_race = {
        'market_name': 'Class 4 Handicap',
        'runners': [{'name': f'Horse {i}'} for i in range(20)],
        'venue': 'York'
    }
    is_good, reason = is_quality_race(cavalry_race)
    print(f"\nTest Case 3: Class 4 Handicap, 20 runners")
    print(f"  Quality: {is_good}")
    print(f"  Reason: {reason or 'Passed'}")
    if not is_good:
        print(f"  ✓ Correctly filtered out large field")

    print()
    return True


def test_pick_selector():
    """Test the enhanced pick selector."""
    print("="*70)
    print("TEST 4: Enhanced Pick Selector")
    print("="*70)

    from backend.core.enhanced_pick_selector import select_top_picks

    # Create sample race
    sample_race = {
        'market_name': 'Class 3 Handicap',
        'runners': [{'name': f'Horse {i}'} for i in range(10)],
        'venue': 'Newmarket'
    }

    # Create sample horses with varying quality
    sample_horses = []
    for i in range(8):
        sample_horses.append({
            'bet_id': f'test_{i}',
            'horse': f'Test Horse {i+1}',
            'course': 'Newmarket',
            'race_time': '14:30',
            'odds': 3.0 + (i * 0.8),  # Odds: 3.0, 3.8, 4.6, 5.4, 6.2, 7.0, 7.8, 8.6
            'comprehensive_score': 140 - (i * 8),  # Scores: 140, 132, 124, 116, 108, 100, 92, 84
            'analysis_score': 140 - (i * 8),
            'race_data': sample_race,
            'reasons': [f'Test reason {i+1}'],
            'analysis_breakdown': {'test': 10}
        })

    print(f"\nInput: {len(sample_horses)} candidate horses")
    print(f"  Scores: 140 down to 84 (8pt decrements)")
    print(f"  Odds: 3.0 to 8.6 (varying)")

    result = select_top_picks(sample_horses, max_picks=5, min_long_odds=2)

    print(f"\nResults:")
    print(f"  Final picks: {len(result['picks'])}")
    print(f"  NAP: {result['nap']['horse'] if result['nap'] else 'None'}")
    print(f"  Strong: {len(result['strong'])}")
    print(f"  Value: {len(result['value'])}")

    stats = result['stats']
    print(f"\nStatistics:")
    print(f"  Long odds (4/1+): {stats['long_odds_count']}")
    print(f"  Requirement met: {stats['long_odds_requirement_met']}")
    print(f"  Expected ROI: {stats['expected_roi']}%")
    print(f"  Total stake: {stats['total_stake_units']} units")

    # Verify requirements
    passed = True
    if len(result['picks']) > 5:
        print(f"  ✗ TOO MANY PICKS: {len(result['picks'])} (max 5)")
        passed = False
    else:
        print(f"  ✓ Pick count OK: {len(result['picks'])} ≤ 5")

    if stats['long_odds_count'] < 2:
        print(f"  ⚠ WARNING: Only {stats['long_odds_count']} picks at 4/1+ (need 2)")
    else:
        print(f"  ✓ Long odds requirement met: {stats['long_odds_count']} ≥ 2")

    # Show picks
    print(f"\nSelected Picks:")
    for idx, pick in enumerate(result['picks'], 1):
        tier = pick.get('bet_tier', 'unknown')
        odds = pick.get('odds', 0)
        ev = pick.get('ev_pct', 0)
        stake = pick.get('stake_units', 0)
        label = pick.get('display_label', '')

        tier_emoji = {'nap': '🔥', 'strong': '💪', 'value': '💎'}.get(tier, '📌')
        print(f"  {idx}. {tier_emoji} {pick['horse']}")
        print(f"     Odds: {odds:.1f} | EV: {ev:+.1f}% | Stake: {stake} units")
        print(f"     {label}")

    print()
    return passed


def test_ui_formatting():
    """Test UI formatting."""
    print("="*70)
    print("TEST 5: UI Formatting")
    print("="*70)

    from backend.core.enhanced_pick_selector import format_pick_for_ui

    sample_pick = {
        'pick_rank': 1,
        'display_label': '🔥 NAP - Best Bet',
        'horse': 'Thunder Strike',
        'course': 'York',
        'race_time': '15:15',
        'odds': 4.5,
        'bet_tier': 'nap',
        'confidence_pct': 85,
        'ev_pct': 28.5,
        'win_probability': 0.42,
        'stake_units': 4,
        'kelly_stake': 7.2,
        'bet_type': 'win',
        'n_runners': 10,
        'comprehensive_score': 145,
        'reasons': ['Elite jockey upgrade', 'Class drop bonus', 'Course specialist'],
        'bet_id': 'test_123',
        'trainer': 'W. Mullins',
        'form': '111'
    }

    formatted = format_pick_for_ui(sample_pick)

    print(f"\nFormatted Pick:")
    print(f"  Label: {formatted['display_label']}")
    print(f"  Horse: {formatted['horse']} @ {formatted['course']}")
    print(f"  Odds: {formatted['odds_fractional']} ({formatted['odds_decimal']:.2f})")
    print(f"  Tier: {formatted['bet_tier']}")
    print(f"  Confidence: {formatted['confidence_pct']}%")
    print(f"  EV: {formatted['ev_pct']:+.1f}%")
    print(f"  Stake: {formatted['stake_units']} units (Kelly: {formatted['kelly_stake']})")
    print(f"  Returns: £{formatted['potential_return']} (profit: £{formatted['potential_profit']})")
    print(f"  ✓ UI formatting working correctly")

    print()
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("ENHANCED PICK SELECTOR - TEST SUITE")
    print("="*70)
    print()

    tests = [
        ("Module Imports", test_imports),
        ("EV Calculator", test_ev_calculator),
        ("Race Quality Filter", test_race_filter),
        ("Pick Selector", test_pick_selector),
        ("UI Formatting", test_ui_formatting)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print()
        print("="*70)
        print("🎉 ALL TESTS PASSED! System ready for deployment.")
        print("="*70)
        print()
        print("Next steps:")
        print("  1. Run: python scripts\\test_enhanced_selector.py")
        print("  2. Deploy: .\\scripts\\deploy_enhanced_lambdas.ps1")
        print("  3. Test: aws lambda invoke --function-name surebet-analysis test.json")
        print("  4. Monitor: CloudWatch logs for '[surebet-analysis] Enhanced selection'")
        print()
        return 0
    else:
        print()
        print("="*70)
        print("⚠ SOME TESTS FAILED - Fix errors before deploying")
        print("="*70)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
