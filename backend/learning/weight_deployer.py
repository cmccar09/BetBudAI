"""
Weight Deployer
===============
Deploys validated weight changes to DynamoDB with versioning,
rollback capability, and monitoring.

Process:
1. Calculate proposed changes
2. Run safety validations
3. Create Weight Version N+1
4. Store in DynamoDB (SureBetBets, SYSTEM_WEIGHTS key)
5. Increment version number
6. Log change details
7. Set rollback checkpoint
8. Monitor next 24h performance
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal


@dataclass
class WeightVersion:
    """A versioned snapshot of weights."""
    version: int
    weights: Dict[str, float]
    created_at: str
    created_by: str
    changes_from_previous: Dict[str, Dict]  # weight -> {old, new, change}
    rationale: str
    validation_passed: bool
    rollback_checkpoint: bool


@dataclass
class DeploymentResult:
    """Result of weight deployment."""
    success: bool
    version: int
    weights_deployed: Dict[str, float]
    changes_applied: Dict[str, Dict]
    rollback_version: Optional[int]
    deployment_time: str
    monitoring_until: str
    message: str


@dataclass
class RollbackTrigger:
    """Conditions that trigger automatic rollback."""
    name: str
    condition: str
    threshold: float
    current_value: Optional[float]
    triggered: bool


class WeightDeployer:
    """
    Deploys weight changes to DynamoDB with versioning and rollback.
    """

    # Rollback trigger thresholds
    STRIKE_RATE_DROP_THRESHOLD = 0.05  # 5% drop
    WIN_DECREASE_THRESHOLD = 0.50  # 50% decrease in wins
    MONITORING_PERIOD_HOURS = 24

    def __init__(
        self,
        dynamodb_table_name: str = 'SureBetBets',
        region: str = 'eu-west-1',
        created_by: str = 'AutoTuningEngine'
    ):
        self.table_name = dynamodb_table_name
        self.region = region
        self.created_by = created_by
        self.dynamodb = None
        self.table = None

    def _get_dynamodb_table(self):
        """Lazy-load DynamoDB table."""
        if self.table is None:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.table = self.dynamodb.Table(self.table_name)
        return self.table

    def _convert_to_decimal(self, obj):
        """Convert floats to Decimal for DynamoDB."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_decimal(v) for v in obj]
        return obj

    def _convert_from_decimal(self, obj):
        """Convert Decimal to float from DynamoDB."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_from_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_from_decimal(v) for v in obj]
        return obj

    def get_current_weights(self) -> Tuple[Dict[str, float], int]:
        """
        Get current weights from DynamoDB.

        Returns:
            (weights_dict, current_version)
        """
        try:
            table = self._get_dynamodb_table()
            response = table.get_item(
                Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
            )

            if 'Item' in response:
                item = response['Item']
                weights = self._convert_from_decimal(item.get('weights', {}))
                version = int(item.get('version', 1))
                return weights, version
            else:
                # No weights in DB, return empty
                return {}, 0

        except Exception as e:
            print(f"[WeightDeployer] Error fetching current weights: {e}")
            return {}, 0

    def get_weight_version_history(self, limit: int = 10) -> List[WeightVersion]:
        """
        Get weight version history from DynamoDB.

        Returns:
            List of WeightVersion objects (newest first)
        """
        try:
            table = self._get_dynamodb_table()
            response = table.get_item(
                Key={'bet_id': 'WEIGHT_VERSIONS', 'bet_date': 'HISTORY'}
            )

            if 'Item' in response:
                versions_data = self._convert_from_decimal(
                    response['Item'].get('versions', [])
                )
                versions = [
                    WeightVersion(**v) for v in versions_data[-limit:]
                ]
                return list(reversed(versions))  # Newest first
            else:
                return []

        except Exception as e:
            print(f"[WeightDeployer] Error fetching version history: {e}")
            return []

    def save_weight_version(
        self,
        version: WeightVersion
    ) -> bool:
        """
        Save a weight version to history.

        Returns:
            True if successful
        """
        try:
            table = self._get_dynamodb_table()

            # Fetch existing history
            response = table.get_item(
                Key={'bet_id': 'WEIGHT_VERSIONS', 'bet_date': 'HISTORY'}
            )

            if 'Item' in response:
                versions = response['Item'].get('versions', [])
            else:
                versions = []

            # Append new version
            versions.append(self._convert_to_decimal(asdict(version)))

            # Save back (keep last 100 versions)
            table.put_item(
                Item={
                    'bet_id': 'WEIGHT_VERSIONS',
                    'bet_date': 'HISTORY',
                    'versions': versions[-100:],  # Keep last 100
                    'updated_at': datetime.now().isoformat()
                }
            )

            return True

        except Exception as e:
            print(f"[WeightDeployer] Error saving weight version: {e}")
            return False

    def deploy_weights(
        self,
        new_weights: Dict[str, float],
        changes: Dict[str, Dict],
        rationale: str,
        validation_passed: bool = True
    ) -> DeploymentResult:
        """
        Deploy new weights to DynamoDB.

        Args:
            new_weights: Complete weight dictionary with new values
            changes: Dict of weight -> {old, new, change}
            rationale: Reason for changes
            validation_passed: Whether validation checks passed

        Returns:
            DeploymentResult
        """
        try:
            # Get current version
            current_weights, current_version = self.get_current_weights()
            new_version = current_version + 1

            # Create weight version snapshot
            version_snapshot = WeightVersion(
                version=new_version,
                weights=new_weights,
                created_at=datetime.now().isoformat(),
                created_by=self.created_by,
                changes_from_previous=changes,
                rationale=rationale,
                validation_passed=validation_passed,
                rollback_checkpoint=True
            )

            # Save to version history
            version_saved = self.save_weight_version(version_snapshot)
            if not version_saved:
                return DeploymentResult(
                    success=False,
                    version=current_version,
                    weights_deployed={},
                    changes_applied={},
                    rollback_version=None,
                    deployment_time=datetime.now().isoformat(),
                    monitoring_until="",
                    message="Failed to save version history"
                )

            # Deploy to active config
            table = self._get_dynamodb_table()
            table.put_item(
                Item={
                    'bet_id': 'SYSTEM_WEIGHTS',
                    'bet_date': 'CONFIG',
                    'weights': self._convert_to_decimal(new_weights),
                    'version': new_version,
                    'updated_at': datetime.now().isoformat(),
                    'updated_by': self.created_by,
                    'rationale': rationale,
                    'rollback_version': current_version,
                    'monitoring_until': (
                        datetime.now() + timedelta(hours=self.MONITORING_PERIOD_HOURS)
                    ).isoformat()
                }
            )

            monitoring_until = (
                datetime.now() + timedelta(hours=self.MONITORING_PERIOD_HOURS)
            ).isoformat()

            return DeploymentResult(
                success=True,
                version=new_version,
                weights_deployed=new_weights,
                changes_applied=changes,
                rollback_version=current_version,
                deployment_time=datetime.now().isoformat(),
                monitoring_until=monitoring_until,
                message=(
                    f"Successfully deployed weight version {new_version}. "
                    f"Applied {len(changes)} changes. "
                    f"Monitoring until {monitoring_until}. "
                    f"Rollback to version {current_version} available."
                )
            )

        except Exception as e:
            return DeploymentResult(
                success=False,
                version=current_version if 'current_version' in locals() else 0,
                weights_deployed={},
                changes_applied={},
                rollback_version=None,
                deployment_time=datetime.now().isoformat(),
                monitoring_until="",
                message=f"Deployment failed: {e}"
            )

    def rollback_to_version(
        self,
        target_version: int,
        reason: str
    ) -> DeploymentResult:
        """
        Rollback to a previous weight version.

        Args:
            target_version: Version number to rollback to
            reason: Reason for rollback

        Returns:
            DeploymentResult
        """
        try:
            # Get version history
            versions = self.get_weight_version_history(limit=100)

            # Find target version
            target = None
            for v in versions:
                if v.version == target_version:
                    target = v
                    break

            if not target:
                return DeploymentResult(
                    success=False,
                    version=0,
                    weights_deployed={},
                    changes_applied={},
                    rollback_version=None,
                    deployment_time=datetime.now().isoformat(),
                    monitoring_until="",
                    message=f"Version {target_version} not found in history"
                )

            # Get current version for comparison
            current_weights, current_version = self.get_current_weights()

            # Calculate changes (reverse)
            changes = {}
            for weight_name, new_value in target.weights.items():
                old_value = current_weights.get(weight_name, new_value)
                if old_value != new_value:
                    changes[weight_name] = {
                        'old': old_value,
                        'new': new_value,
                        'change': new_value - old_value
                    }

            # Deploy the rollback
            rationale = f"ROLLBACK to version {target_version}: {reason}"
            return self.deploy_weights(
                new_weights=target.weights,
                changes=changes,
                rationale=rationale,
                validation_passed=True  # Already validated when originally deployed
            )

        except Exception as e:
            return DeploymentResult(
                success=False,
                version=0,
                weights_deployed={},
                changes_applied={},
                rollback_version=None,
                deployment_time=datetime.now().isoformat(),
                monitoring_until="",
                message=f"Rollback failed: {e}"
            )

    def check_rollback_triggers(
        self,
        current_stats: Dict
    ) -> Tuple[bool, List[RollbackTrigger]]:
        """
        Check if rollback should be triggered based on performance.

        Args:
            current_stats: Dict with 'strike_rate', 'wins', 'baseline_strike_rate', etc.

        Returns:
            (should_rollback, list_of_triggered_conditions)
        """
        triggers = []

        # Trigger 1: Strike rate drop
        current_sr = current_stats.get('strike_rate', 0)
        baseline_sr = current_stats.get('baseline_strike_rate', 0.20)
        sr_drop = baseline_sr - current_sr

        strike_trigger = RollbackTrigger(
            name="strike_rate_drop",
            condition=f"Strike rate drops >{self.STRIKE_RATE_DROP_THRESHOLD*100:.0f}%",
            threshold=self.STRIKE_RATE_DROP_THRESHOLD,
            current_value=sr_drop,
            triggered=sr_drop > self.STRIKE_RATE_DROP_THRESHOLD
        )
        triggers.append(strike_trigger)

        # Trigger 2: Win decrease
        current_wins = current_stats.get('wins', 0)
        baseline_wins = current_stats.get('baseline_wins_7day_avg', 1)
        win_ratio = current_wins / max(baseline_wins, 1)

        win_trigger = RollbackTrigger(
            name="win_decrease",
            condition=f"Wins decrease by >{self.WIN_DECREASE_THRESHOLD*100:.0f}%",
            threshold=self.WIN_DECREASE_THRESHOLD,
            current_value=1.0 - win_ratio,
            triggered=win_ratio < (1.0 - self.WIN_DECREASE_THRESHOLD)
        )
        triggers.append(win_trigger)

        # Trigger 3: Manual override flag
        manual_override = current_stats.get('manual_rollback_flag', False)
        manual_trigger = RollbackTrigger(
            name="manual_override",
            condition="Human operator set rollback flag",
            threshold=1.0,
            current_value=1.0 if manual_override else 0.0,
            triggered=manual_override
        )
        triggers.append(manual_trigger)

        # Should rollback if any trigger is activated
        should_rollback = any(t.triggered for t in triggers)

        return should_rollback, triggers


# Example usage
if __name__ == '__main__':
    deployer = WeightDeployer(created_by='ManualTest')

    print("\n" + "="*70)
    print("WEIGHT DEPLOYER - DEPLOYMENT SIMULATION")
    print("="*70)

    # Get current weights
    current_weights, current_version = deployer.get_current_weights()
    print(f"\nCurrent Version: {current_version}")
    print(f"Current Weights: {len(current_weights)} weights loaded")

    # Simulate new weights (with changes from decision engine)
    new_weights = current_weights.copy()
    changes = {
        'consistency': {'old': 12, 'new': 8, 'change': -4},
        'form_velocity_bonus': {'old': 18, 'new': 12, 'change': -6},
        'class_drop_bonus': {'old': 24, 'new': 28, 'change': 4},
    }

    for weight_name, change_data in changes.items():
        new_weights[weight_name] = change_data['new']

    rationale = (
        "Pattern evidence from 2/2 races showing consistent placer bias. "
        "Reducing placer weights (consistency, form_velocity) and boosting "
        "class_drop detection."
    )

    print(f"\n{'='*70}")
    print("DEPLOYING CHANGES (DRY RUN)")
    print("="*70)
    print(f"\nChanges to apply:")
    for weight_name, change_data in changes.items():
        print(f"  {weight_name}: {change_data['old']} → {change_data['new']} "
              f"({change_data['change']:+.0f})")

    # NOTE: Uncomment to actually deploy
    # result = deployer.deploy_weights(
    #     new_weights=new_weights,
    #     changes=changes,
    #     rationale=rationale,
    #     validation_passed=True
    # )
    #
    # print(f"\n{'='*70}")
    # print("DEPLOYMENT RESULT")
    # print("="*70)
    # print(f"\nSuccess: {result.success}")
    # print(f"Version: {result.version}")
    # print(f"Message: {result.message}")
    # print(f"Monitoring Until: {result.monitoring_until}")
    # print(f"Rollback Available: Version {result.rollback_version}")

    print(f"\n{'='*70}")
    print("Deployment simulation complete (not actually deployed)")
    print("Uncomment code to deploy for real")
    print("="*70)

    # Demo rollback trigger checking
    print(f"\n{'='*70}")
    print("ROLLBACK TRIGGER CHECK")
    print("="*70)

    test_stats = {
        'strike_rate': 0.12,  # Down from baseline
        'baseline_strike_rate': 0.20,
        'wins': 3,
        'baseline_wins_7day_avg': 6,
        'manual_rollback_flag': False
    }

    should_rollback, triggers = deployer.check_rollback_triggers(test_stats)

    print(f"\nShould Rollback: {should_rollback}")
    print(f"\nTrigger Status:")
    for trigger in triggers:
        status = "TRIGGERED" if trigger.triggered else "OK"
        print(f"  [{status}] {trigger.name}: {trigger.condition}")
        if trigger.current_value is not None:
            print(f"    Current: {trigger.current_value:.2f}, Threshold: {trigger.threshold:.2f}")
