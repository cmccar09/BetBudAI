#!/usr/bin/env python3
"""
Daily Learning System Entry Point

Run this script to trigger daily learning analysis:
- Fetches yesterday's settled picks
- Analyzes losses in parallel
- Generates weight adjustment recommendations
- Optionally deploys changes automatically

Usage:
    python scripts/run_daily_learning.py                    # Analyze yesterday
    python scripts/run_daily_learning.py --date 2026-05-19  # Analyze specific date
    python scripts/run_daily_learning.py --auto-deploy      # Auto-deploy high-priority changes
    python scripts/run_daily_learning.py --dry-run          # Preview only, no deployment
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.learning.orchestrator import LearningOrchestrator
from backend.config.weights import WeightManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Daily Learning System - Analyze races and recommend weight changes'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Target date (YYYY-MM-DD), defaults to yesterday'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=3,
        help='Minimum races needed for weight changes (default: 3)'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=10,
        help='Maximum parallel workers (default: 10)'
    )
    parser.add_argument(
        '--auto-deploy',
        action='store_true',
        help='Automatically deploy high-priority changes'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without deploying'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for results (JSON format)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    import logging

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def print_summary(report: dict):
    """Print human-readable summary of learning results."""
    summary = report.get('summary', {})
    aggregation = report.get('aggregation', {})
    deployment = aggregation.get('deployment_plan', {})
    impact = aggregation.get('impact_estimate', {})

    print("\n" + "=" * 70)
    print("DAILY LEARNING SUMMARY")
    print("=" * 70)

    print(f"\nDate: {summary.get('target_date')}")
    print(f"Execution Time: {summary.get('execution_time_seconds')}s")
    print(f"Races Analyzed: {summary.get('losses_analyzed')}/{summary.get('total_picks')}")
    print(f"Win Rate: {summary.get('win_rate', 0) * 100:.1f}%")

    patterns = aggregation.get('patterns', {})
    print(f"\nDominant Loss Type: {patterns.get('dominant_loss_type', 'N/A')}")

    print("\nLoss Type Distribution:")
    for loss_type, count in patterns.get('loss_types', {}).items():
        frequency = patterns.get('loss_type_frequencies', {}).get(loss_type, 0)
        print(f"  - {loss_type}: {count} ({frequency * 100:.1f}%)")

    print("\nTop Missing Signals:")
    signal_counts = patterns.get('missing_signals', {})
    for signal, count in sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        frequency = patterns.get('signal_frequencies', {}).get(signal, 0)
        print(f"  - {signal}: {count} races ({frequency * 100:.1f}%)")

    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)

    print(f"\nDeployment: {deployment.get('recommendation')}")
    print(f"Reason: {deployment.get('reason')}")

    changes = deployment.get('changes_summary', {})
    print(f"\nTotal Changes: {changes.get('total_changes')}")
    print(f"  High Priority: {changes.get('high_priority')}")
    print(f"  Medium Priority: {changes.get('medium_priority')}")
    print(f"  Low Priority: {changes.get('low_priority')}")

    print("\nTop Priority Weight Changes:")
    high_priority = deployment.get('high_priority_changes', [])
    for change in high_priority[:10]:
        weight = change['weight']
        recommended = change['recommended_change']
        confidence = change['confidence']
        occurrence = change['occurrence_frequency']
        sign = '+' if recommended > 0 else ''
        print(f"  - {weight}: {sign}{recommended} (confidence: {confidence:.2f}, {occurrence * 100:.0f}% of races)")

    print("\n" + "-" * 70)
    print("IMPACT ESTIMATE")
    print("-" * 70)

    print(f"Win Rate Improvement: +{impact.get('estimated_win_rate_improvement', 0) * 100:.1f}%")
    print(f"ROI Improvement: +{impact.get('estimated_roi_improvement', 0) * 100:.1f}%")
    print(f"Confidence: {impact.get('confidence', 'N/A')}")

    print("\n" + "=" * 70)


def deploy_weight_changes(deployment_plan: dict, dry_run: bool = False):
    """
    Deploy weight changes to DynamoDB.

    Args:
        deployment_plan: Deployment plan with prioritized changes
        dry_run: If True, preview changes without deploying
    """
    high_priority = deployment_plan.get('high_priority_changes', [])

    if not high_priority:
        print("\nNo high-priority changes to deploy.")
        return

    print("\n" + "-" * 70)
    print("DEPLOYING WEIGHT CHANGES")
    print("-" * 70)

    # Load current weights
    weight_manager = WeightManager()
    current_weights = weight_manager.get_weights()

    # Apply changes
    updated_weights = current_weights.copy()

    for change in high_priority:
        weight_name = change['weight']
        change_amount = change['recommended_change']

        old_value = current_weights.get(weight_name, 0)
        new_value = old_value + change_amount

        # Bounds checking
        new_value = max(0, min(100, new_value))

        updated_weights[weight_name] = new_value

        print(f"\n{weight_name}:")
        print(f"  Current: {old_value}")
        print(f"  Change: {change_amount:+.1f}")
        print(f"  New: {new_value}")
        print(f"  Confidence: {change['confidence']:.2f}")
        print(f"  Reason: {change['reasons'][0] if change['reasons'] else 'N/A'}")

    if dry_run:
        print("\n[DRY RUN] Changes previewed but not deployed.")
        return

    # Confirm deployment
    print("\n" + "-" * 70)
    response = input("Deploy these changes? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("Deployment cancelled.")
        return

    # Deploy to DynamoDB
    success = weight_manager.save_weights(updated_weights)

    if success:
        print("\n✓ Weight changes deployed successfully!")
        print("Changes will be active in next prediction cycle.")
    else:
        print("\n✗ Deployment failed - check logs for details.")


def main():
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    # Create orchestrator
    orchestrator = LearningOrchestrator(
        max_workers=args.max_workers
    )

    # Run learning
    print("Starting Daily Learning System...")
    print(f"Target Date: {args.date or 'yesterday'}")
    print(f"Workers: {args.max_workers}")

    report = orchestrator.orchestrate_daily_learning(
        target_date=args.date,
        min_samples=args.min_samples
    )

    # Check status
    if report.get('status') not in ['success']:
        print(f"\n✗ Learning failed: {report.get('message', 'Unknown error')}")
        return 1

    # Print summary
    print_summary(report)

    # Save output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull report saved to: {args.output}")

    # Deploy changes if requested
    deployment_plan = report.get('aggregation', {}).get('deployment_plan', {})
    recommendation = deployment_plan.get('recommendation')

    if args.auto_deploy and recommendation in ['DEPLOY_IMMEDIATELY', 'DEPLOY_TONIGHT']:
        deploy_weight_changes(deployment_plan, dry_run=args.dry_run)
    elif recommendation in ['DEPLOY_IMMEDIATELY', 'DEPLOY_TONIGHT']:
        print(f"\nRecommendation: {recommendation}")
        print("Use --auto-deploy to deploy changes automatically")

    print("\n✓ Daily Learning Complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
