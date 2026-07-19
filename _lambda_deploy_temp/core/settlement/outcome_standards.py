"""
Standardize outcome values across all betting scripts.
Use this module to ensure consistent outcome values in the database.

STANDARD OUTCOMES (always use these):
- 'WON' - bet won
- 'LOST' - bet lost  
- 'PLACED' - each-way bet placed but didn't win
- 'PENDING' - race hasn't run yet or result not recorded

DO NOT USE: 'win', 'loss', 'won', 'pending' (lowercase variations)
"""

def normalize_outcome(outcome):
    """
    Normalize any outcome variant to standard uppercase format.
    
    Args:
        outcome: String outcome value (can be any case)
        
    Returns:
        Standardized uppercase outcome: 'WON', 'LOST', 'PLACED', 'PENDING', or None
    """
    if outcome is None:
        return None
    
    outcome_upper = str(outcome).upper().strip()
    
    # Map all variations to standard values
    if outcome_upper in ['WIN', 'WON']:
        return 'WON'
    elif outcome_upper in ['LOSS', 'LOST', 'LOSE']:
        return 'LOST'
    elif outcome_upper in ['PLACE', 'PLACED']:
        return 'PLACED'
    elif outcome_upper in ['PENDING', 'PEND', '']:
        return 'PENDING'
    
    # Unknown outcome - return as-is but warn
    print(f"WARNING: Unknown outcome value '{outcome}' - returning None")
    return None


def is_resolved(outcome):
    """
    Check if an outcome is resolved (not pending).
    
    Args:
        outcome: Outcome value
        
    Returns:
        True if outcome is WON, LOST, or PLACED; False if PENDING or None
    """
    normalized = normalize_outcome(outcome)
    return normalized in ['WON', 'LOST', 'PLACED']


def is_win(outcome):
    """Check if outcome represents a win."""
    return normalize_outcome(outcome) == 'WON'


def is_loss(outcome):
    """Check if outcome represents a loss."""
    return normalize_outcome(outcome) == 'LOST'


def is_placed(outcome):
    """Check if outcome represents a place (EW bet)."""
    return normalize_outcome(outcome) == 'PLACED'


def is_pending(outcome):
    """Check if outcome is pending."""
    normalized = normalize_outcome(outcome)
    return normalized == 'PENDING' or normalized is None


# Export constants
OUTCOME_WON = 'WON'
OUTCOME_LOST = 'LOST'
OUTCOME_PLACED = 'PLACED'
OUTCOME_PENDING = 'PENDING'


def calculate_each_way_pnl(finish_pos, total_runners, odds, stake, bet_type='Each Way'):
    """
    Settle a pick's P&L from its finishing position.

    All BetBudAI UI picks are staked Each Way (complete_daily_analysis.py sets
    bet_type='Each Way' and a Kelly-sized stake of 2-8 units). An each-way bet
    splits the stake 50/50 between a win part and a place part:
      - WIN: both the win part (at full odds) AND the place part (at the
        each-way fraction) pay out.
      - PLACED (inside the each-way terms): only the place part pays, at
        (odds-1) * fraction; the win part's stake is lost.
      - Outside the each-way terms (or non-EW bet_type): full stake lost
        unless the horse won outright.

    Each-way terms scale with field size (standard UK bookmaker convention):
      8+ runners  -> 1/5 odds, 3 places paid
      5-7 runners -> 1/4 odds, 2 places paid
      <5 runners  -> each-way not offered (win-only)

    Returns (outcome: 'win'|'placed'|'loss', profit: float rounded to 2dp).
    """
    is_ew = str(bet_type or '').strip().lower().replace('-', ' ') == 'each way'

    if total_runners >= 8:
        ew_fraction, places_paid = 0.2, 3
    elif total_runners >= 5:
        ew_fraction, places_paid = 0.25, 2
    else:
        ew_fraction, places_paid = 0.0, 1

    if finish_pos == 1:
        if is_ew:
            if ew_fraction:
                profit = (stake / 2) * (odds - 1) + (stake / 2) * (odds - 1) * ew_fraction
            else:
                # No place market (<5 runners): win leg (half stake) wins, place leg loses
                profit = (stake / 2) * (odds - 1) - (stake / 2)
        else:
            profit = stake * (odds - 1)
        return 'win', round(profit, 2)

    if is_ew and ew_fraction and finish_pos and finish_pos <= places_paid:
        profit = (stake / 2) * (odds - 1) * ew_fraction - (stake / 2)
        return 'placed', round(profit, 2)

    return 'loss', -round(stake, 2)
