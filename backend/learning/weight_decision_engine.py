"""
Weight Decision Engine
======================
Analyzes aggregated race findings and decides what weights to change,
by how much, and when to deploy.

Core Logic:
- High confidence (50%+ races): Deploy immediately
- Medium confidence (30-50% races): Deploy after 2 days confirmation
- Low confidence (<30% races): Monitor only, no change

Adjustment Magnitude:
- 5+ races in 7 days: ±8-10pts (aggressive)
- 3-4 races in 7 days: ±5-7pts (moderate)
- 2 races in 7 days: ±3-4pts (conservative)
- 1 race: ±0pts (monitor only)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal


@dataclass
class PatternEvidence:
    """Evidence for a specific pattern across races."""
    pattern_name: str
    count: int  # How many races showed this pattern
    total_races: int
    confidence: float  # count / total_races
    weight_recommendations: Dict[str, Dict]  # weight -> {current, suggested, votes}
    first_seen: str  # ISO date
    last_seen: str  # ISO date
    historical_matches: int  # How many times seen in last 30 days


@dataclass
class WeightChange:
    """Proposed weight change with rationale."""
    weight_name: str
    current_value: float
    suggested_value: float
    change: float
    confidence: float
    pattern_support: List[str]  # Which patterns support this change
    frequency_score: float
    recency_score: float
    historical_score: float
    deployment_urgency: str  # "immediate", "2_day", "monitor"
    rationale: str


@dataclass
class DecisionResult:
    """Result of decision engine analysis."""
    date: str
    total_races: int
    wins: int
    losses: int
    strike_rate: float
    immediate_changes: List[WeightChange]
    pending_changes: List[WeightChange]
    monitor_only: List[WeightChange]
    confidence_threshold_met: bool
    recommendation: str


class WeightDecisionEngine:
    """
    Decides what weight changes to make based on aggregated findings.
    """

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.50  # 50%+ races
    MEDIUM_CONFIDENCE = 0.30  # 30-50% races

    # Adjustment magnitudes
    ADJUSTMENT_RULES = {
        'aggressive': {'min_races': 5, 'days': 7, 'magnitude': (8, 10)},
        'moderate': {'min_races': 3, 'days': 7, 'magnitude': (5, 7)},
        'conservative': {'min_races': 2, 'days': 7, 'magnitude': (3, 4)},
        'monitor': {'min_races': 1, 'days': 7, 'magnitude': (0, 0)},
    }

    def __init__(self, min_races_for_change: int = 2):
        self.min_races_for_change = min_races_for_change

    def calculate_confidence(
        self,
        pattern_count: int,
        total_races: int,
        historical_matches: int,
        days_since_first_seen: int = 1
    ) -> Tuple[float, float, float, float]:
        """
        Calculate confidence score for a pattern.

        Returns:
            (total_confidence, frequency_score, recency_score, historical_score)
        """
        # Frequency: How often pattern appears in recent races
        frequency_score = pattern_count / max(total_races, 1)

        # Recency: Prefer patterns seen very recently
        if pattern_count >= 2:
            recency_score = 1.0  # Pattern confirmed in recent data
        else:
            recency_score = 0.5  # Single occurrence

        # Historical: Pattern matches in last 30 days
        historical_score = min(historical_matches / 30.0, 1.0)

        # Weighted combination
        confidence = (
            frequency_score * 0.5 +
            recency_score * 0.3 +
            historical_score * 0.2
        )

        return confidence, frequency_score, recency_score, historical_score

    def determine_adjustment_magnitude(
        self,
        pattern_count: int,
        days_span: int,
        confidence: float
    ) -> Tuple[str, int, int]:
        """
        Determine adjustment magnitude based on pattern frequency.

        Returns:
            (urgency_level, min_adjustment, max_adjustment)
        """
        races_per_7days = (pattern_count / max(days_span, 1)) * 7

        if races_per_7days >= 5:
            rule = self.ADJUSTMENT_RULES['aggressive']
            return 'aggressive', rule['magnitude'][0], rule['magnitude'][1]
        elif races_per_7days >= 3:
            rule = self.ADJUSTMENT_RULES['moderate']
            return 'moderate', rule['magnitude'][0], rule['magnitude'][1]
        elif races_per_7days >= 2:
            rule = self.ADJUSTMENT_RULES['conservative']
            return 'conservative', rule['magnitude'][0], rule['magnitude'][1]
        else:
            rule = self.ADJUSTMENT_RULES['monitor']
            return 'monitor', rule['magnitude'][0], rule['magnitude'][1]

    def calculate_weight_change(
        self,
        weight_name: str,
        current_value: float,
        suggested_value: float,
        votes: int,
        min_adj: int,
        max_adj: int,
        confidence: float
    ) -> float:
        """
        Calculate actual weight change amount.

        Uses suggested value as target, but constrains by magnitude rules.
        """
        desired_change = suggested_value - current_value

        # Constrain by magnitude limits
        if desired_change > 0:
            # Increase
            change = min(abs(desired_change), max_adj)
        else:
            # Decrease
            change = -min(abs(desired_change), max_adj)

        # Apply confidence scaling (higher confidence = larger changes)
        if confidence < self.MEDIUM_CONFIDENCE:
            change = change * 0.5  # Reduce by 50% for low confidence

        # Round to nearest integer
        return round(change)

    def determine_deployment_urgency(
        self,
        confidence: float,
        pattern_count: int,
        total_races: int
    ) -> str:
        """
        Determine when to deploy changes.

        Returns:
            "immediate", "2_day", or "monitor"
        """
        if confidence >= self.HIGH_CONFIDENCE:
            return "immediate"
        elif confidence >= self.MEDIUM_CONFIDENCE and pattern_count >= 2:
            return "2_day"
        else:
            return "monitor"

    def analyze_aggregated_findings(
        self,
        aggregated_data: Dict
    ) -> DecisionResult:
        """
        Analyze aggregated findings from all races and decide on weight changes.

        Args:
            aggregated_data: Dictionary with structure:
                {
                    "date": "2026-05-20",
                    "total_races": 5,
                    "losses": 5,
                    "wins": 0,
                    "patterns": {
                        "consistent_placer_bias": {"count": 2, "confidence": 0.40},
                        ...
                    },
                    "weight_recommendations": {
                        "consistency": {"current": 12, "suggested": 8, "votes": 2},
                        ...
                    }
                }

        Returns:
            DecisionResult with categorized changes
        """
        date_str = aggregated_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        total_races = aggregated_data.get('total_races', 0)
        wins = aggregated_data.get('wins', 0)
        losses = aggregated_data.get('losses', 0)
        strike_rate = wins / max(total_races, 1)

        patterns = aggregated_data.get('patterns', {})
        weight_recommendations = aggregated_data.get('weight_recommendations', {})

        immediate_changes = []
        pending_changes = []
        monitor_only = []

        # Process each weight recommendation
        for weight_name, rec_data in weight_recommendations.items():
            current = rec_data.get('current', 0)
            suggested = rec_data.get('suggested', current)
            votes = rec_data.get('votes', 0)

            # Find supporting patterns
            supporting_patterns = []
            max_pattern_confidence = 0.0
            pattern_count = 0

            for pattern_name, pattern_data in patterns.items():
                # Check if this pattern votes for this weight
                if pattern_data.get('votes_for', {}).get(weight_name):
                    supporting_patterns.append(pattern_name)
                    max_pattern_confidence = max(
                        max_pattern_confidence,
                        pattern_data.get('confidence', 0.0)
                    )
                    pattern_count = max(pattern_count, pattern_data.get('count', 0))

            # Calculate confidence
            confidence, freq_score, recency_score, hist_score = self.calculate_confidence(
                pattern_count=pattern_count,
                total_races=total_races,
                historical_matches=rec_data.get('historical_matches', 0),
                days_since_first_seen=1
            )

            # Determine adjustment magnitude
            urgency_level, min_adj, max_adj = self.determine_adjustment_magnitude(
                pattern_count=pattern_count,
                days_span=1,  # Currently looking at single day
                confidence=confidence
            )

            # Calculate actual change
            change_amount = self.calculate_weight_change(
                weight_name=weight_name,
                current_value=current,
                suggested_value=suggested,
                votes=votes,
                min_adj=min_adj,
                max_adj=max_adj,
                confidence=confidence
            )

            if change_amount == 0:
                continue  # No change needed

            # Determine deployment urgency
            deployment = self.determine_deployment_urgency(
                confidence=confidence,
                pattern_count=pattern_count,
                total_races=total_races
            )

            # Create rationale
            direction = "increase" if change_amount > 0 else "decrease"
            rationale = (
                f"Pattern evidence from {pattern_count}/{total_races} races "
                f"({confidence*100:.0f}% confidence). "
                f"{direction.capitalize()} by {abs(change_amount)}pts to "
                f"{current + change_amount}. "
                f"Urgency: {urgency_level}."
            )

            weight_change = WeightChange(
                weight_name=weight_name,
                current_value=current,
                suggested_value=current + change_amount,
                change=change_amount,
                confidence=confidence,
                pattern_support=supporting_patterns,
                frequency_score=freq_score,
                recency_score=recency_score,
                historical_score=hist_score,
                deployment_urgency=deployment,
                rationale=rationale
            )

            # Categorize by urgency
            if deployment == "immediate":
                immediate_changes.append(weight_change)
            elif deployment == "2_day":
                pending_changes.append(weight_change)
            else:
                monitor_only.append(weight_change)

        # Determine overall recommendation
        if immediate_changes:
            recommendation = (
                f"DEPLOY NOW: {len(immediate_changes)} high-confidence changes detected. "
                f"Strike rate: {strike_rate*100:.0f}%. "
                f"Pattern evidence strong across {total_races} races."
            )
            confidence_met = True
        elif pending_changes:
            recommendation = (
                f"MONITOR: {len(pending_changes)} medium-confidence changes pending. "
                f"Wait for 2-day confirmation before deployment."
            )
            confidence_met = False
        else:
            recommendation = (
                f"HOLD: Insufficient evidence for changes. "
                f"Continue monitoring. Total races: {total_races}."
            )
            confidence_met = False

        return DecisionResult(
            date=date_str,
            total_races=total_races,
            wins=wins,
            losses=losses,
            strike_rate=strike_rate,
            immediate_changes=immediate_changes,
            pending_changes=pending_changes,
            monitor_only=monitor_only,
            confidence_threshold_met=confidence_met,
            recommendation=recommendation
        )

    def export_decision_to_dict(self, decision: DecisionResult) -> Dict:
        """Export decision result to dictionary for JSON serialization."""
        return {
            'date': decision.date,
            'total_races': decision.total_races,
            'wins': decision.wins,
            'losses': decision.losses,
            'strike_rate': float(decision.strike_rate),
            'confidence_threshold_met': decision.confidence_threshold_met,
            'recommendation': decision.recommendation,
            'immediate_changes': [asdict(c) for c in decision.immediate_changes],
            'pending_changes': [asdict(c) for c in decision.pending_changes],
            'monitor_only': [asdict(c) for c in decision.monitor_only],
            'generated_at': datetime.now().isoformat(),
        }


# Example usage
if __name__ == '__main__':
    # Example aggregated data (from today's 2 losses)
    example_data = {
        "date": "2026-05-20",
        "total_races": 2,
        "losses": 2,
        "wins": 0,
        "patterns": {
            "consistent_placer_bias": {
                "count": 2,
                "confidence": 1.0,  # 2/2 races
                "votes_for": {
                    "consistency": True,
                    "form_velocity_bonus": True
                }
            },
            "class_advantage_missed": {
                "count": 1,
                "confidence": 0.5,
                "votes_for": {
                    "class_drop_bonus": True
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
            },
            "class_drop_bonus": {
                "current": 24,
                "suggested": 30,
                "votes": 1,
                "historical_matches": 8
            }
        }
    }

    engine = WeightDecisionEngine()
    decision = engine.analyze_aggregated_findings(example_data)

    print("\n" + "="*70)
    print("WEIGHT DECISION ENGINE - ANALYSIS RESULT")
    print("="*70)
    print(f"\nDate: {decision.date}")
    print(f"Races: {decision.total_races} (Wins: {decision.wins}, Losses: {decision.losses})")
    print(f"Strike Rate: {decision.strike_rate*100:.0f}%")
    print(f"\nRecommendation: {decision.recommendation}")

    if decision.immediate_changes:
        print(f"\n{'='*70}")
        print(f"IMMEDIATE CHANGES ({len(decision.immediate_changes)})")
        print("="*70)
        for change in decision.immediate_changes:
            print(f"\n{change.weight_name}:")
            print(f"  Current: {change.current_value}")
            print(f"  Suggested: {change.suggested_value}")
            print(f"  Change: {change.change:+.0f}pts")
            print(f"  Confidence: {change.confidence*100:.0f}%")
            print(f"  Patterns: {', '.join(change.pattern_support)}")
            print(f"  Rationale: {change.rationale}")

    if decision.pending_changes:
        print(f"\n{'='*70}")
        print(f"PENDING CHANGES ({len(decision.pending_changes)})")
        print("="*70)
        for change in decision.pending_changes:
            print(f"\n{change.weight_name}: {change.current_value} → {change.suggested_value}")

    # Export to JSON
    decision_dict = engine.export_decision_to_dict(decision)
    print(f"\n{'='*70}")
    print("JSON Export:")
    print("="*70)
    print(json.dumps(decision_dict, indent=2))
