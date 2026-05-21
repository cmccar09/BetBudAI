"""
Settlement module - handles result reconciliation and P&L calculation
Sources: Sporting Life results, Betfair results
"""

from .calculator import calculate_pnl, reconcile_result

try:
    from .results_fetcher import (
        fetch_sl_results,
        settle_pending_picks,
        get_todays_results,
    )
except ImportError:
    pass

try:
    from .betfair_results_fetcher import (
        fetch_betfair_results,
    )
except ImportError:
    pass

try:
    from .outcome_standards import normalize_outcome, is_resolved, is_win, is_loss
except ImportError:
    pass

__all__ = [
    'calculate_pnl',
    'reconcile_result',
]

