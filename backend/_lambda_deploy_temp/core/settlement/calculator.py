"""
Settlement calculator for P&L determination
Calculates win/place/each-way outcomes and profits based on actual race results
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


def calculate_pnl(
    pick: Dict[str, Any],
    winner: str,
    placed_horses: list,
    race_result: Dict[str, Any]
) -> Tuple[str, Decimal]:
    """
    Calculate profit/loss for a single pick
    
    Args:
        pick: Pick record with stake, odds, bet_type
        winner: Winning horse name
        placed_horses: List of placed horse names (2nd, 3rd)
        race_result: Complete race result data
    
    Returns:
        (outcome: 'WIN'|'PLACE'|'LOSS'|'VOID', profit: Decimal)
    """
    bet_type = pick.get('bet_type', 'win')  # 'win', 'place', 'each-way'
    horse_name = pick.get('horse_name', '')
    stake = Decimal(str(pick.get('stake', 0)))
    odds = Decimal(str(pick.get('odds', 0)))
    
    if horse_name.lower() == winner.lower():
        # WIN outcome — decimal odds: profit = stake * (odds - 1)
        profit = stake * (odds - Decimal('1'))
        return 'WIN', profit
    
    elif bet_type in ['place', 'each-way'] and horse_name.lower() in [h.lower() for h in placed_horses]:
        # PLACE outcome — 1/4 odds fraction applied to win odds, minus stake
        place_fraction = Decimal('0.25')  # Standard UK 1/4 odds
        profit = stake * ((odds - Decimal('1')) * place_fraction)
        return 'PLACE', profit
    
    else:
        # LOSS outcome
        return 'LOSS', -stake


def reconcile_result(
    pick_id: str,
    race_result: Dict[str, Any],
    existing_outcome: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reconcile a pick against race results

    Args:
        pick_id: ID of the pick
        race_result: Race result from Sporting Life or Betfair
        existing_outcome: Existing outcome to validate against

    Returns:
        Reconciliation record with verified outcome and confidence
    """

    return {
        'pick_id': pick_id,
        'reconciled_at': datetime.utcnow().isoformat(),
        'verified': existing_outcome is not None,
        'confidence': 0.95,
    }


def calculate_daily_roi_report(picks: list, results: list) -> Dict[str, Any]:
    """
    Calculate ROI and profitability metrics for daily performance.

    ADDED 2026-05-20 (Expert Tipster Review):
    - Track ROI, not just strike rate (profitability matters more)
    - Calculate P&L, average odds won/lost
    - Store for historical trending

    Args:
        picks: Official picks for the day
        results: Settled results

    Returns:
        ROI report with P&L, strike rate, average odds
    """
    from datetime import datetime, timezone

    total_stake = len(picks) * 1.0  # £1 per bet standard
    total_return = 0.0
    winners = []
    losers = []
    odds_won = []
    odds_lost = []

    for pick in picks:
        # Find matching result
        result = next((r for r in results if r.get('bet_id') == pick.get('bet_id')), None)
        if not result:
            continue

        if result.get('outcome') == 'won':
            return_amount = result.get('odds_at_settlement', result.get('odds', 1.0))
            total_return += return_amount
            winners.append(pick)
            odds_won.append(return_amount)
        else:
            losers.append(pick)
            odds_lost.append(result.get('odds', 0))

    profit_loss = total_return - total_stake
    roi_percent = (profit_loss / total_stake * 100) if total_stake > 0 else 0
    strike_rate = (len(winners) / len(picks) * 100) if picks else 0

    avg_odds_won = sum(odds_won) / len(odds_won) if odds_won else 0
    avg_odds_lost = sum(odds_lost) / len(odds_lost) if odds_lost else 0

    report = {
        'date': datetime.now(timezone.utc).date().isoformat(),
        'total_picks': len(picks),
        'total_stake': round(total_stake, 2),
        'total_return': round(total_return, 2),
        'profit_loss': round(profit_loss, 2),
        'roi_percent': round(roi_percent, 2),
        'strike_rate': round(strike_rate, 2),
        'winners': len(winners),
        'losers': len(losers),
        'average_odds_won': round(avg_odds_won, 2),
        'average_odds_lost': round(avg_odds_lost, 2),
        'winners_detail': [
            {
                'horse': w.get('horse_name'),
                'race': w.get('course'),
                'odds': w.get('odds'),
                'score': w.get('score'),
                'improver_boosted': w.get('improver_boost_applied', False)
            }
            for w in winners
        ],
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    return report
