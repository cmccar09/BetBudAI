# BetBudAI Debugging Quick Reference

**One-page reference for common debugging tasks**

---

## Featured Meeting Issues

### Check API Response
```bash
# Quick check - shows outcomes for top 5 races
curl -s "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park" | \
python -c "import sys,json; d=json.load(sys.stdin); [print(f\"{r['time_user']} {r['runners'][0]['horse']:20s} {r['runners'][0].get('outcome','?')}\") for r in d['races'][:5]]"
```

### Check DynamoDB Records
```bash
# Find all records for a specific horse (may have duplicates!)
aws dynamodb query \
  --table-name SureBetBets \
  --key-condition-expression "bet_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' \
  --region eu-west-1 \
  --query 'Items[?contains(bet_id.S, `Rolltight`)].[bet_id.S,outcome.S,is_featured_meeting.BOOL]'
```

### Fix Wrong Outcome
```bash
# Run the fix script
python scripts/fix_main_system_outcomes.py
```

### Restart Lambda (Force Refresh)
```bash
# Update environment variable to force restart
aws lambda update-function-configuration \
  --function-name betbudai-picks-api \
  --region eu-west-1 \
  --environment "Variables={CACHE_BUST=$(date +%s)}"

# Wait 5 seconds, then test
sleep 5 && curl "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park"
```

---

## ROI Calculations

### Check Overall ROI
```bash
curl -s "https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results/cumulative-roi" | python -m json.tool | grep -A 2 "roi"
```

### Calculate ROI from Script
```bash
python scripts/calculate_roi.py --date 2026-05-20
```

---

## Database Operations

### Query All Picks for Date
```bash
aws dynamodb query \
  --table-name SureBetBets \
  --key-condition-expression "bet_date = :date" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"}}' \
  --region eu-west-1 \
  --output table
```

### Find Featured Picks Only
```bash
aws dynamodb query \
  --table-name SureBetBets \
  --key-condition-expression "bet_date = :date" \
  --filter-expression "is_featured_meeting = :featured" \
  --expression-attribute-values '{":date":{"S":"2026-05-20"},":featured":{"BOOL":true}}' \
  --region eu-west-1 \
  --query 'Items[*].[bet_id.S,horse.S,outcome.S]'
```

### Update Single Outcome (Python)
```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

table.update_item(
    Key={'bet_date': '2026-05-20', 'bet_id': 'YOUR_BET_ID_HERE'},
    UpdateExpression='SET #out = :win, #res = :win2',
    ExpressionAttributeNames={'#out': 'outcome', '#res': 'result'},
    ExpressionAttributeValues={':win': 'win', ':win2': 'WIN'}
)
```

---

## Deployment

### Deploy Frontend to Amplify
```bash
cd frontend
amplify publish --yes
```

### Deploy Lambda Function
```bash
# From project root
python scripts/deploy_lambda.py --function betbudai-picks-api
```

### Check Deployment Status
```bash
# Amplify deployment status
aws amplify list-apps --region eu-west-1

# Lambda last modified
aws lambda get-function --function-name betbudai-picks-api --region eu-west-1 --query 'Configuration.LastModified'
```

---

## Logging & Monitoring

### Lambda Logs (Last 5 Minutes)
```bash
aws logs tail /aws/lambda/betbudai-picks-api --region eu-west-1 --since 5m --follow
```

### Check Lambda Errors
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/betbudai-picks-api \
  --region eu-west-1 \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 3600))000
```

---

## Testing

### Test Featured Meeting API Locally
```bash
# Run local API test
python scripts/test_featured_api.py --date 2026-05-20 --course "Gowran Park"
```

### Test Frontend Locally
```bash
cd frontend
npm start
# Opens http://localhost:3000
```

---

## Common Errors

### "Permission denied: build/static"
```bash
# Clean build directory
rm -rf frontend/build
cd frontend && npm run build
```

### "Lambda timeout"
```bash
# Increase Lambda timeout
aws lambda update-function-configuration \
  --function-name betbudai-picks-api \
  --region eu-west-1 \
  --timeout 30
```

### "API returns 502 Bad Gateway"
```bash
# Check Lambda logs
aws logs tail /aws/lambda/betbudai-picks-api --region eu-west-1 --since 1h

# Check Lambda configuration
aws lambda get-function-configuration --function-name betbudai-picks-api --region eu-west-1
```

---

## File Locations

### Backend
- Lambda function: `backend/api/lambda_function.py`
- Featured meeting handler: Line ~963 in lambda_function.py
- Outcome normalization: Line ~1045 in lambda_function.py

### Frontend
- React app: `frontend/src/App.js`
- Featured meeting UI: Search for "Featured Meeting" in App.js

### Scripts
- Fix outcomes: `scripts/fix_main_system_outcomes.py`
- Add winners: `scripts/update_featured_results_corrected.py`
- Calculate ROI: `scripts/calculate_roi.py`

### Documentation
- Complete data flow: `docs/FEATURED_MEETING_DATA_FLOW.md`
- This reference: `docs/DEBUGGING_QUICK_REFERENCE.md`

---

## AWS Resource IDs

- **Lambda:** betbudai-picks-api (eu-west-1)
- **API Gateway:** e5na6ldp35 (SureBet API EU)
- **DynamoDB:** SureBetBets (eu-west-1)
- **Amplify:** d2cp2pfnzl7t60 (dev environment)
- **Base API URL:** https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com

---

**Last Updated:** 2026-05-20  
**See Also:** docs/FEATURED_MEETING_DATA_FLOW.md for detailed debugging guide
