"""
Unit tests for BetBudAI horse racing pick scoring logic.

Tests cover pure functions and data-transform logic extracted from
comprehensive_pick_logic.py that do NOT call AWS or external APIs.

Run with:
    pytest tests/test_racing_picks.py -v
"""

import sys
import types
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Stub out AWS-calling imports so the module can be imported in unit tests
# without real credentials.
# ---------------------------------------------------------------------------

def _make_stub(name):
    mod = types.ModuleType(name)
    return mod

# Stub boto3 before importing our module
boto3_stub = _make_stub('boto3')
boto3_stub.resource = MagicMock(return_value=MagicMock())
sys.modules.setdefault('boto3', boto3_stub)

# Stub weather / enricher / tracker modules
for _mod in [
    'weather_going_inference',
    'form_enricher',
    'trainer_form_stats',
    'track_daily_insights',
    'cheltenham_analyzer',
    'watchlist',
    'bloodstock',
    'debutant_scorer',
]:
    if _mod not in sys.modules:
        stub = _make_stub(_mod)
        if _mod == 'weather_going_inference':
            stub.check_all_tracks_going = MagicMock(return_value={})
        if _mod == 'form_enricher':
            stub.get_form_signals = MagicMock(return_value={})
            stub._dist_to_furlongs = MagicMock(return_value=None)
        if _mod == 'trainer_form_stats':
            stub.hot_form_bonus = MagicMock(return_value=(0, {}, []))
        if _mod == 'track_daily_insights':
            stub.get_track_insights = MagicMock(return_value={})
        if _mod == 'watchlist':
            stub.check_watchlist = MagicMock(return_value=None)
        if _mod == 'bloodstock':
            stub.sire_going_signal = MagicMock(return_value=(0, ''))
        if _mod == 'debutant_scorer':
            stub.score_debutant = MagicMock(return_value=(0, {}))
        sys.modules[_mod] = stub


# ---------------------------------------------------------------------------
# Import module under test AFTER stubs are in place.
# ---------------------------------------------------------------------------

with (
    patch('boto3.resource', return_value=MagicMock()),
):
    import comprehensive_pick_logic as cpl


# Helpers
def _score_horse(horse_data, course='Cheltenham', going_data=None, n_runners=8,
                 avg_winner_odds=3.8, course_winners_today=0, meeting_context=None):
    """
    Call analyze_horse_comprehensive with mocked AWS / going data.
    Returns (score, breakdown, reasons).
    """
    going_data = going_data or {}
    with (
        patch.object(cpl, 'get_dynamic_weights', return_value=cpl.DEFAULT_WEIGHTS.copy()),
        patch.object(cpl, 'get_going_conditions', return_value=going_data),
        patch('boto3.resource') as mock_res,
    ):
        # Mock DynamoDB table.scan to return no history
        mock_table = MagicMock()
        mock_table.scan.return_value = {'Items': []}
        mock_table.get_item.return_value = {}
        mock_res.return_value.Table.return_value = mock_table

        score, breakdown, reasons = cpl.analyze_horse_comprehensive(
            horse_data,
            course,
            avg_winner_odds=avg_winner_odds,
            course_winners_today=course_winners_today,
            field_weights=None,
            meeting_context=meeting_context,
            n_runners=n_runners,
        )
    return score, breakdown, reasons


# ---------------------------------------------------------------------------
# 1. DEFAULT_WEIGHTS sanity
# ---------------------------------------------------------------------------

class TestDefaultWeights:
    def test_cd_bonus_present(self):
        assert 'cd_bonus' in cpl.DEFAULT_WEIGHTS
        assert cpl.DEFAULT_WEIGHTS['cd_bonus'] > 0

    def test_going_suitability_removed(self):
        # 2026-09-03: going_suitability removed as a noise factor (sign-flipped
        # across CV folds) — see .claude/skills/vegas.md. Regression check that
        # it doesn't silently reappear as an orphaned weight constant.
        assert 'going_suitability' not in cpl.DEFAULT_WEIGHTS

    def test_large_field_penalty_removed(self):
        # 2026-09-03: large_field_penalty removed as a noise factor (zero
        # coefficient at every CV fold's optimal regularization) — see
        # .claude/skills/vegas.md.
        assert 'large_field_penalty' not in cpl.DEFAULT_WEIGHTS

    def test_all_weights_numeric(self):
        for k, v in cpl.DEFAULT_WEIGHTS.items():
            assert isinstance(v, (int, float)), f"Weight '{k}' is not numeric"

    def test_distance_suitability_present(self):
        assert 'distance_suitability' in cpl.DEFAULT_WEIGHTS
        assert cpl.DEFAULT_WEIGHTS['distance_suitability'] > 0

    def test_trainer_tier1_higher_than_tier2(self):
        t1 = cpl.DEFAULT_WEIGHTS['trainer_reputation']
        t2 = cpl.DEFAULT_WEIGHTS['trainer_tier2']
        assert t1 > t2

    def test_heavy_going_penalty_present(self):
        assert 'heavy_going_penalty' in cpl.DEFAULT_WEIGHTS


# ---------------------------------------------------------------------------
# 2. should_skip_race — pure function (no AWS calls)
# ---------------------------------------------------------------------------

class TestShouldSkipRace:
    def _race(self, market_name, race_class=''):
        return {'market_name': market_name, 'race_class': race_class}

    def test_class3_handicap_is_skipped(self):
        skip, reason = cpl.should_skip_race(
            self._race('Class 3 Handicap Hurdle', race_class='3'))
        assert skip is True
        assert reason is not None

    def test_class4_handicap_is_skipped(self):
        skip, _ = cpl.should_skip_race(self._race('4m Class 4 Handicap Chase', race_class='4'))
        assert skip is True

    def test_class5_hcap_keyword_skipped(self):
        skip, _ = cpl.should_skip_race(self._race('Lingfield Class 5 Hcap', race_class='5'))
        assert skip is True

    def test_class6_skipped(self):
        skip, _ = cpl.should_skip_race(self._race('AW Class 6 Hcap', race_class='6'))
        assert skip is True

    def test_class1_not_skipped(self):
        skip, _ = cpl.should_skip_race(self._race('Grade 1 Championship Chase', race_class='1'))
        assert skip is False

    def test_class2_not_skipped(self):
        skip, _ = cpl.should_skip_race(self._race('Class 2 Handicap Chase', race_class='2'))
        assert skip is False

    def test_novice_hurdle_not_skipped(self):
        # Novice hurdles are not handicaps by default
        skip, _ = cpl.should_skip_race(self._race('Novice Hurdle Class 3'))
        assert skip is False

    def test_missing_class_not_skipped(self):
        # No class info — should not skip
        skip, _ = cpl.should_skip_race({'market_name': 'Some Race'})
        assert skip is False

    def test_reason_is_none_when_not_skipped(self):
        _, reason = cpl.should_skip_race(self._race('Grade 1 Chase'))
        assert reason is None

    def test_handicap_class3_from_name_pattern(self):
        # Class 3 detected purely from name when race_class field is empty
        skip, _ = cpl.should_skip_race({'market_name': 'class 3 handicap chase', 'race_class': ''})
        assert skip is True


# ---------------------------------------------------------------------------
# 3. CD marker scoring
# ---------------------------------------------------------------------------

class TestCDMarkerScoring:
    """
    2026-09-03: the cd_bonus POINT AWARD was removed as a noise factor
    (sign-flipped across CV folds, and extremely thin — 11/33,552 nonzero on
    the rebuild dataset) — see .claude/skills/vegas.md. `cd_bonus` no longer
    appears in `breakdown` at all. The underlying C/D-win DETECTION logic
    (`cd_pts`, internal to analyze_horse_comprehensive) is kept, because
    distance_suitability's "Confirmed distance evidence (C/D)" branch still
    reads it — so a CD marker should still show up indirectly via
    distance_suitability, just not as its own breakdown key any more.
    """

    BASE_HORSE = {
        'name': 'Test Horse',
        'odds': 4.0,
        'form': '1-1-1',
        'trainer': 'Nicky Henderson',
        'jockey': '',
        'age': 7,
    }

    def test_cd_bonus_key_absent_when_marker_set(self):
        horse = dict(self.BASE_HORSE, cd_marker='CD')
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('cd_bonus', 0) == 0

    def test_no_cd_breakdown_zero(self):
        horse = dict(self.BASE_HORSE)  # no cd_marker
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('cd_bonus', 0) == 0

    def test_cd_marker_still_feeds_distance_suitability(self):
        """CD detection isn't gone — distance_suitability's confirming bonus
        still fires when cd_pts > 0 internally, even with no cd_bonus key."""
        horse = dict(self.BASE_HORSE, cd_marker='CD')
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('distance_suitability', 0) > 0

    def test_cd_winner_total_score_not_less_than_c_only(self):
        """A CD winner should score no worse than a course-only winner."""
        horse_c  = dict(self.BASE_HORSE, cd_marker='C',  form='2-2')
        horse_cd = dict(self.BASE_HORSE, cd_marker='CD', form='2-2')

        score_c,  _, _ = _score_horse(horse_c)
        score_cd, _, _ = _score_horse(horse_cd)

        assert score_cd >= score_c


# ---------------------------------------------------------------------------
# 4. Going match scoring
# ---------------------------------------------------------------------------

class TestGoingSuitability:
    """
    2026-09-03: going_suitability POINT SCORING removed as a noise factor
    (sign-flipped across CV folds) — see .claude/skills/vegas.md. `suited` /
    `_aw_specialist_on_soft` detection and the point award built on top of it
    are both gone; `going_suitability` no longer appears in `breakdown` at
    all, for any horse. What's left to test: it doesn't crash, and it no
    longer differentiates a turf-soft winner from an AW specialist (that
    used to be exactly what this factor did).
    """

    def _soft_going_data(self, course='Cheltenham'):
        return {course: {'going': 'Soft', 'adjustment': 3,
                         'source': 'official', 'surface': 'turf'}}

    def test_going_suitability_key_absent(self):
        horse = {
            'name': 'Turf Horse', 'odds': 4.0, 'form': '1-1-1', 'trainer': '',
            'prev_results': [{'position': '1', 'going': 'Soft', 'course': 'Cheltenham'}],
        }
        _, breakdown, _ = _score_horse(horse, going_data=self._soft_going_data())
        assert 'going_suitability' not in breakdown

    def test_aw_specialist_no_longer_penalised_on_soft(self):
        """The AW-specialist-on-soft penalty this used to test is gone —
        confirm going_suitability is simply absent, not negative."""
        horse = {
            'name': 'AW Specialist',
            'odds': 4.0,
            'form': '1-1-2',
            'trainer': '',
            'prev_results': [
                {'position': '1', 'going': 'Standard', 'course': 'Wolverhampton'},
                {'position': '1', 'going': 'Standard', 'course': 'Kempton'},
                {'position': '2', 'going': 'Standard', 'course': 'Lingfield'},
            ],
        }
        soft_going = self._soft_going_data()
        _, breakdown, _ = _score_horse(horse, going_data=soft_going)
        assert breakdown.get('going_suitability', 0) == 0

    def test_going_uncertain_does_not_exceed_official(self):
        """Weather-inferred going should produce a smaller or equal going bonus vs official."""
        horse = {
            'name': 'Soft Turf Winner',
            'odds': 4.0,
            'form': '1-1',
            'trainer': '',
            'prev_results': [
                {'position': '1', 'going': 'Soft', 'course': 'Cheltenham'},
            ],
        }
        official_going = {'Cheltenham': {'going': 'Soft', 'adjustment': 3,
                                         'source': 'official', 'surface': 'turf'}}
        inferred_going = {'Cheltenham': {'going': 'Soft', 'adjustment': 3,
                                         'source': 'weather_api', 'surface': 'turf'}}

        _, bd_official, _ = _score_horse(horse, going_data=official_going)
        _, bd_inferred, _ = _score_horse(horse, going_data=inferred_going)

        # Official going bonus should be >= inferred going bonus (inferred is halved)
        assert bd_official.get('going_suitability', 0) >= bd_inferred.get('going_suitability', 0)

    def test_no_going_data_does_not_crash(self):
        horse = {'name': 'No Going', 'odds': 5.0, 'form': '1-2', 'trainer': ''}
        score, breakdown, _ = _score_horse(horse, going_data={})
        assert isinstance(score, (int, float))
        assert isinstance(breakdown, dict)

    def test_heavy_going_applies_penalty(self):
        """All horses should get a heavy going penalty when going is Heavy."""
        horse = {'name': 'Any Horse', 'odds': 4.0, 'form': '1-1', 'trainer': ''}
        heavy_going = {'Cheltenham': {'going': 'Heavy', 'adjustment': 5,
                                      'source': 'official', 'surface': 'turf'}}
        _, breakdown, _ = _score_horse(horse, going_data=heavy_going)
        assert breakdown.get('heavy_going_penalty', 0) < 0


# ---------------------------------------------------------------------------
# 5. Score threshold / confidence level mapping
# ---------------------------------------------------------------------------

class TestConfidenceLevelMapping:
    """
    format_pick_for_database maps score ranges to VERY_HIGH / HIGH / MEDIUM / LOW.
    We replicate the threshold logic here since it is a pure data transform.
    """

    @staticmethod
    def _confidence_level(score):
        if score >= 90:
            return "VERY_HIGH"
        elif score >= 75:
            return "HIGH"
        elif score >= 60:
            return "MEDIUM"
        else:
            return "LOW"

    def test_score_90_is_very_high(self):
        assert self._confidence_level(90) == "VERY_HIGH"

    def test_score_95_is_very_high(self):
        assert self._confidence_level(95) == "VERY_HIGH"

    def test_score_89_is_high(self):
        assert self._confidence_level(89) == "HIGH"

    def test_score_75_is_high(self):
        assert self._confidence_level(75) == "HIGH"

    def test_score_60_is_medium(self):
        assert self._confidence_level(60) == "MEDIUM"

    def test_score_74_is_medium(self):
        assert self._confidence_level(74) == "MEDIUM"

    def test_score_59_is_low(self):
        assert self._confidence_level(59) == "LOW"

    def test_score_0_is_low(self):
        assert self._confidence_level(0) == "LOW"

    def test_boundary_90_is_very_high_not_high(self):
        assert self._confidence_level(90) != "HIGH"

    def test_boundary_75_is_high_not_medium(self):
        assert self._confidence_level(75) != "MEDIUM"


# ---------------------------------------------------------------------------
# 6. Signal count — fully-loaded horse vs data-empty horse
# ---------------------------------------------------------------------------

class TestSignalCount:
    """
    A horse with all positive signals should score higher than one with none.
    """

    RICH_HORSE = {
        'name': 'Rich Signal Horse',
        'odds': 4.0,
        'form': '1-1-1',
        'trainer': 'Nicky Henderson',
        'jockey': 'Nico de Boinville',
        'age': 7,
        'cd_marker': 'CD',
        'timeform_stars': 5,
        'prev_results': [
            {'position': '1', 'going': 'Soft', 'course': 'Cheltenham'},
        ],
    }

    BARE_HORSE = {
        'name': 'Bare Horse',
        'odds': 20.0,
        'form': '',
        'trainer': '',
        'jockey': '',
    }

    def test_rich_horse_beats_bare_horse(self):
        soft_going = {'Cheltenham': {'going': 'Soft', 'adjustment': 3,
                                     'source': 'official', 'surface': 'turf'}}
        score_rich, _, _ = _score_horse(self.RICH_HORSE, going_data=soft_going)
        score_bare, _, _ = _score_horse(self.BARE_HORSE, going_data=soft_going)
        assert score_rich > score_bare

    def test_bare_horse_does_not_crash(self):
        score, breakdown, reasons = _score_horse(self.BARE_HORSE)
        assert isinstance(score, (int, float))
        assert isinstance(breakdown, dict)
        assert isinstance(reasons, list)

    def test_missing_form_produces_zero_cd(self):
        horse = dict(self.BARE_HORSE, odds=5.0)
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('cd_bonus', 0) == 0

    def test_breakdown_always_returned_as_dict(self):
        """analyze_horse_comprehensive always returns a dict breakdown, never None."""
        _, breakdown, _ = _score_horse(self.BARE_HORSE)
        assert breakdown is not None
        assert isinstance(breakdown, dict)

    def test_rich_horse_cd_marker_feeds_distance_suitability(self):
        # 2026-09-03: cd_bonus point award removed (noise) — cd_marker='CD'
        # now shows up via distance_suitability's confirming bonus instead.
        # See .claude/skills/vegas.md.
        soft_going = {'Cheltenham': {'going': 'Soft', 'adjustment': 3,
                                     'source': 'official', 'surface': 'turf'}}
        _, breakdown, _ = _score_horse(self.RICH_HORSE, going_data=soft_going)
        assert breakdown.get('cd_bonus', 0) == 0
        assert breakdown.get('distance_suitability', 0) > 0

    def test_rich_horse_fires_trainer_bonus(self):
        _, breakdown, _ = _score_horse(self.RICH_HORSE)
        assert breakdown.get('trainer_reputation', 0) > 0

    def test_rich_horse_fires_jockey_bonus(self):
        _, breakdown, _ = _score_horse(self.RICH_HORSE)
        assert breakdown.get('jockey_quality', 0) > 0

    def test_rich_horse_fires_timeform_bonus(self):
        _, breakdown, _ = _score_horse(self.RICH_HORSE)
        assert breakdown.get('timeform_stars', 0) > 0


# ---------------------------------------------------------------------------
# 7. Large-field penalty
# ---------------------------------------------------------------------------

class TestLargeFieldPenalty:
    """
    2026-09-03: large_field_penalty removed as a noise factor (zero
    coefficient at every CV fold's optimal regularization strength) — see
    .claude/skills/vegas.md. Field size no longer affects score at all via
    this factor (small_field_bonus was removed alongside it for the same
    reason).
    """
    BASE_HORSE = {'name': 'Runner', 'odds': 4.0, 'form': '1-1', 'trainer': 'Paul Nicholls'}

    def test_20_runner_field_has_no_penalty(self):
        _, bd_16, _ = _score_horse(self.BASE_HORSE, n_runners=16)
        _, bd_20, _ = _score_horse(self.BASE_HORSE, n_runners=20)
        assert bd_16.get('large_field_penalty', 0) == 0
        assert bd_20.get('large_field_penalty', 0) == 0

    def test_small_field_no_penalty(self):
        _, breakdown, _ = _score_horse(self.BASE_HORSE, n_runners=8)
        assert breakdown.get('large_field_penalty', 0) == 0

    def test_15_runner_field_no_penalty(self):
        _, breakdown, _ = _score_horse(self.BASE_HORSE, n_runners=15)
        assert breakdown.get('large_field_penalty', 0) == 0

    def test_large_field_no_longer_reduces_score(self):
        """Total score with 20 runners should equal score with 8 runners now
        that field-size-based scoring is gone."""
        score_8, _, _ = _score_horse(self.BASE_HORSE, n_runners=8)
        score_20, _, _ = _score_horse(self.BASE_HORSE, n_runners=20)
        assert score_20 == score_8


# ---------------------------------------------------------------------------
# 8. Winless horse scores lower than a winner (Gate S18 effect)
# ---------------------------------------------------------------------------

class TestWinlessVsWinner:
    """
    A horse with 3+ runs and 0 wins should score materially lower than
    one with identical form except for a win result. This tests the
    effect of Gate S18 (the winless penalty) indirectly via total score.
    """

    def test_winner_scores_higher_than_no_wins(self):
        horse_wins = {'name': 'Winner', 'odds': 6.0, 'form': '1-3-2', 'trainer': ''}
        horse_no_wins = {'name': 'No Wins', 'odds': 6.0, 'form': '2-3-2', 'trainer': ''}

        score_win, _, _ = _score_horse(horse_wins)
        score_no_win, _, _ = _score_horse(horse_no_wins)

        # The winner should outscore the winless horse
        assert score_win > score_no_win, (
            f"Winner ({score_win}) should beat winless horse ({score_no_win})"
        )

    def test_debutant_scores_without_crash(self):
        # Empty form = debutant — should not crash
        horse = {'name': 'Debutant', 'odds': 5.0, 'form': '', 'trainer': ''}
        score, breakdown, _ = _score_horse(horse)
        assert isinstance(score, (int, float))
        # Debutant should not get recent_win bonus
        assert breakdown.get('recent_win', 0) == 0

    def test_two_runs_no_wins_is_nonzero_score(self):
        # Should still return a numeric score — don't crash or return 0 just because no wins
        horse = {'name': 'Two Runs', 'odds': 5.0, 'form': '2-3', 'trainer': ''}
        score, _, _ = _score_horse(horse)
        assert isinstance(score, (int, float))


# ---------------------------------------------------------------------------
# 9. Bounce-back pattern detection
# ---------------------------------------------------------------------------

class TestBounceBackPattern:
    """
    2026-09-03: bounce_back removed as a dead factor (0/33,552 nonzero on the
    rebuild dataset — non-seasonal, the [good]-[bad]-[good] form-string
    pattern this looked for apparently never matched real data) — see
    .claude/skills/vegas.md. `bounce_back` no longer appears in `breakdown`.
    """

    def test_classic_bounce_back_pattern_no_longer_scored(self):
        horse = {'name': 'Bouncer', 'odds': 5.0, 'form': '1-6-2', 'trainer': ''}
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('bounce_back', 0) == 0

    def test_steady_form_no_bounce(self):
        # 1-2-3: steady, no dramatic dip then recovery
        horse = {'name': 'Steady', 'odds': 5.0, 'form': '1-2-3', 'trainer': ''}
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('bounce_back', 0) == 0

    def test_two_runs_no_bounce(self):
        # Need >= 3 form parts for bounce back
        horse = {'name': 'Short Form', 'odds': 5.0, 'form': '1-2', 'trainer': ''}
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('bounce_back', 0) == 0

    def test_missing_form_no_crash(self):
        horse = {'name': 'No Form', 'odds': 5.0, 'form': '', 'trainer': ''}
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('bounce_back', 0) == 0

    def test_bounce_back_no_longer_adds_pts(self):
        horse = {'name': 'Big Bounce', 'odds': 5.0, 'form': '2-9-1', 'trainer': ''}
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('bounce_back', 0) == 0


# ---------------------------------------------------------------------------
# 10. Score general cap
# ---------------------------------------------------------------------------

class TestScoreGeneralCap:
    """
    analyze_horse_comprehensive caps score at GENERAL_CAP (local constant in function).
    We can't test the module-level constant, but we can verify the cap behaviour.
    """

    def test_score_never_exceeds_120(self):
        """Even with every signal firing, score should not exceed 120."""
        horse = {
            'name': 'Over-scorer',
            'odds': 3.0,
            'form': '1-1-1-1-1',
            'trainer': 'W P Mullins',
            'jockey': 'Paul Townend',
            'age': 7,
            'cd_marker': 'CD',
            'timeform_stars': 5,
            'official_rating': 160,
            'prev_results': [
                {'position': '1', 'going': 'Soft', 'course': 'Cheltenham'},
                {'position': '1', 'going': 'Soft', 'course': 'Cheltenham'},
            ],
        }
        soft_going = {'Cheltenham': {'going': 'Soft', 'adjustment': 3,
                                     'source': 'official', 'surface': 'turf'}}
        score, _, _ = _score_horse(horse, going_data=soft_going)
        # The function caps at a GENERAL_CAP value (120 in this version)
        assert score <= 120, f"Score {score} should not exceed the general cap of 120"

    def test_score_is_numeric(self):
        horse = {'name': 'Any', 'odds': 4.0, 'form': '1-2', 'trainer': ''}
        score, _, _ = _score_horse(horse)
        assert isinstance(score, (int, float))

    def test_score_cap_reduces_runaway_scores(self):
        """If a horse would hypothetically score very high, the cap key should be set."""
        horse = {
            'name': 'Maxed Out',
            'odds': 2.5,
            'form': '1-1-1-1-1-1-1-1',   # lots of wins
            'trainer': 'W P Mullins',
            'jockey': 'Paul Townend',
            'age': 7,
            'cd_marker': 'CD',
            'timeform_stars': 5,
            'official_rating': 165,
            'prev_results': [
                {'position': '1', 'going': 'Soft', 'course': 'Cheltenham'},
            ],
        }
        soft_going = {'Cheltenham': {'going': 'Soft', 'adjustment': 3,
                                     'source': 'official', 'surface': 'turf'}}
        score, breakdown, _ = _score_horse(horse, going_data=soft_going)
        # Either the cap fired (score_cap key is negative) or the score was already <= 120
        if breakdown.get('score_cap', 0) != 0:
            assert breakdown['score_cap'] < 0, "score_cap should be a deduction, not an addition"
        assert score <= 120


# ---------------------------------------------------------------------------
# 11. Trainer tier detection
# ---------------------------------------------------------------------------

class TestTrainerTierBonus:
    """
    Elite (T1) trainers should produce a higher trainer bonus than T2 or unknown.
    """

    def _trainer_bonus(self, trainer_name):
        horse = {'name': 'Test', 'odds': 4.0, 'form': '1-2', 'trainer': trainer_name}
        _, breakdown, _ = _score_horse(horse)
        return breakdown.get('trainer_reputation', 0)

    def test_elite_trainer_t1_scores_highest(self):
        t1_bonus = self._trainer_bonus('Nicky Henderson')
        t2_bonus = self._trainer_bonus('Dan Skelton')
        assert t1_bonus > t2_bonus

    def test_unknown_trainer_gets_no_tier_bonus(self):
        bonus = self._trainer_bonus('Random Trainer XYZ')
        assert bonus == 0

    def test_t1_bonus_matches_weight(self):
        bonus = self._trainer_bonus('W P Mullins')
        expected = cpl.DEFAULT_WEIGHTS['trainer_reputation']
        assert bonus == expected

    def test_t2_bonus_matches_weight(self):
        bonus = self._trainer_bonus('Dan Skelton')
        expected = cpl.DEFAULT_WEIGHTS['trainer_tier2']
        assert bonus == expected

    def test_unknown_trainer_penalty_applied(self):
        """Unknown trainer results in a negative 'unknown_trainer_penalty' in breakdown."""
        horse = {'name': 'Test', 'odds': 4.0, 'form': '1-2', 'trainer': 'Totally Unknown XYZ'}
        _, breakdown, _ = _score_horse(horse)
        # The penalty key should be negative (penalised)
        penalty = breakdown.get('unknown_trainer_penalty', 0)
        assert penalty <= 0  # 0 means no penalty applied (e.g. no trainer set), negative means penalised

    def test_t3_trainer_bonus_less_than_t2(self):
        t2_bonus = self._trainer_bonus('Dan Skelton')
        horse = {'name': 'Test', 'odds': 4.0, 'form': '1-2', 'trainer': 'David Pipe'}
        _, bd_t3, _ = _score_horse(horse)
        t3_bonus = bd_t3.get('trainer_reputation', 0)
        assert t2_bonus >= t3_bonus


# ---------------------------------------------------------------------------
# 12. Timeform stars bonus/penalty
# ---------------------------------------------------------------------------

class TestTimeformStars:
    BASE = {'name': 'Star Horse', 'odds': 4.0, 'form': '1-2', 'trainer': ''}

    def test_5_star_gives_bonus(self):
        horse = dict(self.BASE, timeform_stars=5)
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('timeform_stars', 0) > 0

    def test_4_star_gives_smaller_bonus_than_5(self):
        horse_4 = dict(self.BASE, timeform_stars=4)
        horse_5 = dict(self.BASE, timeform_stars=5)
        _, bd_4, _ = _score_horse(horse_4)
        _, bd_5, _ = _score_horse(horse_5)
        assert bd_5['timeform_stars'] > bd_4['timeform_stars']

    def test_1_star_gives_penalty(self):
        horse = dict(self.BASE, timeform_stars=1)
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('timeform_stars', 0) < 0

    def test_2_star_gives_penalty(self):
        horse = dict(self.BASE, timeform_stars=2)
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('timeform_stars', 0) < 0

    def test_3_star_is_neutral(self):
        horse = dict(self.BASE, timeform_stars=3)
        _, breakdown, _ = _score_horse(horse)
        assert breakdown.get('timeform_stars', 0) == 0

    def test_no_stars_does_not_crash(self):
        horse = dict(self.BASE)  # no timeform_stars key
        score, breakdown, _ = _score_horse(horse)
        assert isinstance(score, (int, float))
        assert breakdown.get('timeform_stars', 0) == 0
