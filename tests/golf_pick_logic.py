"""
golf_pick_logic.py — Stub implementations for golf pick selection logic.

These functions encode the rules defined in .claude/skills/pick-golf.md
(Sections A–D). The unit tests in test_golf_picks.py exercise this module.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Section A — Course-fit scoring
# ---------------------------------------------------------------------------

# Signal keys that qualify a player as a links specialist.
# Each key maps to the signal checklist in Section A of the skill file.
LINKS_FIT_SIGNALS = [
    "previous_top10_open_venue",       # 1
    "low_ball_flight",                  # 2
    "driving_accuracy_over_62",         # 3
    "sand_save_over_58",                # 4
    "won_or_top5_scottish_irish_open",  # 5
    "grew_up_links_country",            # 6
    "ryder_cup_wins_uk_ireland",        # 7
    "strong_wind_short_game",           # 8
    "previous_top5_royal_birkdale",     # 9
    "press_labelled_links_lover",       # 10
]

# Archetype modifier to add on top of raw signal count score (per point rules
# in Section A the modifier is added as a flat bonus before normalisation).
ARCHETYPE_MODIFIERS = {
    "links_specialist": 25,
    "parkland_bomber": 5,
    "links_adjacent": 12,
    "course_debutant": -5,
    "links_risk": -15,
}


@dataclass
class PlayerProfile:
    name: str
    signals: List[str] = field(default_factory=list)   # subset of LINKS_FIT_SIGNALS
    archetype: Optional[str] = None                     # one of ARCHETYPE_MODIFIERS keys
    odds: float = 0.0                                   # decimal odds (e.g. 26.0 = 25/1)
    ryder_cup_windy_record: bool = False
    major_wins: int = 0


def course_fit_score(player: PlayerProfile) -> int:
    """
    Return an integer course-fit score for a links major.

    Scoring rules (Section A):
      - 1 point per valid signal present in player.signals
      - Plus archetype modifier if player.archetype is set
    5+ signals = HIGH FIT; 3-4 = MEDIUM; < 3 = LOW / RISK
    """
    signal_points = sum(1 for s in player.signals if s in LINKS_FIT_SIGNALS)
    modifier = ARCHETYPE_MODIFIERS.get(player.archetype or "", 0)
    return signal_points + modifier


def links_fit_label(score: int) -> str:
    """
    Convert a raw course-fit score to a human-readable label.
    Thresholds from Section A signal checklist.

    Score = signal_count + archetype_modifier.
    For pure signal scores (no archetype):
      5+ signals (score >= 5) = HIGH FIT
      3-4 signals (score >= 3) = MEDIUM FIT
      < 3 (score < 3, >= 0) = LOW FIT
      negative = LINKS RISK (links_risk archetype applied)
    For scores boosted by archetype modifiers these thresholds still hold
    because modifiers shift the effective signal count equivalent upward.
    """
    if score >= 5:
        return "HIGH FIT"
    if score >= 3:
        return "MEDIUM FIT"
    if score >= 0:
        return "LOW FIT"
    return "LINKS RISK"


# ---------------------------------------------------------------------------
# Section B — Wind impact
# ---------------------------------------------------------------------------

def wind_impact(
    player: PlayerProfile,
    wind_mph: float,
    base_ew_confidence: str = "MEDIUM",
) -> dict:
    """
    Apply Section B wind rules to a player pick.

    Returns a dict with:
      - ew_confidence: adjusted confidence tier (HIGH / MEDIUM / LOW)
      - favourite_discounted: bool — whether the short-price discount fired
      - longshot_upgraded: bool — whether the longshot uplift fired
      - accuracy_weight: int — driving accuracy signal weight (pts)
      - distance_weight: int — distance signal weight (pts)
      - cut_line_adjustment: int — shots to add to cut line estimate
    """
    CONFIDENCE_ORDER = ["HIGH", "MEDIUM", "LOW"]

    def _tier_up(tier: str) -> str:
        idx = CONFIDENCE_ORDER.index(tier)
        return CONFIDENCE_ORDER[max(0, idx - 1)]

    def _tier_down(tier: str) -> str:
        idx = CONFIDENCE_ORDER.index(tier)
        return CONFIDENCE_ORDER[min(len(CONFIDENCE_ORDER) - 1, idx + 1)]

    ew_confidence = base_ew_confidence
    favourite_discounted = False
    longshot_upgraded = False
    cut_line_adjustment = 0

    # Standard accuracy / distance weights (calm conditions)
    accuracy_weight = 3
    distance_weight = 5

    if wind_mph > 15:
        cut_line_adjustment = 2  # par goes up ~2 shots

        # Rule 1: favourite discount — decimal odds < 6.0 equates to shorter than 5/1
        if player.odds < 6.0:
            ew_confidence = _tier_down(ew_confidence)
            favourite_discounted = True

        # Rule 2: longshot uplift — 15/1+ (decimal >= 16) with 3+ links signals
        link_signal_count = sum(1 for s in player.signals if s in LINKS_FIT_SIGNALS)
        if player.odds >= 16.0 and link_signal_count >= 3:
            ew_confidence = _tier_up(ew_confidence)
            longshot_upgraded = True

        # Rule 5: reweight accuracy vs distance in wind
        accuracy_weight = 8
        distance_weight = 1

    if wind_mph > 25:
        # Extreme conditions — additional cut line stress
        cut_line_adjustment = 4

    return {
        "ew_confidence": ew_confidence,
        "favourite_discounted": favourite_discounted,
        "longshot_upgraded": longshot_upgraded,
        "accuracy_weight": accuracy_weight,
        "distance_weight": distance_weight,
        "cut_line_adjustment": cut_line_adjustment,
    }


# ---------------------------------------------------------------------------
# Section C — Cut line prediction
# ---------------------------------------------------------------------------

# Cut line estimates (vs par) per wind condition bucket.
# Tuple = (low end, high end); midpoint used for probability calculations.
CUT_LINE_ESTIMATES = {
    "calm":    (-5, -3),    # < 10 mph
    "breezy":  (-3, -1),    # 10-15 mph
    "windy":   (1,   3),    # 15-25 mph
    "extreme": (4,   6),    # > 25 mph
}


def wind_bucket(wind_mph: float) -> str:
    if wind_mph < 10:
        return "calm"
    if wind_mph < 15:
        return "breezy"
    if wind_mph <= 25:
        return "windy"
    return "extreme"


def cut_line_midpoint(wind_mph: float) -> float:
    """Return the midpoint of the cut line estimate for given wind speed."""
    low, high = CUT_LINE_ESTIMATES[wind_bucket(wind_mph)]
    return (low + high) / 2


def cut_probability(
    projected_36hole_score: int,
    wind_mph: float,
) -> float:
    """
    Estimate probability (0.0–1.0) of a player making the cut.

    Uses the margin between the player's projected 36-hole score (vs par)
    and the estimated cut line midpoint, mapped to probability buckets
    from Section C.

      R < C - 4  ->  0.95 (> 90%)
      R in [C-4, C-2)  ->  0.80 (70-90%)
      R in [C-2, C+1]  ->  0.55 (40-70%)
      R > C + 1  ->  0.30 (< 40%)
    """
    cut = cut_line_midpoint(wind_mph)
    margin = projected_36hole_score - cut   # negative = player is under the cut line

    if margin < -4:
        return 0.95
    if margin <= -2:
        return 0.80
    if margin <= 1:
        return 0.55
    return 0.30


def ew_viable(
    player: PlayerProfile,
    projected_36hole_score: int,
    wind_mph: float,
    min_links_signals: int = 2,
) -> bool:
    """
    Return True if an each-way bet is viable under Section C rules.

    Requires:
    - Player odds >= 16.0 (16/1+ for value EW)
    - Cut probability >= 0.55
    - At least min_links_signals links fit signals

    At odds 12-16, require 3+ signals.
    """
    p_cut = cut_probability(projected_36hole_score, wind_mph)
    link_count = sum(1 for s in player.signals if s in LINKS_FIT_SIGNALS)

    if p_cut < 0.40:
        return False

    if player.odds >= 16.0:
        return p_cut >= 0.55 and link_count >= min_links_signals
    if player.odds >= 13.0:
        return p_cut >= 0.55 and link_count >= 3
    # Below 12/1 (decimal < 13) — not EW value per skill file edge principle
    return False


# ---------------------------------------------------------------------------
# Section D — In-tournament adjustment triggers
# ---------------------------------------------------------------------------

def r1_adjustment(r1_score_vs_par: int) -> str:
    """
    Return the adjustment action after Round 1.

    Actions: UPGRADE / HOLD / CAUTION / DOWNGRADE / CUT_FLAG
    Thresholds from Section D After Round 1 table.
    """
    if r1_score_vs_par <= -5:
        return "UPGRADE"
    if r1_score_vs_par <= -3:
        return "HOLD"
    if r1_score_vs_par <= -1:
        return "HOLD"
    if r1_score_vs_par == 0:
        return "CAUTION"
    if r1_score_vs_par <= 2:
        return "DOWNGRADE"
    return "CUT_FLAG"


def r3_adjustment(shots_off_lead: int, has_major_win: bool) -> str:
    """
    Return the 54-hole (moving day) adjustment action.

    shots_off_lead: positive integer — how many shots behind the leader.
    has_major_win: whether the player has previously won a major.
    Actions: UPGRADE / HOLD / SPECULATIVE_HOLD / CLOSE
    Thresholds from Section D After Round 3 table.
    """
    if shots_off_lead == 0:
        return "UPGRADE"
    if shots_off_lead <= 3:
        return "HOLD"
    if shots_off_lead <= 6:
        return "SPECULATIVE_HOLD" if has_major_win else "CLOSE"
    return "CLOSE"


# ---------------------------------------------------------------------------
# Section A/B combined — EW value flag
# ---------------------------------------------------------------------------

def ew_value_flag(
    player: PlayerProfile,
    wind_mph: float = 0.0,
    projected_36hole_score: int = -2,
) -> bool:
    """
    Return True if a player qualifies for an EW VALUE flag.

    Criteria (combining Section A edge principle + Section B wind uplift):
    - Odds between 15/1 (decimal 16.0) and 30/1 (decimal 31.0)
    - Links fit score >= 3 signals
    - EW viable (cut probability acceptable)
    """
    if not (16.0 <= player.odds <= 31.0):
        return False
    link_count = sum(1 for s in player.signals if s in LINKS_FIT_SIGNALS)
    if link_count < 3:
        return False
    return ew_viable(player, projected_36hole_score, wind_mph, min_links_signals=3)
