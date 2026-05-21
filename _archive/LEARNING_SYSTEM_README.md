# Daily Learning and Automated Improvement System

## Overview

Your betting system now includes a comprehensive learning engine that:
- **Analyzes past performance** daily
- **Adjusts strategies** based on what works
- **Optimizes bankroll** management
- **Calculates optimal stakes** using Kelly Criterion
- **Tracks toward 50% weekly returns**

## How the Learning System Works

### 1. **Daily Learning Cycle** (`daily_learning_cycle.py`)

Runs every morning before the first races:

```powershell
python daily_learning_cycle.py
```

**What it does:**
- Loads all bet results from last 30 days from DynamoDB
- Analyzes performance by:
  - Odds ranges (favorites vs outsiders vs longshots)
  - Bet types (WIN vs EACH-WAY)
  - Courses (which tracks we perform best at)
  - Common mistake patterns
  - Winning patterns and tags
- Updates `prompt.txt` with learned insights
- Adjusts current bankroll based on actual P&L
- Updates Lambda environment variables

### 2. **Bankroll Management**

**Starting bankroll:** €1,000  
**Target:** 50% weekly returns (€500/week)

**Strategy:**
- Uses **fractional Kelly Criterion** (25% Kelly for safety)
- Never risks more than **5% of bankroll** on a single bet
- Minimum stake: **€2**
- Stakes round to nearest **€0.50**

**Stake calculation factors:**
- Odds value
- Win probability (p_win)
- Place probability (p_place for EW bets)
- Current bankroll
- Bet type (WIN vs EW)

### 3. **Lambda Integration** (`lambda_learning_layer.py`)

Every time Lambda runs (every 2 hours), it:

1. **Analyzes recent performance** (last 7 days)
2. **Calculates current bankroll** from actual results
3. **Adjusts confidence** levels based on recent ROI:
   - ROI < -10%: Reduce confidence by 15 points
   - ROI < 0%: Reduce confidence by 5 points
   - ROI > 20%: Increase confidence by 5 points
4. **Calculates optimal stakes** for each pick
5. **Adds expected ROI** to each selection

### 4. **UI Display**

The frontend now shows for each pick:
- **💰 Suggested Stake:** The exact amount to bet (e.g., €8.50)
- **Bankroll:** Current total bankroll
- **Expected ROI:** Projected return on this bet

## Running the System

### Initial Setup

1. **Set initial bankroll** in Lambda environment:
```powershell
aws lambda update-function-configuration `
  --function-name BettingWorkflowScheduled `
  --environment "Variables={BANKROLL=1000.0,...}"
```

2. **Schedule daily learning** (run at 8 AM before races):
```powershell
# Create Windows Task Scheduler task
.\setup_daily_learning_task.ps1
```

### Daily Workflow

**8:00 AM** - Daily learning cycle runs automatically:
- Analyzes yesterday's results
- Updates strategy with insights
- Adjusts bankroll

**10 AM, 12 PM, 2 PM, 4 PM, 6 PM, 8 PM, 10 PM** - Lambda runs:
- Fetches latest odds
- Generates picks with detailed analysis
- Calculates optimal stakes
- Stores in DynamoDB

**Frontend** - View picks anytime:
- See suggested stake amounts
- Track current bankroll
- Monitor expected returns

### Manual Learning Run

Force a learning cycle anytime:
```powershell
python daily_learning_cycle.py
```

## Performance Tracking

### What Gets Analyzed

**By Odds Range:**
- Favorites (odds < 3.0)
- Mid-prices (3.0 - 6.0)
- Outsiders (6.0 - 12.0)
- Longshots (> 12.0)

**By Course:**
- Win rates at specific tracks
- Best performing venues
- Tracks to avoid

**By Bet Type:**
- WIN strike rate
- EW place rate
- ROI comparison

**Mistake Patterns:**
- High-confidence losers
- Failed tag combinations
- Suspicious race patterns

**Success Patterns:**
- Winning tag combinations
- Profitable course/distance forms
- Effective research factors

### Learning Insights Applied

The system automatically:
- **Avoids** patterns that lose money
- **Focuses** on profitable selections
- **Adjusts** confidence thresholds
- **Prioritizes** winning courses/trainers
- **Flags** suspicious races

Example insights:
```
• AVOID longshot selections - losing 15% ROI
• FOCUS on mid_price selections - strong 22% ROI
• Prioritize selections at: Cheltenham, Newmarket, Ascot
• Be cautious at: Southwell, Wolverhampton, Lingfield
• Winning pattern: prioritize COURSE_WINNER selections
```

## Bankroll Growth Projection

**Target:** 50% weekly returns

**Weekly:**
- Week 1: €1,000 → €1,500
- Week 2: €1,500 → €2,250
- Week 3: €2,250 → €3,375
- Week 4: €3,375 → €5,063

**Monthly:** ~400% growth if target achieved

**Safety Features:**
- Maximum 5% risk per bet prevents catastrophic losses
- Stop-loss at 20% of initial bankroll (€200 minimum)
- Confidence adjustments reduce stakes during losing streaks
- Kelly Criterion optimizes long-term growth

## Monitoring Your Progress

### Check Current Bankroll

```powershell
aws lambda get-function-configuration `
  --function-name BettingWorkflowScheduled `
  --query 'Environment.Variables.BANKROLL'
```

### View Recent Performance

```powershell
aws dynamodb scan `
  --table-name SureBetBets `
  --filter-expression "attribute_exists(#result)" `
  --expression-attribute-names '{"#result":"result"}' `
  --max-items 20
```

### Run Performance Analysis

```python
python learning_engine.py
```

## Files in Learning System

- **`learning_engine.py`** - Core learning algorithms and pattern analysis
- **`lambda_learning_layer.py`** - Lightweight learning for Lambda (bankroll tracking, stake calculation)
- **`daily_learning_cycle.py`** - Daily automation script
- **`prompt.txt`** - Gets automatically updated with insights

## Environment Variables

Lambda needs:
```
BANKROLL=1000.0               # Current bankroll (auto-updated)
TARGET_WEEKLY_RETURN=0.50     # 50% weekly target
BETFAIR_USERNAME=cmccar02
BETFAIR_PASSWORD=Liv!23456
BETFAIR_APP_KEY=XDDM8EHzaw8tokvQ
SUREBET_DDB_TABLE=SureBetBets
```

## Best Practices

1. **Let the system learn** - Don't override stakes initially
2. **Track all results** - Mark wins/losses in DynamoDB
3. **Run daily learning** - Keep the AI improving
4. **Monitor bankroll** - Watch the growth
5. **Trust the math** - Kelly Criterion is proven
6. **Be patient** - 50% weekly is aggressive but achievable with edge

## Updating Bet Results

After each race, update results in DynamoDB:

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SureBetBets')

table.update_item(
    Key={'bet_id': '<bet_id_here>'},
    UpdateExpression='SET #result = :result',
    ExpressionAttributeNames={'#result': 'result'},
    ExpressionAttributeValues={':result': 'won'}  # or 'placed' or 'lost'
)
```

Or use the bulk update script:
```powershell
python update_results_from_betfair.py
```

---

**Your system is now a learning, improving betting machine! 🚀**

Each day it gets smarter. Each bet is optimally sized. The target: professional gambler level returns.
