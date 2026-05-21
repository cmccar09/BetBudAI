#!/usr/bin/env python3
"""
Monitor Weight Performance
==========================
Dashboard to monitor weight system performance after deployment.

Usage:
    python scripts/monitor_weight_performance.py              # Current status
    python scripts/monitor_weight_performance.py --watch      # Continuous monitoring
    python scripts/monitor_weight_performance.py --history 7  # Last 7 days
"""

import sys
import os
import argparse
import time
from datetime import datetime, timedelta
from typing import Dict, List

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

try:
    import boto3
    from boto3.dynamodb.conditions import Key
    from decimal import Decimal
    DYNAMODB_AVAILABLE = True
except ImportError:
    DYNAMODB_AVAILABLE = False
    print("Warning: boto3 not available, using mock data")

from learning.weight_deployer import WeightDeployer


def get_current_deployment_status(deployer: WeightDeployer) -> Dict:
    """Get current deployment and monitoring status."""
    try:
        table = deployer._get_dynamodb_table()
        response = table.get_item(
            Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
        )

        if 'Item' not in response:
            return {
                'deployed': False,
                'message': 'No weights deployed'
            }

        item = response['Item']

        return {
            'deployed': True,
            'version': int(item.get('version', 0)),
            'updated_at': item.get('updated_at', 'Unknown'),
            'updated_by': item.get('updated_by', 'Unknown'),
            'rationale': item.get('rationale', 'No rationale provided'),
            'rollback_version': int(item.get('rollback_version', 0)),
            'monitoring_until': item.get('monitoring_until', 'Unknown'),
            'weights_count': len(item.get('weights', {}))
        }

    except Exception as e:
        return {
            'deployed': False,
            'message': f'Error fetching status: {e}'
        }


def get_performance_stats(
    deployer: WeightDeployer,
    days_back: int = 1
) -> Dict:
    """Get performance statistics for monitoring."""
    try:
        table = deployer._get_dynamodb_table()

        # Get today's stats
        response = table.get_item(
            Key={'bet_id': 'SYSTEM_STATS', 'bet_date': 'LAST_24H'}
        )

        if 'Item' in response:
            stats = response['Item']
            return {
                'available': True,
                'strike_rate': float(stats.get('strike_rate', 0)),
                'wins': int(stats.get('wins', 0)),
                'total_picks': int(stats.get('total_picks', 0)),
                'roi': float(stats.get('roi', 0)),
                'avg_odds': float(stats.get('avg_odds', 0)),
                'baseline_strike_rate': float(stats.get('baseline_strike_rate', 0.20)),
                'baseline_wins_7day_avg': int(stats.get('baseline_wins_7day_avg', 5))
            }
        else:
            return {
                'available': False,
                'message': 'No performance stats available'
            }

    except Exception as e:
        return {
            'available': False,
            'message': f'Error fetching stats: {e}'
        }


def check_rollback_status(deployer: WeightDeployer, stats: Dict) -> Dict:
    """Check if rollback conditions are met."""
    if not stats.get('available'):
        return {
            'should_rollback': False,
            'reason': 'No stats available'
        }

    should_rollback, triggers = deployer.check_rollback_triggers(stats)

    triggered_conditions = [t for t in triggers if t.triggered]

    return {
        'should_rollback': should_rollback,
        'triggered_conditions': triggered_conditions,
        'all_triggers': triggers
    }


def display_dashboard(
    deployment: Dict,
    stats: Dict,
    rollback: Dict,
    versions: List
):
    """Display comprehensive monitoring dashboard."""
    print("\n" + "="*70)
    print("WEIGHT SYSTEM MONITORING DASHBOARD")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Deployment Status
    print("\n" + "="*70)
    print("DEPLOYMENT STATUS")
    print("="*70)

    if deployment.get('deployed'):
        print(f"\nCurrent Version: {deployment['version']}")
        print(f"Updated: {deployment['updated_at']}")
        print(f"Updated By: {deployment['updated_by']}")
        print(f"Weights: {deployment['weights_count']}")
        print(f"Monitoring Until: {deployment['monitoring_until']}")
        print(f"Rollback Version: {deployment['rollback_version']}")
        print(f"\nRationale:")
        print(f"  {deployment['rationale'][:100]}...")

        # Check if monitoring window is active
        try:
            monitoring_until = datetime.fromisoformat(deployment['monitoring_until'].replace('Z', '+00:00'))
            now = datetime.now(monitoring_until.tzinfo)
            if now < monitoring_until:
                remaining = monitoring_until - now
                hours_remaining = remaining.total_seconds() / 3600
                print(f"\nMonitoring: ACTIVE ({hours_remaining:.1f}h remaining)")
            else:
                print(f"\nMonitoring: COMPLETE")
        except:
            print(f"\nMonitoring: Unknown")

    else:
        print(f"\nStatus: {deployment.get('message', 'Unknown')}")

    # Performance Stats
    print("\n" + "="*70)
    print("PERFORMANCE (Last 24h)")
    print("="*70)

    if stats.get('available'):
        strike_rate = stats['strike_rate']
        baseline_sr = stats['baseline_strike_rate']
        sr_change = strike_rate - baseline_sr

        print(f"\nStrike Rate:    {strike_rate*100:.1f}% ", end="")
        if sr_change > 0:
            print(f"(+{sr_change*100:.1f}% vs baseline)")
        else:
            print(f"({sr_change*100:.1f}% vs baseline)")

        print(f"Wins:           {stats['wins']}/{stats['total_picks']}")
        print(f"ROI:            {stats['roi']*100:+.1f}%")
        print(f"Avg Odds:       {stats['avg_odds']:.2f}")

        print(f"\nBaseline:")
        print(f"  Strike Rate:  {baseline_sr*100:.1f}%")
        print(f"  7-day Avg:    {stats['baseline_wins_7day_avg']} wins")

        # Visual indicator
        if sr_change >= 0.05:
            print(f"\nStatus: EXCELLENT (Strike rate +{sr_change*100:.0f}%)")
        elif sr_change >= 0:
            print(f"\nStatus: GOOD (Strike rate stable)")
        elif sr_change >= -0.03:
            print(f"\nStatus: ACCEPTABLE (Minor decline)")
        else:
            print(f"\nStatus: POOR (Significant decline)")

    else:
        print(f"\n{stats.get('message', 'Unknown')}")

    # Rollback Status
    print("\n" + "="*70)
    print("ROLLBACK STATUS")
    print("="*70)

    if rollback.get('should_rollback'):
        print(f"\nWARNING: ROLLBACK RECOMMENDED")
        print(f"\nTriggered Conditions:")
        for trigger in rollback['triggered_conditions']:
            print(f"  [TRIGGERED] {trigger.name}")
            print(f"    {trigger.condition}")
            if trigger.current_value is not None:
                print(f"    Current: {trigger.current_value:.2f}, Threshold: {trigger.threshold:.2f}")

        print(f"\nAction Required:")
        print(f"  1. Review performance data")
        print(f"  2. Rollback to version {deployment.get('rollback_version', 'N/A')}")
        print(f"  3. Command: python scripts/deploy_weight_changes.py --rollback {deployment.get('rollback_version', 'N/A')}")

    else:
        print(f"\nStatus: OK (No rollback needed)")
        print(f"\nAll Triggers:")
        for trigger in rollback.get('all_triggers', []):
            status = "TRIGGERED" if trigger.triggered else "OK"
            print(f"  [{status}] {trigger.name}")

    # Version History
    if versions:
        print("\n" + "="*70)
        print("RECENT VERSION HISTORY")
        print("="*70)

        for v in versions[:5]:
            print(f"\nVersion {v.version}:")
            print(f"  Created: {v.created_at}")
            print(f"  By: {v.created_by}")
            print(f"  Changes: {len(v.changes_from_previous)}")
            if v.changes_from_previous:
                for wname, change_data in list(v.changes_from_previous.items())[:2]:
                    old = change_data.get('old', 0)
                    new = change_data.get('new', 0)
                    change = change_data.get('change', 0)
                    print(f"    {wname}: {old} -> {new} ({change:+.0f})")

    print("\n" + "="*70)


def watch_mode(deployer: WeightDeployer, interval: int = 300):
    """Continuous monitoring mode (refresh every interval seconds)."""
    print(f"\nStarting watch mode (refresh every {interval}s, Ctrl+C to exit)...")

    try:
        while True:
            # Clear screen (works on Windows and Unix)
            os.system('cls' if os.name == 'nt' else 'clear')

            deployment = get_current_deployment_status(deployer)
            stats = get_performance_stats(deployer)
            rollback = check_rollback_status(deployer, stats)
            versions = deployer.get_weight_version_history(limit=5)

            display_dashboard(deployment, stats, rollback, versions)

            print(f"\nRefreshing in {interval}s... (Ctrl+C to exit)")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nWatch mode stopped.")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor weight system performance'
    )
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Continuous monitoring mode'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Refresh interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--history',
        type=int,
        default=5,
        help='Number of versions to show in history (default: 5)'
    )

    args = parser.parse_args()

    if not DYNAMODB_AVAILABLE:
        print("\nError: boto3 not available. Install with: pip install boto3")
        return

    deployer = WeightDeployer(created_by='monitor_script')

    if args.watch:
        watch_mode(deployer, interval=args.interval)
    else:
        # One-time display
        deployment = get_current_deployment_status(deployer)
        stats = get_performance_stats(deployer)
        rollback = check_rollback_status(deployer, stats)
        versions = deployer.get_weight_version_history(limit=args.history)

        display_dashboard(deployment, stats, rollback, versions)

        print("\nTip: Use --watch for continuous monitoring")


if __name__ == '__main__':
    main()
