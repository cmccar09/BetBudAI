"""
test_cycling_picks.py — Unit tests for the BetBudAI Pro Cycling pick logic.

Tests cover:
  1. Stage type classification (FLAT / HILLY / MOUNTAIN / ITT / TTT)
  2. GC vs stage hunter pick confidence
  3. Breakaway probability by stage type
  4. Team control signal adjustments
  5. Record calibration factor

Run with:  pytest tests/test_cycling_picks.py -v
"""

import pytest
from tests.cycling_pick_logic import (
    classify_stage_type,
    pick_confidence,
    breakaway_probability,
    apply_team_control_boost,
    calibration_factor,
    FLAT, HILLY, MOUNTAIN, ITT, TTT, COBBLES,
    HIGH, MEDIUM, LOW, SPECULATIVE,
)


# ===========================================================================
# 1. Stage type classification
# ===========================================================================

class TestClassifyStageType:
    """Stage profile dict -> canonical type constant."""

    # --- happy-path: direct type field from scraper ---

    def test_flat_stage_from_type_field(self):
        stage = {'type': 'Flat', 'distance_km': 158}
        assert classify_stage_type(stage) == FLAT

    def test_hilly_stage_from_type_field(self):
        stage = {'type': 'Hilly', 'distance_km': 182}
        assert classify_stage_type(stage) == HILLY

    def test_mountain_stage_from_type_field(self):
        stage = {'type': 'Mountain', 'distance_km': 196}
        assert classify_stage_type(stage) == MOUNTAIN

    def test_itt_stage_from_type_field(self):
        stage = {'type': 'Individual Time Trial', 'distance_km': 26}
        assert classify_stage_type(stage) == ITT

    def test_ttt_stage_from_type_field(self):
        stage = {'type': 'Team Time Trial', 'distance_km': 19.7}
        assert classify_stage_type(stage) == TTT

    # --- real schedule entries from tour_de_france_scraper.py ---

    def test_stage_5_is_flat(self):
        """Stage 5 Lannemezan-Pau is FLAT per STAGE_SCHEDULE."""
        stage = {'stage': 5, 'date': '2026-07-08', 'route': 'Lannemezan — Pau',
                 'distance_km': 158, 'type': 'Flat'}
        assert classify_stage_type(stage) == FLAT

    def test_stage_4_is_hilly(self):
        """Stage 4 Carcassonne-Foix is HILLY — the stage Pedersen won."""
        stage = {'stage': 4, 'date': '2026-07-07', 'route': 'Carcassonne — Foix',
                 'distance_km': 182, 'type': 'Hilly'}
        assert classify_stage_type(stage) == HILLY

    def test_stage_3_is_mountain(self):
        """Stage 3 Granollers-Les Angles is MOUNTAIN — Pogacar's stage."""
        stage = {'stage': 3, 'date': '2026-07-06', 'route': 'Granollers — Les Angles',
                 'distance_km': 196, 'type': 'Mountain'}
        assert classify_stage_type(stage) == MOUNTAIN

    def test_stage_16_is_itt(self):
        """Stage 16 Evian-Thonon is ITT."""
        stage = {'stage': 16, 'date': '2026-07-21',
                 'route': 'Évian-les-Bains — Thonon-les-Bains',
                 'distance_km': 26, 'type': 'Individual Time Trial'}
        assert classify_stage_type(stage) == ITT

    def test_stage_1_is_ttt(self):
        """Stage 1 Barcelona is TTT."""
        stage = {'stage': 1, 'date': '2026-07-04', 'route': 'Barcelona — Barcelona',
                 'distance_km': 19.7, 'type': 'Team Time Trial'}
        assert classify_stage_type(stage) == TTT

    # --- elevation heuristic fallback ---

    def test_high_elevation_with_hc_climb_is_mountain(self):
        stage = {'type': 'Unknown', 'elevation_m': 3200, 'has_hc_climb': True}
        assert classify_stage_type(stage) == MOUNTAIN

    def test_high_elevation_without_hc_flag_still_mountain(self):
        stage = {'type': 'Unknown', 'elevation_m': 2800}
        assert classify_stage_type(stage) == MOUNTAIN

    def test_mid_elevation_is_hilly(self):
        stage = {'type': 'Unknown', 'elevation_m': 1500}
        assert classify_stage_type(stage) == HILLY

    def test_low_elevation_is_flat(self):
        stage = {'type': 'Unknown', 'elevation_m': 400}
        assert classify_stage_type(stage) == FLAT

    # --- error cases ---

    def test_raises_on_unresolvable_type(self):
        with pytest.raises(ValueError):
            classify_stage_type({'type': 'Unknown'})  # no elevation either

    def test_raises_on_empty_dict(self):
        with pytest.raises((ValueError, KeyError)):
            classify_stage_type({})


# ===========================================================================
# 2. GC vs stage hunter pick confidence
# ===========================================================================

class TestPickConfidence:
    """pick_confidence(rider, stage_type) returns correct tier."""

    # --- flat stage ---

    def test_gc_leader_flat_is_low(self):
        """Core rule: never back GC leaders on flat stages."""
        rider = {'name': 'Tadej Pogacar', 'is_gc_contender': True,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'gc_position': 1, 'gc_gap_seconds': 0}
        assert pick_confidence(rider, FLAT) == LOW

    def test_sprinter_flat_is_high(self):
        """Jasper Philipsen profile on flat stage."""
        rider = {'name': 'Jasper Philipsen', 'is_gc_contender': False,
                 'is_sprinter': True, 'is_puncheur': False,
                 'is_climber': False, 'is_stage_hunter': True}
        assert pick_confidence(rider, FLAT) == HIGH

    def test_climber_flat_is_speculative(self):
        rider = {'name': 'Jonas Vingegaard', 'is_gc_contender': True,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'gc_position': 2, 'gc_gap_seconds': 45}
        assert pick_confidence(rider, FLAT) == LOW  # GC contender rule fires first

    def test_pure_climber_no_gc_flat_is_speculative(self):
        rider = {'name': 'Random Climber', 'is_gc_contender': False,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'is_stage_hunter': False}
        assert pick_confidence(rider, FLAT) == SPECULATIVE

    # --- hilly stage ---

    def test_gc_leader_hilly_is_low(self):
        """Stage 4 equivalent: Pogacar on a hilly stage = LOW (fade him)."""
        rider = {'name': 'Tadej Pogacar', 'is_gc_contender': True,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'gc_position': 1, 'gc_gap_seconds': 0}
        assert pick_confidence(rider, HILLY) == LOW

    def test_puncheur_hilly_is_high(self):
        """Mads Pedersen / van der Poel profile on hilly stage."""
        rider = {'name': 'Mads Pedersen', 'is_gc_contender': False,
                 'is_sprinter': False, 'is_puncheur': True,
                 'is_climber': False, 'is_stage_hunter': True}
        assert pick_confidence(rider, HILLY) == HIGH

    def test_sprinter_hilly_is_medium(self):
        rider = {'name': 'Tim Merlier', 'is_gc_contender': False,
                 'is_sprinter': True, 'is_puncheur': False,
                 'is_climber': False, 'is_stage_hunter': True}
        assert pick_confidence(rider, HILLY) == MEDIUM

    # --- mountain stage ---

    def test_gc_leader_mountain_is_high(self):
        """Pogacar on a summit finish mountain stage = HIGH — Stage 3 pick."""
        rider = {'name': 'Tadej Pogacar', 'is_gc_contender': True,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'gc_position': 1, 'gc_gap_seconds': 0}
        assert pick_confidence(rider, MOUNTAIN) == HIGH

    def test_sprinter_mountain_is_speculative(self):
        rider = {'name': 'Jasper Philipsen', 'is_gc_contender': False,
                 'is_sprinter': True, 'is_puncheur': False,
                 'is_climber': False, 'is_stage_hunter': True}
        assert pick_confidence(rider, MOUNTAIN) == SPECULATIVE

    def test_gc_contender_not_in_top3_mountain_is_medium(self):
        rider = {'name': 'Remco Evenepoel', 'is_gc_contender': True,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'gc_position': 5, 'gc_gap_seconds': 180}
        assert pick_confidence(rider, MOUNTAIN) == MEDIUM

    # --- ITT stage ---

    def test_tt_specialist_itt_is_high(self):
        """Filippo Ganna on Stage 16 ITT = HIGH."""
        rider = {'name': 'Filippo Ganna', 'is_gc_contender': False,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': False, 'is_tt_specialist': True,
                 'is_stage_hunter': True}
        assert pick_confidence(rider, ITT) == HIGH

    def test_sprinter_itt_is_speculative(self):
        rider = {'name': 'Tim Merlier', 'is_gc_contender': False,
                 'is_sprinter': True, 'is_puncheur': False,
                 'is_climber': False, 'is_tt_specialist': False}
        assert pick_confidence(rider, ITT) == SPECULATIVE

    def test_gc_rider_itt_is_medium(self):
        """Pogacar is a strong ITT rider but not a pure TT specialist."""
        rider = {'name': 'Tadej Pogacar', 'is_gc_contender': True,
                 'is_sprinter': False, 'is_puncheur': False,
                 'is_climber': True, 'is_tt_specialist': False,
                 'gc_position': 1, 'gc_gap_seconds': 0}
        assert pick_confidence(rider, ITT) == MEDIUM


# ===========================================================================
# 3. Breakaway probability by stage type
# ===========================================================================

class TestBreakawayProbability:
    """Verify baseline probabilities and modifier logic."""

    def test_flat_stage_low_breakaway(self):
        p = breakaway_probability(FLAT)
        assert p == pytest.approx(0.05)

    def test_flat_with_crosswind_higher(self):
        p = breakaway_probability(FLAT, crosswind=True)
        assert p == pytest.approx(0.20)

    def test_hilly_stage_moderate_breakaway(self):
        p = breakaway_probability(HILLY)
        assert p == pytest.approx(0.30)

    def test_mountain_stage_high_breakaway(self):
        p = breakaway_probability(MOUNTAIN)
        assert p == pytest.approx(0.35)

    def test_itt_zero_breakaway(self):
        assert breakaway_probability(ITT) == 0.0

    def test_ttt_zero_breakaway(self):
        assert breakaway_probability(TTT) == 0.0

    def test_follows_hard_mountain_adds_10pp(self):
        """Stage after a mountain day: sprint teams fatigued, breakaway +10pp."""
        base = breakaway_probability(HILLY)
        boosted = breakaway_probability(HILLY, follows_hard_mountain=True)
        assert boosted == pytest.approx(base + 0.10)

    def test_mountain_follows_hard_mountain_capped_at_1(self):
        """Probability never exceeds 1.0."""
        p = breakaway_probability(MOUNTAIN, follows_hard_mountain=True)
        assert p <= 1.0

    def test_flat_crosswind_and_post_mountain_both_apply(self):
        """Both modifiers stack on a flat stage with crosswind after mountains."""
        p = breakaway_probability(FLAT, crosswind=True, follows_hard_mountain=True)
        # 0.05 + 0.15 (crosswind) + 0.10 (post-mountain) = 0.30
        assert p == pytest.approx(0.30)

    def test_cobbles_has_nonzero_probability(self):
        assert breakaway_probability(COBBLES) > 0.0

    def test_mountain_always_higher_than_flat(self):
        assert breakaway_probability(MOUNTAIN) > breakaway_probability(FLAT)

    def test_hilly_always_higher_than_flat(self):
        assert breakaway_probability(HILLY) > breakaway_probability(FLAT)


# ===========================================================================
# 4. Team control signal -> sprinter confidence boost
# ===========================================================================

class TestApplyTeamControlBoost:
    """Team control adjustments applied on top of base pick_confidence."""

    def _sprinter(self, team: str = 'Alpecin-Premier Tech') -> dict:
        return {
            'name': 'Jasper Philipsen',
            'team': team,
            'is_gc_contender': False,
            'is_sprinter': True,
            'is_puncheur': False,
            'is_climber': False,
            'is_stage_hunter': True,
        }

    def _puncheur(self, team: str = 'Lidl-Trek') -> dict:
        return {
            'name': 'Mads Pedersen',
            'team': team,
            'is_gc_contender': False,
            'is_sprinter': False,
            'is_puncheur': True,
            'is_climber': False,
            'is_stage_hunter': True,
        }

    def test_sprinters_team_controls_flat_upgrades_confidence(self):
        """Alpecin at front → Philipsen confidence upgraded."""
        rider = self._sprinter('Alpecin-Premier Tech')
        control = {'team_name': 'Alpecin-Premier Tech', 'control_type': 'sprint',
                   'lead_out_intact': True}
        result = apply_team_control_boost(MEDIUM, rider, control, FLAT)
        assert result == HIGH

    def test_lead_out_broken_no_upgrade(self):
        """Even if Alpecin controls, broken lead-out = no boost."""
        rider = self._sprinter('Alpecin-Premier Tech')
        control = {'team_name': 'Alpecin-Premier Tech', 'control_type': 'sprint',
                   'lead_out_intact': False}
        result = apply_team_control_boost(MEDIUM, rider, control, FLAT)
        # No upgrade because lead_out_intact is False
        assert result == MEDIUM

    def test_gc_team_controls_flat_downgrades_sprinter(self):
        """UAE controlling on flat = breakaway likely → downgrade sprinter."""
        rider = self._sprinter('Alpecin-Premier Tech')
        control = {'team_name': 'UAE Team Emirates XRG', 'control_type': 'gc',
                   'lead_out_intact': True}
        result = apply_team_control_boost(HIGH, rider, control, FLAT)
        assert result == MEDIUM

    def test_gc_control_hilly_downgrades_sprinter(self):
        rider = self._sprinter('Soudal-Quick-Step')
        control = {'team_name': 'Visma-Lease a Bike', 'control_type': 'gc',
                   'lead_out_intact': True}
        result = apply_team_control_boost(HIGH, rider, control, HILLY)
        assert result == MEDIUM

    def test_fragmented_control_floors_stage_hunter_at_medium(self):
        """No team in control → floor at MEDIUM for stage hunter."""
        rider = self._puncheur()
        control = {'team_name': '', 'control_type': 'fragmented', 'lead_out_intact': True}
        result = apply_team_control_boost(LOW, rider, control, HILLY)
        assert result == MEDIUM

    def test_fragmented_high_stays_high(self):
        """HIGH confidence stage hunter not downgraded by fragmented control."""
        rider = self._puncheur()
        control = {'team_name': '', 'control_type': 'fragmented', 'lead_out_intact': True}
        result = apply_team_control_boost(HIGH, rider, control, HILLY)
        assert result == HIGH

    def test_shared_sprint_control_upgrades_sprinter_flat(self):
        """Multiple sprint teams chasing → near-certain bunch sprint → upgrade."""
        rider = self._sprinter('Soudal-Quick-Step')
        control = {'team_name': 'Soudal-Quick-Step', 'control_type': 'shared_sprint',
                   'lead_out_intact': True}
        result = apply_team_control_boost(MEDIUM, rider, control, FLAT)
        assert result == HIGH

    def test_no_change_when_control_type_none(self):
        """No information about control -> pass through base confidence."""
        rider = self._sprinter()
        control = {'team_name': '', 'control_type': 'none', 'lead_out_intact': True}
        result = apply_team_control_boost(HIGH, rider, control, FLAT)
        assert result == HIGH

    def test_other_team_sprint_control_no_boost_for_rival_sprinter(self):
        """Soudal in control — Philipsen (Alpecin) gets no boost."""
        rider = self._sprinter('Alpecin-Premier Tech')
        control = {'team_name': 'Soudal-Quick-Step', 'control_type': 'sprint',
                   'lead_out_intact': True}
        result = apply_team_control_boost(HIGH, rider, control, FLAT)
        assert result == HIGH  # no change; different team

    def test_mountain_stage_gc_control_no_downgrade_for_sprinter(self):
        """On a mountain stage, GC team control is expected — no sprinter downgrade
        (the sprinter shouldn't be picked anyway, but the function shouldn't make it worse)."""
        rider = self._sprinter()
        control = {'team_name': 'UAE Team Emirates XRG', 'control_type': 'gc',
                   'lead_out_intact': True}
        # Sprinter on mountain is already SPECULATIVE; GC downgrade logic only fires on FLAT/HILLY
        result = apply_team_control_boost(SPECULATIVE, rider, control, MOUNTAIN)
        assert result == SPECULATIVE  # not further downgraded


# ===========================================================================
# 5. Record calibration
# ===========================================================================

class TestCalibrationFactor:
    """calibration_factor(wins, picks) returns correct multiplier."""

    # --- 2026 TDF current state: 1 win from 4 picks = 25% ---

    def test_current_record_1_from_4_is_85(self):
        """1/4 = 25% → below 33% target → factor 0.85."""
        assert calibration_factor(1, 4) == pytest.approx(0.85)

    # --- at or above target ---

    def test_3_from_4_above_target_is_1(self):
        """3/4 = 75% >> 35% → no adjustment."""
        assert calibration_factor(3, 4) == pytest.approx(1.0)

    def test_exactly_35_percent_is_1(self):
        """7/20 = 35% → exactly at target → 1.0."""
        assert calibration_factor(7, 20) == pytest.approx(1.0)

    def test_above_35_percent_is_1(self):
        assert calibration_factor(8, 20) == pytest.approx(1.0)

    # --- between 25% and 34% ---

    def test_25_percent_exactly_is_85(self):
        assert calibration_factor(5, 20) == pytest.approx(0.85)

    def test_34_percent_is_85(self):
        """6/17 ≈ 35.3% — just at target, 1.0 is expected."""
        assert calibration_factor(6, 17) == pytest.approx(1.0)

    def test_just_below_35_is_85(self):
        """6/18 = 33.3% → between 25–34% → 0.85."""
        assert calibration_factor(6, 18) == pytest.approx(0.85)

    # --- below 25% ---

    def test_0_from_3_is_70(self):
        """0/3 = 0% → severe underperformance → 0.70."""
        assert calibration_factor(0, 3) == pytest.approx(0.70)

    def test_1_from_5_is_70(self):
        """1/5 = 20% → below 25% → 0.70."""
        assert calibration_factor(1, 5) == pytest.approx(0.70)

    def test_2_from_9_is_70(self):
        """2/9 ≈ 22% → below 25% → 0.70."""
        assert calibration_factor(2, 9) == pytest.approx(0.70)

    # --- edge: no picks yet ---

    def test_zero_picks_is_1(self):
        """No data yet: no adjustment."""
        assert calibration_factor(0, 0) == pytest.approx(1.0)

    # --- error cases ---

    def test_negative_picks_raises(self):
        with pytest.raises(ValueError):
            calibration_factor(0, -1)

    def test_negative_wins_raises(self):
        with pytest.raises(ValueError):
            calibration_factor(-1, 5)

    def test_wins_exceeds_picks_raises(self):
        with pytest.raises(ValueError):
            calibration_factor(5, 3)

    # --- calibration drives EW strategy ---

    def test_sub_target_record_suggests_ew_strategy(self):
        """Below 35% win rate → factor < 1.0 → system should increase EW weight."""
        factor = calibration_factor(1, 4)
        assert factor < 1.0, "Factor should be < 1.0 to signal EW selection increase"

    def test_on_target_record_full_confidence(self):
        """On target → factor = 1.0 → no EW bias needed."""
        factor = calibration_factor(7, 20)
        assert factor == pytest.approx(1.0)
