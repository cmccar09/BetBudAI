"""
tennis_pick_logic.py — Pure functions for BetBudAI Pro Tennis pick analysis.

These are the algorithmic core of the pick-tennis.md skill. All functions are
deterministic and dependency-free (no AWS, no HTTP) so they can be unit-tested.

Functions:
  fatigue_level(sets_played, hours_rest, round_id)   → 'LOW' | 'MED' | 'HIGH'
  grass_h2h_winner(player_a, wins_a, player_b, wins_b, meetings)
                                                      → str | None
  upset_decision(seed_gap, surface_mismatch, grass_h2h_advantage)
                                                      → 'PICK' | 'WATCH' | 'NONE'
  ew_value_flag(fractional_odds_str, round_name, fatigue, retirement_risk)
                                                      → 'VALUE' | 'SPECULATIVE' | 'NONE'
  retirement_risk_flag(age, round_id, sets_in_last_match)
                                                      → bool
"""

from __future__ import annotations


# ── Fatigue Detection ─────────────────────────────────────────────────────────

def fatigue_level(sets_played: int, hours_rest: float, round_id: int = 0) -> str:
    """
    Compute fatigue level from sets played in last match and hours of rest
    before the next scheduled match.

    Parameters
    ----------
    sets_played : int
        Total sets completed in the player's most recent match (e.g. 5 for a
        five-setter, 3 for a straight-sets win in a best-of-5).
    hours_rest : float
        Hours between end of last match and start of next match.
    round_id : int
        Numeric round identifier (1 = R128, 2 = R64, 3 = R32, 4 = R16,
        5 = QF, 6 = SF, 7 = F). Used to tighten fatigue thresholds in late
        rounds (QF+). Pass 0 if unknown.

    Returns
    -------
    str
        'HIGH'  — skip or downgrade to SPECULATIVE
        'MED'   — do not upgrade above MEDIUM confidence
        'LOW'   — no fatigue flag
    """
    is_late_round = round_id >= 5  # QF or later

    if sets_played >= 5:
        if hours_rest < 48:
            return 'HIGH'
        if hours_rest < 72:
            return 'MED'
        return 'LOW'

    if sets_played >= 3:
        if is_late_round and hours_rest < 24:
            return 'MED'
        if hours_rest < 24:
            return 'MED'
        return 'LOW'

    # Straight-sets win (2 sets in best-of-3, 2 sets in best-of-5)
    return 'LOW'


# ── Grass H2H ─────────────────────────────────────────────────────────────────

def grass_h2h_winner(
    player_a: str,
    wins_a: int,
    player_b: str,
    wins_b: int,
    meetings: int,
) -> str | None:
    """
    Determine the grass H2H winner given win counts and total meetings.

    Only returns a winner when the sample is large enough to be meaningful
    (≥ 2 meetings). Ties are returned as None.

    Parameters
    ----------
    player_a : str
        Name of the first player.
    wins_a : int
        Number of grass-surface wins for player_a.
    player_b : str
        Name of the second player.
    wins_b : int
        Number of grass-surface wins for player_b.
    meetings : int
        Total grass meetings between the two players (wins_a + wins_b should
        equal this; caller is responsible for consistency).

    Returns
    -------
    str | None
        Name of the player with the grass H2H edge, or None when:
        - fewer than 2 meetings (sample too small)
        - tied record
    """
    if meetings < 2:
        return None  # sample too small — no signal

    if wins_a > wins_b:
        return player_a
    if wins_b > wins_a:
        return player_b
    return None  # tied


# ── Upset Probability ─────────────────────────────────────────────────────────

def upset_decision(
    seed_gap: int,
    surface_mismatch: bool,
    grass_h2h_advantage: bool,
) -> str:
    """
    Decide whether a lower-seeded player's match warrants an upset PICK,
    an Upset WATCH label, or no flag.

    Parameters
    ----------
    seed_gap : int
        Absolute difference in seeds between the two players.
        e.g. [3] vs [8] → seed_gap = 5.
    surface_mismatch : bool
        True when the higher seed is a clay or hard-court specialist playing
        on grass (career grass win% is ≥ 15 pp below clay win%, or explicitly
        tagged as 'clay specialist').
    grass_h2h_advantage : bool
        True when the lower seed leads the grass H2H 2-1 or better and the
        sample contains ≥ 2 meetings, OR the lower seed is a confirmed grass
        specialist with a top-20 grass win% this season.

    Returns
    -------
    str
        'PICK'  — all three conditions met; make the upset pick at MEDIUM confidence
        'WATCH' — two of three conditions met; flag as Upset Watch, do not pick
        'NONE'  — fewer than two conditions met; no upset signal
    """
    conditions_met = sum([seed_gap >= 5, surface_mismatch, grass_h2h_advantage])

    if conditions_met == 3:
        return 'PICK'
    if conditions_met == 2:
        return 'WATCH'
    return 'NONE'


# ── Each-Way Value ────────────────────────────────────────────────────────────

def _fractional_to_decimal(fractional: str) -> float:
    """Convert a fractional odds string like '6/1' or '4/1' to decimal."""
    try:
        num, den = fractional.split('/')
        return float(num) / float(den) + 1.0
    except Exception:
        raise ValueError(f"Cannot parse fractional odds: {fractional!r}")


def ew_value_flag(
    fractional_odds: str,
    round_name: str,
    fatigue: str = 'LOW',
    retirement_risk: bool = False,
) -> str:
    """
    Assess each-way outright value for a player still in the tournament.

    EW VALUE window: odds 4/1–8/1 (decimal 5.0–9.0) AND in the Quarter-Final.
    Downgrade to SPECULATIVE if the player carries FATIGUE HIGH or RETIREMENT RISK.

    Parameters
    ----------
    fractional_odds : str
        Outright odds in fractional format, e.g. '6/1', '4/1', '10/1'.
    round_name : str
        Current round name. Case-insensitive. Must contain 'quarter' or 'qf'
        to trigger EW value assessment.
    fatigue : str
        Fatigue level from fatigue_level(): 'LOW', 'MED', or 'HIGH'.
    retirement_risk : bool
        True if retirement_risk_flag() returned True for this player.

    Returns
    -------
    str
        'VALUE'       — recommend EW stake at these odds in the QF
        'SPECULATIVE' — odds in range but player carries fatigue/retirement flag,
                        OR odds are >8/1 and player is in QF (too long for EW)
        'NONE'        — odds outside 4/1–8/1 range, or not in QF
    """
    decimal_odds = _fractional_to_decimal(fractional_odds)
    in_qf = 'quarter' in round_name.lower() or 'qf' in round_name.lower()

    EW_LOW = 5.0   # 4/1 decimal
    EW_HIGH = 9.0  # 8/1 decimal

    if not in_qf:
        return 'NONE'

    if decimal_odds < EW_LOW:
        # Shorter than 4/1 — win-only better value
        return 'NONE'

    if decimal_odds > EW_HIGH:
        # Longer than 8/1 in QF — speculative at best
        return 'SPECULATIVE'

    # Odds are in the 4/1–8/1 EW window
    if fatigue == 'HIGH' or retirement_risk:
        return 'SPECULATIVE'

    return 'VALUE'


# ── Retirement Risk ───────────────────────────────────────────────────────────

def retirement_risk_flag(age: int, round_id: int, sets_in_last_match: int) -> bool:
    """
    Return True when a player meets the retirement risk criteria.

    Criteria (ALL must be true):
    - age ≥ 33
    - round_id > 3 (R16 or later: 4=R16, 5=QF, 6=SF, 7=F)
    - sets_in_last_match ≥ 3

    Parameters
    ----------
    age : int
        Player's age in years.
    round_id : int
        Current round numeric ID (see fatigue_level docstring for mapping).
    sets_in_last_match : int
        Total sets played in the player's most recent completed match.

    Returns
    -------
    bool
        True if all three criteria are met.
    """
    return age >= 33 and round_id > 3 and sets_in_last_match >= 3
