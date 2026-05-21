"""
Worker Agent for Single Race Analysis

Each worker analyzes one race:
1. Fetches race result from Sporting Life
2. Identifies winner + top 3 finishers
3. Compares our pick vs winner (form, odds, class, jockey)
4. Calculates score gaps
5. Identifies missing signals
6. Categorizes loss type
7. Generates weight recommendations

Designed to run in parallel with other workers (1-2 minute timeout).
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RaceAnalyzer:
    """Single race analysis worker."""

    def __init__(self):
        self.timeout = 60  # 60 second max per race
        self.retry_count = 3

    def fetch_race_result(
        self,
        course: str,
        race_time: str,
        date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch race result from Sporting Life or cached results.

        Args:
            course: Racecourse name
            race_time: Race time (HH:MM format)
            date: Race date (YYYY-MM-DD)

        Returns:
            Race result dict with winner and placed horses, or None
        """
        try:
            # Import here to avoid circular dependencies
            from backend.core.settlement.sl_results_fetcher import fetch_result_for_race

            result = fetch_result_for_race(course, race_time, date)

            if result:
                logger.debug(f"Fetched result for {course} {race_time}")
                return result
            else:
                logger.warning(f"No result found for {course} {race_time} on {date}")
                return None

        except Exception as e:
            logger.error(f"Error fetching race result: {e}")
            return None

    def extract_winner_details(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract winner details from race result.

        Args:
            result: Race result from Sporting Life

        Returns:
            Winner details dict
        """
        winner = result.get('winner', {})

        return {
            'horse_name': winner.get('name', ''),
            'odds': float(winner.get('odds', 0)),
            'jockey': winner.get('jockey', ''),
            'trainer': winner.get('trainer', ''),
            'draw': winner.get('draw', 0),
            'weight': winner.get('weight', ''),
            'age': winner.get('age', 0),
            'form': winner.get('form', ''),
            'official_rating': winner.get('official_rating', 0),
        }

    def extract_placed_horses(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract 2nd and 3rd place horses.

        Args:
            result: Race result

        Returns:
            List of placed horse dicts
        """
        placed = []

        for position in ['second', 'third']:
            horse = result.get(position, {})
            if horse:
                placed.append({
                    'position': position,
                    'horse_name': horse.get('name', ''),
                    'odds': float(horse.get('odds', 0)),
                    'jockey': horse.get('jockey', ''),
                })

        return placed

    def compare_pick_vs_winner(
        self,
        our_pick: Dict[str, Any],
        winner: Dict[str, Any],
        race_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare our pick against actual winner to identify gaps.

        Args:
            our_pick: Our selection details
            winner: Actual winner details
            race_details: Race context (course, time, etc)

        Returns:
            Comparison dict with gaps and insights
        """
        comparison = {
            'our_pick_name': our_pick.get('horse_name', ''),
            'winner_name': winner.get('horse_name', ''),
            'odds_gap': winner.get('odds', 0) - our_pick.get('odds', 0),
            'score_gap': 0,  # We don't have winner's score (need to reconstruct)
            'jockey_comparison': {
                'our_jockey': our_pick.get('signals', {}).get('jockey', 'unknown'),
                'winning_jockey': winner.get('jockey', 'unknown'),
            },
            'trainer_comparison': {
                'our_trainer': our_pick.get('signals', {}).get('trainer', 'unknown'),
                'winning_trainer': winner.get('trainer', 'unknown'),
            },
            'form_comparison': {
                'our_form': our_pick.get('signals', {}).get('form', ''),
                'winner_form': winner.get('form', ''),
            },
        }

        return comparison

    def identify_missing_signals(
        self,
        comparison: Dict[str, Any],
        winner: Dict[str, Any],
        our_pick: Dict[str, Any]
    ) -> List[str]:
        """
        Identify signals we missed that the winner had.

        Args:
            comparison: Pick vs winner comparison
            winner: Winner details
            our_pick: Our pick details

        Returns:
            List of missing signal names
        """
        missing = []

        # Check form velocity
        winner_form = winner.get('form', '')
        if self._has_improving_form(winner_form):
            missing.append('form_velocity')

        # Check jockey quality
        winner_jockey = winner.get('jockey', '')
        if self._is_top_jockey(winner_jockey):
            our_jockey = our_pick.get('signals', {}).get('jockey', '')
            if not self._is_top_jockey(our_jockey):
                missing.append('jockey_quality')

        # Check course form
        # (Would need course history data - placeholder)
        if winner.get('course_wins', 0) > 0:
            missing.append('course_form')

        # Check class drop signal
        # (Would need class data - placeholder)

        # Check odds positioning
        winner_odds = winner.get('odds', 0)
        if 3.0 <= winner_odds <= 8.0:
            # Winner in sweet spot range
            our_odds = our_pick.get('odds', 0)
            if our_odds < 3.0 or our_odds > 10.0:
                missing.append('odds_sweet_spot')

        return missing

    def _has_improving_form(self, form: str) -> bool:
        """Check if form string shows improvement pattern."""
        if not form or len(form) < 3:
            return False

        # Extract position numbers
        positions = []
        for char in form:
            if char.isdigit():
                positions.append(int(char))

        if len(positions) < 2:
            return False

        # Check for improvement (positions getting lower)
        recent = positions[:3]
        return recent == sorted(recent)

    def _is_top_jockey(self, jockey_name: str) -> bool:
        """Check if jockey is in top tier."""
        if not jockey_name:
            return False

        top_jockeys = [
            'ryan moore', 'william buick', 'frankie dettori', 'oisin murphy',
            'tom marquand', 'hollie doyle', 'jim crowley', 'james doyle',
            'silvestre de sousa', 'daniel tudhope', 'paul hanagan',
            'richard kingscote', 'david probert', 'kieran shoemark'
        ]

        return jockey_name.lower() in top_jockeys

    def categorize_loss(
        self,
        comparison: Dict[str, Any],
        missing_signals: List[str],
        winner: Dict[str, Any],
        our_pick: Dict[str, Any]
    ) -> Tuple[str, str, str]:
        """
        Categorize loss type to guide weight adjustments.

        Categories:
        - improver_missed: Winner had improving form we didn't weight enough
        - class_drop: Winner dropped in class
        - course_specialist: Winner had strong course history
        - jockey_upgrade: Winner had top jockey we undervalued
        - long_shot: Winner was 10/1+, unpredictable
        - market_wrong: We followed market, market was wrong
        - close_call: Marginal difference, no clear pattern

        Args:
            comparison: Pick vs winner comparison
            missing_signals: List of signals we missed
            winner: Winner details
            our_pick: Our pick details

        Returns:
            Tuple of (category, severity, reason)
        """
        winner_odds = winner.get('odds', 0)
        our_odds = our_pick.get('odds', 0)

        # Long shot wins are expected variance
        if winner_odds > 10.0:
            return 'long_shot', 'low', f'Winner at {winner_odds:.1f} odds - expected variance'

        # Form velocity pattern
        if 'form_velocity' in missing_signals:
            return 'improver_missed', 'high', 'Winner had improving form pattern'

        # Jockey quality gap
        if 'jockey_quality' in missing_signals:
            return 'jockey_upgrade', 'high', 'Winner had top jockey we undervalued'

        # Course form specialist
        if 'course_form' in missing_signals:
            return 'course_specialist', 'medium', 'Winner had strong course history'

        # Market positioning error
        if our_odds < 4.0 and winner_odds > 6.0:
            return 'market_wrong', 'medium', 'We backed favorite, outsider won'

        # Close call
        odds_gap = abs(winner_odds - our_odds)
        if odds_gap < 2.0:
            return 'close_call', 'low', 'Marginal difference between selections'

        # Default: model gap
        return 'model_gap', 'medium', 'Winner had features we underweight'

    def recommend_weight_changes(
        self,
        loss_category: str,
        missing_signals: List[str],
        severity: str
    ) -> List[Dict[str, Any]]:
        """
        Generate weight adjustment recommendations based on loss analysis.

        Args:
            loss_category: Loss category type
            missing_signals: Signals we missed
            severity: Impact severity (low/medium/high)

        Returns:
            List of weight change recommendations
        """
        recommendations = []

        # Severity multipliers
        severity_multiplier = {
            'low': 0.5,
            'medium': 1.0,
            'high': 1.5
        }.get(severity, 1.0)

        # Category-specific recommendations
        if loss_category == 'improver_missed':
            recommendations.append({
                'weight': 'form_velocity_bonus',
                'change': +5 * severity_multiplier,
                'reason': 'Improving form pattern not weighted enough',
                'confidence': 0.8
            })

        elif loss_category == 'jockey_upgrade':
            recommendations.append({
                'weight': 'jockey_quality',
                'change': +4 * severity_multiplier,
                'reason': 'Top jockey signal undervalued',
                'confidence': 0.7
            })
            recommendations.append({
                'weight': 'jockey_course_bonus',
                'change': +3 * severity_multiplier,
                'reason': 'Jockey-course combo underweighted',
                'confidence': 0.6
            })

        elif loss_category == 'course_specialist':
            recommendations.append({
                'weight': 'course_bonus',
                'change': +4 * severity_multiplier,
                'reason': 'Course history signal too weak',
                'confidence': 0.7
            })

        elif loss_category == 'market_wrong':
            recommendations.append({
                'weight': 'favorite_correction',
                'change': -2 * severity_multiplier,
                'reason': 'Over-trusting favorite status',
                'confidence': 0.6
            })

        # Signal-specific recommendations
        if 'form_velocity' in missing_signals:
            recommendations.append({
                'weight': 'form_velocity_bonus',
                'change': +3,
                'reason': 'Form trend signal missed',
                'confidence': 0.6
            })

        if 'odds_sweet_spot' in missing_signals:
            recommendations.append({
                'weight': 'sweet_spot',
                'change': +2,
                'reason': 'Odds positioning signal weak',
                'confidence': 0.5
            })

        return recommendations

    def analyze_race(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis function for a single race.

        Args:
            job: Race job specification

        Returns:
            Analysis result dict
        """
        start_time = time.time()
        race_id = job['race_id']

        try:
            # Step 1: Fetch race result
            result = self.fetch_race_result(
                job['course'],
                job['race_time'],
                job['date']
            )

            if not result:
                return {
                    'status': 'error',
                    'race_id': race_id,
                    'error': 'Race result not found',
                    'processing_time': time.time() - start_time
                }

            # Step 2: Extract winner details
            winner = self.extract_winner_details(result)
            placed = self.extract_placed_horses(result)

            # Step 3: Compare our pick vs winner
            comparison = self.compare_pick_vs_winner(
                job['our_pick'],
                winner,
                job
            )

            # Step 4: Identify missing signals
            missing_signals = self.identify_missing_signals(
                comparison,
                winner,
                job['our_pick']
            )

            # Step 5: Categorize loss
            loss_category, severity, reason = self.categorize_loss(
                comparison,
                missing_signals,
                winner,
                job['our_pick']
            )

            # Step 6: Generate recommendations
            recommendations = self.recommend_weight_changes(
                loss_category,
                missing_signals,
                severity
            )

            processing_time = time.time() - start_time

            return {
                'status': 'success',
                'race_id': race_id,
                'date': job['date'],
                'course': job['course'],
                'race_time': job['race_time'],
                'our_pick': job['our_pick']['horse_name'],
                'winner': winner['horse_name'],
                'loss_type': loss_category,
                'severity': severity,
                'reason': reason,
                'missing_signals': missing_signals,
                'comparison': comparison,
                'recommendations': recommendations,
                'placed_horses': placed,
                'processing_time': round(processing_time, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing race {race_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'race_id': race_id,
                'error': str(e),
                'processing_time': time.time() - start_time
            }


# Module-level function for easy parallel invocation
def analyze_single_race(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze a single race (worker entry point).

    Args:
        job: Race job specification

    Returns:
        Analysis result
    """
    analyzer = RaceAnalyzer()
    return analyzer.analyze_race(job)
