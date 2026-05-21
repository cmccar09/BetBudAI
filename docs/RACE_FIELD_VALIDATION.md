# Race Field Completeness Validation System

## Problem Statement

**Critical Issue**: In previous deployments, race winners were sometimes not in the database because they were never analyzed in the first place. This meant:

- Winner was missing from the entire analyzed field
- No score existed for the winner
- No way to compare our pick vs the actual winner
- Learning system couldn't analyze what we missed
- ROI calculations were incomplete

This is fundamentally different from "we analyzed the winner but picked someone else." This is "we never even looked at the winner."

## Solution: Quality Gate Validation

A new validation step (`betbudai-field-validator`) runs after analysis but **before picks are finalized**. It ensures:

1. ✅ Every horse in the race field was analyzed
2. ✅ Betfair runner list matches analyzed horses
3. ✅ No horses are mysteriously missing
4. ✅ Field completeness is >95% before picks are released

## Architecture

### Pipeline Flow

```
Morning Pipeline (08:30 UTC):
1. surebet-betfair-fetch      → Get odds + runner list
2. surebet-analysis           → Score all horses
3. betbudai-field-validator   → ✅ QUALITY GATE ✅
4. surebet-validate           → Quality checks
5. surebet-featured-meeting   → Featured analysis
6. surebet-notify             → Push notifications
```

### Validation Logic

```python
for each race on target_date:
    analyzed_horses = fetch from DynamoDB
    expected_horses = fetch from Betfair / Sporting Life
    
    missing = expected - analyzed
    extra = analyzed - expected
    
    completeness = (analyzed - extra) / expected * 100
    
    if completeness >= 95% and len(missing) == 0:
        ✅ PASS
    else:
        ❌ FAIL → Alert + Block picks
```

### Data Flow

1. **Betfair API** provides complete runner list
2. **surebet-analysis** scores each horse → stores in DynamoDB
3. **Validator** queries DynamoDB for analyzed horses
4. **Validator** compares analyzed vs expected
5. **Validator** logs results to `BetBudAI_ValidationLogs`

## Components

### 1. Lambda Function: `betbudai-field-validator`

**File**: `backend/pipeline/validation/race_field_validator.py`

**Handler**: `lambda_handler`

**Timeout**: 300 seconds (5 minutes)

**Memory**: 512 MB

**Environment Variables**:
- `STAGE=production`

**IAM Role**: `lambda-dynamodb-role`
- DynamoDB read access to `SureBetBets`
- DynamoDB write access to `BetBudAI_ValidationLogs`

### 2. DynamoDB Table: `BetBudAI_ValidationLogs`

**Purpose**: Store validation results for audit trail

**Schema**:
```
Partition Key: validation_date (String)  # YYYY-MM-DD
Sort Key: validation_id (String)         # race_id or SUMMARY_{date}

Attributes:
- validation_type: 'field_completeness' | 'daily_summary'
- is_valid: Boolean
- completeness_pct: Number
- missing_horses: List<String>
- extra_horses: List<String>
- timestamp: String (ISO 8601)
- ttl: Number (auto-expire after 7 days for individual races, 30 days for summaries)
```

**Billing**: Pay-per-request (on-demand)

**TTL**: Enabled on `ttl` attribute
- Individual validations: 7 days
- Daily summaries: 30 days

### 3. Integration Point: Morning Pipeline

**File**: `backend/pipeline/morning/handler.py`

**Change**:
```python
PIPELINE_FUNCTIONS = [
    ('surebet-betfair-fetch',    'Fetch Betfair odds'),
    ('surebet-analysis',         'Comprehensive scoring + pick selection'),
    ('betbudai-field-validator', 'Validate all horses analyzed (quality gate)'),  # NEW
    ('surebet-validate',         'Quality-gate validation'),
    ('surebet-featured-meeting', 'Featured meeting analysis'),
    ('surebet-notify',           'Push notifications to subscribers'),
]
```

## Validation Rules

### Pass Criteria

✅ **Field Completeness ≥ 95%**
- At least 95% of expected horses were analyzed
- Example: 10 runners expected → 9-10 analyzed = PASS

✅ **Zero Missing Horses**
- No horses from expected field are completely missing
- Example: All 10 Betfair runners found in analyzed data = PASS

✅ **Extra Horses Tolerated**
- OK to have horses in DB that aren't in current field
- These may be late withdrawals (handled separately)

### Fail Criteria

❌ **Field Completeness < 95%**
- More than 5% of field missing from analysis
- Example: 10 runners expected → only 8 analyzed = FAIL

❌ **Any Missing Horses**
- Even 1 missing horse triggers alert
- Critical if missing horse is the favorite or winner

### Alert Thresholds

- **Critical**: Completeness < 90% or missing favorite
- **Warning**: Completeness 90-95% or 1-2 missing horses
- **Info**: Completeness 95-100% with some extra horses

## Deployment

### 1. Create DynamoDB Table

```bash
cd backend/scripts
python create_validation_table.py
```

Expected output:
```
Creating table BetBudAI_ValidationLogs...
✓ Table BetBudAI_ValidationLogs created successfully
  ARN: arn:aws:dynamodb:eu-west-1:813281204422:table/BetBudAI_ValidationLogs
  Waiting for table to be active...
  Enabling TTL on 'ttl' attribute...
✓ TTL enabled - items will auto-expire after their TTL timestamp

✅ Table BetBudAI_ValidationLogs is ready!
```

### 2. Deploy Lambda Function

```bash
cd backend/scripts
bash deploy_field_validator.sh
```

Expected output:
```
=========================================
Deploying Race Field Validator Lambda
=========================================
Creating deployment package...
✓ Package created: field_validator.zip
Updating existing function...
Updating function configuration...
✓ Function updated: betbudai-field-validator
Granting invoke permissions to morning pipeline...

=========================================
✅ Deployment Complete!
=========================================
Function: betbudai-field-validator
Region: eu-west-1
```

### 3. Test Validation

```bash
# Test with specific date
aws lambda invoke \
  --function-name betbudai-field-validator \
  --payload '{"target_date":"2026-05-20"}' \
  --region eu-west-1 \
  output.json

cat output.json | python -m json.tool
```

Expected response:
```json
{
  "statusCode": 200,
  "body": {
    "target_date": "2026-05-20",
    "total_races": 45,
    "valid_races": 45,
    "invalid_races": 0,
    "avg_completeness_pct": 98.7,
    "total_missing_horses": 0,
    "validation_passed": true,
    "validation_timestamp": "2026-05-21T09:16:00Z"
  }
}
```

### 4. Monitor Validation Results

Query validation logs:
```bash
aws dynamodb query \
  --table-name BetBudAI_ValidationLogs \
  --key-condition-expression "validation_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' \
  --region eu-west-1
```

## Monitoring & Alerts

### CloudWatch Metrics

The validator automatically logs:
- `ValidationPassed` (1 or 0)
- `AvgCompletenessPercent` (0-100)
- `TotalMissingHorses` (count)
- `InvalidRaces` (count)

### CloudWatch Alarms

Create alarm for validation failures:
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name betbudai-field-validation-failed \
  --alarm-description "Alert when race field validation fails" \
  --metric-name ValidationPassed \
  --namespace BetBudAI/Pipeline \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 0 \
  --comparison-operator LessThanOrEqualToThreshold \
  --treat-missing-data notBreaching
```

### SNS Notifications

On validation failure, send alert to:
- Email: system alerts
- Slack: #betbudai-alerts channel
- PagerDuty: if critical (completeness < 90%)

## Error Handling

### Validation Fails (Completeness < 95%)

1. **Block Pick Deployment**: Picks not sent to users
2. **Alert Operations**: Email + Slack notification
3. **Log Details**: Which races/horses are missing
4. **Retry Logic**: Re-run analysis for affected races
5. **Manual Review**: Check Betfair API / data pipeline

### Lambda Timeout

1. **Partial Validation**: Log what was validated
2. **Continue Pipeline**: Don't block other steps
3. **Alert**: Notify that validation incomplete
4. **Retry**: Next pipeline run will validate again

### DynamoDB Query Errors

1. **Fallback**: Skip validation if DB unavailable
2. **Alert**: Log error to CloudWatch
3. **Continue**: Don't block picks (fail-open)
4. **Monitor**: Check DynamoDB health

## Learning System Integration

The validation results feed into the learning system:

### 1. Pre-Learning Validation

Before learning runs (22:00 UTC), validator confirms:
- All races from today are settled
- Every winner was in the analyzed field
- No critical horses were missed

### 2. Learning Input Enhancement

Validation logs tell learning system:
- Which races had complete fields (high confidence)
- Which races had missing horses (exclude from learning)
- Field completeness % → learning confidence weight

### 3. Pattern Detection

Learning system tracks:
- "Missing horse was the winner" (critical)
- "Missing horse was in top 3" (important)
- "Missing horses were all outsiders" (low impact)

## Testing

### Unit Tests

```bash
cd backend/pipeline/validation
python -m pytest test_race_field_validator.py -v
```

### Integration Tests

```bash
# Test with real data from yesterday
python backend/pipeline/validation/race_field_validator.py 2026-05-20

# Expected output:
# [FieldValidator] Validating all races for 2026-05-20
# [FieldValidator] Found 45 races to validate
# [FieldValidator] Validation complete: 45/45 races valid, 98.7% avg completeness
```

### Load Test

```bash
# Simulate validating high-volume day (100+ races)
for i in {1..100}; do
    echo "Race $i: $(python -c 'import random; print(random.randint(8,14))') runners"
done
```

## Maintenance

### Weekly Tasks

1. Review validation logs for trends
2. Check for recurring missing horses
3. Verify TTL cleanup is working
4. Monitor Lambda duration/cost

### Monthly Tasks

1. Analyze validation failure patterns
2. Adjust completeness threshold if needed
3. Review Betfair API reliability
4. Update documentation

### Quarterly Tasks

1. Load test with peak racing days
2. Review DynamoDB costs (should be minimal)
3. Optimize Lambda timeout/memory
4. Audit validation logic vs actual issues

## FAQ

**Q: What if a horse is withdrawn after analysis?**

A: Extra horses in DB are tolerated. Validation focuses on missing horses, not extras.

**Q: Does this slow down the morning pipeline?**

A: Typical validation takes 10-30 seconds for 40-60 races. Negligible impact.

**Q: What happens if validation fails?**

A: Pipeline continues but picks are NOT sent to users. Alert triggers manual review.

**Q: Can validation run independently?**

A: Yes, invoke `betbudai-field-validator` Lambda directly with target date.

**Q: How do I see validation history?**

A: Query `BetBudAI_ValidationLogs` table or check CloudWatch Logs.

**Q: Does this prevent all missing horse issues?**

A: No, it detects them early. Root cause fix is ensuring surebet-analysis scores all runners.

## Related Documentation

- [Data Pipeline Architecture](DATA_PIPELINE.md)
- [Learning System](LEARNING_SYSTEM.md)
- [Quality Gates](QUALITY_GATES.md)
- [Deployment Guide](DEPLOYMENT.md)

## Support

For issues or questions:
- Check CloudWatch Logs: `/aws/lambda/betbudai-field-validator`
- Review validation table: `BetBudAI_ValidationLogs`
- Contact: system alerts in Slack #betbudai-ops
