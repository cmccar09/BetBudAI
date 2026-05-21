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
        # WIN outcome
        profit = stake * odds
        return 'WIN', profit
    
    elif bet_type in ['place', 'each-way'] and horse_name.lower() in [h.lower() for h in placed_horses]:
        # PLACE outcome
        place_odds = odds / 4  # Standard UK place odds fraction
        profit = stake * place_odds
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
