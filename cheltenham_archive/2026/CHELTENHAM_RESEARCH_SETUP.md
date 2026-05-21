# Daily Cheltenham Research Setup

## Overview
Automated daily monitoring system that tracks potential Cheltenham Festival horses throughout the season.

## What It Does

### Daily (10am UTC)
1. ✅ Scans all today's Grade 1/2/3 races
2. ✅ Identifies horses from elite trainers (Mullins, Elliott, Henderson, etc.)
3. ✅ Tracks scoring trends over time
4. ✅ Flags improving form patterns
5. ✅ Builds historical profiles for Festival picks

### Outputs
- **Daily Report**: Lists all Cheltenham candidates analyzed
- **Improving Form Alert**: Horses trending upward (potential value)
- **High Scorers**: 75+ confidence picks to watch
- **Historical Database**: Track record of each horse's performances

## Setup Instructions

### 1. Create DynamoDB Table

```bash
aws dynamodb create-table \
    --table-name CheltenhamResearch \
    --attribute-definitions \
        AttributeName=horse_name,AttributeType=S \
        AttributeName=research_date,AttributeType=S \
    --key-schema \
        AttributeName=horse_name,KeyType=HASH \
        AttributeName=research_date,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region eu-west-1
```

### 2. Create Global Secondary Index (for date queries)

```bash
aws dynamodb update-table \
    --table-name CheltenhamResearch \
    --attribute-definitions AttributeName=research_date,AttributeType=S \
    --global-secondary-index-updates \
        "[{\"Create\":{\"IndexName\":\"ResearchDateIndex\",\"KeySchema\":[{\"AttributeName\":\"research_date\",\"KeyType\":\"HASH\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}}]" \
    --region eu-west-1
```

### 3. Deploy Lambda Function

```bash
# Package lambda
cd C:\Users\charl\OneDrive\futuregenAI\Betting
Compress-Archive -Path lambda_cheltenham_research.py -DestinationPath cheltenham_research.zip -Force

# Deploy
aws lambda create-function \
    --function-name CheltenhamDailyResearch \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-dynamodb-role \
    --handler lambda_cheltenham_research.lambda_handler \
    --zip-file fileb://cheltenham_research.zip \
    --timeout 60 \
    --region eu-west-1
```

### 4. Create EventBridge Schedule

```bash
# Schedule for 10am daily
aws scheduler create-schedule \
    --name CheltenhamDailyResearch \
    --schedule-expression "cron(0 10 * * ? *)" \
    --flexible-time-window Mode=OFF \
    --target '{
        "Arn": "arn:aws:lambda:eu-west-1:YOUR_ACCOUNT:function:CheltenhamDailyResearch",
        "RoleArn": "arn:aws:iam::YOUR_ACCOUNT:role/EventBridgeSchedulerRole"
    }' \
    --region eu-west-1
```

## Local Testing

### Run Daily Research Manually
```bash
python daily_cheltenham_research.py
```

### View Today's Report Only
```bash
python daily_cheltenham_research.py --track-only
```

### Integration with Existing Workflows
The research runs AFTER `comprehensive_workflow.py` completes, so it has today's picks to analyze.

**Recommended Schedule:**
- 12:15pm: comprehensive_workflow.py runs (analyzes today's races)
- 1:00pm: CheltenhamDailyResearch runs (tracks Cheltenham candidates from today's picks)

## What Gets Tracked

### Candidate Criteria
- ✅ Elite trainer (Mullins, Elliott, Henderson, Nicholls, de Bromhead, Skelton)
- ✅ Grade 1, 2, 3, or Listed race
- ✅ Horse analyzed by comprehensive system
- ✅ Score tracked over time

### Trend Analysis
- **Improving**: Score up 10+ points from recent average
- **Declining**: Score down 10+ points
- **Stable**: Within 10 points of average
- **New**: First time tracked

### Alert Triggers
- Score ≥ 75 (High confidence)
- Form trend = improving
- Elite trainer + improving + 70+ score = **CHELTENHAM WATCH**

## Example Output

```
================================================================================
DAILY CHELTENHAM RESEARCH REPORT - 2026-02-15
================================================================================

SUMMARY:
  Total horses analyzed: 12
  High scorers (75+): 3
  Improving form: 5
  New candidates identified: 2

🔥 IMPROVING FORM (Watch for Cheltenham):
================================================================================
  Stede Bonnet               94pts (+12.5 trend)
    Trainer: W. P. Mullins                Race: 2m Listed Nov Hrd

  The Lovely Man             88pts (+8.3 trend)
    Trainer: Gordon Elliott              Race: 3m3f Listed Hcap Chs

⭐ HIGH SCORERS TODAY (75+ pts):
================================================================================
  Stede Bonnet               94pts VERY_HIGH
    2m Listed Nov Hrd - Punchestown

  The Lovely Man             88pts HIGH
    3m3f Listed Hcap Chs - Punchestown

  Tarbat Ness                85pts HIGH
    2m Hcap - Newcastle

================================================================================
```

## Use Cases

### Pre-Cheltenham (Now - March)
- Track horses in prep races
- Identify improving trends
- Spot horses peaking at right time
- Build confidence in Festival picks

### During Cheltenham Week
- Reference historical scores
- Compare form trends
- Validate high-confidence picks
- Apply Cheltenham bonuses to known quantities

### Post-Festival Learning
- Analyze what worked
- Which trainers/trends delivered
- Improve scoring for next year

## Benefits

1. **Pattern Recognition**: See which horses consistently score high
2. **Form Timing**: Identify horses peaking vs. declining
3. **Trainer Patterns**: Track Mullins/Elliott prep strategies
4. **Value Spotting**: Find improving horses before odds shorten
5. **Confidence Building**: Historical data validates Festival picks

## Next Steps

1. ✅ Create DynamoDB table
2. ✅ Deploy Lambda function
3. ✅ Schedule EventBridge trigger
4. 📊 Run daily for 4 weeks leading to Cheltenham
5. 🎯 Use data to enhance Festival picks

---

**Status**: Ready to deploy and start tracking Cheltenham candidates daily!
