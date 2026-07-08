"""
cycling_pick_logic.py — Stub implementations for pro cycling pick logic.

These functions encode the stage-type classification, GC vs stage hunter
differentiation, breakaway probability model, and team tactics signal from
.claude/skills/pick-cycling.md.

All functions are pure: no external I/O, no DynamoDB, no AWS. They operate
on dicts that mirror the shapes produced by tour_de_france_scraper.py.
"""

from __future__ import annotations
from typing import TypedDict


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class StageData(TypedDict, total=False):
    """Mirrors a single entry from STAGE_SCHEDULE in tour_de_france_scraper.py."""
    stage: int
    date: str
    route: str
    distance_km: float
    type: str                 # 'Flat', 'Hilly', 'Mountain', 'Individual Time Trial', 'Team Time Trial'
    elevation_m: int          # total elevation gain; optional (may not be in schedule)
    has_hc_climb: bool        # has HC or Cat 1 summit finish
    finish_type: str          # 'summit', 'sprint', 'downhill', 'flat'


class RiderProfile(TypedDict, total=False):
    name: str
    team: str
    gc_position: int          # current GC position (1 = leader)
    gc_gap_seconds: int       # time behind GC leader (0 for leader)
    is_gc_contender: bool     # True = Pogacar / Vingegaard / Evenepoel tier
    is_stage_hunter: bool     # True = targets single-day wins
    is_sprinter: bool         # True = pure bunch sprinter
    is_puncheur: bool         # True = hilly/puncheur specialist
    is_climber: bool          # True = pure mountain climber
    is_tt_specialist: bool    # True = individual TT specialist
    stage_wins_this_race: int # wins so far in current race
    last_stage_breakaway: bool # was in a breakaway last stage (may be fatigued)


class TeamControl(TypedDict, total=False):
    """Which team / type of team is controlling the peloton."""
    team_name: str            # e.g. 'Alpecin-Premier Tech'
    control_type: str         # 'sprint', 'gc', 'none', 'fragmented', 'shared_sprint'
    lead_out_intact: bool     # lead-out train still has key riders


# ---------------------------------------------------------------------------
# 1. Stage type classification
# ---------------------------------------------------------------------------

# Canonical stage type constants
FLAT = 'FLAT'
HILLY = 'HILLY'
MOUNTAIN = 'MOUNTAIN'
ITT = 'ITT'
TTT = 'TTT'
COBBLES = 'COBBLES'

# Maps scraper type strings to canonical constants
_SCRAPER_TYPE_MAP = {
    'Flat': FLAT,
    'Hilly': HILLY,
    'Mountain': MOUNTAIN,
    'Individual Time Trial': ITT,
    'Team Time Trial': TTT,
    'Cobbles': COBBLES,
}


def classify_stage_type(stage: StageData) -> str:
    """
    Return the canonical stage type (FLAT / HILLY / MOUNTAIN / ITT / TTT / COBBLES)
    from a stage data dict.

    Primary source: stage['type'] as stored by tour_de_france_scraper.py.
    Secondary heuristics (only used when 'type' is missing or 'Unknown'):
      - elevation_m > 2500 and has_hc_climb -> MOUNTAIN
      - elevation_m in 1000-2500 -> HILLY
      - elevation_m < 1000 -> FLAT

    Args:
        stage: dict with at least a 'type' key (and optionally elevation_m,
               has_hc_climb). Mirrors STAGE_SCHEDULE entries.

    Returns:
        One of the FLAT / HILLY / MOUNTAIN / ITT / TTT / COBBLES constants.

    Raises:
        ValueError: if the stage type cannot be determined.
    """
    raw_type = stage.get('type', '')
    if raw_type in _SCRAPER_TYPE_MAP:
        return _SCRAPER_TYPE_MAP[raw_type]

    # Fallback to elevation heuristics
    elevation = stage.get('elevation_m')
    if elevation is not None:
        if elevation > 2500 and stage.get('has_hc_climb', False):
            return MOUNTAIN
        if elevation > 2500:
            return MOUNTAIN
        if elevation >= 1000:
            return HILLY
        return FLAT

    raise ValueError(
        f"Cannot classify stage type from data: type={raw_type!r}, "
        f"elevation_m={stage.get('elevation_m')!r}"
    )


# ---------------------------------------------------------------------------
# 2. GC vs stage hunter confidence
# ---------------------------------------------------------------------------

# Confidence levels
HIGH = 'HIGH'
MEDIUM = 'MEDIUM'
LOW = 'LOW'
SPECULATIVE = 'SPECULATIVE'


def pick_confidence(rider: RiderProfile, stage_type: str) -> str:
    """
    Return a pick confidence rating for backing this rider on this stage type.

    Core rule (from skill file Step 4):
      - GC leader on FLAT or HILLY -> LOW (fade the GC man)
      - GC leader on MOUNTAIN -> HIGH
      - Stage hunter on FLAT -> HIGH if sprinter, MEDIUM otherwise
      - Stage hunter on HILLY -> HIGH if puncheur
      - TT specialist on ITT -> HIGH
      - Climber on FLAT/HILLY -> SPECULATIVE

    Args:
        rider: RiderProfile dict with role flags set.
        stage_type: one of the canonical constants.

    Returns:
        HIGH / MEDIUM / LOW / SPECULATIVE string.
    """
    is_gc = rider.get('is_gc_contender', False)
    is_sprinter = rider.get('is_sprinter', False)
    is_puncheur = rider.get('is_puncheur', False)
    is_climber = rider.get('is_climber', False)
    is_tt = rider.get('is_tt_specialist', False)
    is_stage_hunter = rider.get('is_stage_hunter', False)

    if stage_type == FLAT:
        if is_gc:
            return LOW          # GC riders save energy on flat stages
        if is_sprinter:
            return HIGH
        if is_puncheur and is_stage_hunter:
            return MEDIUM
        if is_climber:
            return SPECULATIVE
        return MEDIUM

    if stage_type == HILLY:
        if is_gc:
            return LOW          # Same logic — GC riders shelter
        if is_puncheur:
            return HIGH
        if is_sprinter:
            return MEDIUM       # Can win reduced-group sprint if climb is mild
        if is_climber:
            return MEDIUM
        return MEDIUM

    if stage_type == MOUNTAIN:
        if is_gc and rider.get('gc_position', 99) <= 3:
            return HIGH
        if is_climber or is_gc:
            return MEDIUM
        if is_sprinter:
            return SPECULATIVE
        return SPECULATIVE

    if stage_type == ITT:
        if is_tt:
            return HIGH
        if is_gc:
            return MEDIUM       # GC all-rounders are solid TT riders too
        if is_climber:
            return MEDIUM
        if is_sprinter:
            return SPECULATIVE
        return SPECULATIVE

    if stage_type == TTT:
        # TTT winner is a team result — single rider confidence is low/speculative
        return SPECULATIVE

    return SPECULATIVE


# ---------------------------------------------------------------------------
# 3. Breakaway probability by stage type
# ---------------------------------------------------------------------------

def breakaway_probability(stage_type: str, crosswind: bool = False,
                           follows_hard_mountain: bool = False) -> float:
    """
    Return the probability (0.0–1.0) that a breakaway survives to win
    on a given stage type.

    Base rates from historical Grand Tour data 2020–2025 (see skill file Step 5).
    Modifiers:
      - crosswind=True on a flat stage: +15pp (echelon risk)
      - follows_hard_mountain=True: +10pp on any stage type (sprint teams fatigued)

    Args:
        stage_type: canonical stage type constant.
        crosswind: whether significant crosswind is forecast.
        follows_hard_mountain: whether the previous stage was a hard mountain stage.

    Returns:
        Float between 0.0 and 1.0 inclusive.
    """
    BASE = {
        FLAT: 0.05,
        HILLY: 0.30,
        MOUNTAIN: 0.35,
        ITT: 0.00,
        TTT: 0.00,
        COBBLES: 0.25,
    }
    prob = BASE.get(stage_type, 0.10)

    if crosswind and stage_type == FLAT:
        prob += 0.15

    if follows_hard_mountain and stage_type not in (ITT, TTT):
        prob += 0.10

    return min(prob, 1.0)


# ---------------------------------------------------------------------------
# 4. Team control signal → sprinter confidence boost
# ---------------------------------------------------------------------------

def apply_team_control_boost(
    base_confidence: str,
    rider: RiderProfile,
    team_control: TeamControl,
    stage_type: str,
) -> str:
    """
    Adjust pick confidence based on which team is controlling the peloton.

    Rules (from skill file Step 6):
      - Rider's own team in 'sprint' control AND lead_out_intact -> upgrade confidence by one tier
      - GC team in control on flat/hilly -> downgrade sprinter confidence (breakaway more likely)
      - 'fragmented' control -> MEDIUM floor for any stage hunter pick

    Args:
        base_confidence: the starting confidence from pick_confidence().
        rider: the rider being assessed.
        team_control: TeamControl dict describing current peloton dynamics.
        stage_type: canonical stage type.

    Returns:
        Adjusted confidence string.
    """
    tier_order = [SPECULATIVE, LOW, MEDIUM, HIGH]

    def upgrade(conf: str) -> str:
        idx = tier_order.index(conf) if conf in tier_order else 0
        return tier_order[min(idx + 1, len(tier_order) - 1)]

    def downgrade(conf: str) -> str:
        idx = tier_order.index(conf) if conf in tier_order else 0
        return tier_order[max(idx - 1, 0)]

    control_type = team_control.get('control_type', 'none')
    controlling_team = team_control.get('team_name', '')
    lead_out_intact = team_control.get('lead_out_intact', True)
    rider_team = rider.get('team', '')

    # Rider's sprint team is in control and lead-out is intact -> boost
    if (control_type == 'sprint'
            and controlling_team == rider_team
            and lead_out_intact
            and stage_type in (FLAT, HILLY)):
        return upgrade(base_confidence)

    # GC team controlling on flat/hilly stage -> breakaway more likely,
    # downgrade sprinter confidence
    if (control_type == 'gc'
            and rider.get('is_sprinter', False)
            and stage_type in (FLAT, HILLY)):
        return downgrade(base_confidence)

    # Fragmented control -> floor at MEDIUM for stage hunters
    if control_type == 'fragmented' and rider.get('is_stage_hunter', False):
        idx = tier_order.index(base_confidence) if base_confidence in tier_order else 0
        floor_idx = tier_order.index(MEDIUM)
        return tier_order[max(idx, floor_idx)]

    # Shared sprint control -> multiple teams chasing -> near-certain bunch sprint
    if (control_type == 'shared_sprint'
            and rider.get('is_sprinter', False)
            and stage_type == FLAT):
        return upgrade(base_confidence)

    return base_confidence


# ---------------------------------------------------------------------------
# 5. Record calibration
# ---------------------------------------------------------------------------

def calibration_factor(wins: int, picks: int) -> float:
    """
    Return a confidence adjustment multiplier based on current season record.

    Rules (from skill file Step 8):
      - Win rate >= 35% (target)   -> 1.0  (no adjustment)
      - Win rate 25–34%            -> 0.85 (downgrade one tier; increase EW weight)
      - Win rate < 25%             -> 0.70 (significant downgrade; heavy EW focus)

    Args:
        wins: number of correctly predicted stage winners so far this Tour.
        picks: total number of picks made so far (excludes rest days / TTT).

    Returns:
        Float multiplier. Multiply base confidence scores by this factor
        as a signal to the selection engine.

    Raises:
        ValueError: if picks < 0 or wins > picks.
    """
    if picks < 0:
        raise ValueError(f"picks must be >= 0, got {picks}")
    if wins < 0:
        raise ValueError(f"wins must be >= 0, got {wins}")
    if wins > picks:
        raise ValueError(f"wins ({wins}) cannot exceed picks ({picks})")

    if picks == 0:
        return 1.0  # No data yet; no adjustment

    win_rate = wins / picks

    if win_rate >= 0.35:
        return 1.0
    if win_rate >= 0.25:
        return 0.85
    return 0.70
