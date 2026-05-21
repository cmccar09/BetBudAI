# Daily Learning System - Quick Start Guide

## What It Does

Automatically analyzes yesterday's race losses in parallel (10 races in ~1 minute) and recommends weight adjustments to improve predictions.

---

## Quick Start

### 1. Run Analysis (Yesterday's Races)
```bash
python scripts/run_daily_learning.py
```

**Output**:
- Loss patterns identified
- Weight recommendations
- Deployment plan
- Impact estimate

### 2. Review Results
```bash
python scripts/run_daily_learning.py --output report.json
cat report.json
```

### 3. Deploy Changes (Auto)
```bash
python scripts/run_daily_learning.py --auto-deploy
```

### 4. Preview Only (Dry Run)
```bash
python scripts/run_daily_learning.py --dry-run --verbose
```

---

## Common Commands

### Analyze Specific Date
```bash
python scripts/run_daily_learning.py --date 2026-05-19
```

### Use More Workers (Faster)
```bash
python scripts/run_daily_learning.py --max-workers 15
```

### Test System
```bash
python scripts/test_learning_system.py
```

---

## Understanding Output

### Summary Section
```
Date: 2026-05-20
Races Analyzed: 8/15
Win Rate: 46.7%
Dominant Loss Type: improver_missed
```

### Recommendations Section
```
Deployment: DEPLOY_IMMEDIATELY
High Priority: 3 changes

Top Priority Weight Changes:
  - form_velocity_bonus: +5.0 (confidence: 0.72, 80% of races)
  - jockey_quality: +4.0 (confidence: 0.65, 60% of races)
```

### Impact Estimate
```
Win Rate Improvement: +5.0%
ROI Improvement: +8.0%
Confidence: medium
```

---

## Deployment Levels

| Level | Meaning | Action |
|-------|---------|--------|
| `DEPLOY_IMMEDIATELY` | 3+ high-priority changes | Deploy now |
| `DEPLOY_TONIGHT` | 1+ medium-priority changes | Review and deploy |
| `MONITOR` | Only low-priority changes | Continue monitoring |
| `NO_ACTION` | No patterns found | No changes needed |

---

## Configuration

### Environment Variables
```bash
export MAX_WORKERS=10         # Parallel workers (5-20)
export WORKER_TIMEOUT=60      # Seconds per race (30-120)
export MIN_CONFIDENCE=0.3     # Pattern threshold (0.2-0.5)
export MIN_SAMPLES=3          # Minimum races (3-10)
```

### Command Line Options
```bash
python scripts/run_daily_learning.py \
  --date 2026-05-20 \
  --max-workers 10 \
  --min-samples 3 \
  --auto-deploy \
  --output report.json
```

---

## AWS Lambda Setup (Automated)

### 1. Deploy Lambda
```bash
# Lambda function: surebet-learning
# Handler: backend.learning.orchestrator.lambda_handler
# Runtime: Python 3.12
# Memory: 512MB
# Timeout: 5 minutes
```

### 2. EventBridge Trigger
```bash
# Schedule: cron(0 22 * * ? *)  # 22:00 UTC daily
# Payload:
{
  "target_date": null,  # Auto (yesterday)
  "min_samples": 3,
  "max_workers": 10
}
```

### 3. IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:Scan",
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem"
  ],
  "Resource": "arn:aws:dynamodb:eu-west-1:*:table/SureBetBets"
}
```

---

## Troubleshooting

### "No settled picks found"
**Cause**: No races analyzed for target date yet  
**Fix**: Wait for settlement (races settle 30min after finish) or use earlier date

### "Workers timing out"
**Cause**: Sporting Life API slow or network issues  
**Fix**: Increase `--worker-timeout 90` or reduce `--max-workers 5`

### "No patterns detected"
**Cause**: Too few losses (<3 races) or all low severity  
**Fix**: Lower `--min-samples 2` or wait for more data

### "Deployment failed"
**Cause**: DynamoDB permissions or invalid weights  
**Fix**: Check IAM role, validate weight values

---

## Architecture Overview

```
┌─────────────────────────────────────────┐
│   Master Orchestrator                   │
│   - Fetch settled picks (DynamoDB)      │
│   - Filter to losses                    │
│   - Prepare race jobs                   │
│   - Fan-out to workers                  │
└─────────────────────────────────────────┘
              │
              ├──────────────────┐
              ▼                  ▼
  ┌─────────────────┐   ┌─────────────────┐
  │ Worker (Race 1) │   │ Worker (Race N) │
  │ - Fetch result  │   │ - Fetch result  │
  │ - Compare pick  │   │ - Compare pick  │
  │ - Find gaps     │   │ - Find gaps     │
  │ - Recommend     │   │ - Recommend     │
  └─────────────────┘   └─────────────────┘
              │                  │
              └────────┬─────────┘
                       ▼
          ┌───────────────────────┐
          │   Results Aggregator  │
          │   - Find patterns     │
          │   - Rank changes      │
          │   - Create plan       │
          └───────────────────────┘
```

**Performance**: 10 races in ~1 minute (5x faster than sequential)

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/learning/orchestrator.py` | Master coordinator |
| `backend/learning/race_analyzer.py` | Worker analysis logic |
| `backend/learning/aggregator.py` | Results processor |
| `scripts/run_daily_learning.py` | CLI entry point |
| `scripts/test_learning_system.py` | Test suite |
| `FAN_OUT_ARCHITECTURE.md` | Technical documentation |
| `LEARNING_QUICKSTART.md` | This guide |

---

## Next Steps

1. **Test locally**: `python scripts/test_learning_system.py`
2. **Run on historical data**: `python scripts/run_daily_learning.py --date 2026-05-19`
3. **Review recommendations**: Check output carefully
4. **Deploy changes**: Use `--auto-deploy` after validation
5. **Monitor impact**: Track win rate and ROI trends

---

## Support

- **Documentation**: See `FAN_OUT_ARCHITECTURE.md` for technical details
- **Issues**: GitHub Issues or Slack #betbudai-dev
- **Questions**: Tag @engineering in Slack

---

## Key Benefits

✓ **5x faster** than sequential processing  
✓ **Automated** pattern detection  
✓ **Confident** recommendations (30%+ threshold)  
✓ **Safe** deployment with validation  
✓ **Observable** with detailed logging  
✓ **Production-ready** error handling

---

**Version**: 1.0  
**Last Updated**: 2026-05-20
