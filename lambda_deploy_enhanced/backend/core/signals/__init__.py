"""
PHASE 1 FREE SIGNALS MODULE
============================
Four new signals built from existing data (no commercial licenses required).

Expected combined impact: +12-20% strike rate improvement (18% → 30-38%)

Signals:
  1. Run Style Classifier (+5-8%) - Match horse style to race pace
  2. Equipment Detector (+3-5%) - First-time equipment = stable confidence
  3. Jockey Upgrade Detector (+2-4%) - Elite jockey booking = trainer backing
  4. Market Liquidity Analyzer (+2-3%) - Distinguish smart money from noise

Usage:
    from backend.core.signals import enrich_all_signals

    enriched_runners = enrich_all_signals(runners, weights, racecard_html)
"""

from .run_style_classifier import (
    classify_run_style,
    predict_race_pace,
    calculate_pace_match_bonus,
    enrich_runners_with_run_style
)

from .equipment_detector import (
    detect_equipment_changes,
    normalize_equipment,
    extract_equipment_from_sl_html,
    enrich_runners_with_equipment
)

from .jockey_upgrade_detector import (
    detect_jockey_upgrade,
    detect_jockey_downgrade,
    get_jockey_tier,
    enrich_runners_with_jockey_change
)

from .market_liquidity_analyzer import (
    analyze_market_liquidity,
    calculate_market_confidence_score,
    enrich_runners_with_liquidity,
    get_market_summary
)


def enrich_all_signals(runners: list, weights: dict, racecard_html: str = None) -> list:
    """
    Apply all Phase 1 signals to runners.

    This is the main entry point for enriching runners with all new signals.

    Args:
        runners: List of runner dicts
        weights: Scoring weights dict
        racecard_html: Optional Sporting Life HTML for equipment extraction

    Returns:
        Enriched runners list (modified in place)
    """
    # 1. Run style classification
    enrich_runners_with_run_style(runners)

    # 2. Equipment changes (requires racecard HTML)
    enrich_runners_with_equipment(runners, racecard_html)

    # 3. Jockey upgrades
    enrich_runners_with_jockey_change(runners, weights)

    # 4. Market liquidity
    enrich_runners_with_liquidity(runners, weights)

    return runners


__all__ = [
    # Run style
    'classify_run_style',
    'predict_race_pace',
    'calculate_pace_match_bonus',
    'enrich_runners_with_run_style',

    # Equipment
    'detect_equipment_changes',
    'normalize_equipment',
    'extract_equipment_from_sl_html',
    'enrich_runners_with_equipment',

    # Jockey
    'detect_jockey_upgrade',
    'detect_jockey_downgrade',
    'get_jockey_tier',
    'enrich_runners_with_jockey_change',

    # Liquidity
    'analyze_market_liquidity',
    'calculate_market_confidence_score',
    'enrich_runners_with_liquidity',
    'get_market_summary',

    # Main entry point
    'enrich_all_signals',
]
