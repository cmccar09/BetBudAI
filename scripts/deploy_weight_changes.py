#!/usr/bin/env python3
"""
Deploy Weight Changes
=====================
Manual script to deploy weight changes with full validation pipeline.

Usage:
    python scripts/deploy_weight_changes.py --dry-run    # Preview only
    python scripts/deploy_weight_changes.py              # Deploy changes
    python scripts/deploy_weight_changes.py --rollback 5 # Rollback to version 5

Example:
    python scripts/deploy_weight_changes.py --changes consistency=8 form_velocity_bonus=12
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from learning.weight_decision_engine import WeightDecisionEngine, WeightChange
from learning.weight_validator import WeightValidator
from learning.weight_deployer import WeightDeployer
from config.weights import DEFAULT_WEIGHTS


def parse_changes_from_args(change_args: list) -> Dict[str, float]:
    """
    Parse weight changes from command line arguments.

    Args:
        change_args: List of strings like "consistency=8"

    Returns:
        Dict of weight_name -> new_value
    """
    changes = {}
    for arg in change_args:
        if '=' not in arg:
            print(f"Warning: Invalid change format '{arg}'. Expected 'weight_name=value'")
            continue

        weight_name, value_str = arg.split('=', 1)
        try:
            value = float(value_str)
            changes[weight_name] = value
        except ValueError:
            print(f"Warning: Invalid value '{value_str}' for {weight_name}")

    return changes


def display_current_weights(deployer: WeightDeployer):
    """Display current weight configuration."""
    current_weights, current_version = deployer.get_current_weights()

    print("\n" + "="*70)
    print(f"CURRENT WEIGHTS (Version {current_version})")
    print("="*70)

    if current_weights:
        # Group weights by category
        categories = {
            'Form Signals': [
                'recent_win', 'total_wins', 'consistency', 'form_exact_course_win',
                'form_exact_distance_win', 'form_close_2nd', 'form_velocity_bonus',
                'form_velocity_penalty', 'bounce_back_bonus'
            ],
            'Course & Distance': [
                'course_bonus', 'distance_suitability', 'cd_bonus',
                'graded_race_cd_bonus'
            ],
            'Market Signals': [
                'sweet_spot', 'optimal_odds', 'favorite_correction',
                'market_steam_bonus', 'market_drift_penalty', 'market_divergence_penalty'
            ],
            'Class Signals': [
                'class_drop_bonus', 'class_drop_rebound_bonus', 'official_rating_bonus'
            ],
        }

        for category, weight_names in categories.items():
            print(f"\n{category}:")
            for wname in weight_names:
                if wname in current_weights:
                    print(f"  {wname:<30} = {current_weights[wname]:>5.1f}")

    else:
        print("No weights in database (will use defaults)")
        print(f"Defaults: {len(DEFAULT_WEIGHTS)} weights")

    return current_weights, current_version


def display_version_history(deployer: WeightDeployer, limit: int = 5):
    """Display recent version history."""
    versions = deployer.get_weight_version_history(limit=limit)

    print("\n" + "="*70)
    print(f"WEIGHT VERSION HISTORY (Last {limit})")
    print("="*70)

    if not versions:
        print("No version history available")
        return

    for v in versions:
        print(f"\nVersion {v.version}:")
        print(f"  Created: {v.created_at}")
        print(f"  By: {v.created_by}")
        print(f"  Changes: {len(v.changes_from_previous)}")
        print(f"  Validated: {v.validation_passed}")
        print(f"  Rationale: {v.rationale[:80]}...")

        if v.changes_from_previous:
            print(f"  Weight Changes:")
            for wname, change_data in list(v.changes_from_previous.items())[:3]:
                old = change_data.get('old', 0)
                new = change_data.get('new', 0)
                change = change_data.get('change', 0)
                print(f"    {wname}: {old} → {new} ({change:+.0f})")


def deploy_changes_interactive(
    deployer: WeightDeployer,
    validator: WeightValidator,
    proposed_changes: Dict[str, float],
    dry_run: bool = False
):
    """
    Deploy weight changes with full validation and user confirmation.

    Args:
        deployer: WeightDeployer instance
        validator: WeightValidator instance
        proposed_changes: Dict of weight_name -> new_value
        dry_run: If True, only preview changes
    """
    # Get current weights
    current_weights, current_version = deployer.get_current_weights()

    # If no current weights, use defaults
    if not current_weights:
        current_weights = DEFAULT_WEIGHTS.copy()

    # Build changes dict for validation
    changes_for_validation = {}
    for weight_name, new_value in proposed_changes.items():
        if weight_name not in current_weights:
            print(f"Warning: Weight '{weight_name}' not found in current weights")
            continue

        current_value = current_weights[weight_name]
        changes_for_validation[weight_name] = (current_value, new_value)

    if not changes_for_validation:
        print("\nNo valid changes to deploy")
        return

    # Display proposed changes
    print("\n" + "="*70)
    print("PROPOSED CHANGES")
    print("="*70)
    for weight_name, (current, new) in changes_for_validation.items():
        change = new - current
        print(f"  {weight_name:<30}: {current:>5.1f} → {new:>5.1f} ({change:+5.1f})")

    # Run validation
    print("\n" + "="*70)
    print("RUNNING VALIDATION CHECKS")
    print("="*70)

    validation_summary = validator.validate_all_changes(changes_for_validation)

    print(f"\nValidation Result: {'PASS' if validation_summary.all_passed else 'FAIL'}")
    print(f"Checks: {validation_summary.passed_checks}/{validation_summary.total_checks} passed")
    print(f"\n{validation_summary.overall_recommendation}")

    if validation_summary.results:
        for result in validation_summary.results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.weight_name}: {result.recommendation}")

            if result.warnings:
                for warning in result.warnings:
                    print(f"    ⚠ {warning}")

    if not validation_summary.safe_to_deploy:
        print("\n⚠ VALIDATION FAILED - Changes are not safe to deploy")
        if not dry_run:
            confirm = input("\nDeploy anyway? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Deployment cancelled")
                return

    # If dry run, stop here
    if dry_run:
        print("\n" + "="*70)
        print("DRY RUN - No changes deployed")
        print("="*70)
        return

    # Confirm deployment
    print("\n" + "="*70)
    print("READY TO DEPLOY")
    print("="*70)
    confirm = input(f"\nDeploy {len(changes_for_validation)} weight changes? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Deployment cancelled")
        return

    # Build new weights dict
    new_weights = current_weights.copy()
    changes_dict = {}

    for weight_name, (current, new) in changes_for_validation.items():
        new_weights[weight_name] = new
        changes_dict[weight_name] = {
            'old': current,
            'new': new,
            'change': new - current
        }

    # Deploy
    rationale = f"Manual deployment via deploy_weight_changes.py at {datetime.now().isoformat()}"

    print("\nDeploying...")
    result = deployer.deploy_weights(
        new_weights=new_weights,
        changes=changes_dict,
        rationale=rationale,
        validation_passed=validation_summary.all_passed
    )

    # Display result
    print("\n" + "="*70)
    print("DEPLOYMENT RESULT")
    print("="*70)

    if result.success:
        print(f"\n✓ SUCCESS")
        print(f"  Version: {result.version}")
        print(f"  Changes Applied: {len(result.changes_applied)}")
        print(f"  Monitoring Until: {result.monitoring_until}")
        print(f"  Rollback Available: Version {result.rollback_version}")
        print(f"\n{result.message}")
    else:
        print(f"\n✗ FAILED")
        print(f"  {result.message}")


def rollback_to_version(
    deployer: WeightDeployer,
    target_version: int,
    reason: str,
    dry_run: bool = False
):
    """
    Rollback to a specific weight version.

    Args:
        deployer: WeightDeployer instance
        target_version: Version number to rollback to
        reason: Reason for rollback
        dry_run: If True, only preview rollback
    """
    # Get target version details
    versions = deployer.get_weight_version_history(limit=100)
    target = None
    for v in versions:
        if v.version == target_version:
            target = v
            break

    if not target:
        print(f"\n✗ Version {target_version} not found in history")
        return

    # Display target version
    print("\n" + "="*70)
    print(f"ROLLBACK TO VERSION {target_version}")
    print("="*70)
    print(f"\nTarget Version Details:")
    print(f"  Created: {target.created_at}")
    print(f"  By: {target.created_by}")
    print(f"  Rationale: {target.rationale}")
    print(f"  Weights: {len(target.weights)}")

    if dry_run:
        print("\nDRY RUN - No rollback performed")
        return

    # Confirm rollback
    confirm = input(f"\nRollback to version {target_version}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Rollback cancelled")
        return

    # Perform rollback
    print("\nRolling back...")
    result = deployer.rollback_to_version(
        target_version=target_version,
        reason=reason
    )

    # Display result
    print("\n" + "="*70)
    print("ROLLBACK RESULT")
    print("="*70)

    if result.success:
        print(f"\n✓ SUCCESS")
        print(f"  Rolled back to version {target_version}")
        print(f"  New version: {result.version}")
        print(f"  Changes: {len(result.changes_applied)}")
        print(f"\n{result.message}")
    else:
        print(f"\n✗ FAILED")
        print(f"  {result.message}")


def main():
    parser = argparse.ArgumentParser(
        description='Deploy weight changes with validation'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without deploying'
    )
    parser.add_argument(
        '--show-current',
        action='store_true',
        help='Show current weights and exit'
    )
    parser.add_argument(
        '--show-history',
        action='store_true',
        help='Show version history and exit'
    )
    parser.add_argument(
        '--changes',
        nargs='+',
        help='Weight changes in format: weight_name=value (e.g., consistency=8)'
    )
    parser.add_argument(
        '--rollback',
        type=int,
        help='Rollback to specified version'
    )
    parser.add_argument(
        '--reason',
        type=str,
        default='Manual rollback via script',
        help='Reason for rollback'
    )

    args = parser.parse_args()

    # Initialize components
    deployer = WeightDeployer(created_by='manual_deploy_script')
    validator = WeightValidator()

    # Show current weights
    if args.show_current:
        display_current_weights(deployer)
        return

    # Show history
    if args.show_history:
        display_version_history(deployer)
        return

    # Rollback
    if args.rollback:
        rollback_to_version(
            deployer=deployer,
            target_version=args.rollback,
            reason=args.reason,
            dry_run=args.dry_run
        )
        return

    # Deploy changes
    if args.changes:
        proposed_changes = parse_changes_from_args(args.changes)

        if not proposed_changes:
            print("No valid changes specified")
            return

        deploy_changes_interactive(
            deployer=deployer,
            validator=validator,
            proposed_changes=proposed_changes,
            dry_run=args.dry_run
        )
        return

    # No action specified - show help
    parser.print_help()


if __name__ == '__main__':
    main()
