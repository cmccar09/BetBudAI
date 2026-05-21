# Weight Auto-Tuning System

Automated weight adjustment engine that learns from race outcomes and deploys validated changes.

## Quick Start

### Run Tests
```bash
python backend/learning/test_weight_system.py
```

### Manual Deployment
```bash
# Show current weights
python scripts/deploy_weight_changes.py --show-current

# Preview changes
python scripts/deploy_weight_changes.py --changes consistency=8 form_velocity_bonus=12 --dry-run

# Deploy changes
python scripts/deploy_weight_changes.py --changes consistency=8 form_velocity_bonus=12

# Rollback to version 4
python scripts/deploy_weight_changes.py --rollback 4 --reason "Performance issues"
```

### Programmatic Usage
```python
from backend.learning import (
    WeightDecisionEngine,
    WeightValidator,
    WeightDeployer
)

# 1. Analyze findings
engine = WeightDecisionEngine()
decision = engine.analyze_aggregated_findings(aggregated_data)

# 2. Validate changes
validator = WeightValidator()
validation = validator.validate_all_changes(changes_dict)

# 3. Deploy if safe
if validation.safe_to_deploy:
    deployer = WeightDeployer()
    result = deployer.deploy_weights(new_weights, changes, rationale)
```

## Components

### 1. Weight Decision Engine (`weight_decision_engine.py`)
- Analyzes aggregated race findings
- Calculates confidence scores
- Determines adjustment magnitude
- Prioritizes by urgency

**Key Classes**:
- `WeightDecisionEngine` - Main decision logic
- `WeightChange` - Proposed weight change with rationale
- `DecisionResult` - Analysis result with categorized changes

### 2. Weight Validator (`weight_validator.py`)
- Validates weight bounds (0-40)
- Checks score impact (<20% of total)
- Detects conflicting changes
- Validates historical performance
- Checks strike rate floor (>15%)

**Key Classes**:
- `WeightValidator` - Safety validation logic
- `ValidationResult` - Single weight validation result
- `ValidationSummary` - Overall validation summary

### 3. Weight Deployer (`weight_deployer.py`)
- Manages weight versions
- Deploys to DynamoDB
- Sets up rollback checkpoints
- Monitors performance
- Triggers automatic rollback

**Key Classes**:
- `WeightDeployer` - Deployment and versioning
- `WeightVersion` - Versioned weight snapshot
- `DeploymentResult` - Deployment outcome
- `RollbackTrigger` - Rollback condition checker

## Decision Rules

### Confidence Thresholds
| Confidence | Action | Timeline |
|-----------|--------|----------|
| ≥50% | Deploy immediately | Within 1 hour |
| 30-50% | Deploy after confirmation | After 2 days |
| <30% | Monitor only | No deployment |

### Adjustment Magnitudes
| Races in 7 Days | Adjustment Range |
|----------------|------------------|
| 5+ | ±8 to ±10pts |
| 3-4 | ±5 to ±7pts |
| 2 | ±3 to ±4pts |
| 1 | 0pts (monitor) |

## Safety Validations

1. **Bounds Check**: 0 ≤ weight ≤ 40
2. **Score Impact**: Change < 20% of total score
3. **Conflict Detection**: No contradictory changes in related groups
4. **Historical Validation**: Would improve last 30 days (future)
5. **Strike Rate Floor**: Won't drop below 15%

## Rollback Triggers

Automatic rollback occurs if:
- Strike rate drops >5% for 2 consecutive days
- Wins decrease >50% vs 7-day average
- Manual override flag set
- Critical calculation error

## DynamoDB Schema

### Active Weights
```
Table: SureBetBets
Key: {bet_id: "SYSTEM_WEIGHTS", bet_date: "CONFIG"}
```

### Version History
```
Table: SureBetBets
Key: {bet_id: "WEIGHT_VERSIONS", bet_date: "HISTORY"}
```

## Example: Today's Changes (2026-05-20)

**Pattern Detected**: Consistent placer bias (2/2 races)

**Recommended Changes**:
- `consistency`: 12 → 8 (-4pts)
- `form_velocity_bonus`: 18 → 12 (-6pts)

**Rationale**: System picking horses that consistently place 2nd/3rd but don't win. Reduce placer-rewarding weights.

**Confidence**: 73% (high)
**Urgency**: Immediate

**Deploy Command**:
```bash
python scripts/deploy_weight_changes.py \
  --changes consistency=8 form_velocity_bonus=12
```

## Monitoring

After deployment, system monitors for 24 hours:
- Track strike rate every hour
- Compare to baseline
- Auto-rollback if performance drops

## Documentation

See [WEIGHT_AUTO_TUNING_RULES.md](../../WEIGHT_AUTO_TUNING_RULES.md) for complete rules and examples.

## Testing

```bash
# Run all tests
python backend/learning/test_weight_system.py

# Test individual components
python backend/learning/weight_decision_engine.py
python backend/learning/weight_validator.py
python backend/learning/weight_deployer.py
```

## Architecture

```
Race Outcomes
     ↓
Pattern Detection
     ↓
Aggregated Findings
     ↓
┌──────────────────────┐
│ Weight Decision      │ → Confidence scoring
│ Engine               │ → Magnitude calculation
└──────────────────────┘
     ↓
┌──────────────────────┐
│ Weight Validator     │ → Safety checks
│                      │ → Conflict detection
└──────────────────────┘
     ↓
┌──────────────────────┐
│ Weight Deployer      │ → Version management
│                      │ → DynamoDB update
│                      │ → Rollback setup
└──────────────────────┘
     ↓
Monitoring (24h)
     ↓
Auto-rollback if needed
```

## Configuration

Edit `backend/learning/weight_decision_engine.py`:
```python
HIGH_CONFIDENCE = 0.50
MEDIUM_CONFIDENCE = 0.30

ADJUSTMENT_RULES = {
    'aggressive': {'min_races': 5, 'magnitude': (8, 10)},
    'moderate': {'min_races': 3, 'magnitude': (5, 7)},
    'conservative': {'min_races': 2, 'magnitude': (3, 4)},
}
```

Edit `backend/learning/weight_validator.py`:
```python
MIN_WEIGHT = 0
MAX_WEIGHT = 40
MAX_TOTAL_SCORE_IMPACT = 0.20
MIN_STRIKE_RATE = 0.15
```

Edit `backend/learning/weight_deployer.py`:
```python
STRIKE_RATE_DROP_THRESHOLD = 0.05
WIN_DECREASE_THRESHOLD = 0.50
MONITORING_PERIOD_HOURS = 24
```

## Troubleshooting

### Validation Fails
```bash
# Check current weights
python scripts/deploy_weight_changes.py --show-current

# Preview changes before deploying
python scripts/deploy_weight_changes.py --changes <changes> --dry-run
```

### Performance Drop After Deployment
```bash
# Check rollback triggers
# (Automatic rollback will trigger if thresholds exceeded)

# Manual rollback
python scripts/deploy_weight_changes.py --rollback <version> --reason "Performance drop"
```

### Changes Not Reflected in Picks
1. Check weight cache TTL (5 minutes by default)
2. Verify DynamoDB has correct version
3. Restart application if needed

## Support

- Full documentation: [WEIGHT_AUTO_TUNING_RULES.md](../../WEIGHT_AUTO_TUNING_RULES.md)
- Test suite: `backend/learning/test_weight_system.py`
- Manual deployment: `scripts/deploy_weight_changes.py`

---

**Last Updated**: 2026-05-20  
**Status**: Production Ready
