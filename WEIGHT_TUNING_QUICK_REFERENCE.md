# Weight Auto-Tuning - Quick Reference Card

## Essential Commands

### Testing
```bash
# Run all tests
python backend/learning/test_weight_system.py
```

### Viewing
```bash
# Show current weights
python scripts/deploy_weight_changes.py --show-current

# Show version history
python scripts/deploy_weight_changes.py --show-history
```

### Deploying
```bash
# Preview changes (dry run)
python scripts/deploy_weight_changes.py \
  --changes consistency=8 form_velocity_bonus=12 \
  --dry-run

# Deploy changes
python scripts/deploy_weight_changes.py \
  --changes consistency=8 form_velocity_bonus=12
```

### Monitoring
```bash
# One-time status
python scripts/monitor_weight_performance.py

# Continuous monitoring (refresh every 5 minutes)
python scripts/monitor_weight_performance.py --watch
```

### Rollback
```bash
# Rollback to version 4
python scripts/deploy_weight_changes.py \
  --rollback 4 \
  --reason "Performance declined"
```

---

## Decision Rules

### Confidence Thresholds
- **≥50%**: Deploy immediately
- **30-50%**: Deploy after 2 days
- **<30%**: Monitor only

### Adjustment Magnitude
- **5+ races/7days**: ±8-10pts (aggressive)
- **3-4 races/7days**: ±5-7pts (moderate)
- **2 races/7days**: ±3-4pts (conservative)
- **1 race/7days**: 0pts (monitor)

### Rollback Triggers
- Strike rate drops >5%
- Wins decrease >50%
- Manual override flag
- Critical error

---

## Safety Checks

1. **Bounds**: 0 ≤ weight ≤ 40
2. **Score Impact**: Change < 20% of total
3. **Conflicts**: No contradictory changes
4. **Strike Rate**: Won't drop below 15%
5. **Historical**: Would improve past performance

---

## Today's Changes (2026-05-20)

### Pattern
2/2 picks came 3rd (placer bias)

### Changes
```python
consistency: 12 → 8 (-4pts)
form_velocity_bonus: 18 → 12 (-6pts)
```

### Deploy
```bash
python scripts/deploy_weight_changes.py \
  --changes consistency=8 form_velocity_bonus=12
```

---

## Programmatic Usage

```python
from backend.learning import (
    WeightDecisionEngine,
    WeightValidator,
    WeightDeployer
)

# 1. Analyze
engine = WeightDecisionEngine()
decision = engine.analyze_aggregated_findings(data)

# 2. Validate
validator = WeightValidator()
validation = validator.validate_all_changes(changes)

# 3. Deploy
if validation.safe_to_deploy:
    deployer = WeightDeployer()
    result = deployer.deploy_weights(weights, changes, rationale)
```

---

## Files

### Core
- `backend/learning/weight_decision_engine.py`
- `backend/learning/weight_validator.py`
- `backend/learning/weight_deployer.py`

### Scripts
- `scripts/deploy_weight_changes.py`
- `scripts/monitor_weight_performance.py`

### Docs
- `WEIGHT_AUTO_TUNING_RULES.md` - Complete rules
- `WEIGHT_AUTO_TUNING_DEPLOYMENT_SUMMARY.md` - Deployment guide
- `backend/learning/README.md` - Quick start

---

## DynamoDB Keys

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

---

## Configuration

### Confidence Thresholds
`backend/learning/weight_decision_engine.py`
```python
HIGH_CONFIDENCE = 0.50
MEDIUM_CONFIDENCE = 0.30
```

### Validation Bounds
`backend/learning/weight_validator.py`
```python
MIN_WEIGHT = 0
MAX_WEIGHT = 40
MAX_TOTAL_SCORE_IMPACT = 0.20
```

### Rollback Settings
`backend/learning/weight_deployer.py`
```python
STRIKE_RATE_DROP_THRESHOLD = 0.05
MONITORING_PERIOD_HOURS = 24
```

---

## Troubleshooting

### Changes not reflected?
- Wait 5 min (cache TTL)
- Check DynamoDB version
- Restart application

### Validation fails?
- Use `--dry-run` to preview
- Check conflicting weights
- Adjust magnitudes

### Need to rollback?
```bash
python scripts/deploy_weight_changes.py --rollback <version>
```

---

**Quick Help**: See `WEIGHT_AUTO_TUNING_RULES.md` for complete documentation
