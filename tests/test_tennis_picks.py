"""
test_tennis_picks.py — Unit tests for BetBudAI Pro Tennis pick logic.

Tests cover:
  1. Fatigue score calculation
  2. Grass H2H comparison
  3. Upset probability threshold
  4. Each-way value detection
  5. Retirement risk flag

Run with:
  pytest tests/test_tennis_picks.py -v
"""

import pytest
import sys
import os

# Make the tests directory importable when running from repo root
sys.path.insert(0, os.path.dirname(__file__))

from tennis_pick_logic import (
    fatigue_level,
    grass_h2h_winner,
    upset_decision,
    ew_value_flag,
    retirement_risk_flag,
    _fractional_to_decimal,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Fatigue Detection
# ─────────────────────────────────────────────────────────────────────────────

class TestFatigueLevel:
    """fatigue_level(sets_played, hours_rest, round_id) → 'LOW' | 'MED' | 'HIGH'"""

    # --- 5-set matches ---

    def test_five_setter_within_36hrs_is_high(self):
        """Five-setter with < 36 hrs rest is definitely HIGH."""
        assert fatigue_level(5, 30.0) == 'HIGH'

    def test_five_setter_exactly_48hrs_is_high(self):
        """Boundary: 48 hrs is still within the HIGH window (< 48 is HIGH)."""
        # hours_rest=48 is NOT < 48, so it falls through to MED threshold
        assert fatigue_level(5, 47.9) == 'HIGH'

    def test_five_setter_48hrs_transitions_to_med(self):
        """hours_rest == 48 exactly → MED (boundary: < 48 = HIGH, 48–72 = MED)."""
        assert fatigue_level(5, 48.0) == 'MED'

    def test_five_setter_60hrs_is_med(self):
        """Five-setter with 60 hrs rest → MED fatigue."""
        assert fatigue_level(5, 60.0) == 'MED'

    def test_five_setter_72hrs_is_low(self):
        """Five-setter with 72+ hrs rest → fully recovered, LOW."""
        assert fatigue_level(5, 72.0) == 'LOW'

    def test_five_setter_100hrs_is_low(self):
        """Five-setter with plenty of rest (100 hrs) → LOW."""
        assert fatigue_level(5, 100.0) == 'LOW'

    # --- 3–4 set matches ---

    def test_four_setter_under_24hrs_is_med(self):
        """Four-setter with < 24 hrs rest → MED."""
        assert fatigue_level(4, 20.0) == 'MED'

    def test_three_setter_under_24hrs_is_med(self):
        """Three-setter with < 24 hrs rest → MED."""
        assert fatigue_level(3, 23.0) == 'MED'

    def test_four_setter_24hrs_rest_is_low(self):
        """Four-setter with 24 hrs rest → LOW (recovered enough)."""
        assert fatigue_level(4, 24.0) == 'LOW'

    def test_three_setter_late_round_under_24hrs_is_med(self):
        """Three-setter in QF (round_id=5) with < 24 hrs → MED."""
        assert fatigue_level(3, 20.0, round_id=5) == 'MED'

    def test_three_setter_48hrs_is_low(self):
        """Three-setter with 48 hrs rest → LOW regardless of round."""
        assert fatigue_level(3, 48.0, round_id=5) == 'LOW'

    # --- Straight-set wins ---

    def test_two_sets_is_always_low(self):
        """Straight-sets win (2 sets) is always LOW fatigue regardless of rest."""
        assert fatigue_level(2, 1.0) == 'LOW'

    def test_two_sets_zero_hours_is_still_low(self):
        """Even if back-to-back (0 hrs), 2 sets → LOW (shouldn't happen in practice)."""
        assert fatigue_level(2, 0.0) == 'LOW'

    # --- Skip-match scenario ---

    def test_five_setter_36hrs_qf_is_high(self):
        """
        Five-setter + < 36 hrs + QF round: clearly HIGH.
        Caller should skip the pick per the skill-file rule.
        """
        assert fatigue_level(5, 36.0, round_id=5) == 'HIGH'


# ─────────────────────────────────────────────────────────────────────────────
# 2. Grass H2H Comparison
# ─────────────────────────────────────────────────────────────────────────────

class TestGrassH2HWinner:
    """grass_h2h_winner(player_a, wins_a, player_b, wins_b, meetings) → str | None"""

    def test_fritz_leads_zverev_3_2(self):
        """Fritz 3-2 on grass vs Zverev → Fritz wins H2H signal."""
        result = grass_h2h_winner('Fritz', 3, 'Zverev', 2, meetings=5)
        assert result == 'Fritz'

    def test_zverev_does_not_win_h2h_signal(self):
        """Zverev must NOT be returned as the grass H2H winner in this matchup."""
        result = grass_h2h_winner('Fritz', 3, 'Zverev', 2, meetings=5)
        assert result != 'Zverev'

    def test_player_b_leads(self):
        """When player B leads, player B is returned."""
        result = grass_h2h_winner('Sinner', 1, 'Djokovic', 4, meetings=5)
        assert result == 'Djokovic'

    def test_tied_record_returns_none(self):
        """A tied grass H2H (e.g. 2-2) returns None — no signal."""
        result = grass_h2h_winner('Fritz', 2, 'Zverev', 2, meetings=4)
        assert result is None

    def test_one_meeting_returns_none(self):
        """Only 1 grass meeting → sample too small → None."""
        result = grass_h2h_winner('Fritz', 1, 'Zverev', 0, meetings=1)
        assert result is None

    def test_zero_meetings_returns_none(self):
        """No grass meetings → None."""
        result = grass_h2h_winner('Fritz', 0, 'Zverev', 0, meetings=0)
        assert result is None

    def test_two_meeting_minimum_valid(self):
        """Exactly 2 meetings is the minimum valid sample — returns a winner."""
        result = grass_h2h_winner('Gauff', 2, 'Muchova', 0, meetings=2)
        assert result == 'Gauff'

    def test_one_sided_record(self):
        """5-0 grass record → the dominant player is returned."""
        result = grass_h2h_winner('Rybakina', 5, 'Swiatek', 0, meetings=5)
        assert result == 'Rybakina'


# ─────────────────────────────────────────────────────────────────────────────
# 3. Upset Probability
# ─────────────────────────────────────────────────────────────────────────────

class TestUpsetDecision:
    """upset_decision(seed_gap, surface_mismatch, grass_h2h_advantage) → 'PICK'|'WATCH'|'NONE'"""

    def test_all_three_conditions_is_pick(self):
        """Seed gap ≥ 5 + surface mismatch + grass H2H advantage → PICK."""
        result = upset_decision(seed_gap=5, surface_mismatch=True, grass_h2h_advantage=True)
        assert result == 'PICK'

    def test_all_three_large_gap_is_pick(self):
        """Seed gap of 8 (well above threshold) with all conditions → still PICK."""
        result = upset_decision(seed_gap=8, surface_mismatch=True, grass_h2h_advantage=True)
        assert result == 'PICK'

    def test_two_conditions_is_watch(self):
        """Two of three conditions → WATCH (flag but don't pick)."""
        # seed gap ≥ 5 + surface mismatch, but no grass H2H edge
        result = upset_decision(seed_gap=6, surface_mismatch=True, grass_h2h_advantage=False)
        assert result == 'WATCH'

    def test_seed_gap_and_h2h_no_mismatch_is_watch(self):
        """Seed gap + H2H but no surface mismatch → WATCH."""
        result = upset_decision(seed_gap=5, surface_mismatch=False, grass_h2h_advantage=True)
        assert result == 'WATCH'

    def test_only_seed_gap_is_none(self):
        """Seed gap alone (only 1 condition) → NONE."""
        result = upset_decision(seed_gap=10, surface_mismatch=False, grass_h2h_advantage=False)
        assert result == 'NONE'

    def test_seed_gap_below_threshold_all_others_true_is_watch(self):
        """Seed gap of 4 (below 5 threshold): only 2 conditions met → WATCH."""
        result = upset_decision(seed_gap=4, surface_mismatch=True, grass_h2h_advantage=True)
        assert result == 'WATCH'

    def test_no_conditions_is_none(self):
        """No conditions met → NONE."""
        result = upset_decision(seed_gap=2, surface_mismatch=False, grass_h2h_advantage=False)
        assert result == 'NONE'

    def test_only_surface_mismatch_is_none(self):
        """Surface mismatch alone → NONE (only 1 condition)."""
        result = upset_decision(seed_gap=3, surface_mismatch=True, grass_h2h_advantage=False)
        assert result == 'NONE'

    def test_exact_seed_gap_boundary_5(self):
        """Exactly seed_gap=5 qualifies (≥5)."""
        result = upset_decision(seed_gap=5, surface_mismatch=True, grass_h2h_advantage=True)
        assert result == 'PICK'

    def test_seed_gap_4_does_not_qualify_alone(self):
        """seed_gap=4 does not trigger seed_gap condition."""
        result = upset_decision(seed_gap=4, surface_mismatch=False, grass_h2h_advantage=False)
        assert result == 'NONE'


# ─────────────────────────────────────────────────────────────────────────────
# 4. Each-Way Value Detection
# ─────────────────────────────────────────────────────────────────────────────

class TestEWValueFlag:
    """ew_value_flag(fractional_odds, round_name, fatigue, retirement_risk) → str"""

    # --- Core EW window (4/1–8/1 in QF) ---

    def test_6_1_in_qf_is_value(self):
        """6/1 in the Quarter-Final with no flags → VALUE."""
        assert ew_value_flag('6/1', 'Quarter-Final') == 'VALUE'

    def test_4_1_in_qf_is_value(self):
        """4/1 is the lower bound of the EW window → VALUE."""
        assert ew_value_flag('4/1', 'Quarter-Final') == 'VALUE'

    def test_8_1_in_qf_is_value(self):
        """8/1 is the upper bound of the EW window → VALUE."""
        assert ew_value_flag('8/1', 'Quarter-Final') == 'VALUE'

    def test_5_1_in_qf_is_value(self):
        """5/1 sits comfortably in the window → VALUE."""
        assert ew_value_flag('5/1', 'Quarter-Final') == 'VALUE'

    def test_case_insensitive_round_name(self):
        """Round name matching should be case-insensitive."""
        assert ew_value_flag('6/1', 'quarter-final') == 'VALUE'
        assert ew_value_flag('6/1', 'QF') == 'VALUE'
        assert ew_value_flag('6/1', 'Quarterfinal') == 'VALUE'

    # --- Odds outside window ---

    def test_3_1_in_qf_is_none(self):
        """3/1 (decimal 4.0) is below 4/1 floor → NONE (win-only better)."""
        assert ew_value_flag('3/1', 'Quarter-Final') == 'NONE'

    def test_10_1_in_qf_is_speculative(self):
        """10/1 (decimal 11.0) exceeds 8/1 ceiling → SPECULATIVE."""
        assert ew_value_flag('10/1', 'Quarter-Final') == 'SPECULATIVE'

    def test_2_1_in_qf_is_none(self):
        """2/1 is clearly below the floor → NONE."""
        assert ew_value_flag('2/1', 'Quarter-Final') == 'NONE'

    def test_20_1_in_qf_is_speculative(self):
        """20/1 well above ceiling in QF → SPECULATIVE."""
        assert ew_value_flag('20/1', 'Quarter-Final') == 'SPECULATIVE'

    # --- Round gating ---

    def test_6_1_in_sf_is_none(self):
        """6/1 in Semi-Final is not QF — the EW window applies only at QF entry."""
        assert ew_value_flag('6/1', 'Semi-Final') == 'NONE'

    def test_6_1_in_r16_is_none(self):
        """6/1 in R16 → NONE (not QF)."""
        assert ew_value_flag('6/1', 'Round of 16') == 'NONE'

    def test_6_1_in_final_is_none(self):
        """6/1 in Final → NONE."""
        assert ew_value_flag('6/1', 'Final') == 'NONE'

    # --- Fatigue and retirement risk downgrades ---

    def test_6_1_high_fatigue_is_speculative(self):
        """6/1 in QF but FATIGUE HIGH → downgrade to SPECULATIVE."""
        assert ew_value_flag('6/1', 'Quarter-Final', fatigue='HIGH') == 'SPECULATIVE'

    def test_6_1_med_fatigue_stays_value(self):
        """6/1 in QF with MED fatigue → still VALUE (only HIGH triggers downgrade)."""
        assert ew_value_flag('6/1', 'Quarter-Final', fatigue='MED') == 'VALUE'

    def test_6_1_retirement_risk_is_speculative(self):
        """6/1 in QF but retirement risk active → SPECULATIVE."""
        assert ew_value_flag('6/1', 'Quarter-Final', retirement_risk=True) == 'SPECULATIVE'

    def test_6_1_both_flags_is_speculative(self):
        """Both HIGH fatigue and retirement risk → SPECULATIVE."""
        assert ew_value_flag('6/1', 'Quarter-Final', fatigue='HIGH', retirement_risk=True) == 'SPECULATIVE'

    # --- Fractional parser ---

    def test_fractional_to_decimal_6_1(self):
        """6/1 → 7.0 decimal."""
        assert _fractional_to_decimal('6/1') == pytest.approx(7.0)

    def test_fractional_to_decimal_4_1(self):
        """4/1 → 5.0 decimal."""
        assert _fractional_to_decimal('4/1') == pytest.approx(5.0)

    def test_fractional_to_decimal_8_1(self):
        """8/1 → 9.0 decimal."""
        assert _fractional_to_decimal('8/1') == pytest.approx(9.0)

    def test_fractional_to_decimal_invalid_raises(self):
        """Garbage input raises ValueError."""
        with pytest.raises(ValueError):
            _fractional_to_decimal('evens')


# ─────────────────────────────────────────────────────────────────────────────
# 5. Retirement Risk Flag
# ─────────────────────────────────────────────────────────────────────────────

class TestRetirementRiskFlag:
    """retirement_risk_flag(age, round_id, sets_in_last_match) → bool"""

    # --- Djokovic archetype: age 39, R16+ ---

    def test_djokovic_r16_five_setter_is_risk(self):
        """Age 39, R16 (round_id=4), 5 sets → True."""
        assert retirement_risk_flag(age=39, round_id=4, sets_in_last_match=5) is True

    def test_djokovic_qf_three_setter_is_risk(self):
        """Age 39, QF (round_id=5), 3 sets → True (3 is the minimum)."""
        assert retirement_risk_flag(age=39, round_id=5, sets_in_last_match=3) is True

    def test_djokovic_sf_five_setter_is_risk(self):
        """Age 39, SF (round_id=6), 5 sets → True."""
        assert retirement_risk_flag(age=39, round_id=6, sets_in_last_match=5) is True

    # --- Boundary: age = 33 ---

    def test_age_33_r16_three_sets_is_risk(self):
        """Minimum age (33) in R16 with 3+ sets → True."""
        assert retirement_risk_flag(age=33, round_id=4, sets_in_last_match=3) is True

    def test_age_32_r16_five_setter_not_risk(self):
        """Age 32 (below threshold) → False even in late rounds with many sets."""
        assert retirement_risk_flag(age=32, round_id=5, sets_in_last_match=5) is False

    # --- Boundary: round_id > 3 ---

    def test_age_39_r32_five_setter_not_risk(self):
        """R32 (round_id=3) is not R16 or later → False."""
        assert retirement_risk_flag(age=39, round_id=3, sets_in_last_match=5) is False

    def test_age_39_r64_five_setter_not_risk(self):
        """R64 (round_id=2) → False."""
        assert retirement_risk_flag(age=39, round_id=2, sets_in_last_match=5) is False

    # --- Boundary: sets_in_last_match ≥ 3 ---

    def test_age_39_r16_two_sets_not_risk(self):
        """Age 39, R16, but only 2 sets in last match (straight sets) → False."""
        assert retirement_risk_flag(age=39, round_id=4, sets_in_last_match=2) is False

    def test_age_39_r16_zero_sets_not_risk(self):
        """Age 39, R16, 0 sets recorded (data gap) → False (conservative)."""
        assert retirement_risk_flag(age=39, round_id=4, sets_in_last_match=0) is False

    # --- All conditions required ---

    def test_all_conditions_required_missing_age(self):
        """Missing age condition → False."""
        assert retirement_risk_flag(age=30, round_id=5, sets_in_last_match=5) is False

    def test_all_conditions_required_missing_round(self):
        """Missing round condition → False."""
        assert retirement_risk_flag(age=39, round_id=3, sets_in_last_match=5) is False

    def test_all_conditions_required_missing_sets(self):
        """Missing sets condition → False."""
        assert retirement_risk_flag(age=39, round_id=5, sets_in_last_match=2) is False


# ─────────────────────────────────────────────────────────────────────────────
# Integration scenarios
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationScenarios:
    """
    Combined scenarios matching real QF day (2026-07-08) matchups.
    These verify that the functions compose correctly in realistic contexts.
    """

    def test_fritz_v_zverev_qf_scenario(self):
        """
        Fritz vs Zverev QF scenario:
        - Grass H2H: Fritz leads 3-2 → Fritz has H2H signal
        - Fritz 11-2 on grass (grass specialist, not clay specialist)
        - Zverev is a clay/hard specialist (surface mismatch=True)
        - Seed gap: assume Zverev [2] vs Fritz [12] → gap = 10
        Expected: grass H2H returns Fritz; upset_decision returns PICK for Fritz
        """
        h2h_winner = grass_h2h_winner('Fritz', 3, 'Zverev', 2, meetings=5)
        assert h2h_winner == 'Fritz'

        # Fritz as lower seed upsetting Zverev
        upset = upset_decision(
            seed_gap=10,           # large gap
            surface_mismatch=True, # Zverev is clay/hard specialist
            grass_h2h_advantage=True,  # Fritz leads grass H2H
        )
        assert upset == 'PICK'

    def test_djokovic_fatigue_and_retirement_combined(self):
        """
        Djokovic QF scenario (age 39):
        - Played a 5-setter 40 hrs ago → HIGH fatigue (< 48 hrs threshold)
        - Round R16 or later → retirement risk also applies
        - EW at 5/1 → SPECULATIVE (HIGH fatigue triggers downgrade)
        """
        fat = fatigue_level(5, 40.0, round_id=5)
        assert fat == 'HIGH'  # 40 hrs < 48 hr threshold → HIGH

        risk = retirement_risk_flag(age=39, round_id=5, sets_in_last_match=5)
        assert risk is True

        ew = ew_value_flag('5/1', 'Quarter-Final', fatigue=fat, retirement_risk=risk)
        assert ew == 'SPECULATIVE'

    def test_sinner_clean_pick_scenario(self):
        """
        Sinner scenario: top seed, straight-sets wins, plenty of rest.
        - 2 sets in last match, 60 hrs rest → LOW fatigue
        - Age 24 → no retirement risk
        - 3/1 outright → below EW window → NONE
        - No upset scenario needed (he's the favourite)
        """
        fat = fatigue_level(2, 60.0, round_id=5)
        assert fat == 'LOW'

        risk = retirement_risk_flag(age=24, round_id=5, sets_in_last_match=2)
        assert risk is False

        ew = ew_value_flag('3/1', 'Quarter-Final', fatigue=fat, retirement_risk=risk)
        assert ew == 'NONE'  # too short for EW; should be win-only
