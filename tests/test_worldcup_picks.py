"""
tests/test_worldcup_picks.py

Unit tests for worldcup_picks.py pure-logic functions.
No AWS mocks required — all functions operate on plain Python dicts.

Run with:  pytest tests/test_worldcup_picks.py -v
"""

import pytest
import sys
import os

# Allow importing from repo root without an install step
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worldcup_picks import (
    momentum_score,
    goal_dominance_signal,
    stage_form_weight,
    stage_group_result_weight,
    stage_fatigue_weight,
    outright_value_flag,
    should_skip_match_bet,
    confidence_tier,
)


# ── momentum_score ────────────────────────────────────────────────────────────

class TestMomentumScore:

    def test_big_win_three_plus_goals(self):
        """France 4-0 → dominant, highest score."""
        match = {'outcome': 'win', 'goal_margin': 4,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == 3

    def test_big_win_exactly_three_goals(self):
        match = {'outcome': 'win', 'goal_margin': 3,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == 3

    def test_convincing_win_two_goals(self):
        """Spain 2-0 → convincing but not dominant."""
        match = {'outcome': 'win', 'goal_margin': 2,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == 2

    def test_tight_win_one_goal_early(self):
        """England 1-0 (goal at 35') → efficient, score +1."""
        match = {'outcome': 'win', 'goal_margin': 1,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == 1

    def test_late_winner_does_not_reward(self):
        """Mexico 1-0 (goal at 87') → lucky, score 0."""
        match = {'outcome': 'win', 'goal_margin': 1,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': True}
        assert momentum_score(match) == 0

    def test_extra_time_win(self):
        """Team wins in AET but not pens → -1 (fatigue)."""
        match = {'outcome': 'win', 'goal_margin': 1,
                 'via_extra_time': True, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == -1

    def test_penalty_shootout_win(self):
        """Switzerland beat Colombia on pens → -2 (worst momentum)."""
        match = {'outcome': 'win', 'goal_margin': 0,
                 'via_extra_time': True, 'via_penalties': True, 'late_winner': False}
        assert momentum_score(match) == -2

    def test_penalties_score_lower_than_aet(self):
        """Penalties must always be worse than AET."""
        aet_match   = {'outcome': 'win', 'goal_margin': 1,
                       'via_extra_time': True, 'via_penalties': False, 'late_winner': False}
        pens_match  = {'outcome': 'win', 'goal_margin': 0,
                       'via_extra_time': True, 'via_penalties': True, 'late_winner': False}
        assert momentum_score(pens_match) < momentum_score(aet_match)

    def test_big_win_beats_penalties(self):
        """Dominant win vs penalty win should be 5+ points apart in signal strength."""
        big_win  = {'outcome': 'win', 'goal_margin': 4,
                    'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        pens_win = {'outcome': 'win', 'goal_margin': 0,
                    'via_extra_time': True, 'via_penalties': True, 'late_winner': False}
        assert momentum_score(big_win) - momentum_score(pens_win) >= 5

    def test_draw_returns_zero(self):
        """Draws are neutral — shouldn't arise at KO stage but must be handled."""
        match = {'outcome': 'draw', 'goal_margin': 0,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == 0

    def test_loss_returns_zero(self):
        """Losses won't appear in KO stage picks but function should not raise."""
        match = {'outcome': 'loss', 'goal_margin': 0,
                 'via_extra_time': False, 'via_penalties': False, 'late_winner': False}
        assert momentum_score(match) == 0

    def test_missing_keys_do_not_raise(self):
        """Minimal dict (only 'outcome') should not raise KeyError."""
        match = {'outcome': 'win'}
        result = momentum_score(match)
        assert isinstance(result, int)


# ── goal_dominance_signal ─────────────────────────────────────────────────────

class TestGoalDominanceSignal:

    def test_zero_goals_scored_red_flag(self):
        """Team with 0 goals scored — never back with HIGH confidence."""
        assert goal_dominance_signal(0, 0) == 'RED_FLAG'

    def test_zero_goals_scored_with_conceded(self):
        """0 goals for regardless of goals against → RED_FLAG."""
        assert goal_dominance_signal(0, 3) == 'RED_FLAG'

    def test_dominant_gd_eight_plus(self):
        assert goal_dominance_signal(10, 1) == 'CLASS'   # GD +9

    def test_dominant_gd_exactly_eight(self):
        assert goal_dominance_signal(9, 1) == 'CLASS'    # GD +8

    def test_strong_gd_four_to_seven(self):
        assert goal_dominance_signal(7, 2) == 'STRONG'   # GD +5

    def test_strong_gd_exactly_four(self):
        assert goal_dominance_signal(5, 1) == 'STRONG'   # GD +4

    def test_normal_gd_one_to_three(self):
        assert goal_dominance_signal(3, 2) == 'NORMAL'   # GD +1

    def test_zero_gd_concern(self):
        """Team that scored but also conceded same number → CONCERN."""
        assert goal_dominance_signal(3, 3) == 'CONCERN'  # GD 0

    def test_negative_gd_concern(self):
        """Teams that concede more than they score → CONCERN."""
        assert goal_dominance_signal(2, 4) == 'CONCERN'  # GD -2

    def test_all_draws_gd_zero(self):
        """Team that drew every game — 0-0, 0-0, 0-0 — zero goals, GD 0."""
        assert goal_dominance_signal(0, 0) == 'RED_FLAG'


# ── stage weighting ───────────────────────────────────────────────────────────

class TestStageWeighting:

    def test_qf_form_weight_higher_than_r16(self):
        """QF should weight recent form more heavily than R16."""
        assert stage_form_weight('qf') > stage_form_weight('r16')

    def test_sf_form_weight_highest(self):
        """SF/Final should have the highest form multiplier."""
        assert stage_form_weight('sf') >= stage_form_weight('qf')

    def test_final_form_weight_equals_sf(self):
        assert stage_form_weight('final') == stage_form_weight('sf')

    def test_qf_discounts_group_result(self):
        """QF group-result weight must be significantly less than R16."""
        assert stage_group_result_weight('qf') < stage_group_result_weight('r16')

    def test_sf_ignores_group_result(self):
        """SF and Final should give zero weight to group-stage results."""
        assert stage_group_result_weight('sf') == 0.0
        assert stage_group_result_weight('final') == 0.0

    def test_group_stage_has_lower_form_weight_than_qf(self):
        assert stage_form_weight('group') < stage_form_weight('qf')

    def test_fatigue_weight_increases_at_qf(self):
        """Fatigue flags should be more impactful at QF than R16."""
        assert stage_fatigue_weight('qf') > stage_fatigue_weight('r16')

    def test_fatigue_weight_highest_at_sf_final(self):
        assert stage_fatigue_weight('sf') >= stage_fatigue_weight('qf')
        assert stage_fatigue_weight('final') >= stage_fatigue_weight('qf')

    def test_unknown_stage_returns_safe_default(self):
        """Unknown stage string should not raise and should return >= 1.0."""
        assert stage_form_weight('banana_round') >= 1.0


# ── outright_value_flag ───────────────────────────────────────────────────────

class TestOutrightValueFlag:

    def test_sf_team_at_four_to_one_is_value(self):
        """Norway at 5.0 decimal in SF → OUTRIGHT_VALUE."""
        assert outright_value_flag('Norway', 'sf', 5.0) == 'OUTRIGHT_VALUE'

    def test_sf_team_exactly_four_decimal(self):
        """Boundary: 4.0 decimal (3/1) in SF → OUTRIGHT_VALUE."""
        assert outright_value_flag('Norway', 'sf', 4.0) == 'OUTRIGHT_VALUE'

    def test_sf_team_below_threshold_no_flag(self):
        """France at 1.8 in SF → no outright flag (not value)."""
        assert outright_value_flag('France', 'sf', 1.8) is None

    def test_final_team_at_three_decimal_value(self):
        """Argentina at 3.0 in Final → FINAL_VALUE_BET."""
        assert outright_value_flag('Argentina', 'final', 3.0) == 'FINAL_VALUE_BET'

    def test_final_team_below_threshold_no_flag(self):
        """France at 1.5 in Final → no flag."""
        assert outright_value_flag('France', 'final', 1.5) is None

    def test_qf_dark_horse_at_seven_plus(self):
        """Team at 7.0+ decimal in QF → UPSET_HOLD."""
        assert outright_value_flag('Ecuador', 'qf', 7.0) == 'UPSET_HOLD'

    def test_qf_moderate_odds_no_upset_flag(self):
        """Team at 4.0 in QF is not a dark horse — no UPSET_HOLD."""
        assert outright_value_flag('England', 'qf', 4.0) is None

    def test_r16_stage_never_flags_outright(self):
        """R16 is too early for outright value flags."""
        assert outright_value_flag('Spain', 'r16', 8.0) is None

    def test_group_stage_never_flags_outright(self):
        assert outright_value_flag('Japan', 'group', 10.0) is None


# ── should_skip_match_bet ─────────────────────────────────────────────────────

class TestShouldSkipMatchBet:

    def test_very_short_odds_skip(self):
        """1.25 decimal (1/4) → skip the match bet."""
        assert should_skip_match_bet(1.25) is True

    def test_boundary_exactly_1_5_not_skip(self):
        """1.5 is exactly at the threshold (skip only if strictly < 1.5) → do NOT skip."""
        assert should_skip_match_bet(1.5) is False

    def test_just_above_threshold_do_not_skip(self):
        """1.51 → consider the bet (just clears the threshold)."""
        assert should_skip_match_bet(1.51) is False

    def test_evens_always_bet(self):
        """2.0 (evens) is prime match-betting territory."""
        assert should_skip_match_bet(2.0) is False

    def test_underdog_odds_always_bet(self):
        """4.0 or higher odds → never skip on this criterion."""
        assert should_skip_match_bet(4.0) is False


# ── confidence_tier ───────────────────────────────────────────────────────────

class TestConfidenceTier:

    # -- QF-stage rules --

    def test_qf_high_confidence_requires_momentum(self):
        """At QF, 4 factors + good momentum + no fatigue → HIGH."""
        assert confidence_tier(4, 'qf', momentum=2, fatigue_flags=0) == 'HIGH'

    def test_qf_four_factors_no_momentum_not_high(self):
        """At QF, 4 factors but zero momentum → cannot be HIGH."""
        result = confidence_tier(4, 'qf', momentum=0, fatigue_flags=0)
        assert result in ('MEDIUM', 'SPECULATIVE')
        assert result != 'HIGH'

    def test_qf_four_factors_with_fatigue_not_high(self):
        """At QF, 4 factors + momentum but fatigue flag → drops to MEDIUM."""
        result = confidence_tier(4, 'qf', momentum=2, fatigue_flags=1)
        assert result != 'HIGH'

    def test_qf_three_factors_is_medium(self):
        assert confidence_tier(3, 'qf', momentum=0, fatigue_flags=0) == 'MEDIUM'

    def test_qf_two_factors_is_speculative(self):
        assert confidence_tier(2, 'qf', momentum=0, fatigue_flags=0) == 'SPECULATIVE'

    def test_qf_one_factor_is_speculative(self):
        assert confidence_tier(1, 'qf', momentum=1, fatigue_flags=0) == 'SPECULATIVE'

    # -- SF-stage rules --

    def test_sf_five_factors_no_fatigue_high(self):
        assert confidence_tier(5, 'sf', momentum=2, fatigue_flags=0) == 'HIGH'

    def test_sf_four_factors_medium(self):
        """SF requires 5+ factors for HIGH; 4 factors drops to MEDIUM."""
        assert confidence_tier(4, 'sf', momentum=1, fatigue_flags=0) == 'MEDIUM'

    # -- Pre-KO stage rules --

    def test_r16_four_factors_is_high(self):
        """R16 doesn't require momentum signal for HIGH."""
        assert confidence_tier(4, 'r16', momentum=0, fatigue_flags=0) == 'HIGH'

    def test_r16_three_factors_is_medium(self):
        assert confidence_tier(3, 'r16', momentum=0, fatigue_flags=0) == 'MEDIUM'

    def test_group_two_factors_is_medium(self):
        assert confidence_tier(2, 'group', momentum=0, fatigue_flags=0) == 'MEDIUM'

    def test_group_one_factor_is_speculative(self):
        assert confidence_tier(1, 'group', momentum=0, fatigue_flags=0) == 'SPECULATIVE'

    # -- Penalty-winner scenario (calibration rule 3) --

    def test_pens_winner_low_momentum_cannot_be_high(self):
        """A team that won on pens (momentum -2) should never achieve HIGH."""
        result = confidence_tier(5, 'qf', momentum=-2, fatigue_flags=1)
        assert result != 'HIGH'

    # -- Edge cases --

    def test_zero_factors_always_speculative(self):
        for stage in ('group', 'r16', 'qf', 'sf', 'final'):
            assert confidence_tier(0, stage, momentum=0, fatigue_flags=0) == 'SPECULATIVE'

    def test_result_is_always_valid_string(self):
        """confidence_tier must always return one of three valid strings."""
        valid = {'HIGH', 'MEDIUM', 'SPECULATIVE'}
        for factors in range(6):
            for stage in ('group', 'r16', 'qf', 'sf', 'final'):
                for momentum in (-2, 0, 1, 3):
                    for fatigue in (0, 1, 2):
                        result = confidence_tier(factors, stage, momentum, fatigue)
                        assert result in valid, (
                            f"Unexpected result '{result}' for "
                            f"factors={factors}, stage={stage}, "
                            f"momentum={momentum}, fatigue={fatigue}"
                        )
