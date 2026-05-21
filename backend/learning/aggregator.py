"""
Results Aggregator for Multi-Race Learning

Processes all worker outputs to:
1. Identify common patterns (3+ races with same issue)
2. Calculate confidence scores (pattern frequency / total races)
3. Rank weight changes by priority
4. Generate deployment plan

Output: Actionable weight adjustment recommendations with confidence scores.
"""

import logging
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timezone
import statistics

logger = logging.getLogger(__name__)


class ResultsAggregator:
    """Aggregates findings from multiple race analyses."""

    def __init__(self, min_confidence: float = 0.3):
        self.min_confidence = min_confidence  # 30%+ of races must show pattern

    def extract_patterns(
        self,
        analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract common patterns across all race analyses.

        Args:
            analyses: List of race analysis results

        Returns:
            Pattern summary dict
        """
        if not analyses:
            return {}

        # Loss type distribution
        loss_types = [a.get('loss_type', 'unknown') for a in analyses]
        loss_type_counts = Counter(loss_types)

        # Severity distribution
        severities = [a.get('severity', 'low') for a in analyses]
        severity_counts = Counter(severities)

        # Missing signals aggregation
        all_missing_signals = []
        for analysis in analyses:
            all_missing_signals.extend(analysis.get('missing_signals', []))
        signal_counts = Counter(all_missing_signals)

        # Calculate frequencies
        total_races = len(analyses)

        return {
            'loss_types': dict(loss_type_counts),
            'loss_type_frequencies': {
                lt: count / total_races
                for lt, count in loss_type_counts.items()
            },
            'dominant_loss_type': loss_type_counts.most_common(1)[0][0] if loss_type_counts else None,
            'severity_distribution': dict(severity_counts),
            'missing_signals': dict(signal_counts),
            'signal_frequencies': {
                signal: count / total_races
                for signal, count in signal_counts.items()
            },
            'total_races': total_races,
        }

    def aggregate_recommendations(
        self,
        analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate weight recommendations from all analyses.

        Args:
            analyses: List of race analysis results

        Returns:
            Consolidated recommendations sorted by priority
        """
        # Collect all recommendations
        weight_changes = defaultdict(list)

        for analysis in analyses:
            recommendations = analysis.get('recommendations', [])
            for rec in recommendations:
                weight_name = rec.get('weight')
                if weight_name:
                    weight_changes[weight_name].append({
                        'change': rec.get('change', 0),
                        'reason': rec.get('reason', ''),
                        'confidence': rec.get('confidence', 0.5),
                        'race_id': analysis.get('race_id', ''),
                    })

        # Aggregate by weight
        consolidated = []

        for weight_name, changes in weight_changes.items():
            # Calculate aggregate change (median to reduce outlier impact)
            change_values = [c['change'] for c in changes]
            median_change = statistics.median(change_values)
            mean_change = statistics.mean(change_values)

            # Calculate confidence (occurrence frequency * avg confidence)
            occurrence_frequency = len(changes) / len(analyses)
            avg_confidence = statistics.mean([c['confidence'] for c in changes])
            combined_confidence = occurrence_frequency * avg_confidence

            # Collect unique reasons
            reasons = list(set([c['reason'] for c in changes]))

            consolidated.append({
                'weight': weight_name,
                'recommended_change': round(median_change, 1),
                'mean_change': round(mean_change, 1),
                'occurrence_count': len(changes),
                'occurrence_frequency': round(occurrence_frequency, 3),
                'confidence': round(combined_confidence, 3),
                'reasons': reasons[:3],  # Top 3 reasons
                'supporting_races': [c['race_id'] for c in changes],
            })

        # Sort by confidence (high confidence = strong signal)
        consolidated.sort(key=lambda x: x['confidence'], reverse=True)

        return consolidated

    def prioritize_changes(
        self,
        recommendations: List[Dict[str, Any]],
        patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize weight changes based on confidence and impact.

        Args:
            recommendations: Aggregated recommendations
            patterns: Pattern analysis

        Returns:
            Prioritized recommendations with deployment urgency
        """
        prioritized = []

        for rec in recommendations:
            # Skip low-confidence recommendations
            if rec['confidence'] < self.min_confidence:
                continue

            # Calculate priority score
            confidence = rec['confidence']
            occurrence = rec['occurrence_frequency']
            change_magnitude = abs(rec['recommended_change'])

            # Priority = confidence * occurrence * magnitude_factor
            magnitude_factor = min(change_magnitude / 5.0, 2.0)  # Cap at 2x
            priority_score = confidence * occurrence * magnitude_factor

            # Determine urgency
            if priority_score > 0.8 and confidence > 0.6:
                urgency = 'high'
            elif priority_score > 0.4 and confidence > 0.4:
                urgency = 'medium'
            else:
                urgency = 'low'

            prioritized.append({
                **rec,
                'priority_score': round(priority_score, 3),
                'urgency': urgency,
            })

        # Sort by priority score
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)

        return prioritized

    def generate_deployment_plan(
        self,
        prioritized_changes: List[Dict[str, Any]],
        patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate actionable deployment plan.

        Args:
            prioritized_changes: Prioritized weight recommendations
            patterns: Pattern analysis

        Returns:
            Deployment plan dict
        """
        # Split by urgency
        high_priority = [c for c in prioritized_changes if c['urgency'] == 'high']
        medium_priority = [c for c in prioritized_changes if c['urgency'] == 'medium']
        low_priority = [c for c in prioritized_changes if c['urgency'] == 'low']

        # Generate deployment recommendation
        if high_priority:
            deploy_recommendation = 'DEPLOY_IMMEDIATELY'
            deploy_reason = f"{len(high_priority)} high-priority changes identified"
        elif medium_priority:
            deploy_recommendation = 'DEPLOY_TONIGHT'
            deploy_reason = f"{len(medium_priority)} medium-priority changes identified"
        elif low_priority:
            deploy_recommendation = 'MONITOR'
            deploy_reason = "Only low-priority changes, continue monitoring"
        else:
            deploy_recommendation = 'NO_ACTION'
            deploy_reason = "No confident patterns found"

        # Generate change summary
        total_changes = len(prioritized_changes)
        total_increase = sum(c['recommended_change'] for c in prioritized_changes if c['recommended_change'] > 0)
        total_decrease = sum(c['recommended_change'] for c in prioritized_changes if c['recommended_change'] < 0)

        return {
            'recommendation': deploy_recommendation,
            'reason': deploy_reason,
            'changes_summary': {
                'total_changes': total_changes,
                'high_priority': len(high_priority),
                'medium_priority': len(medium_priority),
                'low_priority': len(low_priority),
                'total_increase': round(total_increase, 1),
                'total_decrease': round(total_decrease, 1),
            },
            'high_priority_changes': high_priority,
            'medium_priority_changes': medium_priority,
            'low_priority_changes': low_priority,
            'dominant_issue': patterns.get('dominant_loss_type', 'unknown'),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def calculate_impact_estimate(
        self,
        deployment_plan: Dict[str, Any],
        patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estimate impact of proposed changes.

        Args:
            deployment_plan: Generated deployment plan
            patterns: Pattern analysis

        Returns:
            Impact estimate dict
        """
        total_races = patterns.get('total_races', 0)
        high_priority_count = len(deployment_plan.get('high_priority_changes', []))

        # Conservative impact estimates
        if high_priority_count >= 3:
            estimated_win_rate_improvement = 0.05  # +5%
            estimated_roi_improvement = 0.08  # +8%
        elif high_priority_count >= 1:
            estimated_win_rate_improvement = 0.03  # +3%
            estimated_roi_improvement = 0.05  # +5%
        else:
            estimated_win_rate_improvement = 0.01  # +1%
            estimated_roi_improvement = 0.02  # +2%

        return {
            'estimated_win_rate_improvement': round(estimated_win_rate_improvement, 3),
            'estimated_roi_improvement': round(estimated_roi_improvement, 3),
            'confidence': 'medium' if high_priority_count >= 2 else 'low',
            'races_analyzed': total_races,
            'notes': [
                f"Based on {total_races} race analysis",
                f"{high_priority_count} high-confidence patterns",
                "Conservative estimates - actual impact may vary"
            ]
        }


def aggregate_findings(
    analyses: List[Dict[str, Any]],
    min_confidence: float = 0.3
) -> Dict[str, Any]:
    """
    Main aggregation function (entry point).

    Args:
        analyses: List of race analysis results
        min_confidence: Minimum confidence threshold for patterns

    Returns:
        Complete aggregation report
    """
    if not analyses:
        return {
            'status': 'no_data',
            'message': 'No analyses to aggregate',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    aggregator = ResultsAggregator(min_confidence=min_confidence)

    logger.info(f"Aggregating findings from {len(analyses)} race analyses")

    # Step 1: Extract patterns
    patterns = aggregator.extract_patterns(analyses)
    logger.info(f"Identified patterns: {patterns.get('dominant_loss_type')}")

    # Step 2: Aggregate recommendations
    recommendations = aggregator.aggregate_recommendations(analyses)
    logger.info(f"Aggregated {len(recommendations)} weight recommendations")

    # Step 3: Prioritize changes
    prioritized = aggregator.prioritize_changes(recommendations, patterns)
    logger.info(f"Prioritized {len(prioritized)} changes above confidence threshold")

    # Step 4: Generate deployment plan
    deployment_plan = aggregator.generate_deployment_plan(prioritized, patterns)
    logger.info(f"Deployment recommendation: {deployment_plan['recommendation']}")

    # Step 5: Estimate impact
    impact_estimate = aggregator.calculate_impact_estimate(deployment_plan, patterns)

    return {
        'status': 'success',
        'patterns': patterns,
        'recommendations': recommendations[:20],  # Top 20 for readability
        'prioritized_changes': prioritized,
        'deployment_plan': deployment_plan,
        'impact_estimate': impact_estimate,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
