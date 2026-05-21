# Weight Auto-Tuning System - Complete Rules

**Version**: 1.0  
**Last Updated**: 2026-05-20  
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Decision Engine Rules](#decision-engine-rules)
4. [Adjustment Magnitude Rules](#adjustment-magnitude-rules)
5. [Safety Validations](#safety-validations)
6. [Deployment Process](#deployment-process)
7. [Rollback Mechanisms](#rollback-mechanisms)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [A/B Testing Mode](#ab-testing-mode-optional)
10. [Usage Examples](#usage-examples)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Weight Auto-Tuning System is a self-learning engine that:
- Analyzes race outcomes to identify systematic biases
- Calculates confidence-scored weight adjustments
- Validates changes for safety
- Deploys updates with versioning and rollback
- Monitors performance and triggers automatic rollback if needed

**Key Principle**: Only deploy changes when evidence is strong and safety checks pass.

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Learning Pipeline                         │
│                                                              │
│  1. Race Analysis → 2. Pattern Detection → 3. Aggregation   │
│         ↓                    ↓                    ↓          │
│    Individual findings   Pattern evidence    Weight recs    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Weight Decision Engine                         │
│  - Calculate confidence scores                               │
│  - Determine adjustment magnitude                            │
│  - Prioritize by urgency                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Weight Validator                             │
│  - Bounds checking                                           │
│  - Score impact analysis                                     │
│  - Conflict detection                                        │
│  - Historical validation                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Weight Deployer                              │
│  - Version management                                        │
│  - DynamoDB updates                                          │
│  - Rollback checkpoint                                       │
│  - Monitoring setup                                          │
└─────────────────────────────────────────────────────────────┘
```

### Files

- **`backend/learning/weight_decision_engine.py`** - Decision logic
- **`backend/learning/weight_validator.py`** - Safety checks
- **`backend/learning/weight_deployer.py`** - DynamoDB deployment
- **`scripts/deploy_weight_changes.py`** - Manual deployment CLI

---

## Decision Engine Rules

### Confidence Scoring Algorithm

```python
def calculate_confidence(pattern_count, total_races, historical_matches):
    # Frequency: How often pattern appears
    frequency_score = pattern_count / total_races
    
    # Recency: Prefer patterns seen very recently
    recency_score = 1.0 if pattern_count >= 2 else 0.5
    
    # Historical: Pattern matches in last 30 days
    historical_score = historical_matches / 30
    
    # Weighted combination
    confidence = (
        frequency_score * 0.5 +    # 50% weight
        recency_score * 0.3 +       # 30% weight
        historical_score * 0.2      # 20% weight
    )
    
    return confidence
```

### Deployment Urgency Thresholds

| Confidence | Pattern Frequency | Action | Timeline |
|-----------|------------------|--------|----------|
| **High** (≥50%) | 50%+ of races | **Deploy immediately** | Within 1 hour |
| **Medium** (30-50%) | 30-50% of races | **Deploy after confirmation** | After 2 days |
| **Low** (<30%) | <30% of races | **Monitor only** | No deployment |

### Example Scenarios

#### Scenario 1: High Confidence (Deploy Immediately)
```json
{
  "pattern": "consistent_placer_bias",
  "pattern_count": 2,
  "total_races": 2,
  "frequency_score": 1.0,
  "recency_score": 1.0,
  "historical_matches": 5,
  "historical_score": 0.17,
  "confidence": 0.73,
  "urgency": "immediate"
}
```
**Action**: Deploy weight changes immediately (confidence > 50%).

#### Scenario 2: Medium Confidence (Wait for Confirmation)
```json
{
  "pattern": "class_advantage_missed",
  "pattern_count": 1,
  "total_races": 3,
  "frequency_score": 0.33,
  "recency_score": 0.5,
  "historical_matches": 8,
  "historical_score": 0.27,
  "confidence": 0.36,
  "urgency": "2_day"
}
```
**Action**: Monitor for 2 days. Deploy if pattern persists.

#### Scenario 3: Low Confidence (Monitor Only)
```json
{
  "pattern": "pace_mismatch",
  "pattern_count": 1,
  "total_races": 5,
  "frequency_score": 0.20,
  "recency_score": 0.5,
  "historical_matches": 2,
  "historical_score": 0.07,
  "confidence": 0.22,
  "urgency": "monitor"
}
```
**Action**: Log for future analysis. No weight changes.

---

## Adjustment Magnitude Rules

### Frequency-Based Magnitude

| Races in 7 Days | Level | Adjustment Range | Use Case |
|----------------|-------|------------------|----------|
| **5+ races** | Aggressive | ±8 to ±10pts | Strong repeated pattern |
| **3-4 races** | Moderate | ±5 to ±7pts | Consistent evidence |
| **2 races** | Conservative | ±3 to ±4pts | Initial confirmation |
| **1 race** | Monitor | 0pts | Insufficient data |

### Confidence Scaling

If confidence is below 30% (medium threshold), reduce magnitude by 50%:

```python
if confidence < 0.30:
    adjustment = adjustment * 0.5
```

### Example Calculations

#### Example 1: Aggressive Adjustment (2/2 races in 1 day)
```
Pattern: consistent_placer_bias
Races: 2 in 1 day
Races per 7 days: (2/1) * 7 = 14
Confidence: 1.0 (100%)
Level: Aggressive
Range: ±8 to ±10pts

Weight: consistency
Current: 12
Suggested: 8
Desired change: -4
Final change: -4pts (within range)
New value: 8
```

#### Example 2: Moderate Adjustment (3/5 races in 3 days)
```
Pattern: market_underweighting
Races: 3 in 3 days
Races per 7 days: (3/3) * 7 = 7
Confidence: 0.60
Level: Moderate
Range: ±5 to ±7pts

Weight: favorite_correction
Current: 5
Suggested: 12
Desired change: +7
Final change: +7pts (at max of range)
New value: 12
```

#### Example 3: Conservative with Low Confidence
```
Pattern: trainer_combo_weak
Races: 2 in 2 days
Races per 7 days: (2/2) * 7 = 7
Confidence: 0.25 (low)
Level: Conservative
Range: ±3 to ±4pts

Weight: trainer_combo_bonus
Current: 8
Suggested: 4
Desired change: -4
Confidence scaling: -4 * 0.5 = -2
Final change: -2pts
New value: 6
```

---

## Safety Validations

All proposed changes must pass these checks before deployment:

### 1. Weight Bounds Check

```python
MIN_WEIGHT = 0
MAX_WEIGHT = 40

# Check
if new_value < MIN_WEIGHT or new_value > MAX_WEIGHT:
    FAIL: "Weight out of bounds"
```

**Rationale**: Weights outside this range cause extreme scoring distortion.

### 2. Total Score Impact Check

```python
MAX_TOTAL_SCORE_IMPACT = 0.20  # 20% of total possible score
TYPICAL_MAX_SCORE = 200

# Check
change_magnitude = abs(new_value - current_value)
impact_ratio = change_magnitude / TYPICAL_MAX_SCORE

if impact_ratio > MAX_TOTAL_SCORE_IMPACT:
    FAIL: "Change too large"
```

**Rationale**: Single weight changes shouldn't dominate overall scoring.

### 3. Conflict Detection

Check for contradictory changes within related weight groups:

```python
related_groups = {
    'form_cluster': [
        'recent_win', 'consistency', 'form_velocity_bonus',
        'form_close_2nd', 'bounce_back_bonus'
    ],
    'market_signals': [
        'sweet_spot', 'optimal_odds', 'favorite_correction',
        'market_steam_bonus'
    ],
    'class_signals': [
        'class_drop_bonus', 'class_drop_rebound_bonus',
        'official_rating_bonus'
    ]
}

# Check: No group should have both increases and decreases
for group_name, weight_names in related_groups.items():
    directions = [get_direction(w) for w in weight_names if w in changes]
    if 'increase' in directions and 'decrease' in directions:
        FAIL: f"Conflicting changes in {group_name}"
```

**Rationale**: Related weights should move together, not against each other.

### 4. Historical Performance Validation

```python
# Simplified check: Warn if large form weight decreases
form_weights = ['recent_win', 'form_velocity_bonus', 'consistency']
total_decrease = sum(
    current - new 
    for weight in form_weights 
    if new < current
)

if total_decrease > 15:
    WARNING: "Large form weight decrease may reduce strike rate"
```

**Full Implementation** (future):
1. Fetch last 30 days of picks
2. Re-score with new weights
3. Compare win rates
4. Fail if new weights perform worse

### 5. Strike Rate Floor Check

```python
MIN_STRIKE_RATE = 0.15  # 15% minimum

# Heuristic: Check net change in winner-boosting weights
winner_boost_weights = [
    'recent_win', 'form_exact_course_win', 'form_exact_distance_win',
    'class_drop_bonus', 'bounce_back_bonus'
]

net_change = sum(new - current for w in winner_boost_weights)

if net_change < -15:
    FAIL: "Risk of strike rate dropping below 15%"
```

---

## Deployment Process

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Calculate Proposed Changes                           │
│    - Decision engine analyzes patterns                   │
│    - Generates weight recommendations                    │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Run Safety Validations                               │
│    ✓ Bounds check                                       │
│    ✓ Score impact                                       │
│    ✓ Conflict detection                                 │
│    ✓ Historical validation                              │
│    ✓ Strike rate floor                                  │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Create Version Snapshot                              │
│    - Version N+1                                         │
│    - Full weight dict                                    │
│    - Change details                                      │
│    - Rationale                                           │
│    - Timestamp                                           │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Save to DynamoDB                                      │
│    Primary: SureBetBets.SYSTEM_WEIGHTS                   │
│    History: SureBetBets.WEIGHT_VERSIONS                  │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Set Rollback Checkpoint                              │
│    - Store previous version                              │
│    - Set monitoring window (24h)                         │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Monitor Performance                                   │
│    - Track strike rate                                   │
│    - Track wins vs baseline                              │
│    - Check rollback triggers                             │
└─────────────────────────────────────────────────────────┘
```

### DynamoDB Schema

#### Active Weights
```json
{
  "bet_id": "SYSTEM_WEIGHTS",
  "bet_date": "CONFIG",
  "weights": {
    "recent_win": 14,
    "consistency": 8,
    "form_velocity_bonus": 12,
    ...
  },
  "version": 5,
  "updated_at": "2026-05-20T15:30:00Z",
  "updated_by": "AutoTuningEngine",
  "rationale": "Pattern evidence from 2/2 races...",
  "rollback_version": 4,
  "monitoring_until": "2026-05-21T15:30:00Z"
}
```

#### Version History
```json
{
  "bet_id": "WEIGHT_VERSIONS",
  "bet_date": "HISTORY",
  "versions": [
    {
      "version": 5,
      "weights": { ... },
      "created_at": "2026-05-20T15:30:00Z",
      "created_by": "AutoTuningEngine",
      "changes_from_previous": {
        "consistency": {"old": 12, "new": 8, "change": -4},
        "form_velocity_bonus": {"old": 18, "new": 12, "change": -6}
      },
      "rationale": "Pattern evidence from 2/2 races...",
      "validation_passed": true,
      "rollback_checkpoint": true
    },
    ...
  ],
  "updated_at": "2026-05-20T15:30:00Z"
}
```

---

## Rollback Mechanisms

### Automatic Rollback Triggers

| Trigger | Condition | Threshold | Action |
|---------|-----------|-----------|--------|
| **Strike Rate Drop** | Current SR < Baseline SR | 5% drop | Auto rollback |
| **Win Decrease** | Current wins < Baseline wins | 50% decrease | Auto rollback |
| **Manual Override** | Operator sets flag | Flag = true | Auto rollback |
| **Critical Error** | Weight calculation error | Any error | Auto rollback |

### Rollback Process

```python
# Check triggers every hour during monitoring window
def check_rollback_triggers(current_stats):
    # Trigger 1: Strike rate
    sr_drop = baseline_sr - current_sr
    if sr_drop > 0.05:
        trigger_rollback("Strike rate dropped by 5%+")
    
    # Trigger 2: Win count
    win_ratio = current_wins / baseline_wins_7day_avg
    if win_ratio < 0.50:
        trigger_rollback("Win count decreased by 50%+")
    
    # Trigger 3: Manual flag
    if manual_rollback_flag:
        trigger_rollback("Manual override by operator")

def trigger_rollback(reason):
    # Get rollback version from active config
    rollback_version = get_rollback_version()
    
    # Deploy rollback
    deployer.rollback_to_version(
        target_version=rollback_version,
        reason=reason
    )
    
    # Alert operator
    send_alert(f"ROLLBACK: {reason}")
```

### Manual Rollback

```bash
# Rollback to specific version
python scripts/deploy_weight_changes.py --rollback 4 --reason "Poor performance"

# Preview rollback
python scripts/deploy_weight_changes.py --rollback 4 --dry-run
```

---

## Monitoring & Alerting

### Metrics to Track

#### Real-Time (During Monitoring Window)
- Strike rate (hourly)
- Win count (hourly)
- Average odds of winners
- Average confidence scores
- Pick distribution

#### Daily (After Monitoring Window)
- Strike rate vs baseline
- Win rate vs baseline
- ROI change
- Top performing weights (by contribution)
- Weights that need adjustment

### Alert Conditions

| Severity | Condition | Action |
|----------|-----------|--------|
| **CRITICAL** | Strike rate < 10% for 2+ hours | Auto rollback + SMS |
| **WARNING** | Strike rate < 15% for 4+ hours | Email alert |
| **INFO** | Strike rate > 30% for 24h | Success notification |

### Dashboard (Future Enhancement)

```
Weight Performance Dashboard
============================

Current Version: 5
Deployed: 2026-05-20 15:30 UTC
Monitoring: Active (12h remaining)
Rollback: Version 4 (ready)

Performance (Last 24h)
----------------------
Strike Rate:    28% (↑3% vs baseline)
Wins:           7/25 (vs 5/25 baseline)
ROI:            +12.5%
Avg Odds:       4.2

Top Contributing Weights
-------------------------
1. class_drop_bonus:        +22pts avg (3 wins)
2. course_bonus:            +18pts avg (4 wins)
3. form_velocity_bonus:     +15pts avg (2 wins)

Weights Needing Adjustment
---------------------------
1. consistency:             Overweight (0 wins, 5 picks)
2. market_divergence:       Underweight (missed 2 winners)
```

---

## A/B Testing Mode (Optional)

### Purpose
Test new weights on a subset of picks before full deployment.

### Implementation

```python
def select_weights_for_pick(pick_id, ab_test_active=True):
    if not ab_test_active:
        return get_current_weights()
    
    # 80% new weights, 20% old weights
    if hash(pick_id) % 100 < 80:
        weights = get_weights_version('new')
        pick_metadata['weight_version'] = 'new'
    else:
        weights = get_weights_version('old')
        pick_metadata['weight_version'] = 'old'
    
    return weights
```

### Analysis After 7 Days

```python
def analyze_ab_test_results():
    new_picks = get_picks_with_version('new')
    old_picks = get_picks_with_version('old')
    
    new_sr = calculate_strike_rate(new_picks)
    old_sr = calculate_strike_rate(old_picks)
    
    improvement = (new_sr - old_sr) / old_sr
    
    if improvement > 0.03:  # 3% improvement
        deploy_full("New weights 3%+ better")
    elif improvement < -0.03:
        rollback("New weights 3%+ worse")
    else:
        extend_test("Inconclusive, extend 7 more days")
```

---

## Usage Examples

### Example 1: Automatic Deployment (Cron Job)

```bash
# Run daily learning pipeline (8:00 PM UTC after all races)
0 20 * * * cd /app && python backend/learning/orchestrator.py --auto-deploy

# Orchestrator will:
# 1. Analyze all races from today
# 2. Aggregate findings
# 3. Run decision engine
# 4. Validate changes
# 5. Deploy if high confidence
# 6. Log results
```

### Example 2: Manual Deployment

```bash
# Show current weights
python scripts/deploy_weight_changes.py --show-current

# Preview changes
python scripts/deploy_weight_changes.py \
  --changes consistency=8 form_velocity_bonus=12 \
  --dry-run

# Deploy changes
python scripts/deploy_weight_changes.py \
  --changes consistency=8 form_velocity_bonus=12

# Deployment flow:
# 1. Validates changes
# 2. Shows preview
# 3. Asks for confirmation
# 4. Deploys if confirmed
# 5. Sets up monitoring
```

### Example 3: Emergency Rollback

```bash
# Show version history
python scripts/deploy_weight_changes.py --show-history

# Rollback to version 4
python scripts/deploy_weight_changes.py \
  --rollback 4 \
  --reason "Strike rate dropped to 8%"

# Rollback flow:
# 1. Fetches version 4 weights
# 2. Shows preview
# 3. Asks for confirmation
# 4. Deploys rollback as new version
```

### Example 4: Programmatic Usage

```python
from backend.learning import (
    WeightDecisionEngine,
    WeightValidator,
    WeightDeployer
)

# Aggregated findings from learning pipeline
findings = {
    "date": "2026-05-20",
    "total_races": 5,
    "wins": 1,
    "losses": 4,
    "patterns": {
        "consistent_placer_bias": {
            "count": 3,
            "confidence": 0.60,
            "votes_for": {
                "consistency": True,
                "form_velocity_bonus": True
            }
        }
    },
    "weight_recommendations": {
        "consistency": {
            "current": 12,
            "suggested": 8,
            "votes": 3,
            "historical_matches": 7
        },
        "form_velocity_bonus": {
            "current": 18,
            "suggested": 12,
            "votes": 3,
            "historical_matches": 5
        }
    }
}

# 1. Decision Engine
engine = WeightDecisionEngine()
decision = engine.analyze_aggregated_findings(findings)

if decision.immediate_changes:
    # 2. Prepare changes
    changes_for_validation = {}
    new_weights = get_current_weights()
    
    for change in decision.immediate_changes:
        changes_for_validation[change.weight_name] = (
            change.current_value,
            change.suggested_value
        )
        new_weights[change.weight_name] = change.suggested_value
    
    # 3. Validate
    validator = WeightValidator()
    validation = validator.validate_all_changes(changes_for_validation)
    
    if validation.safe_to_deploy:
        # 4. Deploy
        deployer = WeightDeployer()
        
        changes_dict = {
            wname: {
                'old': current,
                'new': new,
                'change': new - current
            }
            for wname, (current, new) in changes_for_validation.items()
        }
        
        result = deployer.deploy_weights(
            new_weights=new_weights,
            changes=changes_dict,
            rationale=decision.recommendation,
            validation_passed=True
        )
        
        print(f"Deployed version {result.version}")
```

---

## Troubleshooting

### Problem: Validation Fails (Weight Out of Bounds)

**Symptom**:
```
✗ FAIL - consistency: Bounds check: Weight -2 below minimum 0
```

**Solution**:
Adjust the suggested change magnitude:
```python
# Instead of -14 change, use smaller magnitude
suggested_value = max(current_value - 10, MIN_WEIGHT)
```

### Problem: Conflicting Changes Detected

**Symptom**:
```
✗ FAIL - Conflicts detected: form_cluster has both increases and decreases
```

**Solution**:
Review related weights and ensure they move together:
```python
# If reducing placer weights, reduce all of them
changes = {
    'consistency': (12, 8),           # Decrease
    'form_velocity_bonus': (18, 12),  # Decrease
    'form_close_2nd': (14, 10)        # Decrease (add this)
}
```

### Problem: Rollback Triggered Too Quickly

**Symptom**:
```
ROLLBACK: Strike rate dropped by 5%+ after 2 hours
```

**Solution**:
1. Check if sample size too small (wait for more picks)
2. Adjust rollback thresholds if too sensitive:
```python
STRIKE_RATE_DROP_THRESHOLD = 0.08  # Increase to 8%
```

### Problem: Changes Not Reflected in Picks

**Symptom**:
Weights deployed but picks still using old values.

**Solution**:
1. Check cache TTL in `weights.py`:
```python
'ttl_seconds': 300  # 5 minute cache
```

2. Clear cache manually:
```python
from backend.config.weights import _weights_cache
_weights_cache['weights'] = None
_weights_cache['timestamp'] = None
```

3. Verify DynamoDB has correct version:
```bash
python scripts/deploy_weight_changes.py --show-current
```

### Problem: Historical Validation Not Working

**Symptom**:
```
Warning: Could not validate historical: 'Item' not in response
```

**Solution**:
Ensure SYSTEM_STATS item exists in DynamoDB:
```python
table.put_item(
    Item={
        'bet_id': 'SYSTEM_STATS',
        'bet_date': 'LAST_30_DAYS',
        'strike_rate': 0.22,
        'total_picks': 150,
        'wins': 33
    }
)
```

---

## Configuration

### Environment Variables

```bash
# DynamoDB
DYNAMODB_TABLE_NAME=SureBetBets
AWS_REGION=eu-west-1

# Auto-tuning thresholds
MIN_WEIGHT=0
MAX_WEIGHT=40
MAX_SCORE_IMPACT=0.20
MIN_STRIKE_RATE=0.15

# Rollback
STRIKE_RATE_DROP_THRESHOLD=0.05
WIN_DECREASE_THRESHOLD=0.50
MONITORING_PERIOD_HOURS=24

# Confidence thresholds
HIGH_CONFIDENCE=0.50
MEDIUM_CONFIDENCE=0.30
```

### Adjustment Rules (Editable)

Edit `backend/learning/weight_decision_engine.py`:

```python
# Confidence thresholds
HIGH_CONFIDENCE = 0.50  # 50%+ races
MEDIUM_CONFIDENCE = 0.30  # 30-50% races

# Adjustment magnitudes
ADJUSTMENT_RULES = {
    'aggressive': {'min_races': 5, 'days': 7, 'magnitude': (8, 10)},
    'moderate': {'min_races': 3, 'days': 7, 'magnitude': (5, 7)},
    'conservative': {'min_races': 2, 'days': 7, 'magnitude': (3, 4)},
    'monitor': {'min_races': 1, 'days': 7, 'magnitude': (0, 0)},
}
```

---

## Future Enhancements

### Phase 2 (Next 30 Days)
- [ ] Full historical validation (re-score past 30 days)
- [ ] A/B testing framework
- [ ] Real-time monitoring dashboard
- [ ] SMS/Slack alerts
- [ ] Multi-pattern conflict resolution

### Phase 3 (Next 90 Days)
- [ ] Machine learning confidence models
- [ ] Automated rollback with Bayesian change detection
- [ ] Weight contribution analysis (Shapley values)
- [ ] Adaptive adjustment magnitudes
- [ ] Multi-objective optimization

---

## Support

For issues or questions:
- Review logs: `backend/learning/*.log`
- Check DynamoDB: `SureBetBets.SYSTEM_WEIGHTS`
- Manual intervention: `scripts/deploy_weight_changes.py --rollback`

**Last Updated**: 2026-05-20  
**Maintained By**: BetBudAI Learning Team
