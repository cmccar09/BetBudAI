"""
Daily Learning System for BetBudAI
===================================
Fan-out parallel processing architecture that analyzes race outcomes
to continuously improve prediction weights.

Components:
- orchestrator.py: Master coordinator, fetches picks, spawns workers
- race_analyzer.py: Worker agent, analyzes single race
- aggregator.py: Results processor, generates recommendations

Legacy components (deprecated):
- weight_decision_engine.py: Old weight adjustment logic
- weight_validator.py: Old validation logic
- weight_deployer.py: Old deployment logic

Usage:
    from backend.learning.orchestrator import LearningOrchestrator

    orchestrator = LearningOrchestrator()
    report = orchestrator.orchestrate_daily_learning(target_date='2026-05-20')
"""

# New parallel learning system
from backend.learning.orchestrator import LearningOrchestrator
from backend.learning.race_analyzer import RaceAnalyzer, analyze_single_race
from backend.learning.aggregator import ResultsAggregator, aggregate_findings

# Legacy components (keep for backward compatibility)
try:
    from backend.learning.weight_decision_engine import WeightDecisionEngine
    from backend.learning.weight_validator import WeightValidator
    from backend.learning.weight_deployer import WeightDeployer
    _legacy_available = True
except ImportError:
    _legacy_available = False

__all__ = [
    'LearningOrchestrator',
    'RaceAnalyzer',
    'analyze_single_race',
    'ResultsAggregator',
    'aggregate_findings',
]

if _legacy_available:
    __all__.extend(['WeightDecisionEngine', 'WeightValidator', 'WeightDeployer'])
