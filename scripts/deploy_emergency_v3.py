#!/usr/bin/env python3
"""
Emergency Weight Version 3 Deployment
=====================================

Deploy emergency weight adjustments to fix "consistent placer" bias.

ISSUE: Weight V2 caused 2/2 picks to finish 3rd (100% third place rate)
ROOT CAUSE: Overweighted consistency + form_velocity (placer signals)
FIX: Reduce placer signals, increase winner signals

Usage:
    python scripts/deploy_emergency_v3.py
    python scripts/deploy_emergency_v3.py --dry-run  # Test only
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal
import sys


# EMERGENCY WEIGHT VERSION 3 (2026-05-20 Evening)
# Fix "consistent placer" bias from Version 2
EMERGENCY_WEIGHTS_V3 = {
    # Core form signals - REBALANCED for WINNERS not PLACERS
    'recent_win': 18,  # ↑ INCREASED 14→18 (+28%): Winning predicts winning
    'total_wins': 8,
    'consistency': 8,  # ↓ REDUCED 12→8 (-33%): Stop rewarding serial placers
    'form_exact_course_win': 20,
    'form_exact_distance_win': 20,
    'form_close_2nd': 14,
    'form_velocity_bonus': 12,  # ↓ REDUCED 18→12 (-33%): Gradual improvement ≠ winning
    'form_velocity_penalty': 10,

    # Course & distance
    'course_bonus': 12,
    'distance_suitability': 16,
    'cd_bonus': 16,
    'graded_race_cd_bonus': 8,

    # Market signals - INCREASED (trust market for favorites)
    'sweet_spot': 8,
    'optimal_odds': 8,
    'favorite_correction': 10,  # ↑ INCREASED 5→10 (+100%): Trust market when odds < 5.0
    'market_steam_bonus': 10,
    'market_drift_penalty': 6,
    'market_divergence_penalty': 18,
    'score_gap_illusion_penalty': 12,

    # Trainer & jockey - STRENGTHEN elite connections
    'trainer_reputation': 18,  # ↑ INCREASED 16→18 (+12%): Elite trainers get winners
    'trainer_tier2': 8,
    'trainer_tier3': 4,
    'trainer_combo_bonus': 8,
    'trainer_form_bonus': 8,
    'trainer_course_bonus': 12,
    'same_trainer_rival_penalty': 10,
    'jockey_quality': 14,  # ↑ INCREASED 12→14 (+16%): Elite jockeys WIN
    'jockey_tier2': 6,
    'jockey_course_bonus': 15,
    'meeting_focus_trainer': 10,
    'meeting_focus_jockey': 10,
    'meeting_focus_combo': 10,

    # Going & conditions
    'going_suitability': 16,
    'heavy_going_penalty': 12,
    'track_pattern_bonus': 8,

    # Race characteristics
    'weight_penalty': 10,
    'age_bonus': 7,
    'novice_race_penalty': 8,
    'large_field_penalty': 10,
    'aw_evening_penalty': 12,
    'aw_low_class_penalty': 50,
    'irish_handicap_penalty': 10,

    # Ratings & class - STRENGTHEN (class droppers WIN)
    'official_rating_bonus': 8,
    'class_drop_bonus': 30,  # ↑ INCREASED 24→30 (+25%): Class droppers WIN, not place
    'class_drop_rebound_bonus': 20,

    # Form patterns - REBALANCED
    'bounce_back_bonus': 10,  # ↓ REDUCED 14→10 (-28%): Recovery ≠ explosive winning form
    'pu_winner_bounce': 6,
    'short_form_improvement': 8,
    'unexposed_bonus': 12,

    # Timeform
    'timeform_5star_bonus': 12,
    'timeform_4star_bonus': 8,
    'timeform_3star_bonus': 4,
    'timeform_lowstar_penalty': 6,

    # Risk controls
    'recent_non_completion_penalty': 10,
    'current_form_edge_bonus': 8,
    'potential_hype_penalty': 10,
    'unknown_trainer_penalty': 8,
    'new_trainer_debut': 5,

    # Database knowledge
    'database_history': 15,

    # Phase 1 signals (if active)
    'pace_match_bonus': 12,
    'jockey_upgrade_bonus': 10,
    'equipment_change_bonus': 8,
    'market_liquidity_bonus': 6,
    'pace_match_penalty': 8,
    'jockey_downgrade_penalty': 8,
    'equipment_removal_penalty': 6,
    'market_liquidity_penalty': 4,
}


def convert_to_decimal(weights):
    """Convert float weights to Decimal for DynamoDB."""
    return {k: Decimal(str(v)) for k, v in weights.items()}


def deploy_weights(dry_run=False):
    """Deploy emergency weights to DynamoDB."""

    print("\n" + "="*80)
    print("EMERGENCY WEIGHT VERSION 3 DEPLOYMENT")
    print("="*80 + "\n")

    print("ISSUE: Weight V2 caused 2/2 picks to finish 3rd place (100% third place rate)")
    print("ROOT CAUSE: Overweighted consistency + form_velocity (placer signals)")
    print("FIX: Reduce placer signals, increase winner signals\n")

    # Show changes
    print("KEY CHANGES IN VERSION 3:")
    print("-" * 80)
    print(f"{'Signal':<30} {'V2':<8} {'V3':<8} {'Change':<12} {'Reason':<30}")
    print("-" * 80)

    changes = [
        ('recent_win', 14, 18, '+28%', 'Winning predicts winning'),
        ('consistency', 12, 8, '-33%', 'Stop rewarding placers'),
        ('form_velocity_bonus', 18, 12, '-33%', 'Gradual ≠ winning'),
        ('bounce_back_bonus', 14, 10, '-28%', 'Recovery ≠ explosive'),
        ('class_drop_bonus', 24, 30, '+25%', 'Class droppers WIN'),
        ('favorite_correction', 5, 10, '+100%', 'Trust market < 5.0'),
        ('trainer_reputation', 16, 18, '+12%', 'Elite trainers WIN'),
        ('jockey_quality', 12, 14, '+16%', 'Elite jockeys WIN'),
    ]

    for signal, v2, v3, change, reason in changes:
        print(f"{signal:<30} {v2:<8} {v3:<8} {change:<12} {reason:<30}")

    print("\n")
    print("IMPACT ANALYSIS:")
    print("-" * 80)

    # Calculate total placer vs winner signals
    v2_placer_total = 12 + 18 + 14  # consistency + form_velocity + bounce_back
    v3_placer_total = 8 + 12 + 10

    v2_winner_total = 14 + 24 + 5 + 16 + 12  # recent_win + class_drop + favorite + trainer + jockey
    v3_winner_total = 18 + 30 + 10 + 18 + 14

    print(f"'Placer Signals' (consistency + form_velocity + bounce_back):")
    print(f"  V2: {v2_placer_total}pts → V3: {v3_placer_total}pts ({(v3_placer_total-v2_placer_total)/v2_placer_total*100:+.0f}%)")

    print(f"\n'Winner Signals' (recent_win + class_drop + favorite + trainer + jockey):")
    print(f"  V2: {v2_winner_total}pts → V3: {v3_winner_total}pts ({(v3_winner_total-v2_winner_total)/v2_winner_total*100:+.0f}%)")

    print("\n")
    print("EXPECTED OUTCOME:")
    print("-" * 80)
    print("✅ Top picks will favor CLASS DROPPERS with WINNING FORM")
    print("✅ Reduce selection of 'consistent placers' (gradual improvers)")
    print("✅ Strike rate shift: 0% (3rd place) → 30-40% (1st/2nd place)")
    print("✅ Phase 1 will amplify WINNERS not PLACERS (when active)")

    print("\n")

    if dry_run:
        print("DRY RUN MODE: Weights NOT deployed to DynamoDB")
        print("Run without --dry-run to deploy")
        print("\n")

        # Show what would be deployed
        print("WEIGHTS THAT WOULD BE DEPLOYED:")
        print("-" * 80)
        print(json.dumps(EMERGENCY_WEIGHTS_V3, indent=2, sort_keys=True))
        print("\n")
        return True

    # Confirm deployment
    print("CONFIRM DEPLOYMENT")
    print("-" * 80)
    print("This will update DynamoDB with Weight Version 3")
    print("Tomorrow's picks (May 21 08:30 UTC) will use these weights")
    print("")
    response = input("Deploy to production? (yes/no): ")

    if response.lower() != 'yes':
        print("\nDeployment CANCELLED")
        return False

    # Deploy to DynamoDB
    print("\nDeploying to DynamoDB...")

    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')

        weights_decimal = convert_to_decimal(EMERGENCY_WEIGHTS_V3)

        table.put_item(
            Item={
                'bet_id': 'SYSTEM_WEIGHTS',
                'bet_date': 'CONFIG',
                'weights': weights_decimal,
                'updated_at': datetime.now().isoformat(),
                'version': 3,
                'version_name': 'V3_EMERGENCY_WINNER_BIAS',
                'deployment_reason': 'Fix consistent placer bias - 2/2 picks finished 3rd',
                'deployed_by': 'emergency_deployment_script',
                'changes': {
                    'reduced_placer_signals': {
                        'consistency': '12→8 (-33%)',
                        'form_velocity_bonus': '18→12 (-33%)',
                        'bounce_back_bonus': '14→10 (-28%)',
                    },
                    'increased_winner_signals': {
                        'recent_win': '14→18 (+28%)',
                        'class_drop_bonus': '24→30 (+25%)',
                        'favorite_correction': '5→10 (+100%)',
                        'trainer_reputation': '16→18 (+12%)',
                        'jockey_quality': '12→14 (+16%)',
                    }
                }
            }
        )

        print("✅ Weights deployed successfully to DynamoDB")
        print(f"✅ Version: 3 (V3_EMERGENCY_WINNER_BIAS)")
        print(f"✅ Timestamp: {datetime.now().isoformat()}")

        # Verify deployment
        print("\nVerifying deployment...")
        response = table.get_item(
            Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
        )

        if 'Item' in response:
            version = response['Item'].get('version')
            updated_at = response['Item'].get('updated_at')
            print(f"✅ Verified: Version {version} deployed at {updated_at}")
        else:
            print("⚠️  Warning: Could not verify deployment")

        print("\n")
        print("NEXT STEPS:")
        print("-" * 80)
        print("1. ✅ Weight V3 deployed to production")
        print("2. ⏳ Tomorrow 08:30 UTC: Morning pipeline uses V3 + Phase 1")
        print("3. ⏳ Monitor: Do picks favor class droppers (not placers)?")
        print("4. ⏳ Validate: Strike rate 30-40% (from current 0%)")
        print("\n")

        return True

    except Exception as e:
        print(f"\n❌ ERROR deploying weights: {e}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials configured")
        print("2. Verify DynamoDB table 'SureBetBets' exists")
        print("3. Check IAM permissions for dynamodb:PutItem")
        print("4. Try: aws dynamodb describe-table --table-name SureBetBets")
        print("\n")
        return False


def verify_current_weights():
    """Check current weights in DynamoDB."""
    print("\nFetching current weights from DynamoDB...")

    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('SureBetBets')

        response = table.get_item(
            Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
        )

        if 'Item' in response:
            item = response['Item']
            version = item.get('version', 'Unknown')
            updated_at = item.get('updated_at', 'Unknown')

            print(f"\nCurrent Version: {version}")
            print(f"Last Updated: {updated_at}")

            weights = item.get('weights', {})

            print("\nKey Weight Values:")
            print("-" * 80)
            key_signals = [
                'recent_win', 'consistency', 'form_velocity_bonus',
                'bounce_back_bonus', 'class_drop_bonus', 'favorite_correction',
                'trainer_reputation', 'jockey_quality'
            ]

            for signal in key_signals:
                value = float(weights.get(signal, 0)) if signal in weights else 'NOT FOUND'
                print(f"{signal:<30} {value}")

            return True
        else:
            print("No weights found in database")
            return False

    except Exception as e:
        print(f"Error fetching weights: {e}")
        return False


def main():
    """Main deployment function."""

    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv

    # Show current weights
    print("\n" + "="*80)
    print("CURRENT WEIGHTS IN DATABASE")
    print("="*80)
    verify_current_weights()

    # Deploy new weights
    success = deploy_weights(dry_run=dry_run)

    if success:
        if not dry_run:
            print("="*80)
            print("✅ DEPLOYMENT COMPLETE")
            print("="*80)
            print("\nWeight Version 3 is now active")
            print("Tomorrow's picks (May 21 08:30 UTC) will use these weights")
            print("\nExpected improvement:")
            print("- Strike rate: 0% → 30-40%")
            print("- Picks: Consistent placers → Class droppers with winning form")
            print("- Outcome: 1st/2nd place finishes (not 3rd)")
            print("\n")
        else:
            print("="*80)
            print("DRY RUN COMPLETE")
            print("="*80)
            print("\nRun without --dry-run to deploy to production")
            print("\n")
    else:
        print("="*80)
        print("❌ DEPLOYMENT FAILED")
        print("="*80)
        print("\nWeights NOT deployed. Check errors above.")
        print("\n")


if __name__ == '__main__':
    main()
