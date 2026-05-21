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
