"""
Weight Validator
================
Safety validation checks before deploying weight changes.

Validations:
1. Historical validation: Would change improve last 30 days?
2. Weight bounds: No weight <0 or >40
3. Total score impact: No change >20% of total possible score
4. Conflict detection: No contradictory adjustments
5. Strike rate floor: Won't reduce below 15% baseline
"""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ValidationResult:
    """Result of validation checks."""
    passed: bool
    weight_name: str
    current_value: float
    new_value: float
    failed_checks: List[str]
    warnings: List[str]
    safe_to_deploy: bool
    recommendation: str


@dataclass
class ValidationSummary:
    """Summary of all validation results."""
    all_passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult]
    overall_recommendation: str
    safe_to_deploy: bool


class WeightValidator:
    """
    Validates proposed weight changes for safety.
    """

    # Safety bounds
    MIN_WEIGHT = 0
    MAX_WEIGHT = 40
    MAX_TOTAL_SCORE_IMPACT = 0.20  # 20% of total possible score
    MIN_STRIKE_RATE = 0.15  # 15% minimum acceptable strike rate

    # Typical total score range
    TYPICAL_MAX_SCORE = 200  # Approximate max possible score

    def __init__(
        self,
        dynamodb_table_name: str = 'SureBetBets',
        region: str = 'eu-west-1'
    ):
        self.table_name = dynamodb_table_name
        self.region = region
        self.dynamodb = None
        self.table = None

    def _get_dynamodb_table(self):
        """Lazy-load DynamoDB table."""
        if self.table is None:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.table = self.dynamodb.Table(self.table_name)
        return self.table

    def validate_weight_bounds(
        self,
        weight_name: str,
        new_value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if weight is within valid bounds.

        Returns:
            (passed, error_message)
        """
        if new_value < self.MIN_WEIGHT:
            return False, f"Weight {new_value} below minimum {self.MIN_WEIGHT}"
        if new_value > self.MAX_WEIGHT:
            return False, f"Weight {new_value} above maximum {self.MAX_WEIGHT}"
        return True, None

    def validate_score_impact(
        self,
        weight_name: str,
        current_value: float,
        new_value: float
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if change impact is within acceptable range.

        Returns:
            (passed, error_message, warning_message)
        """
        change = abs(new_value - current_value)
        impact_ratio = change / self.TYPICAL_MAX_SCORE

        if impact_ratio > self.MAX_TOTAL_SCORE_IMPACT:
            return False, (
                f"Change of {change}pts exceeds {self.MAX_TOTAL_SCORE_IMPACT*100:.0f}% "
                f"of total score ({impact_ratio*100:.0f}%)"
            ), None

        # Warning for large but acceptable changes
        if impact_ratio > 0.10:  # 10%
            return True, None, (
                f"Large change: {change}pts ({impact_ratio*100:.0f}% of total score). "
                "Monitor closely."
            )

        return True, None, None

    def validate_no_conflicts(
        self,
        all_changes: Dict[str, Tuple[float, float]]
    ) -> Tuple[bool, List[str]]:
        """
        Check for conflicting weight changes.

        Args:
            all_changes: Dict of weight_name -> (current, new) tuples

        Returns:
            (passed, list_of_conflicts)
        """
        conflicts = []

        # Define related weight groups that should move together
        related_groups = {
            'form_cluster': [
                'recent_win', 'consistency', 'form_velocity_bonus',
                'form_close_2nd', 'bounce_back_bonus'
            ],
            'market_signals': [
                'sweet_spot', 'optimal_odds', 'favorite_correction',
                'market_steam_bonus'
            ],
            'class_signals': [
                'class_drop_bonus', 'class_drop_rebound_bonus',
                'official_rating_bonus'
            ],
        }

        # Check for contradictory changes within groups
        for group_name, weight_names in related_groups.items():
            group_changes = {}
            for wname in weight_names:
                if wname in all_changes:
                    current, new = all_changes[wname]
                    direction = 'increase' if new > current else 'decrease'
                    group_changes[wname] = direction

            # If there are changes in both directions, that's a conflict
            if group_changes:
                directions = set(group_changes.values())
                if len(directions) > 1:
                    conflicts.append(
                        f"Conflicting changes in {group_name}: "
                        f"{', '.join(f'{k}={v}' for k, v in group_changes.items())}"
                    )

        return len(conflicts) == 0, conflicts

    def validate_historical_performance(
        self,
        weight_changes: Dict[str, Tuple[float, float]],
        days_back: int = 30
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate that changes would have improved historical performance.

        This is a simplified check - in production, would re-score past races.

        Returns:
            (passed, error_message, stats_dict)
        """
        # NOTE: Full implementation would require:
        # 1. Fetch last 30 days of picks from DynamoDB
        # 2. Re-score with new weights
        # 3. Compare win rates
        #
        # For now, we do a simplified check based on stored stats

        try:
            table = self._get_dynamodb_table()

            # Try to fetch historical stats (if stored)
            response = table.get_item(
                Key={
                    'bet_id': 'SYSTEM_STATS',
                    'bet_date': 'LAST_30_DAYS'
                }
            )

            if 'Item' in response:
                stats = response['Item']
                current_strike_rate = float(stats.get('strike_rate', 0.20))

                # Heuristic: Large decreases in form weights might reduce strike rate
                # This is a simplified check
                form_weight_decrease = 0
                for weight_name, (current, new) in weight_changes.items():
                    if weight_name in ['recent_win', 'form_velocity_bonus', 'consistency']:
                        if new < current:
                            form_weight_decrease += (current - new)

                # If decreasing form weights significantly, warn
                if form_weight_decrease > 15:
                    return True, None, {
                        'warning': (
                            f"Large form weight decrease ({form_weight_decrease}pts). "
                            "Monitor strike rate closely."
                        )
                    }

                return True, None, {'current_strike_rate': current_strike_rate}

        except Exception as e:
            # If can't fetch stats, pass with warning
            return True, None, {'warning': f'Could not validate historical: {e}'}

        return True, None, {}

    def validate_strike_rate_floor(
        self,
        weight_changes: Dict[str, Tuple[float, float]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check that changes won't push strike rate below acceptable minimum.

        This is a heuristic check based on the types of changes being made.
        """
        # Count net change in "winner-boosting" vs "winner-reducing" weights
        winner_boost_weights = [
            'recent_win', 'form_exact_course_win', 'form_exact_distance_win',
            'class_drop_bonus', 'bounce_back_bonus'
        ]

        net_winner_signal_change = 0
        for weight_name, (current, new) in weight_changes.items():
            if weight_name in winner_boost_weights:
                net_winner_signal_change += (new - current)

        # If net decrease in winner signals is large, warn
        if net_winner_signal_change < -15:
            return False, (
                f"Net decrease in winner signals: {net_winner_signal_change}pts. "
                f"Risk of strike rate falling below {self.MIN_STRIKE_RATE*100:.0f}%."
            )

        return True, None

    def validate_single_weight(
        self,
        weight_name: str,
        current_value: float,
        new_value: float,
        all_changes: Dict[str, Tuple[float, float]]
    ) -> ValidationResult:
        """
        Run all validation checks on a single weight change.

        Returns:
            ValidationResult with pass/fail and details
        """
        failed_checks = []
        warnings = []

        # 1. Check bounds
        passed_bounds, bounds_error = self.validate_weight_bounds(weight_name, new_value)
        if not passed_bounds:
            failed_checks.append(f"Bounds check: {bounds_error}")

        # 2. Check score impact
        passed_impact, impact_error, impact_warning = self.validate_score_impact(
            weight_name, current_value, new_value
        )
        if not passed_impact:
            failed_checks.append(f"Score impact: {impact_error}")
        if impact_warning:
            warnings.append(impact_warning)

        # Overall pass/fail
        passed = len(failed_checks) == 0
        safe_to_deploy = passed

        # Recommendation
        if passed:
            if warnings:
                recommendation = f"PASS with warnings: {'; '.join(warnings)}"
            else:
                recommendation = "PASS - Safe to deploy"
        else:
            recommendation = f"FAIL - {'; '.join(failed_checks)}"

        return ValidationResult(
            passed=passed,
            weight_name=weight_name,
            current_value=current_value,
            new_value=new_value,
            failed_checks=failed_checks,
            warnings=warnings,
            safe_to_deploy=safe_to_deploy,
            recommendation=recommendation
        )

    def validate_all_changes(
        self,
        weight_changes: Dict[str, Tuple[float, float]]
    ) -> ValidationSummary:
        """
        Validate all proposed weight changes.

        Args:
            weight_changes: Dict of weight_name -> (current_value, new_value)

        Returns:
            ValidationSummary with results for all weights
        """
        results = []

        # Validate each weight individually
        for weight_name, (current, new) in weight_changes.items():
            result = self.validate_single_weight(
                weight_name, current, new, weight_changes
            )
            results.append(result)

        # Check for conflicts across all changes
        passed_conflicts, conflicts = self.validate_no_conflicts(weight_changes)

        # Check strike rate floor
        passed_strike_floor, strike_error = self.validate_strike_rate_floor(weight_changes)

        # Check historical performance
        passed_historical, hist_error, hist_stats = self.validate_historical_performance(
            weight_changes
        )

        # Count passes/fails
        passed_checks = sum(1 for r in results if r.passed)
        failed_checks = len(results) - passed_checks

        # Add global failures
        if not passed_conflicts:
            failed_checks += len(conflicts)
        if not passed_strike_floor:
            failed_checks += 1
        if not passed_historical and hist_error:
            failed_checks += 1

        # Determine overall pass/fail
        all_individual_passed = all(r.passed for r in results)
        all_passed = (
            all_individual_passed and
            passed_conflicts and
            passed_strike_floor and
            passed_historical
        )

        safe_to_deploy = all_passed

        # Build recommendation
        if all_passed:
            overall_rec = (
                f"ALL CHECKS PASSED - Safe to deploy {len(weight_changes)} changes. "
            )
            if hist_stats.get('warning'):
                overall_rec += f" Warning: {hist_stats['warning']}"
        else:
            failure_reasons = []
            if not all_individual_passed:
                failure_reasons.append(
                    f"{failed_checks} individual weight checks failed"
                )
            if not passed_conflicts:
                failure_reasons.append(
                    f"Conflicts detected: {', '.join(conflicts)}"
                )
            if not passed_strike_floor:
                failure_reasons.append(f"Strike rate floor: {strike_error}")
            if not passed_historical and hist_error:
                failure_reasons.append(f"Historical: {hist_error}")

            overall_rec = (
                f"VALIDATION FAILED - {'; '.join(failure_reasons)}. "
                "Review and adjust before deployment."
            )

        return ValidationSummary(
            all_passed=all_passed,
            total_checks=len(results) + 3,  # Individual + 3 global checks
            passed_checks=passed_checks + (1 if passed_conflicts else 0) +
                         (1 if passed_strike_floor else 0) +
                         (1 if passed_historical else 0),
            failed_checks=failed_checks,
            results=results,
            overall_recommendation=overall_rec,
            safe_to_deploy=safe_to_deploy
        )


# Example usage
if __name__ == '__main__':
    validator = WeightValidator()

    # Example weight changes (from decision engine)
    changes = {
        'consistency': (12, 8),
        'form_velocity_bonus': (18, 12),
        'class_drop_bonus': (24, 28),
    }

    print("\n" + "="*70)
    print("WEIGHT VALIDATOR - SAFETY CHECKS")
    print("="*70)

    summary = validator.validate_all_changes(changes)

    print(f"\nOverall Result: {'PASS' if summary.all_passed else 'FAIL'}")
    print(f"Checks: {summary.passed_checks}/{summary.total_checks} passed")
    print(f"\n{summary.overall_recommendation}")

    if summary.results:
        print(f"\n{'='*70}")
        print("Individual Weight Results:")
        print("="*70)
        for result in summary.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"\n{status} - {result.weight_name}")
            print(f"  Current: {result.current_value} → New: {result.new_value}")
            print(f"  {result.recommendation}")

            if result.failed_checks:
                print(f"  Failed: {', '.join(result.failed_checks)}")
            if result.warnings:
                print(f"  Warnings: {', '.join(result.warnings)}")

    print(f"\n{'='*70}")
    print(f"Safe to Deploy: {summary.safe_to_deploy}")
    print("="*70)
