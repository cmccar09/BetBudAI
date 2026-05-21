"""
Master Orchestrator for Daily Race Learning System

Fan-out architecture that processes 5-15 races per day in parallel.
Each race is analyzed by a dedicated worker agent that:
1. Fetches race results
2. Compares our pick vs actual winner
3. Identifies missing signals
4. Recommends weight adjustments

The orchestrator then aggregates all findings and makes deployment decisions.
"""

import json
import logging
import time
import statistics
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

logger = logging.getLogger(__name__)


class LearningOrchestrator:
    """Master orchestrator for daily race learning."""

    def __init__(
        self,
        dynamodb_table: str = 'SureBetBets',
        region: str = 'eu-west-1',
        max_workers: int = 10,
        worker_timeout: int = 60
    ):
        self.dynamodb_table = dynamodb_table
        self.region = region
        self.max_workers = max_workers
        self.worker_timeout = worker_timeout

        if boto3:
            self.dynamodb = boto3.resource('dynamodb', region_name=region)
            self.table = self.dynamodb.Table(dynamodb_table)
        else:
            self.dynamodb = None
            self.table = None
            logger.warning("boto3 not available - running in offline mode")

    def fetch_settled_picks(self, target_date: str) -> List[Dict[str, Any]]:
        """
        Fetch all settled picks from DynamoDB for the target date.

        Args:
            target_date: Date in YYYY-MM-DD format

        Returns:
            List of settled pick records with outcomes
        """
        if not self.table:
            logger.warning("DynamoDB not available - returning mock data")
            return []

        try:
            logger.info(f"Fetching settled picks for {target_date}")

            # Query pattern: bet_id starts with date (e.g., "2026-05-20")
            response = self.table.scan(
                FilterExpression='begins_with(bet_id, :date) AND attribute_exists(outcome)',
                ExpressionAttributeValues={':date': target_date}
            )

            items = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression='begins_with(bet_id, :date) AND attribute_exists(outcome)',
                    ExpressionAttributeValues={':date': target_date},
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))

            logger.info(f"Found {len(items)} settled picks for {target_date}")
            return items

        except Exception as e:
            logger.error(f"Error fetching settled picks: {e}", exc_info=True)
            return []

    def filter_losses(self, picks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter picks to only include losses (for learning).

        Args:
            picks: All settled picks

        Returns:
            Only picks where outcome was LOSS or PLACE (not WIN)
        """
        losses = []
        for pick in picks:
            outcome = pick.get('outcome', '').upper()
            if outcome in ['LOSS', 'PLACE']:
                losses.append(pick)

        logger.info(f"Filtered to {len(losses)} losses from {len(picks)} total picks")
        return losses

    def prepare_race_jobs(self, losses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare race analysis jobs from loss records.

        Each job contains:
        - race_id: Unique identifier
        - date: Race date
        - course: Racecourse name
        - race_time: Scheduled time
        - our_pick: Our selection details
        - bet_id: Reference to DynamoDB record

        Args:
            losses: Filtered loss records

        Returns:
            List of race job specifications
        """
        jobs = []
        seen_races = set()

        for loss in losses:
            # Extract race identifiers
            bet_id = loss.get('bet_id', '')
            bet_date = loss.get('bet_date', '')
            course = loss.get('course', '')
            race_time = loss.get('race_time', '')

            # Create unique race ID
            race_id = f"{bet_date}_{course}_{race_time}"

            # Skip duplicates (multiple picks on same race)
            if race_id in seen_races:
                continue

            seen_races.add(race_id)

            job = {
                'race_id': race_id,
                'date': bet_date,
                'course': course,
                'race_time': race_time,
                'our_pick': {
                    'horse_name': loss.get('horse_name', ''),
                    'odds': float(loss.get('odds', 0)),
                    'score': float(loss.get('score', 0)),
                    'confidence': float(loss.get('confidence', 0)),
                    'signals': loss.get('signals', {}),
                    'bet_type': loss.get('bet_type', 'win'),
                },
                'bet_id': bet_id,
                'market_id': loss.get('market_id', ''),
                'outcome': loss.get('outcome', ''),
            }

            jobs.append(job)

        logger.info(f"Prepared {len(jobs)} race analysis jobs")
        return jobs

    def run_parallel_analysis(
        self,
        race_jobs: List[Dict[str, Any]],
        analyzer_func: callable
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Execute race analysis jobs in parallel.

        Args:
            race_jobs: List of race job specifications
            analyzer_func: Worker function to analyze each race

        Returns:
            Tuple of (successful_analyses, failed_jobs)
        """
        start_time = time.time()
        successful = []
        failed = []

        logger.info(
            f"Starting parallel analysis of {len(race_jobs)} races "
            f"(max_workers={self.max_workers}, timeout={self.worker_timeout}s)"
        )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_job = {
                executor.submit(analyzer_func, job): job
                for job in race_jobs
            }

            # Collect results as they complete
            for future in as_completed(future_to_job, timeout=self.worker_timeout * len(race_jobs)):
                job = future_to_job[future]
                race_id = job['race_id']

                try:
                    result = future.result(timeout=self.worker_timeout)

                    if result.get('status') == 'success':
                        successful.append(result)
                        logger.info(f"✓ {race_id} - {result.get('loss_type', 'unknown')}")
                    else:
                        failed.append({
                            'race_id': race_id,
                            'error': result.get('error', 'Unknown error'),
                            'job': job
                        })
                        logger.warning(f"✗ {race_id} - {result.get('error', 'failed')}")

                except Exception as e:
                    failed.append({
                        'race_id': race_id,
                        'error': str(e),
                        'job': job
                    })
                    logger.error(f"✗ {race_id} - Exception: {e}")

        elapsed = time.time() - start_time
        logger.info(
            f"Parallel analysis complete: {len(successful)} succeeded, "
            f"{len(failed)} failed in {elapsed:.1f}s"
        )

        return successful, failed

    def orchestrate_daily_learning(
        self,
        target_date: Optional[str] = None,
        min_samples: int = 3
    ) -> Dict[str, Any]:
        """
        Main orchestration flow for daily learning.

        Steps:
        1. Fetch settled picks from DynamoDB
        2. Filter to losses only
        3. Prepare race analysis jobs
        4. Fan out to parallel workers
        5. Aggregate results
        6. Make weight adjustment decisions

        Args:
            target_date: Date to analyze (YYYY-MM-DD), defaults to yesterday
            min_samples: Minimum races needed to make weight changes

        Returns:
            Complete learning report with recommendations
        """
        start_time = time.time()

        # Default to yesterday (today's races just settled)
        if not target_date:
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            target_date = yesterday.strftime('%Y-%m-%d')

        logger.info(f"=== Starting Daily Learning for {target_date} ===")

        # Step 1: Fetch settled picks
        all_picks = self.fetch_settled_picks(target_date)

        if not all_picks:
            return {
                'status': 'no_data',
                'target_date': target_date,
                'message': 'No settled picks found for target date',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        # Step 2: Filter to losses
        losses = self.filter_losses(all_picks)

        if not losses:
            return {
                'status': 'no_losses',
                'target_date': target_date,
                'total_picks': len(all_picks),
                'message': 'No losses found - perfect day!',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

        # Step 3: Prepare race jobs
        race_jobs = self.prepare_race_jobs(losses)

        if len(race_jobs) < min_samples:
            logger.warning(
                f"Only {len(race_jobs)} races available, need {min_samples} minimum"
            )

        # Step 4: Import and run parallel analysis
        from backend.learning.race_analyzer import analyze_single_race

        successful_analyses, failed_jobs = self.run_parallel_analysis(
            race_jobs,
            analyze_single_race
        )

        # Step 5: Aggregate results
        from backend.learning.aggregator import aggregate_findings

        aggregation = aggregate_findings(
            successful_analyses,
            min_confidence=0.3  # 30%+ of races show same pattern
        )

        # Calculate summary statistics
        elapsed = time.time() - start_time

        summary = {
            'status': 'success',
            'target_date': target_date,
            'execution_time_seconds': round(elapsed, 2),
            'total_picks': len(all_picks),
            'losses_analyzed': len(successful_analyses),
            'failed_analyses': len(failed_jobs),
            'win_rate': round((len(all_picks) - len(losses)) / len(all_picks), 3) if all_picks else 0,
            'parallel_workers': self.max_workers,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        report = {
            'summary': summary,
            'aggregation': aggregation,
            'failed_jobs': failed_jobs,
            'detailed_analyses': successful_analyses[:10],  # First 10 for debugging
        }

        logger.info(f"=== Daily Learning Complete in {elapsed:.1f}s ===")
        logger.info(f"Analyzed: {len(successful_analyses)}/{len(race_jobs)} races")
        logger.info(f"Patterns found: {len(aggregation.get('patterns', []))}")
        logger.info(f"Recommendations: {len(aggregation.get('recommendations', []))}")

        return report


def lambda_handler(event, context):
    """
    AWS Lambda handler for daily learning orchestrator.

    Event payload:
    {
        "target_date": "2026-05-20",  # Optional, defaults to yesterday
        "min_samples": 3,              # Optional, minimum races for weight changes
        "max_workers": 10              # Optional, parallel worker limit
    }
    """
    target_date = event.get('target_date')
    min_samples = event.get('min_samples', 3)
    max_workers = event.get('max_workers', 10)

    orchestrator = LearningOrchestrator(max_workers=max_workers)

    try:
        report = orchestrator.orchestrate_daily_learning(
            target_date=target_date,
            min_samples=min_samples
        )

        return {
            'statusCode': 200,
            'body': json.dumps(report, default=str)
        }

    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
