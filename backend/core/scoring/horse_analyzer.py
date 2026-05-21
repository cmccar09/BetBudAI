"""
Horse scoring analyzer - wraps comprehensive_pick_logic with modular interface
Provides analyze_horse_comprehensive and related scoring functions

NOTE: This module imports from __init__.py which contains the full comprehensive_pick_logic.py
with all scoring signals (50+ signals with dynamic weights).
"""

try:
    from . import (
        analyze_horse_comprehensive,
        DEFAULT_WEIGHTS,
        get_comprehensive_pick,
        get_dynamic_weights,
        should_skip_race,
        format_pick_for_database,
    )
except ImportError:
    DEFAULT_WEIGHTS = {}

    def analyze_horse_comprehensive(*args, **kwargs):
        return {'score': 50.0}

    def get_comprehensive_pick(*args, **kwargs):
        return None

    def get_dynamic_weights():
        return DEFAULT_WEIGHTS

    def should_skip_race(race_data):
        return False, None

    def format_pick_for_database(*args, **kwargs):
        return {}

__all__ = [
    'analyze_horse_comprehensive',
    'DEFAULT_WEIGHTS',
    'get_comprehensive_pick',
    'get_dynamic_weights',
    'should_skip_race',
    'format_pick_for_database',
]
