"""
test_golf_picks.py — pytest unit tests for golf pick selection logic.

Tests correspond to rules in .claude/skills/pick-golf.md Sections A-D.
Run with: pytest tests/test_golf_picks.py -v
"""

import pytest
import sys
import os

# Make the tests directory importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.dirname(__file__))

from golf_pick_logic import (
    PlayerProfile,
    LINKS_FIT_SIGNALS,
    ARCHETYPE_MODIFIERS,
    course_fit_score,
    links_fit_label,
    wind_impact,
    wind_bucket,
    cut_line_midpoint,
    cut_probability,
    ew_viable,
    r1_adjustment,
    r3_adjustment,
    ew_value_flag,
)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def links_specialist():
    """Tommy Fleetwood-style player: 8 links signals, links_specialist archetype."""
    return PlayerProfile(
        name="Tommy Fleetwood",
        signals=[
            "previous_top10_open_venue",
            "low_ball_flight",
            "driving_accuracy_over_62",
            "sand_save_over_58",
            "won_or_top5_scottish_irish_open",
            "grew_up_links_country",
            "ryder_cup_wins_uk_ireland",
            "strong_wind_short_game",
        ],
        archetype="links_specialist",
        odds=26.0,   # 25/1
        ryder_cup_windy_record=True,
        major_wins=0,
    )


@pytest.fixture
def course_debutant():
    """US parkland specialist: 1 links signal, course_debutant archetype."""
    return PlayerProfile(
        name="Parkland Pro",
        signals=["driving_accuracy_over_62"],
        archetype="course_debutant",
        odds=12.0,   # 11/1
        ryder_cup_windy_record=False,
        major_wins=1,
    )


@pytest.fixture
def links_risk_player():
    """High-spin player with no links credentials."""
    return PlayerProfile(
        name="Spin King",
        signals=[],
        archetype="links_risk",
        odds=8.0,    # 7/1
        ryder_cup_windy_record=False,
        major_wins=0,
    )


@pytest.fixture
def short_priced_favourite():
    """World number 1 — links form adequate but odds too short."""
    return PlayerProfile(
        name="Scottie Scheffler",
        signals=[
            "previous_top10_open_venue",
            "low_ball_flight",
        ],
        archetype="parkland_bomber",
        odds=4.5,    # ~7/2
        ryder_cup_windy_record=False,
        major_wins=2,
    )


@pytest.fixture
def longshot_links_specialist():
    """Unknown links specialist: 4 signals, 20/1 price."""
    return PlayerProfile(
        name="Robert MacIntyre",
        signals=[
            "previous_top10_open_venue",
            "grew_up_links_country",
            "won_or_top5_scottish_irish_open",
            "strong_wind_short_game",
        ],
        archetype="links_adjacent",
        odds=21.0,   # 20/1
        ryder_cup_windy_record=True,
        major_wins=0,
    )


# ===========================================================================
# Section A — Course-fit scoring
# ===========================================================================

class TestCourseFitScore:

    def test_links_specialist_high_score(self, links_specialist):
        """8 signals + 25 modifier = 33 — well above HIGH FIT threshold."""
        score = course_fit_score(links_specialist)
        assert score >= 28, f"Expected HIGH FIT score (>=28), got {score}"

    def test_links_specialist_label(self, links_specialist):
        score = course_fit_score(links_specialist)
        label = links_fit_label(score)
        assert label == "HIGH FIT"

    def test_course_debutant_low_score(self, course_debutant):
        """1 signal + (-5) modifier = -4 — LOW FIT or LINKS RISK."""
        score = course_fit_score(course_debutant)
        assert score < 5, f"Expected low score (< 5), got {score}"

    def test_course_debutant_label(self, course_debutant):
        score = course_fit_score(course_debutant)
        label = links_fit_label(score)
        assert label in ("LOW FIT", "LINKS RISK")

    def test_links_risk_negative_score(self, links_risk_player):
        """No signals + (-15) modifier = -15 — must return LINKS RISK label."""
        score = course_fit_score(links_risk_player)
        assert score < 0
        assert links_fit_label(score) == "LINKS RISK"

    def test_no_archetype_signals_only(self):
        """Player with 5 signals but no archetype: score = 5, HIGH FIT threshold."""
        player = PlayerProfile(
            name="Signal Only",
            signals=LINKS_FIT_SIGNALS[:5],
            archetype=None,
            odds=20.0,
        )
        score = course_fit_score(player)
        assert score == 5
        assert links_fit_label(score) == "HIGH FIT"

    def test_all_signals_links_specialist(self):
        """10 signals + 25 modifier = 35."""
        player = PlayerProfile(
            name="McIlroy",
            signals=LINKS_FIT_SIGNALS,
            archetype="links_specialist",
            odds=6.0,
        )
        assert course_fit_score(player) == 35

    def test_parkland_bomber_medium_fit(self):
        """2 signals + 5 modifier = 7 — above HIGH FIT threshold of 5."""
        player = PlayerProfile(
            name="Dustin Johnson",
            signals=["low_ball_flight", "driving_accuracy_over_62"],
            archetype="parkland_bomber",
            odds=15.0,
        )
        score = course_fit_score(player)
        assert score == 7
        # 7 >= 5 -> HIGH FIT (parkland bomber with two genuine links signals)
        assert links_fit_label(score) == "HIGH FIT"


# ===========================================================================
# Section B — Wind impact
# ===========================================================================

class TestWindImpact:

    def test_calm_no_adjustment(self, short_priced_favourite):
        """< 10 mph: no wind rules fire — weights and cut line unchanged."""
        result = wind_impact(short_priced_favourite, wind_mph=5.0, base_ew_confidence="HIGH")
        assert result["ew_confidence"] == "HIGH"
        assert result["favourite_discounted"] is False
        assert result["longshot_upgraded"] is False
        assert result["accuracy_weight"] == 3
        assert result["distance_weight"] == 5
        assert result["cut_line_adjustment"] == 0

    def test_windy_favourite_discount(self, short_priced_favourite):
        """
        Wind > 15 mph + odds < 6.0 -> favourite discount fires.
        Confidence tier should drop by one.
        """
        result = wind_impact(short_priced_favourite, wind_mph=20.0, base_ew_confidence="HIGH")
        assert result["favourite_discounted"] is True
        assert result["ew_confidence"] == "MEDIUM"   # HIGH -> MEDIUM

    def test_windy_favourite_discount_already_medium(self, short_priced_favourite):
        """Starting at MEDIUM with favourite discount -> LOW."""
        result = wind_impact(short_priced_favourite, wind_mph=20.0, base_ew_confidence="MEDIUM")
        assert result["ew_confidence"] == "LOW"

    def test_windy_longshot_uplift(self, longshot_links_specialist):
        """
        Wind > 15 mph + odds >= 16 + 3+ links signals -> longshot uplift fires.
        Confidence tier should rise by one.
        """
        result = wind_impact(longshot_links_specialist, wind_mph=18.0, base_ew_confidence="MEDIUM")
        assert result["longshot_upgraded"] is True
        assert result["ew_confidence"] == "HIGH"   # MEDIUM -> HIGH

    def test_windy_longshot_no_uplift_too_few_signals(self, links_risk_player):
        """Longshot odds but zero signals — uplift must NOT fire."""
        links_risk_player.odds = 21.0
        result = wind_impact(links_risk_player, wind_mph=20.0, base_ew_confidence="MEDIUM")
        assert result["longshot_upgraded"] is False

    def test_windy_accuracy_weight_increases(self, longshot_links_specialist):
        """Wind > 15 mph: accuracy weight 8, distance weight 1."""
        result = wind_impact(longshot_links_specialist, wind_mph=22.0)
        assert result["accuracy_weight"] == 8
        assert result["distance_weight"] == 1

    def test_extreme_wind_cut_line_adjustment(self, links_specialist):
        """Wind > 25 mph: cut_line_adjustment = 4."""
        result = wind_impact(links_specialist, wind_mph=30.0)
        assert result["cut_line_adjustment"] == 4

    def test_windy_cut_line_adjustment(self, links_specialist):
        """Wind 15-25 mph: cut_line_adjustment = 2."""
        result = wind_impact(links_specialist, wind_mph=20.0)
        assert result["cut_line_adjustment"] == 2


# ===========================================================================
# Section C — Cut line prediction
# ===========================================================================

class TestCutLinePrediction:

    def test_cut_line_calm(self):
        """Calm conditions: cut line midpoint = -4."""
        assert cut_line_midpoint(5.0) == -4.0

    def test_cut_line_windy(self):
        """Windy conditions (15-25 mph): midpoint = 2."""
        assert cut_line_midpoint(20.0) == 2.0

    def test_cut_line_extreme(self):
        """Extreme wind: midpoint = 5."""
        assert cut_line_midpoint(28.0) == 5.0

    def test_cut_probability_certain_qualifier(self):
        """Player at -10 vs par in calm (cut line -4): margin = -6 < -4 -> 0.95."""
        prob = cut_probability(-10, wind_mph=5.0)
        assert prob == pytest.approx(0.95)

    def test_cut_probability_borderline(self):
        """Player at 0 vs par in windy (cut line ~2): margin = -2, bucket 70-90% -> 0.80."""
        prob = cut_probability(0, wind_mph=20.0)
        assert prob == pytest.approx(0.80)

    def test_cut_probability_likely_miss(self):
        """Player at +5 vs par in windy (cut line ~2): margin = +3 > 1 -> 0.30."""
        prob = cut_probability(5, wind_mph=20.0)
        assert prob == pytest.approx(0.30)

    def test_cut_probability_borderline_zone(self):
        """Player at even par in calm (cut line -4): margin = +4 > 1 -> 0.30."""
        prob = cut_probability(0, wind_mph=5.0)
        assert prob == pytest.approx(0.30)

    def test_ew_viable_good_links_longshot(self, links_specialist):
        """
        Links specialist at 25/1, projected -4 in breezy conditions:
        cut probability > 0.55, links signals >= 2 -> EW viable.
        """
        assert ew_viable(links_specialist, projected_36hole_score=-4, wind_mph=12.0)

    def test_ew_not_viable_short_odds(self, short_priced_favourite):
        """Decimal odds 4.5 (< 13.0): never EW value per skill file edge principle."""
        assert not ew_viable(short_priced_favourite, projected_36hole_score=-5, wind_mph=5.0)

    def test_ew_not_viable_cut_risk(self, links_specialist):
        """
        Even with links signals, if cut probability < 0.40 (score far over par)
        the EW bet is flagged as not viable.
        """
        # Calm cut line = -4, player at +4 -> margin = +8 -> 0.30 probability
        assert not ew_viable(links_specialist, projected_36hole_score=4, wind_mph=5.0)

    def test_ew_not_viable_too_few_signals(self, course_debutant):
        """Only 1 links signal at 11/1 odds — not viable."""
        assert not ew_viable(course_debutant, projected_36hole_score=-3, wind_mph=10.0)


# ===========================================================================
# Section D — In-tournament triggers
# ===========================================================================

class TestInTournamentTriggers:

    # --- After Round 1 ---

    def test_r1_upgrade(self):
        assert r1_adjustment(-5) == "UPGRADE"
        assert r1_adjustment(-6) == "UPGRADE"

    def test_r1_hold_on_leaderboard(self):
        assert r1_adjustment(-3) == "HOLD"
        assert r1_adjustment(-4) == "HOLD"

    def test_r1_hold_mid_pack(self):
        assert r1_adjustment(-1) == "HOLD"
        assert r1_adjustment(-2) == "HOLD"

    def test_r1_caution_even_par(self):
        assert r1_adjustment(0) == "CAUTION"

    def test_r1_downgrade(self):
        assert r1_adjustment(1) == "DOWNGRADE"
        assert r1_adjustment(2) == "DOWNGRADE"

    def test_r1_cut_flag(self):
        assert r1_adjustment(3) == "CUT_FLAG"
        assert r1_adjustment(5) == "CUT_FLAG"

    # --- After Round 3 (54-hole position) ---

    def test_r3_upgrade_leader(self):
        assert r3_adjustment(shots_off_lead=0, has_major_win=True) == "UPGRADE"
        assert r3_adjustment(shots_off_lead=0, has_major_win=False) == "UPGRADE"

    def test_r3_hold_close(self):
        assert r3_adjustment(shots_off_lead=1, has_major_win=True) == "HOLD"
        assert r3_adjustment(shots_off_lead=3, has_major_win=False) == "HOLD"

    def test_r3_speculative_hold_with_major_win(self):
        """4-6 shots back but has major win history -> SPECULATIVE_HOLD."""
        assert r3_adjustment(shots_off_lead=4, has_major_win=True) == "SPECULATIVE_HOLD"
        assert r3_adjustment(shots_off_lead=6, has_major_win=True) == "SPECULATIVE_HOLD"

    def test_r3_close_without_major_win(self):
        """4-6 shots back, no major win -> close the position."""
        assert r3_adjustment(shots_off_lead=5, has_major_win=False) == "CLOSE"

    def test_r3_close_too_far_back(self):
        """7+ shots back always close regardless of pedigree."""
        assert r3_adjustment(shots_off_lead=7, has_major_win=True) == "CLOSE"
        assert r3_adjustment(shots_off_lead=10, has_major_win=False) == "CLOSE"


# ===========================================================================
# EW Value Flag (combined Section A + B logic)
# ===========================================================================

class TestEWValueFlag:

    def test_ew_flag_fleetwood_calm(self, links_specialist):
        """
        Fleetwood: 8 signals, 25/1, calm conditions, projected -4.
        All criteria met -> EW VALUE flag.
        """
        assert ew_value_flag(
            links_specialist,
            wind_mph=5.0,
            projected_36hole_score=-4,
        )

    def test_ew_flag_fleetwood_windy(self, links_specialist):
        """Same player in windy conditions — should still flag."""
        assert ew_value_flag(
            links_specialist,
            wind_mph=20.0,
            projected_36hole_score=-2,
        )

    def test_no_ew_flag_short_odds(self, short_priced_favourite):
        """Odds 4.5 (< 16.0) — no EW VALUE flag."""
        assert not ew_value_flag(
            short_priced_favourite,
            wind_mph=5.0,
            projected_36hole_score=-5,
        )

    def test_no_ew_flag_too_long_odds(self, links_specialist):
        """Odds 35.0 (> 31.0) — outside EW VALUE range."""
        links_specialist.odds = 35.0
        assert not ew_value_flag(
            links_specialist,
            wind_mph=5.0,
            projected_36hole_score=-4,
        )

    def test_no_ew_flag_too_few_signals(self, course_debutant):
        """Course debutant: 1 signal, 11/1 — no flag."""
        course_debutant.odds = 18.0
        assert not ew_value_flag(
            course_debutant,
            wind_mph=5.0,
            projected_36hole_score=-3,
        )

    def test_ew_flag_longshot_specialist(self, longshot_links_specialist):
        """
        Robert MacIntyre type: 4 links signals at 20/1.
        In calm conditions with solid 36-hole projection -> EW VALUE.
        """
        assert ew_value_flag(
            longshot_links_specialist,
            wind_mph=8.0,
            projected_36hole_score=-3,
        )

    def test_no_ew_flag_cut_risk(self, links_specialist):
        """
        Even the links specialist does not get an EW flag if projected
        score puts them as a strong cut-miss risk.
        """
        # Calm cut line = -4, at +3 -> margin = +7 -> cut probability 0.30
        assert not ew_value_flag(
            links_specialist,
            wind_mph=5.0,
            projected_36hole_score=3,
        )

    def test_mcilroy_not_ew_value(self):
        """
        McIlroy at 6/1 is outright value, not EW value (odds too short for EW range).
        """
        mcilroy = PlayerProfile(
            name="Rory McIlroy",
            signals=LINKS_FIT_SIGNALS,  # all 10 signals
            archetype="links_specialist",
            odds=7.0,   # 6/1 — below 16.0 minimum
            ryder_cup_windy_record=True,
            major_wins=5,
        )
        assert not ew_value_flag(mcilroy, wind_mph=10.0, projected_36hole_score=-5)
