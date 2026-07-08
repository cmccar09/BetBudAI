"""
rugby_pick_logic.py — Stub implementations of rugby pick-selection logic.

These functions encode the rules described in .claude/skills/pick-rugby.md and
are exercised by tests/test_rugby_picks.py.  The implementations here are
intentionally simple (no external I/O, no DynamoDB) so the test suite runs
offline — ideal for CI and local validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

STRENGTH_TIER = {
    "South Africa": 1, "New Zealand": 2, "France": 3, "Ireland": 4,
    "England": 5, "Argentina": 6, "Australia": 7, "Scotland": 8,
    "Wales": 9, "Fiji": 10, "Italy": 11, "Japan": 12,
}

SH_TEAMS = {"South Africa", "New Zealand", "Australia", "Argentina"}
NH_TEAMS = {"France", "Ireland", "England", "Scotland", "Wales", "Italy"}


@dataclass
class Fixture:
    home: str
    away: str
    round: int = 1
    venue_hemisphere: str = "SH"   # "SH" or "NH" — hemisphere where match is played


@dataclass
class TeamResult:
    """A single round result for a team."""
    team: str
    opponent: str
    score_for: int
    score_against: int
    tries_scored: int = 0

    @property
    def margin(self) -> int:
        return self.score_for - self.score_against

    @property
    def won(self) -> bool:
        return self.score_for > self.score_against


@dataclass
class PlayerRecord:
    name: str
    team: str
    position: str          # e.g. "wing", "flanker", "number8"
    minutes_r1: int = 0
    minutes_r2: int = 0
    in_squad: bool = True
    scored_r1: bool = False

    @property
    def cumulative_minutes(self) -> int:
        return self.minutes_r1 + self.minutes_r2


@dataclass
class VenueRecord:
    """Records of a team's results at a specific venue."""
    team: str
    venue: str
    results: list[bool] = field(default_factory=list)  # True = win, chronological

    @property
    def last_n_wins(self) -> int:
        """Count of consecutive wins from the most recent result backwards."""
        count = 0
        for result in reversed(self.results):
            if result:
                count += 1
            else:
                break
        return count


# ---------------------------------------------------------------------------
# 1. Home advantage adjustment
# ---------------------------------------------------------------------------

def home_advantage_adjustment(fixture: Fixture) -> int:
    """
    Return the points adjustment to apply to the predicted margin based on
    which hemisphere the match is played in relative to the teams involved.

    Rules from skill file:
    - NH team at home vs NH away: +6 (midpoint of +5 to +7)
    - SH team at home vs SH away: +6
    - SH team playing in NH venue (away): -8 from their baseline
    - NH team playing in SH venue (away): -8 from their baseline
    - Both teams from the same group and playing at home: +6

    The adjustment is always from the home team's perspective (positive means
    home team benefits).  For cross-hemisphere matches in NH venues the SH
    team is the away side, so the NH home team gains +8 on top of the tier
    difference.  We model this as the home team gaining +8.
    """
    home_is_SH = fixture.home in SH_TEAMS
    away_is_SH = fixture.away in SH_TEAMS
    playing_in_NH = fixture.venue_hemisphere == "NH"
    playing_in_SH = fixture.venue_hemisphere == "SH"

    # SH team playing away in NH venue
    if away_is_SH and playing_in_NH:
        return 8   # NH home team gains 8 pts advantage
    # NH team playing away in SH venue
    if not away_is_SH and playing_in_SH:
        return 8   # SH home team gains 8 pts advantage
    # Same hemisphere — standard home advantage
    return 6


# ---------------------------------------------------------------------------
# 2. Tournament momentum
# ---------------------------------------------------------------------------

BLOWOUT_THRESHOLD = 20   # points
CONFIDENCE_PENALTY = 10  # pts subtracted from predicted margin


def tournament_momentum_penalty(result: TeamResult) -> dict:
    """
    Given a team's most recent result, return a momentum assessment dict:
        {
            "label": "BOUNCE_BACK" | "CONFIDENCE_DAMAGED" | "NEUTRAL",
            "margin_penalty": int,   # subtract from predicted margin next round
            "confidence_downgrade": bool,
            "upset_watch": bool,
        }

    Rules from skill file:
    - Lost by 20+ -> CONFIDENCE_DAMAGED, -10 to predicted margin, downgrade confidence
    - Lost by < 10 to a legitimate higher-tier opponent -> BOUNCE_BACK
    - Won or drew -> NEUTRAL
    """
    if result.won:
        return {
            "label": "NEUTRAL",
            "margin_penalty": 0,
            "confidence_downgrade": False,
            "upset_watch": False,
        }

    loss_margin = abs(result.margin)

    if loss_margin >= BLOWOUT_THRESHOLD:
        return {
            "label": "CONFIDENCE_DAMAGED",
            "margin_penalty": CONFIDENCE_PENALTY,
            "confidence_downgrade": True,
            "upset_watch": True,
        }

    # Close loss (< 10 pts) — bounce-back candidate
    if loss_margin < 10:
        return {
            "label": "BOUNCE_BACK",
            "margin_penalty": 0,
            "confidence_downgrade": False,
            "upset_watch": False,
        }

    # Loss of 10-19 pts — moderate concern, partial penalty
    return {
        "label": "NEUTRAL",
        "margin_penalty": 5,
        "confidence_downgrade": False,
        "upset_watch": False,
    }


# ---------------------------------------------------------------------------
# 3. Try-scorer confidence
# ---------------------------------------------------------------------------

def try_scorer_confidence(player: PlayerRecord, team_r1: TeamResult) -> dict:
    """
    Score a potential First Try Scorer pick using the signal checklist from
    the skill file.  Returns:
        {
            "signals_hit": int,   # out of max 5 checkable signals (squad is mandatory gate)
            "recommended": bool,
            "reason": str,
        }

    Mandatory gate: if player is not in squad, recommended = False immediately.
    Signal scoring:
      +2 if team scored 4+ tries in R1
      +2 if player scored in R1
      +1 if player is a wing (position in {"wing", "11", "14"})
      +1 if team won R1 (facing a lower-tier or struggling opponent)
    Maximum checkable signals = 4 (squad is just a gate, not scored).
    """
    if not player.in_squad:
        return {
            "signals_hit": 0,
            "recommended": False,
            "reason": "Player not in squad — pick voided.",
        }

    signals = 0
    reasons = []

    wing_positions = {"wing", "11", "14"}
    if team_r1.tries_scored >= 4:
        signals += 2
        reasons.append(f"team scored {team_r1.tries_scored} tries in R1")
    if player.scored_r1:
        signals += 2
        reasons.append("player scored in R1")
    if player.position.lower() in wing_positions:
        signals += 1
        reasons.append("wing position")
    if team_r1.won:
        signals += 1
        reasons.append("team won R1")

    recommended = signals >= 3
    return {
        "signals_hit": signals,
        "recommended": recommended,
        "reason": "; ".join(reasons) if reasons else "no signals",
    }


# ---------------------------------------------------------------------------
# 4. Fatigue model
# ---------------------------------------------------------------------------

FATIGUE_MINUTES_THRESHOLD = 160


def fatigue_flag(player: PlayerRecord) -> dict:
    """
    Assess rotation risk for a player based on cumulative minutes played.

    Rules from skill file:
    - 160+ minutes across 2 matches -> ROTATION RISK
    - SH team in July -> less fatigue (in-season); reduce margin impact for SA/NZ
    - Tier 2 sides with thin squads -> larger margin impact

    Returns:
        {
            "rotation_risk": bool,
            "cumulative_minutes": int,
            "margin_impact": int,   # pts to subtract from team's predicted margin
            "note": str,
        }
    """
    cumulative = player.cumulative_minutes

    if cumulative < FATIGUE_MINUTES_THRESHOLD:
        return {
            "rotation_risk": False,
            "cumulative_minutes": cumulative,
            "margin_impact": 0,
            "note": f"{cumulative} mins — no fatigue concern",
        }

    # Player has hit threshold
    team = player.team
    if team in {"South Africa", "New Zealand"}:
        # Deep squads — bench quality high; small margin impact
        margin_impact = 3
        note = f"{cumulative} mins — ROTATION RISK (SA/NZ — expect change, bench is strong, -3 pts margin)"
    elif team in SH_TEAMS or team in {"Ireland", "France", "England"}:
        margin_impact = 5
        note = f"{cumulative} mins — ROTATION RISK (-5 pts margin)"
    else:
        # Tier 2 thin squads
        margin_impact = 10
        note = f"{cumulative} mins — ROTATION RISK (thin squad, -10 pts margin, confidence to SPECULATIVE)"

    return {
        "rotation_risk": True,
        "cumulative_minutes": cumulative,
        "margin_impact": margin_impact,
        "note": note,
    }


# ---------------------------------------------------------------------------
# 5. Upset detection
# ---------------------------------------------------------------------------

def upset_watch(
    underdog_venue_record: VenueRecord,
    favourite_last_result: TeamResult,
    underdog_tier: int,
    favourite_tier: int,
    venue_wins_required: int = 3,
    big_loss_threshold: int = 10,
) -> dict:
    """
    Determine whether an upset watch flag should be raised.

    Required conditions (all three must be true):
      1. underdog is lower-ranked (higher tier number)
      2. underdog has won their last `venue_wins_required` at this venue
      3. favourite lost by `big_loss_threshold`+ in their most recent match

    Returns:
        {
            "upset_watch": bool,
            "conditions_met": int,   # how many of the 3 required conditions are true
            "reason": str,
        }
    """
    conditions = []

    # 1. Underdog is genuinely lower-ranked
    is_underdog = underdog_tier > favourite_tier
    conditions.append(is_underdog)

    # 2. Underdog has won last N at this venue
    consecutive_wins = underdog_venue_record.last_n_wins
    has_venue_form = consecutive_wins >= venue_wins_required
    conditions.append(has_venue_form)

    # 3. Favourite came off a big loss
    fav_loss_margin = abs(favourite_last_result.margin)
    fav_lost_big = (not favourite_last_result.won) and (fav_loss_margin >= big_loss_threshold)
    conditions.append(fav_lost_big)

    met = sum(conditions)
    all_met = all(conditions)

    parts = []
    if is_underdog:
        parts.append(f"underdog (tier {underdog_tier} vs {favourite_tier})")
    if has_venue_form:
        parts.append(f"{consecutive_wins} consecutive wins at venue")
    if fav_lost_big:
        parts.append(f"favourite lost by {fav_loss_margin} in last match")

    return {
        "upset_watch": all_met,
        "conditions_met": met,
        "reason": "; ".join(parts) if parts else "no conditions met",
    }
