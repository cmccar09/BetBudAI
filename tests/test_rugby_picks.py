"""
test_rugby_picks.py — Unit tests for rugby pick-selection logic.

Covers the five models added in .claude/skills/pick-rugby.md:
  1. Home advantage adjustment (SH team away in NH = +8 pts to home team)
  2. Tournament momentum (lost by 20+ in R1 -> confidence penalty)
  3. Try-scorer confidence (wing + team 4+ tries in R1 = value pick)
  4. Fatigue model (160+ minutes = rotation risk flag)
  5. Upset detection (3 venue wins + opponent big loss = UPSET WATCH)

Run with:  pytest tests/test_rugby_picks.py -v
"""

import sys
import os

# Allow import from repo root when running from within tests/ or from root
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import pytest
from rugby_pick_logic import (
    Fixture,
    TeamResult,
    PlayerRecord,
    VenueRecord,
    home_advantage_adjustment,
    tournament_momentum_penalty,
    try_scorer_confidence,
    fatigue_flag,
    upset_watch,
    BLOWOUT_THRESHOLD,
    CONFIDENCE_PENALTY,
    FATIGUE_MINUTES_THRESHOLD,
)


# ===========================================================================
# 1. Home advantage adjustment
# ===========================================================================

class TestHomeAdvantageAdjustment:
    """SH team playing in NH venue loses ~8 pts from baseline (modelled as +8 to NH home)."""

    def test_sh_away_in_nh_gives_8_point_adjustment(self):
        """NZ touring Twickenham — NH home team gains 8 pts."""
        fixture = Fixture(home="England", away="New Zealand", venue_hemisphere="NH")
        adj = home_advantage_adjustment(fixture)
        assert adj == 8, f"Expected 8 pts for SH away in NH, got {adj}"

    def test_sa_away_in_nh_gives_8_point_adjustment(self):
        """SA at Aviva Dublin — Ireland home advantage boosted by SH-away penalty."""
        fixture = Fixture(home="Ireland", away="South Africa", venue_hemisphere="NH")
        adj = home_advantage_adjustment(fixture)
        assert adj == 8

    def test_nh_away_in_sh_gives_8_point_adjustment(self):
        """France in Auckland — NZ home advantage boosted by NH-away penalty (July series)."""
        fixture = Fixture(home="New Zealand", away="France", venue_hemisphere="SH")
        adj = home_advantage_adjustment(fixture)
        assert adj == 8

    def test_england_away_in_sh_gives_8_point_adjustment(self):
        """England in Pretoria — SA home advantage + NH-away penalty."""
        fixture = Fixture(home="South Africa", away="England", venue_hemisphere="SH")
        adj = home_advantage_adjustment(fixture)
        assert adj == 8

    def test_same_hemisphere_nh_gives_standard_advantage(self):
        """Ireland vs Scotland at Aviva — standard NH home advantage (+6)."""
        fixture = Fixture(home="Ireland", away="Scotland", venue_hemisphere="NH")
        adj = home_advantage_adjustment(fixture)
        assert adj == 6

    def test_same_hemisphere_sh_gives_standard_advantage(self):
        """NZ vs Australia in Wellington — standard SH home advantage (+6)."""
        fixture = Fixture(home="New Zealand", away="Australia", venue_hemisphere="SH")
        adj = home_advantage_adjustment(fixture)
        assert adj == 6

    def test_adjustment_is_positive_int(self):
        """Adjustment must always be a non-negative integer."""
        for home, away, hemi in [
            ("France", "New Zealand", "NH"),
            ("New Zealand", "France", "SH"),
            ("Ireland", "Scotland", "NH"),
            ("South Africa", "Australia", "SH"),
        ]:
            fixture = Fixture(home=home, away=away, venue_hemisphere=hemi)
            adj = home_advantage_adjustment(fixture)
            assert isinstance(adj, int) and adj >= 0


# ===========================================================================
# 2. Tournament momentum
# ===========================================================================

class TestTournamentMomentum:
    """Lost by 20+ in R1 -> CONFIDENCE_DAMAGED with -10 margin penalty."""

    def test_blowout_loss_gives_confidence_damaged(self):
        """England lost 45-21 to SA (24-pt margin) -> CONFIDENCE_DAMAGED."""
        result = TeamResult(team="England", opponent="South Africa",
                            score_for=21, score_against=45)
        momentum = tournament_momentum_penalty(result)
        assert momentum["label"] == "CONFIDENCE_DAMAGED"

    def test_blowout_loss_applies_correct_penalty(self):
        """Confidence penalty must be exactly CONFIDENCE_PENALTY (10 pts)."""
        result = TeamResult(team="Argentina", opponent="Scotland",
                            score_for=38, score_against=58)
        momentum = tournament_momentum_penalty(result)
        assert momentum["margin_penalty"] == CONFIDENCE_PENALTY

    def test_blowout_loss_triggers_confidence_downgrade(self):
        result = TeamResult(team="England", opponent="South Africa",
                            score_for=21, score_against=45)
        momentum = tournament_momentum_penalty(result)
        assert momentum["confidence_downgrade"] is True

    def test_blowout_loss_triggers_upset_watch(self):
        """Next opponent should be flagged as upset watch candidate."""
        result = TeamResult(team="England", opponent="South Africa",
                            score_for=21, score_against=45)
        momentum = tournament_momentum_penalty(result)
        assert momentum["upset_watch"] is True

    def test_close_loss_gives_bounce_back(self):
        """France lost 34-32 to NZ (2-pt margin) -> BOUNCE_BACK."""
        result = TeamResult(team="France", opponent="New Zealand",
                            score_for=32, score_against=34)
        momentum = tournament_momentum_penalty(result)
        assert momentum["label"] == "BOUNCE_BACK"

    def test_close_loss_has_no_penalty(self):
        result = TeamResult(team="France", opponent="New Zealand",
                            score_for=32, score_against=34)
        momentum = tournament_momentum_penalty(result)
        assert momentum["margin_penalty"] == 0

    def test_win_gives_neutral(self):
        result = TeamResult(team="Ireland", opponent="Japan",
                            score_for=55, score_against=17)
        momentum = tournament_momentum_penalty(result)
        assert momentum["label"] == "NEUTRAL"
        assert momentum["margin_penalty"] == 0
        assert momentum["confidence_downgrade"] is False

    def test_exactly_at_blowout_threshold(self):
        """Loss of exactly BLOWOUT_THRESHOLD points should be CONFIDENCE_DAMAGED."""
        result = TeamResult(team="Wales", opponent="Scotland",
                            score_for=10, score_against=10 + BLOWOUT_THRESHOLD)
        momentum = tournament_momentum_penalty(result)
        assert momentum["label"] == "CONFIDENCE_DAMAGED"

    def test_one_below_blowout_threshold_is_not_confidence_damaged(self):
        """Loss of BLOWOUT_THRESHOLD - 1 should NOT be CONFIDENCE_DAMAGED."""
        result = TeamResult(team="Wales", opponent="Scotland",
                            score_for=10, score_against=10 + BLOWOUT_THRESHOLD - 1)
        momentum = tournament_momentum_penalty(result)
        assert momentum["label"] != "CONFIDENCE_DAMAGED"


# ===========================================================================
# 3. Try-scorer confidence
# ===========================================================================

class TestTryScorerConfidence:
    """Wing player on a team that scored 4+ tries in R1 = high-confidence FTS pick."""

    def _wing_player(self, in_squad=True, scored_r1=False, team="Ireland") -> PlayerRecord:
        return PlayerRecord(
            name="Test Wing", team=team, position="wing",
            in_squad=in_squad, scored_r1=scored_r1,
        )

    def _strong_r1(self, tries=5) -> TeamResult:
        return TeamResult(team="Ireland", opponent="Japan",
                          score_for=55, score_against=17, tries_scored=tries)

    def test_wing_team_4_plus_tries_r1_is_recommended(self):
        """Wing + team scored 4+ tries in R1 = recommended pick."""
        player = self._wing_player(scored_r1=True)
        result = self._strong_r1(tries=5)
        confidence = try_scorer_confidence(player, result)
        assert confidence["recommended"] is True

    def test_wing_not_in_squad_is_never_recommended(self):
        """Mandatory gate: player not in squad -> recommended=False regardless of signals."""
        player = self._wing_player(in_squad=False)
        result = self._strong_r1(tries=6)
        confidence = try_scorer_confidence(player, result)
        assert confidence["recommended"] is False
        assert confidence["signals_hit"] == 0

    def test_wing_team_4_plus_tries_r1_hits_multiple_signals(self):
        """Wing + 4+ tries + player scored in R1 + team won = >= 3 signals."""
        player = self._wing_player(scored_r1=True)
        result = self._strong_r1(tries=5)
        confidence = try_scorer_confidence(player, result)
        assert confidence["signals_hit"] >= 3

    def test_exactly_4_tries_triggers_bonus(self):
        """4 tries (not 5) is still sufficient to trigger the +2 bonus."""
        player = self._wing_player()
        result = self._strong_r1(tries=4)
        confidence = try_scorer_confidence(player, result)
        # wing (+1) + 4 tries (+2) + team won (+1) = 4 signals
        assert confidence["signals_hit"] >= 3

    def test_3_tries_not_enough_for_team_bonus(self):
        """3 tries in R1 does not trigger the +2 team bonus."""
        player = self._wing_player()
        result = TeamResult(team="Ireland", opponent="Japan",
                            score_for=20, score_against=10, tries_scored=3)
        confidence = try_scorer_confidence(player, result)
        # wing (+1) + team won (+1) = 2 signals only; not recommended
        assert confidence["signals_hit"] < 3
        assert confidence["recommended"] is False

    def test_non_wing_position_loses_one_signal(self):
        """Flanker (position 7) does not get the wing bonus."""
        player = PlayerRecord(name="Flanker", team="Ireland", position="flanker",
                              in_squad=True, scored_r1=True)
        result = self._strong_r1(tries=5)
        confidence = try_scorer_confidence(player, result)
        # 4+ tries (+2) + scored in R1 (+2) + team won (+1) = 5, still recommended
        # (the wing bonus is just missing)
        assert confidence["recommended"] is True
        # But if we compare to the wing version, signals should be 1 lower
        wing_player = self._wing_player(scored_r1=True)
        wing_confidence = try_scorer_confidence(wing_player, result)
        assert wing_confidence["signals_hit"] > confidence["signals_hit"]

    def test_squad_check_reason_message(self):
        """Not-in-squad picks must return a clear reason string."""
        player = self._wing_player(in_squad=False)
        result = self._strong_r1()
        confidence = try_scorer_confidence(player, result)
        assert "squad" in confidence["reason"].lower()


# ===========================================================================
# 4. Fatigue model
# ===========================================================================

class TestFatigueModel:
    """Player with 160+ minutes across 2 matches = rotation risk flag."""

    def test_160_minutes_triggers_rotation_risk(self):
        """Full 80 each game = 160 mins = ROTATION RISK."""
        player = PlayerRecord(name="Starter", team="Wales", position="wing",
                              minutes_r1=80, minutes_r2=80)
        result = fatigue_flag(player)
        assert result["rotation_risk"] is True

    def test_159_minutes_no_rotation_risk(self):
        """One minute below threshold = no risk."""
        player = PlayerRecord(name="Sub", team="Wales", position="wing",
                              minutes_r1=79, minutes_r2=80)
        result = fatigue_flag(player)
        assert result["rotation_risk"] is False
        assert result["margin_impact"] == 0

    def test_cumulative_minutes_is_sum(self):
        """cumulative_minutes must equal r1 + r2 minutes."""
        player = PlayerRecord(name="Player", team="England", position="8",
                              minutes_r1=70, minutes_r2=80)
        result = fatigue_flag(player)
        assert result["cumulative_minutes"] == 150

    def test_sa_nz_rotation_risk_smaller_margin_impact(self):
        """SA/NZ deep squads: margin impact is 3 pts (not 10)."""
        sa_player = PlayerRecord(name="SA Lock", team="South Africa", position="lock",
                                 minutes_r1=80, minutes_r2=80)
        nz_player = PlayerRecord(name="NZ Prop", team="New Zealand", position="prop",
                                 minutes_r1=80, minutes_r2=80)
        sa_result = fatigue_flag(sa_player)
        nz_result = fatigue_flag(nz_player)
        assert sa_result["rotation_risk"] is True
        assert sa_result["margin_impact"] == 3
        assert nz_result["margin_impact"] == 3

    def test_tier2_thin_squad_larger_margin_impact(self):
        """Wales (thin squad) player at 160+ mins = 10 pts margin impact."""
        player = PlayerRecord(name="Wales Wing", team="Wales", position="wing",
                              minutes_r1=80, minutes_r2=80)
        result = fatigue_flag(player)
        assert result["rotation_risk"] is True
        assert result["margin_impact"] == 10

    def test_zero_minutes_no_risk(self):
        """Unused player has no fatigue risk."""
        player = PlayerRecord(name="Unused Sub", team="Ireland", position="prop",
                              minutes_r1=0, minutes_r2=0)
        result = fatigue_flag(player)
        assert result["rotation_risk"] is False
        assert result["cumulative_minutes"] == 0

    def test_exactly_at_threshold(self):
        """Exactly 160 minutes should trigger rotation risk."""
        player = PlayerRecord(name="Edge Case", team="Scotland", position="fly-half",
                              minutes_r1=80, minutes_r2=80)
        assert player.cumulative_minutes == FATIGUE_MINUTES_THRESHOLD
        result = fatigue_flag(player)
        assert result["rotation_risk"] is True


# ===========================================================================
# 5. Upset detection
# ===========================================================================

class TestUpsetDetection:
    """3 consecutive wins at venue + opponent big loss = UPSET WATCH flag."""

    def _scotland_venue_record(self, wins: int) -> VenueRecord:
        """Scotland at Murrayfield with `wins` consecutive wins."""
        results = [True] * wins
        return VenueRecord(team="Scotland", venue="Murrayfield", results=results)

    def _argentina_big_loss(self) -> TeamResult:
        # Real score was 47-38 (9 pts) but for test purposes we use a 10-pt loss
        # to sit exactly on the threshold defined in the skill file (10+ pts).
        return TeamResult(team="Argentina", opponent="Scotland",
                          score_for=37, score_against=47)

    def test_all_conditions_met_raises_upset_watch(self):
        """Scotland (Tier 2) vs Argentina (Tier 1): 3 venue wins + Argentina lost by 10+ pts."""
        venue = self._scotland_venue_record(wins=3)
        fav_result = self._argentina_big_loss()
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=8,    # Scotland
            favourite_tier=6,   # Argentina
        )
        assert result["upset_watch"] is True
        assert result["conditions_met"] == 3

    def test_missing_venue_form_no_upset_watch(self):
        """Only 2 consecutive wins at venue — UPSET WATCH not raised."""
        venue = self._scotland_venue_record(wins=2)
        fav_result = self._argentina_big_loss()
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=8,
            favourite_tier=6,
        )
        assert result["upset_watch"] is False
        assert result["conditions_met"] < 3

    def test_favourite_won_last_match_no_upset_watch(self):
        """Favourite won their last match — no big-loss condition."""
        venue = self._scotland_venue_record(wins=3)
        fav_result = TeamResult(team="Argentina", opponent="Japan",
                                score_for=40, score_against=10)
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=8,
            favourite_tier=6,
        )
        assert result["upset_watch"] is False

    def test_underdog_actually_higher_tier_no_upset_watch(self):
        """If 'underdog' is actually higher-ranked, upset condition 1 fails."""
        venue = VenueRecord(team="Ireland", venue="Aviva", results=[True, True, True])
        fav_result = TeamResult(team="Japan", opponent="Italy",
                                score_for=10, score_against=40)
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=4,   # Ireland — stronger team
            favourite_tier=12, # Japan — weaker team
        )
        assert result["upset_watch"] is False

    def test_favourite_small_loss_below_threshold_no_upset_watch(self):
        """Favourite lost by only 5 pts — does not meet big-loss threshold (10 pts)."""
        venue = self._scotland_venue_record(wins=3)
        small_loss = TeamResult(team="Argentina", opponent="Scotland",
                                score_for=20, score_against=25)  # 5-pt loss
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=small_loss,
            underdog_tier=8,
            favourite_tier=6,
            big_loss_threshold=10,
        )
        assert result["upset_watch"] is False

    def test_exactly_3_wins_meets_condition(self):
        """Exactly 3 consecutive venue wins is sufficient."""
        venue = VenueRecord(team="Fiji", venue="Suva", results=[False, True, True, True])
        fav_result = TeamResult(team="England", opponent="South Africa",
                                score_for=21, score_against=45)
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=10,   # Fiji
            favourite_tier=5,   # England
        )
        assert result["upset_watch"] is True

    def test_conditions_met_count_correct(self):
        """conditions_met should count exactly how many of the 3 conditions are true."""
        # Only condition 1 (underdog tier) and condition 3 (big loss) are met
        venue = self._scotland_venue_record(wins=0)  # 0 venue wins
        fav_result = self._argentina_big_loss()
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=8,
            favourite_tier=6,
        )
        assert result["conditions_met"] == 2

    def test_reason_string_is_populated(self):
        """Result always includes a human-readable reason string."""
        venue = self._scotland_venue_record(wins=3)
        fav_result = self._argentina_big_loss()
        result = upset_watch(
            underdog_venue_record=venue,
            favourite_last_result=fav_result,
            underdog_tier=8,
            favourite_tier=6,
        )
        assert len(result["reason"]) > 0
