# BetBudAI Automated Learning System - Production Design

**Version**: 1.0  
**Date**: 2026-05-20  
**Status**: Production-Ready Design  
**Target Deployment**: Week of 2026-05-20

---

## Executive Summary

This document outlines a comprehensive automated learning system that performs deep loss analysis on EVERY race, processes historical data, and auto-tunes scoring weights daily. The system leverages the existing agentic orchestration architecture and extends it with specialized loss analysis agents and weight optimization logic.

**Key Goals**:
- Analyze 100% of losses (not just samples)
- Identify systematic biases in scoring model
- Auto-adjust weights based on validated patterns
- Increase strike rate from 20-25% to 30-35% within 60 days
- Achieve monthly profitability (ROI >10%)

**Architecture**: Fan-out orchestration with 5-10 parallel loss analysis agents, centralized aggregation, and safe weight deployment with A/B testing and rollback.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Daily Learning Pipeline](#2-daily-learning-pipeline)
3. [Deep Loss Analysis Process](#3-deep-loss-analysis-process)
4. [Fan-Out Orchestration](#4-fan-out-orchestration)
5. [Weight Auto-Adjustment Logic](#5-weight-auto-adjustment-logic)
6. [Monthly Historical Analysis](#6-monthly-historical-analysis)
7. [Storage Schema](#7-storage-schema)
8. [Validation & Safety](#8-validation--safety)
9. [Implementation Plan](#9-implementation-plan)
10. [Code Structure](#10-code-structure)
11. [Deployment Checklist](#11-deployment-checklist)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AUTOMATED LEARNING SYSTEM                       │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  EventBridge │──────▶│    Master    │──────▶│   DynamoDB   │
│  21:30 UTC   │       │ Orchestrator │       │   Learning   │
└──────────────┘       │    Lambda    │       │   Insights   │
                       └──────┬───────┘       └──────────────┘
                              │
                              │ Fan-out (5-10 workers)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Loss Analysis │     │ Loss Analysis │ ... │ Loss Analysis │
│   Worker 1    │     │   Worker 2    │     │   Worker N    │
│               │     │               │     │               │
│ • Fetch SL    │     │ • Fetch SL    │     │ • Fetch SL    │
│ • Compare     │     │ • Compare     │     │ • Compare     │
│ • Categorize  │     │ • Categorize  │     │ • Categorize  │
│ • Recommend   │     │ • Recommend   │     │ • Recommend   │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Aggregation    │
                    │    & Pattern     │
                    │   Recognition    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Weight Optimizer │
                    │                  │
                    │ • Calculate Δs   │
                    │ • Safety Checks  │
                    │ • Deploy to DB   │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
        ┌──────────────┐        ┌──────────────┐
        │  SureBetBets │        │  CloudWatch  │
        │    (Weights  │        │   Metrics    │
        │     Config)  │        │   & Alarms   │
        └──────────────┘        └──────────────┘
```

### 1.2 Component Overview

| Component | Purpose | Technology | Scaling |
|-----------|---------|------------|---------|
| **Master Orchestrator** | Fetch settled picks, spawn workers, aggregate findings | Lambda (Python 3.11) | 1 instance |
| **Loss Analysis Workers** | Analyze individual races in parallel | Lambda (Python 3.11) | 5-10 concurrent |
| **Weight Optimizer** | Calculate weight adjustments, validate, deploy | Lambda (Python 3.11) | 1 instance |
| **Historical Analyzer** | Monthly batch analysis (30 days) | Lambda (15min timeout) | 1 instance |
| **Learning Insights Table** | Store individual loss analyses | DynamoDB | On-demand |
| **Pattern Aggregator** | Aggregate patterns across losses | Lambda/DynamoDB | 1 instance |

### 1.3 Integration Points

```
EXISTING SYSTEM                          NEW LEARNING SYSTEM
───────────────────                      ───────────────────

┌──────────────────┐                    ┌──────────────────┐
│  Evening Pipeline│                    │ Daily Learning   │
│   (21:00 UTC)    │                    │   (21:30 UTC)    │
│                  │                    │                  │
│ • SL Results     │──────────┐         │ • Query settled  │
│ • Settlement     │          │         │   picks (21:00+) │
│ • P&L Calc       │          │         │ • Loss analysis  │
└──────────────────┘          │         │ • Weight tune    │
                              │         └──────────────────┘
                              │                  │
                              ▼                  ▼
                       ┌──────────────────────────┐
                       │   SureBetBets Table      │
                       │                          │
                       │ • actual_result: LOSS    │
                       │ • race_winner            │
                       │ • selection_id           │
                       │ • score breakdown        │
                       └──────────────────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────┐
                       │   Weights Config         │
                       │   (SYSTEM_WEIGHTS)       │
                       │                          │
                       │ • Auto-updated daily     │
                       │ • Hot-reload (5min TTL)  │
                       └──────────────────────────┘
```

---

## 2. Daily Learning Pipeline

### 2.1 Pipeline Overview

**Trigger**: EventBridge cron rule at 21:30 UTC (30 minutes after evening settlement)

**Duration**: 5-8 minutes (parallel processing)

**Frequency**: Daily

### 2.2 Pipeline Steps

```
STEP 1: FETCH SETTLED PICKS (Master Orchestrator)
──────────────────────────────────────────────────
Input:  EventBridge trigger
Action: 
  - Query SureBetBets table for today's settled picks
  - Filter: actual_result = 'LOSS' OR 'WIN' (need both for context)
  - Extract: bet_id, horse, course, race_time, selection_id, 
             market_id, score breakdown, actual_result, race_winner
Output: List of 20-40 settled picks

STEP 2: FAN-OUT WORKERS (Master Orchestrator)
──────────────────────────────────────────────
Input:  List of settled picks with actual_result = 'LOSS'
Action:
  - Group losses into batches (1-2 races per worker)
  - Spawn 5-10 Lambda workers concurrently
  - Pass race context + bet record to each worker
Output: Worker invocation metadata

STEP 3: LOSS ANALYSIS (Workers, Parallel)
──────────────────────────────────────────
Input:  Single race + our pick + result data
Action:
  FOR EACH LOSS:
    1. Fetch race result from Sporting Life (winner + placed horses)
    2. Fetch full racecard data (all runners, odds, form)
    3. Compare our pick vs actual winner:
       - Odds differential
       - Form velocity (our pick vs winner)
       - Jockey upgrade (winner had better jockey?)
       - Trainer form (winner's trainer in better form?)
       - Class advantage (winner dropping class?)
       - Course history (winner had C&D wins we missed?)
       - Consistent placer bias (winner always places, we picked recent winner)
    4. Identify missing signals:
       - What features did winner have that we ignored?
       - What weight would have elevated winner above our pick?
    5. Calculate score gap:
       - Reconstruct winner's score
       - Gap = winner_score - our_pick_score
    6. Categorize loss type:
       - consistent_placer_missed (winner: 2-2-3-2-1, our pick: 1-7-5-1-8)
       - class_drop_missed (winner dropped from Class 2 to Class 4)
       - jockey_upgrade_missed (winner had Dettori, we picked apprentice)
       - trainer_form_missed (winner's trainer 3/5 winners this week)
       - pace_mismatch (winner suited fast pace, we picked front-runner)
       - form_velocity_missed (winner improving, our pick static)
       - course_specialist_missed (winner 3/5 at venue, we picked 0/10)
    7. Generate weight recommendations:
       {
         'consistency': +8,  # Boost consistent placers
         'class_drop_bonus': +12,  # Strengthen class droppers
         'recent_win': -5,  # Reduce over-reliance on last win
       }
Output: Loss analysis record → DynamoDB LearningInsights table

STEP 4: AGGREGATION (Master Orchestrator)
──────────────────────────────────────────
Input:  All worker results (20-40 loss analyses)
Action:
  1. Collect all loss analyses from DynamoDB
  2. Group by loss category:
     - consistent_placer_missed: 12 occurrences
     - class_drop_missed: 8 occurrences
     - jockey_upgrade_missed: 5 occurrences
     - etc.
  3. Extract common patterns:
     - 60% of losses: winner had better consistency than our pick
     - 40% of losses: winner dropping class (we under-weight class_drop)
     - 25% of losses: winner had jockey upgrade (Dettori, Buick, Moore)
  4. Calculate pattern confidence:
     - High confidence (5+ occurrences): Apply aggressive adjustment
     - Medium confidence (3-4 occurrences): Apply moderate adjustment
     - Low confidence (1-2 occurrences): Monitor, no adjustment yet
Output: Pattern summary + weight adjustment proposals

STEP 5: WEIGHT OPTIMIZATION (Weight Optimizer Lambda)
──────────────────────────────────────────────────────
Input:  Pattern summary + current weights
Action:
  1. Load current weights from DynamoDB (SYSTEM_WEIGHTS config)
  2. Calculate proposed adjustments:
     FOR EACH pattern with confidence ≥ 80%:
       IF pattern confirmed 5+ times in 7 days:
         adjustment = ±8 points (aggressive)
       ELSE IF pattern confirmed 3-4 times:
         adjustment = ±4 points (moderate)
       ELSE IF pattern confirmed 2 times:
         adjustment = ±2 points (conservative)
       ELSE:
         adjustment = 0 (monitor only)
  3. Apply safety bounds:
     - Max adjustment per weight per day: ±10 points
     - Min weight value: 0
     - Max weight value: 50
     - Total weight sum: normalize to ~400 points
  4. Validate no extreme changes (alert if any weight changes >15 pts)
  5. Store proposed weights in staging
  6. Deploy to production if validation passes
Output: Updated weights in SureBetBets table (SYSTEM_WEIGHTS)

STEP 6: VALIDATION & MONITORING
────────────────────────────────
Input:  Deployed weights
Action:
  1. Publish CloudWatch metrics:
     - DailyLearningCycles
     - TotalLossesAnalyzed
     - PatternsIdentified
     - WeightsAdjusted (count)
     - AvgWeightDelta
     - MaxWeightDelta
  2. Create CloudWatch alarm if:
     - MaxWeightDelta > 15 (human review needed)
     - WeightsAdjusted > 10 in single day (too aggressive)
  3. Store audit log in DynamoDB:
     - timestamp
     - old_weights
     - new_weights
     - patterns_detected
     - confidence_scores
     - approved_by: 'auto' or 'manual'
Output: Metrics + audit trail
```

### 2.3 Pipeline State Machine (Step Functions JSON)

```json
{
  "Comment": "Daily Learning Pipeline - Auto-tune weights from loss analysis",
  "StartAt": "FetchSettledPicks",
  "States": {
    "FetchSettledPicks": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-fetch-settled",
      "Next": "FanOutLossAnalysis",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 2,
          "MaxAttempts": 2,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "NotifyFailure"
        }
      ]
    },
    "FanOutLossAnalysis": {
      "Type": "Map",
      "ItemsPath": "$.losses",
      "MaxConcurrency": 10,
      "Iterator": {
        "StartAt": "AnalyzeSingleLoss",
        "States": {
          "AnalyzeSingleLoss": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-analyze-loss",
            "End": true,
            "Retry": [
              {
                "ErrorEquals": ["States.TaskFailed"],
                "IntervalSeconds": 1,
                "MaxAttempts": 2,
                "BackoffRate": 1.5
              }
            ]
          }
        }
      },
      "Next": "AggregatePatterns"
    },
    "AggregatePatterns": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-aggregate",
      "Next": "OptimizeWeights",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 2,
          "MaxAttempts": 2,
          "BackoffRate": 2.0
        }
      ]
    },
    "OptimizeWeights": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-optimize-weights",
      "Next": "ValidateWeights",
      "Retry": [
        {
          "ErrorEquals": ["States.TaskFailed"],
          "IntervalSeconds": 2,
          "MaxAttempts": 2,
          "BackoffRate": 2.0
        }
      ]
    },
    "ValidateWeights": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-validate-weights",
      "Next": "CheckValidation"
    },
    "CheckValidation": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.validation.passed",
          "BooleanEquals": true,
          "Next": "DeployWeights"
        },
        {
          "Variable": "$.validation.passed",
          "BooleanEquals": false,
          "Next": "NotifyManualReview"
        }
      ],
      "Default": "NotifyFailure"
    },
    "DeployWeights": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-deploy-weights",
      "Next": "PublishMetrics"
    },
    "PublishMetrics": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-publish-metrics",
      "End": true
    },
    "NotifyManualReview": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-notify-review",
      "End": true
    },
    "NotifyFailure": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-notify-failure",
      "End": true
    }
  }
}
```

---

## 3. Deep Loss Analysis Process

### 3.1 Loss Analysis Worker Logic

**Function**: `learning-analyze-loss` Lambda  
**Timeout**: 60 seconds  
**Memory**: 512 MB  
**Concurrency**: 10

#### Input Schema
```python
{
    "bet_id": "20260520_1430_Ascot_GoldenMiller",
    "bet_date": "2026-05-20",
    "horse": "Golden Miller",
    "course": "Ascot",
    "race_time": "14:30",
    "selection_id": "12345678",
    "market_id": "1.234567890",
    "odds": 4.5,
    "actual_result": "LOSS",
    "race_winner": "Silver Streak",
    "score_breakdown": {
        "recent_win": 16,
        "consistency": 6,
        "form_velocity_bonus": 10,
        "course_bonus": 12,
        "jockey_quality": 12,
        "class_drop_bonus": 0,
        "going_suitability": 16,
        "total_score": 92
    }
}
```

#### Processing Steps

```python
def analyze_single_loss(bet_record):
    """
    Deep analysis of why our pick lost.
    
    Returns:
        {
            'loss_id': str,
            'category': str,
            'missing_signals': list,
            'score_gap': float,
            'weight_recommendations': dict,
            'confidence': float
        }
    """
    
    # 1. FETCH RACE RESULT
    race_result = fetch_sporting_life_result(
        course=bet_record['course'],
        race_time=bet_record['race_time'],
        date=bet_record['bet_date']
    )
    # Returns: {
    #   winner: {name, jockey, trainer, odds, sp, form},
    #   placed: [{name, jockey, position}, ...],
    #   all_runners: [{name, position, beaten_dist, ...}, ...]
    # }
    
    # 2. FETCH FULL RACECARD (our pick + winner data)
    racecard = fetch_racecard_data(
        market_id=bet_record['market_id'],
        date=bet_record['bet_date']
    )
    # Returns all runners with full form, stats, ratings
    
    # 3. EXTRACT OUR PICK & WINNER DETAILS
    our_pick = next(
        (r for r in racecard['runners'] if r['name'] == bet_record['horse']),
        None
    )
    winner = next(
        (r for r in racecard['runners'] if r['name'] == race_result['winner']['name']),
        None
    )
    
    # 4. COMPARE KEY FEATURES
    comparison = {
        'odds_gap': winner['odds'] - our_pick['odds'],
        'form_consistency_gap': calculate_consistency(winner['form']) - 
                                 calculate_consistency(our_pick['form']),
        'recent_wins_gap': winner['recent_wins'] - our_pick['recent_wins'],
        'course_wins_gap': winner['course_wins'] - our_pick['course_wins'],
        'class_advantage': winner.get('class_drop', False) and not our_pick.get('class_drop', False),
        'jockey_quality_gap': get_jockey_rank(winner['jockey']) - 
                               get_jockey_rank(our_pick['jockey']),
        'trainer_form_gap': winner['trainer_14d_sr'] - our_pick['trainer_14d_sr'],
        'form_velocity_gap': calculate_form_velocity(winner['form']) - 
                              calculate_form_velocity(our_pick['form'])
    }
    
    # 5. IDENTIFY MISSING SIGNALS
    missing_signals = []
    
    if comparison['form_consistency_gap'] > 15:
        missing_signals.append({
            'signal': 'consistency',
            'gap': comparison['form_consistency_gap'],
            'description': f"Winner ({winner['name']}) had consistent form (2-2-1-3-2) vs our pick's volatile form (1-8-5-1-9)"
        })
    
    if comparison['class_advantage']:
        missing_signals.append({
            'signal': 'class_drop',
            'gap': 1,
            'description': f"Winner dropped from Class 2 to Class 4, we under-weighted this advantage"
        })
    
    if comparison['jockey_quality_gap'] > 2:
        missing_signals.append({
            'signal': 'jockey_upgrade',
            'gap': comparison['jockey_quality_gap'],
            'description': f"Winner had elite jockey ({winner['jockey']}), our pick had apprentice"
        })
    
    if comparison['course_wins_gap'] > 2:
        missing_signals.append({
            'signal': 'course_specialist',
            'gap': comparison['course_wins_gap'],
            'description': f"Winner is course specialist (4/6 C&D), we picked outsider (0/10 C&D)"
        })
    
    if comparison['form_velocity_gap'] > 20:
        missing_signals.append({
            'signal': 'form_improvement',
            'gap': comparison['form_velocity_gap'],
            'description': f"Winner on upward trajectory (5-3-2-1), our pick static (2-2-3-2)"
        })
    
    # 6. CATEGORIZE LOSS TYPE
    category = categorize_loss(comparison, missing_signals)
    # Returns: 'consistent_placer_missed', 'class_drop_missed', etc.
    
    # 7. CALCULATE SCORE GAP
    # Reconstruct winner's score using current weights
    winner_score = calculate_horse_score(winner, current_weights)
    our_pick_score = bet_record['score_breakdown']['total_score']
    score_gap = winner_score - our_pick_score
    
    # 8. GENERATE WEIGHT RECOMMENDATIONS
    recommendations = {}
    
    if 'consistency' in [s['signal'] for s in missing_signals]:
        # Winner had better consistency, boost consistency weight
        recommendations['consistency'] = +8
    
    if 'class_drop' in [s['signal'] for s in missing_signals]:
        # Class drops are under-weighted, boost significantly
        recommendations['class_drop_bonus'] = +12
    
    if 'recent_win' in bet_record['score_breakdown'] and bet_record['score_breakdown']['recent_win'] > 12:
        # We over-relied on recent win, reduce weight
        recommendations['recent_win'] = -5
    
    if 'jockey_upgrade' in [s['signal'] for s in missing_signals]:
        recommendations['jockey_quality'] = +6
        recommendations['jockey_course_bonus'] = +8
    
    if 'course_specialist' in [s['signal'] for s in missing_signals]:
        recommendations['course_bonus'] = +8
        recommendations['cd_bonus'] = +10
    
    # 9. CALCULATE CONFIDENCE
    confidence = calculate_confidence(
        num_signals=len(missing_signals),
        score_gap=abs(score_gap),
        odds_gap=abs(comparison['odds_gap'])
    )
    # High confidence if: 3+ missing signals, score gap >10, odds gap <5
    
    # 10. RETURN ANALYSIS
    return {
        'loss_id': f"{bet_record['bet_date']}_{bet_record['bet_id']}",
        'date': bet_record['bet_date'],
        'race_id': f"{bet_record['course']}_{bet_record['race_time']}",
        'our_pick': {
            'name': our_pick['name'],
            'odds': our_pick['odds'],
            'score': our_pick_score,
            'score_breakdown': bet_record['score_breakdown']
        },
        'actual_winner': {
            'name': winner['name'],
            'odds': winner['odds'],
            'reconstructed_score': winner_score,
            'form': winner['form'],
            'jockey': winner['jockey'],
            'trainer': winner['trainer']
        },
        'missing_signals': missing_signals,
        'loss_category': category,
        'score_gap': score_gap,
        'weight_recommendations': recommendations,
        'confidence_score': confidence,
        'analyzed_at': datetime.utcnow().isoformat()
    }
```

### 3.2 Loss Categories

| Category | Description | Typical Weight Fix | Priority |
|----------|-------------|-------------------|----------|
| **consistent_placer_missed** | Winner always places (2-2-3-1), we picked recent winner (1-7-5-8) | Boost `consistency` +8-12 | HIGH |
| **class_drop_missed** | Winner dropped class (Class 2 → 4), we didn't weight it enough | Boost `class_drop_bonus` +10-15 | HIGH |
| **jockey_upgrade_missed** | Winner had elite jockey (Dettori), we picked apprentice | Boost `jockey_quality` +6-10 | MEDIUM |
| **trainer_form_missed** | Winner's trainer 4/5 recent, we picked 1/10 trainer | Boost `trainer_form_bonus` +8 | MEDIUM |
| **pace_mismatch** | Winner suited pace, we picked wrong running style | Add pace signals | LOW |
| **form_velocity_missed** | Winner improving (5-3-2-1), we picked static (2-2-2-3) | Boost `form_velocity_bonus` +10 | HIGH |
| **course_specialist_missed** | Winner 4/6 C&D, we picked 0/10 | Boost `course_bonus`, `cd_bonus` +8-12 | MEDIUM |
| **recent_win_bias** | Over-relied on last win, ignored overall form | Reduce `recent_win` -5-8 | HIGH |
| **market_overweight** | Followed favorite blindly, ignored value | Reduce `favorite_correction` -5 | MEDIUM |
| **long_shot** | Winner >15.0 odds, unpredictable | No action | IGNORE |

### 3.3 Helper Functions

```python
def calculate_consistency(form_string):
    """
    Calculate consistency score from form string.
    
    Consistent form (2-2-3-2-1) = HIGH score
    Volatile form (1-8-5-1-9) = LOW score
    
    Args:
        form_string: "22321" or "18519"
    
    Returns:
        Consistency score 0-100
    """
    positions = [int(c) for c in form_string if c.isdigit()]
    if not positions:
        return 50
    
    # Calculate standard deviation (lower = more consistent)
    mean_pos = sum(positions) / len(positions)
    variance = sum((p - mean_pos) ** 2 for p in positions) / len(positions)
    std_dev = variance ** 0.5
    
    # Convert to 0-100 scale (lower std_dev = higher consistency)
    consistency = max(0, 100 - (std_dev * 15))
    
    return round(consistency, 2)


def calculate_form_velocity(form_string):
    """
    Calculate form trajectory (improving/declining).
    
    Improving (5-3-2-1) = HIGH positive velocity
    Declining (1-2-3-5) = NEGATIVE velocity
    Static (2-2-2-3) = NEAR ZERO velocity
    
    Returns:
        Velocity score -50 to +50
    """
    positions = [int(c) for c in form_string if c.isdigit()][:5]
    if len(positions) < 3:
        return 0
    
    # Calculate trend: recent positions should be lower (better)
    weights = [5, 4, 3, 2, 1]  # Recent runs weighted more
    weighted_avg_recent = sum(p * w for p, w in zip(positions[:3], weights[:3])) / sum(weights[:3])
    weighted_avg_old = sum(p * w for p, w in zip(positions[3:], weights[3:])) / sum(weights[3:]) if len(positions) > 3 else weighted_avg_recent
    
    # Positive velocity = improving (recent better than old)
    velocity = (weighted_avg_old - weighted_avg_recent) * 10
    
    return round(max(-50, min(50, velocity)), 2)


def get_jockey_rank(jockey_name):
    """
    Return jockey tier ranking.
    
    Tier 1 (Elite): Dettori, Buick, Murphy, Moore, etc. = 1
    Tier 2 (Good): = 2
    Tier 3 (Average): = 3
    Apprentice: = 5
    Unknown: = 4
    """
    ELITE_JOCKEYS = [
        'Frankie Dettori', 'William Buick', 'Oisin Murphy', 'Ryan Moore',
        'James Doyle', 'Tom Marquand', 'Hollie Doyle', 'Jim Crowley'
    ]
    
    GOOD_JOCKEYS = [
        'David Probert', 'Callum Shepherd', 'Richard Kingscote',
        'Kieran Shoemark', 'Rossa Ryan', 'Cieren Fallon'
    ]
    
    if any(elite in jockey_name for elite in ELITE_JOCKEYS):
        return 1
    elif any(good in jockey_name for good in GOOD_JOCKEYS):
        return 2
    elif 'apprentice' in jockey_name.lower() or '(' in jockey_name:
        return 5
    elif jockey_name.strip():
        return 3
    else:
        return 4


def categorize_loss(comparison, missing_signals):
    """
    Categorize loss based on comparison and missing signals.
    """
    signal_types = [s['signal'] for s in missing_signals]
    
    if 'consistency' in signal_types and comparison['form_consistency_gap'] > 15:
        return 'consistent_placer_missed'
    elif 'class_drop' in signal_types:
        return 'class_drop_missed'
    elif 'jockey_upgrade' in signal_types:
        return 'jockey_upgrade_missed'
    elif 'form_improvement' in signal_types and comparison['form_velocity_gap'] > 20:
        return 'form_velocity_missed'
    elif 'course_specialist' in signal_types:
        return 'course_specialist_missed'
    elif comparison.get('odds_gap', 0) < -10:
        return 'market_overweight'
    else:
        return 'general_model_miss'


def calculate_confidence(num_signals, score_gap, odds_gap):
    """
    Calculate confidence in loss analysis.
    
    High confidence = many clear signals, large score gap, similar odds
    Low confidence = few signals, small gap, huge odds difference
    """
    base = 50
    
    # More signals = higher confidence
    base += num_signals * 10
    
    # Larger score gap = clearer miss
    if abs(score_gap) > 15:
        base += 20
    elif abs(score_gap) > 10:
        base += 10
    
    # Similar odds = we should have picked winner
    if abs(odds_gap) < 3:
        base += 15
    elif abs(odds_gap) < 6:
        base += 5
    
    return min(100, max(0, base))
```

---

## 4. Fan-Out Orchestration

### 4.1 Master Orchestrator Lambda

**Function**: `learning-master-orchestrator`  
**Timeout**: 10 minutes  
**Memory**: 1024 MB  
**Trigger**: EventBridge cron (21:30 UTC daily)

```python
import boto3
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

lambda_client = boto3.client('lambda', region_name='eu-west-1')
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
bets_table = dynamodb.Table('SureBetBets')
insights_table = dynamodb.Table('BetBudAI_LearningInsights')


def lambda_handler(event, context):
    """
    Master orchestrator: Fetch losses, fan out to workers, aggregate results.
    """
    
    print("[LEARNING] Starting daily learning pipeline...")
    
    # STEP 1: Fetch settled picks from today
    today = datetime.utcnow().strftime('%Y-%m-%d')
    settled_picks = fetch_settled_picks(today)
    
    print(f"[LEARNING] Found {len(settled_picks)} settled picks")
    
    # Filter losses only
    losses = [p for p in settled_picks if p.get('actual_result') == 'LOSS']
    
    print(f"[LEARNING] {len(losses)} losses to analyze")
    
    if not losses:
        print("[LEARNING] No losses today - skipping analysis")
        return {
            'status': 'success',
            'message': 'No losses to analyze',
            'losses_analyzed': 0
        }
    
    # STEP 2: Fan-out to workers (5-10 concurrent)
    max_workers = min(10, len(losses))
    
    print(f"[LEARNING] Spawning {max_workers} parallel workers...")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(invoke_loss_worker, loss): loss 
            for loss in losses
        }
        
        for future in as_completed(futures):
            loss = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(f"[LEARNING] ✓ Analyzed {loss['horse']} @ {loss['course']}")
            except Exception as exc:
                print(f"[LEARNING] ✗ Worker failed for {loss['horse']}: {exc}")
    
    print(f"[LEARNING] {len(results)} losses analyzed successfully")
    
    # STEP 3: Aggregate patterns
    patterns = aggregate_patterns(results)
    
    print(f"[LEARNING] Patterns detected: {json.dumps(patterns['top_categories'], indent=2)}")
    
    # STEP 4: Calculate weight adjustments
    weight_adjustments = calculate_weight_adjustments(patterns)
    
    print(f"[LEARNING] Proposed weight adjustments: {json.dumps(weight_adjustments, indent=2)}")
    
    # STEP 5: Validate & deploy
    if validate_weight_adjustments(weight_adjustments):
        deploy_weights(weight_adjustments)
        print("[LEARNING] ✓ Weights deployed successfully")
    else:
        print("[LEARNING] ⚠ Weights failed validation - manual review needed")
        notify_manual_review(weight_adjustments)
    
    # STEP 6: Publish metrics
    publish_metrics({
        'losses_analyzed': len(results),
        'patterns_found': len(patterns['top_categories']),
        'weights_adjusted': len(weight_adjustments)
    })
    
    return {
        'status': 'success',
        'losses_analyzed': len(results),
        'patterns': patterns['top_categories'],
        'weight_adjustments': weight_adjustments
    }


def fetch_settled_picks(date):
    """Fetch all settled picks for a given date."""
    response = bets_table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='attribute_exists(actual_result)',
        ExpressionAttributeValues={':date': date}
    )
    return response.get('Items', [])


def invoke_loss_worker(loss_record):
    """Invoke a single loss analysis worker Lambda."""
    response = lambda_client.invoke(
        FunctionName='learning-analyze-loss',
        InvocationType='RequestResponse',  # Synchronous
        Payload=json.dumps(loss_record)
    )
    
    result = json.loads(response['Payload'].read())
    
    # Store in DynamoDB
    insights_table.put_item(Item=result)
    
    return result


def aggregate_patterns(loss_analyses):
    """Aggregate patterns across all losses."""
    from collections import Counter
    
    categories = Counter([a['loss_category'] for a in loss_analyses])
    
    all_recommendations = {}
    for analysis in loss_analyses:
        for weight, delta in analysis.get('weight_recommendations', {}).items():
            if weight not in all_recommendations:
                all_recommendations[weight] = []
            all_recommendations[weight].append(delta)
    
    return {
        'top_categories': dict(categories.most_common(5)),
        'weight_recommendations': {
            weight: sum(deltas) / len(deltas)  # Average recommendation
            for weight, deltas in all_recommendations.items()
        },
        'total_losses': len(loss_analyses)
    }


def calculate_weight_adjustments(patterns):
    """Calculate final weight adjustments based on patterns."""
    adjustments = {}
    
    # Get historical pattern frequency (last 7 days)
    historical_patterns = fetch_last_7_days_patterns()
    
    for weight, avg_delta in patterns['weight_recommendations'].items():
        # Count how many times this pattern appeared in last 7 days
        frequency = historical_patterns.get(weight, 0)
        
        if frequency >= 5:
            # High confidence - aggressive adjustment
            adjustment = round(avg_delta * 1.5)
            confidence = 'high'
        elif frequency >= 3:
            # Medium confidence - moderate adjustment
            adjustment = round(avg_delta * 1.0)
            confidence = 'medium'
        elif frequency >= 2:
            # Low confidence - conservative adjustment
            adjustment = round(avg_delta * 0.5)
            confidence = 'low'
        else:
            # Single occurrence - monitor only
            adjustment = 0
            confidence = 'monitor'
        
        # Apply safety bounds
        adjustment = max(-10, min(10, adjustment))
        
        if adjustment != 0:
            adjustments[weight] = {
                'delta': adjustment,
                'confidence': confidence,
                'frequency_7d': frequency
            }
    
    return adjustments


def validate_weight_adjustments(adjustments):
    """Validate weight adjustments are safe."""
    if not adjustments:
        return True
    
    # Check no extreme changes
    max_delta = max(abs(a['delta']) for a in adjustments.values())
    if max_delta > 15:
        print(f"[LEARNING] ⚠ Extreme weight change detected: {max_delta}")
        return False
    
    # Check total adjustments not too aggressive
    if len(adjustments) > 10:
        print(f"[LEARNING] ⚠ Too many weights changing at once: {len(adjustments)}")
        return False
    
    return True


def deploy_weights(adjustments):
    """Deploy new weights to DynamoDB."""
    from config.weights import WeightManager, DEFAULT_WEIGHTS
    
    manager = WeightManager()
    current = manager.get_weights()
    
    # Apply adjustments
    new_weights = current.copy()
    for weight, adjustment in adjustments.items():
        old_value = new_weights.get(weight, DEFAULT_WEIGHTS.get(weight, 0))
        new_value = old_value + adjustment['delta']
        new_value = max(0, min(50, new_value))  # Bound 0-50
        new_weights[weight] = new_value
        
        print(f"[LEARNING] {weight}: {old_value} → {new_value} ({adjustment['delta']:+d})")
    
    # Save to DynamoDB
    manager.save_weights(new_weights)
    
    # Store audit log
    store_audit_log(current, new_weights, adjustments)


def fetch_last_7_days_patterns():
    """Fetch pattern frequency from last 7 days."""
    from collections import defaultdict
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    # Query LearningInsights table for last 7 days
    # (Simplified - actual implementation would scan/query properly)
    pattern_counts = defaultdict(int)
    
    # Count how many times each weight appeared in recommendations
    # This would be a DynamoDB query in practice
    
    return pattern_counts


def store_audit_log(old_weights, new_weights, adjustments):
    """Store audit trail of weight changes."""
    audit_table = dynamodb.Table('BetBudAI_AuditLog')
    
    audit_table.put_item(Item={
        'audit_id': f"weight_change_{datetime.utcnow().isoformat()}",
        'timestamp': datetime.utcnow().isoformat(),
        'type': 'weight_adjustment',
        'old_weights': old_weights,
        'new_weights': new_weights,
        'adjustments': adjustments,
        'approved_by': 'automated_learning'
    })


def notify_manual_review(adjustments):
    """Send SNS notification for manual review."""
    sns = boto3.client('sns', region_name='eu-west-1')
    
    message = f"""
    BetBudAI Learning System - Manual Review Required
    
    Proposed weight adjustments failed validation.
    
    Adjustments:
    {json.dumps(adjustments, indent=2)}
    
    Please review and approve manually.
    """
    
    sns.publish(
        TopicArn='arn:aws:sns:eu-west-1:ACCOUNT:betbudai-alerts',
        Subject='[BetBudAI] Weight Adjustment Needs Review',
        Message=message
    )


def publish_metrics(metrics):
    """Publish CloudWatch metrics."""
    cloudwatch = boto3.client('cloudwatch', region_name='eu-west-1')
    
    cloudwatch.put_metric_data(
        Namespace='BetBudAI/Learning',
        MetricData=[
            {
                'MetricName': 'DailyLossesAnalyzed',
                'Value': metrics['losses_analyzed'],
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            },
            {
                'MetricName': 'PatternsDetected',
                'Value': metrics['patterns_found'],
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            },
            {
                'MetricName': 'WeightsAdjusted',
                'Value': metrics['weights_adjusted'],
                'Unit': 'Count',
                'Timestamp': datetime.utcnow()
            }
        ]
    )
```

### 4.2 Concurrency Control

```python
# EventBridge Rule Configuration
{
    "Name": "daily-learning-pipeline",
    "ScheduleExpression": "cron(30 21 * * ? *)",  # 21:30 UTC daily
    "State": "ENABLED",
    "Targets": [
        {
            "Arn": "arn:aws:lambda:eu-west-1:ACCOUNT:function:learning-master-orchestrator",
            "Id": "1",
            "RetryPolicy": {
                "MaximumRetryAttempts": 2,
                "MaximumEventAge": 3600
            }
        }
    ]
}

# Lambda Concurrency Configuration
{
    "learning-analyze-loss": {
        "ReservedConcurrentExecutions": 10,  # Max 10 parallel workers
        "ProvisionedConcurrency": 5  # Keep 5 warm for fast start
    },
    "learning-master-orchestrator": {
        "ReservedConcurrentExecutions": 1  # Only 1 orchestrator at a time
    }
}
```

---

## 5. Weight Auto-Adjustment Logic

### 5.1 Adjustment Rules Matrix

| Pattern Frequency (7 days) | Confidence | Adjustment Magnitude | Example |
|----------------------------|------------|---------------------|---------|
| 5+ occurrences | HIGH | ±8-10 points | `consistency` seen in 6/7 losses → +10 |
| 3-4 occurrences | MEDIUM | ±4-6 points | `class_drop` seen in 4/7 losses → +6 |
| 2 occurrences | LOW | ±1-3 points | `jockey_upgrade` seen in 2/7 → +2 |
| 1 occurrence | MONITOR | 0 points | Track only, no change |

### 5.2 Safety Bounds

```python
WEIGHT_ADJUSTMENT_RULES = {
    'max_delta_per_day': 10,      # Max ±10 points per weight per day
    'max_weight_value': 50,        # No weight can exceed 50
    'min_weight_value': 0,         # No negative weights
    'max_simultaneous_changes': 10, # Max 10 weights changing at once
    'min_confidence_to_deploy': 70, # Must be 70%+ confident
    'rollback_threshold': 5,       # Rollback if strike rate drops >5% for 3 days
}


def apply_safety_bounds(weight_name, current_value, proposed_delta):
    """Apply safety bounds to weight adjustment."""
    
    # Calculate new value
    new_value = current_value + proposed_delta
    
    # Bound to 0-50 range
    new_value = max(0, min(50, new_value))
    
    # Limit daily delta
    actual_delta = new_value - current_value
    if abs(actual_delta) > WEIGHT_ADJUSTMENT_RULES['max_delta_per_day']:
        actual_delta = (
            WEIGHT_ADJUSTMENT_RULES['max_delta_per_day'] 
            if actual_delta > 0 
            else -WEIGHT_ADJUSTMENT_RULES['max_delta_per_day']
        )
        new_value = current_value + actual_delta
    
    return new_value, actual_delta
```

### 5.3 Weight Adjustment Examples

#### Example 1: Consistent Placer Pattern

```
PATTERN DETECTED:
- 8/10 losses had winners with high consistency (2-2-3-1-2 form)
- Our picks had recent wins but volatile form (1-8-5-1-9)
- Current weight: consistency = 12
- Recommendation: +10 points (boost to 22)

ADJUSTMENT LOGIC:
frequency_7d = 8  (appeared in 8 of last 10 losses)
confidence = HIGH (8 >= 5)
base_delta = +10
safety_check = PASS (10 <= max_delta_per_day)
new_value = 12 + 10 = 22
DEPLOY ✓
```

#### Example 2: Class Drop Pattern

```
PATTERN DETECTED:
- 5/10 losses had winners dropping class (Class 2 → Class 4)
- Current weight: class_drop_bonus = 24
- Recommendation: +8 points (boost to 32)

ADJUSTMENT LOGIC:
frequency_7d = 5  (confirmed pattern)
confidence = HIGH (5 >= 5)
base_delta = +8
safety_check = PASS
new_value = 24 + 8 = 32
DEPLOY ✓
```

#### Example 3: Recent Win Over-Reliance

```
PATTERN DETECTED:
- 6/10 losses: we picked horse with recent win (1 in last 5 runs)
- Winners had NO recent wins but consistent places (3-2-3-2-2)
- Current weight: recent_win = 14
- Recommendation: -6 points (reduce to 8)

ADJUSTMENT LOGIC:
frequency_7d = 6  (consistent pattern)
confidence = HIGH (6 >= 5)
base_delta = -6
safety_check = PASS
new_value = 14 - 6 = 8
DEPLOY ✓
```

#### Example 4: Low Confidence - Monitor Only

```
PATTERN DETECTED:
- 1/10 losses: pace mismatch (winner suited fast pace)
- Current weight: (no pace signal exists yet)
- Recommendation: Add pace signal

ADJUSTMENT LOGIC:
frequency_7d = 1  (single occurrence)
confidence = MONITOR (1 < 2)
base_delta = 0  (no change yet)
action = MONITOR (track for 7 more days)
DEPLOY: NO (monitor only)
```

### 5.4 Rollback Logic

```python
def check_rollback_trigger():
    """
    Check if weight changes should be rolled back.
    
    Rollback triggers:
    - Strike rate drops >5% below baseline for 3 consecutive days
    - ROI drops >10% below baseline for 3 consecutive days
    - System generates <5 picks per day for 2 days
    """
    
    # Fetch last 3 days performance
    last_3_days = fetch_performance_last_n_days(3)
    
    baseline_strike_rate = get_baseline_strike_rate()  # Historical average
    
    # Check if strike rate dropped significantly
    recent_strike_rate = last_3_days['strike_rate']
    
    if recent_strike_rate < baseline_strike_rate - 0.05:
        # Strike rate dropped >5%
        consecutive_drops = count_consecutive_performance_drops()
        
        if consecutive_drops >= 3:
            print("[ROLLBACK] Strike rate dropped >5% for 3 days - ROLLBACK TRIGGERED")
            rollback_to_previous_weights()
            notify_rollback()
            return True
    
    return False


def rollback_to_previous_weights():
    """Rollback to weights from 7 days ago."""
    from config.weights import WeightManager
    
    # Fetch audit log from 7 days ago
    audit_table = dynamodb.Table('BetBudAI_AuditLog')
    
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Get last known good weights
    response = audit_table.query(
        KeyConditionExpression='audit_id BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':start': f'weight_change_{seven_days_ago}',
            ':end': f'weight_change_{seven_days_ago}T23:59:59'
        },
        ScanIndexForward=False,
        Limit=1
    )
    
    if response['Items']:
        old_weights = response['Items'][0]['old_weights']
        
        manager = WeightManager()
        manager.save_weights(old_weights)
        
        print(f"[ROLLBACK] ✓ Rolled back to weights from {seven_days_ago}")
```

---

## 6. Monthly Historical Analysis

### 6.1 Monthly Pipeline

**Function**: `learning-historical-analyzer`  
**Timeout**: 15 minutes  
**Memory**: 2048 MB  
**Trigger**: EventBridge cron (1st of month, 02:00 UTC)

```python
def lambda_handler(event, context):
    """
    Monthly historical analysis: Process last 30 days of results.
    
    Goals:
    - Validate current weights against 150-200 settled races
    - Identify systematic biases not visible in daily analysis
    - Generate confidence scores for each weight
    - Recommend major structural changes (if needed)
    """
    
    print("[HISTORICAL] Starting monthly historical analysis...")
    
    # Fetch last 30 days of settled picks
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    all_settled = fetch_settled_picks_date_range(start_date, end_date)
    
    print(f"[HISTORICAL] Analyzing {len(all_settled)} races from last 30 days")
    
    losses = [p for p in all_settled if p.get('actual_result') == 'LOSS']
    wins = [p for p in all_settled if p.get('actual_result') == 'WIN']
    
    print(f"[HISTORICAL] {len(wins)} wins, {len(losses)} losses")
    print(f"[HISTORICAL] Strike rate: {len(wins) / len(all_settled) * 100:.1f}%")
    
    # Analyze all losses (can use existing loss analysis function)
    loss_analyses = []
    
    for loss in losses:
        try:
            analysis = analyze_single_loss(loss)
            loss_analyses.append(analysis)
        except Exception as e:
            print(f"[HISTORICAL] ✗ Failed to analyze {loss['horse']}: {e}")
    
    # Aggregate patterns
    patterns = aggregate_historical_patterns(loss_analyses)
    
    # Calculate weight confidence scores
    weight_confidence = calculate_weight_confidence(wins, losses, loss_analyses)
    
    # Identify systematic biases
    biases = identify_systematic_biases(loss_analyses)
    
    # Generate recommendations
    recommendations = generate_historical_recommendations(patterns, biases, weight_confidence)
    
    # Store historical report
    store_historical_report({
        'period_start': start_date.isoformat(),
        'period_end': end_date.isoformat(),
        'total_races': len(all_settled),
        'wins': len(wins),
        'losses': len(losses),
        'strike_rate': len(wins) / len(all_settled),
        'patterns': patterns,
        'biases': biases,
        'weight_confidence': weight_confidence,
        'recommendations': recommendations
    })
    
    # Notify if major changes recommended
    if any(r['priority'] == 'critical' for r in recommendations):
        notify_critical_recommendations(recommendations)
    
    return {
        'status': 'success',
        'races_analyzed': len(all_settled),
        'patterns_found': len(patterns),
        'recommendations': recommendations
    }


def aggregate_historical_patterns(loss_analyses):
    """Aggregate patterns across 30 days."""
    from collections import Counter
    
    # Category distribution
    categories = Counter([a['loss_category'] for a in loss_analyses])
    
    # Most common missing signals
    all_signals = []
    for analysis in loss_analyses:
        all_signals.extend([s['signal'] for s in analysis.get('missing_signals', [])])
    
    signal_counts = Counter(all_signals)
    
    return {
        'top_loss_categories': dict(categories.most_common(10)),
        'most_common_missing_signals': dict(signal_counts.most_common(15)),
        'total_losses': len(loss_analyses)
    }


def calculate_weight_confidence(wins, losses, loss_analyses):
    """
    Calculate confidence score for each weight.
    
    High confidence = weight performs well (wins) and rarely appears as missing (losses)
    Low confidence = weight underperforms (missing in many losses)
    """
    from collections import defaultdict
    
    weight_performance = defaultdict(lambda: {'hits': 0, 'misses': 0, 'missing_count': 0})
    
    # Analyze wins: which weights contributed most
    for win in wins:
        breakdown = win.get('score_breakdown', {})
        for weight, value in breakdown.items():
            if value > 0:
                weight_performance[weight]['hits'] += 1
    
    # Analyze losses: which weights were missing or weak
    for analysis in loss_analyses:
        recommendations = analysis.get('weight_recommendations', {})
        for weight, delta in recommendations.items():
            if delta > 0:  # Positive delta = weight should be higher
                weight_performance[weight]['missing_count'] += 1
            weight_performance[weight]['misses'] += 1
    
    # Calculate confidence score
    confidence_scores = {}
    
    for weight, stats in weight_performance.items():
        total = stats['hits'] + stats['misses']
        if total == 0:
            confidence = 50
        else:
            hit_rate = stats['hits'] / total
            miss_penalty = stats['missing_count'] / total
            confidence = (hit_rate * 100) - (miss_penalty * 50)
            confidence = max(0, min(100, confidence))
        
        confidence_scores[weight] = {
            'score': round(confidence, 2),
            'hits': stats['hits'],
            'misses': stats['misses'],
            'missing_count': stats['missing_count']
        }
    
    return confidence_scores


def identify_systematic_biases(loss_analyses):
    """
    Identify systematic biases in the model.
    
    Examples:
    - Always picking recent winners over consistent placers
    - Ignoring class drops
    - Over-trusting market favorites
    - Missing course specialists
    """
    from collections import Counter
    
    biases = []
    
    # Check for consistent placer bias
    consistent_placer_losses = [
        a for a in loss_analyses 
        if a['loss_category'] == 'consistent_placer_missed'
    ]
    
    if len(consistent_placer_losses) > len(loss_analyses) * 0.25:
        biases.append({
            'bias': 'consistent_placer_underweight',
            'description': 'Model favors recent winners over consistent placers',
            'frequency': len(consistent_placer_losses),
            'percentage': len(consistent_placer_losses) / len(loss_analyses) * 100,
            'recommendation': 'Boost consistency weight by +10-15 points',
            'priority': 'critical'
        })
    
    # Check for class drop bias
    class_drop_losses = [
        a for a in loss_analyses 
        if a['loss_category'] == 'class_drop_missed'
    ]
    
    if len(class_drop_losses) > len(loss_analyses) * 0.20:
        biases.append({
            'bias': 'class_drop_underweight',
            'description': 'Model misses class droppers (horses dropping 2+ classes)',
            'frequency': len(class_drop_losses),
            'percentage': len(class_drop_losses) / len(loss_analyses) * 100,
            'recommendation': 'Boost class_drop_bonus by +15-20 points',
            'priority': 'critical'
        })
    
    # Check for jockey bias
    jockey_losses = [
        a for a in loss_analyses 
        if a['loss_category'] == 'jockey_upgrade_missed'
    ]
    
    if len(jockey_losses) > len(loss_analyses) * 0.15:
        biases.append({
            'bias': 'elite_jockey_underweight',
            'description': 'Model undervalues elite jockey upgrades (Dettori, Buick, etc)',
            'frequency': len(jockey_losses),
            'percentage': len(jockey_losses) / len(loss_analyses) * 100,
            'recommendation': 'Boost jockey_quality and jockey_course_bonus by +8-10 points',
            'priority': 'high'
        })
    
    return biases


def generate_historical_recommendations(patterns, biases, weight_confidence):
    """Generate actionable recommendations from historical analysis."""
    recommendations = []
    
    # From biases
    for bias in biases:
        recommendations.append({
            'type': 'weight_adjustment',
            'reason': bias['description'],
            'action': bias['recommendation'],
            'priority': bias['priority'],
            'evidence': f"{bias['frequency']} occurrences ({bias['percentage']:.1f}%)"
        })
    
    # From low-confidence weights
    for weight, conf in weight_confidence.items():
        if conf['score'] < 30:
            recommendations.append({
                'type': 'weight_review',
                'reason': f"Low confidence in {weight} weight",
                'action': f"Review {weight} - may be ineffective or mis-calibrated",
                'priority': 'medium',
                'evidence': f"Confidence: {conf['score']:.1f}%, Hits: {conf['hits']}, Misses: {conf['misses']}"
            })
    
    # Sort by priority
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    recommendations.sort(key=lambda r: priority_order.get(r['priority'], 99))
    
    return recommendations


def store_historical_report(report):
    """Store historical analysis report in DynamoDB."""
    reports_table = dynamodb.Table('BetBudAI_HistoricalReports')
    
    reports_table.put_item(Item={
        'report_id': f"historical_{report['period_end'][:10]}",
        'timestamp': datetime.utcnow().isoformat(),
        **report
    })


def notify_critical_recommendations(recommendations):
    """Send notification for critical recommendations."""
    sns = boto3.client('sns', region_name='eu-west-1')
    
    critical = [r for r in recommendations if r['priority'] == 'critical']
    
    message = f"""
    BetBudAI Historical Analysis - Critical Recommendations
    
    {len(critical)} critical issues detected in last 30 days:
    
    """
    
    for rec in critical:
        message += f"\n- {rec['reason']}\n  Action: {rec['action']}\n  Evidence: {rec['evidence']}\n"
    
    sns.publish(
        TopicArn='arn:aws:sns:eu-west-1:ACCOUNT:betbudai-alerts',
        Subject='[BetBudAI] Critical Weight Issues Detected',
        Message=message
    )
```

---

## 7. Storage Schema

### 7.1 DynamoDB Tables

#### Table: `BetBudAI_LearningInsights`

**Purpose**: Store individual loss analyses

```python
{
    'loss_id': 'STRING (HASH)',  # "20260520_1430_Ascot_GoldenMiller"
    'analyzed_at': 'STRING (RANGE)',  # ISO timestamp
    'date': 'STRING',  # "2026-05-20"
    'race_id': 'STRING',  # "Ascot_14:30"
    'our_pick': {
        'name': 'STRING',
        'odds': 'NUMBER',
        'score': 'NUMBER',
        'score_breakdown': {
            'recent_win': 'NUMBER',
            'consistency': 'NUMBER',
            # ... all weight components
        }
    },
    'actual_winner': {
        'name': 'STRING',
        'odds': 'NUMBER',
        'reconstructed_score': 'NUMBER',
        'form': 'STRING',
        'jockey': 'STRING',
        'trainer': 'STRING'
    },
    'missing_signals': [
        {
            'signal': 'STRING',  # 'consistency', 'class_drop', etc.
            'gap': 'NUMBER',
            'description': 'STRING'
        }
    ],
    'loss_category': 'STRING',  # 'consistent_placer_missed', etc.
    'score_gap': 'NUMBER',  # Winner score - our pick score
    'weight_recommendations': {
        'consistency': 'NUMBER',  # +8
        'class_drop_bonus': 'NUMBER',  # +12
        # ... recommended deltas
    },
    'confidence_score': 'NUMBER',  # 0-100
    'ttl': 'NUMBER'  # Auto-expire after 90 days
}
```

**Indexes**:
- GSI1: `date-analyzed_at-index` (for querying by date)
- GSI2: `loss_category-analyzed_at-index` (for pattern aggregation)

#### Table: `BetBudAI_HistoricalReports`

**Purpose**: Store monthly historical analysis reports

```python
{
    'report_id': 'STRING (HASH)',  # "historical_2026-05-20"
    'timestamp': 'STRING',
    'period_start': 'STRING',
    'period_end': 'STRING',
    'total_races': 'NUMBER',
    'wins': 'NUMBER',
    'losses': 'NUMBER',
    'strike_rate': 'NUMBER',
    'patterns': {
        'top_loss_categories': 'MAP',
        'most_common_missing_signals': 'MAP',
        'total_losses': 'NUMBER'
    },
    'biases': [
        {
            'bias': 'STRING',
            'description': 'STRING',
            'frequency': 'NUMBER',
            'percentage': 'NUMBER',
            'recommendation': 'STRING',
            'priority': 'STRING'
        }
    ],
    'weight_confidence': 'MAP',  # weight -> confidence score
    'recommendations': [
        {
            'type': 'STRING',
            'reason': 'STRING',
            'action': 'STRING',
            'priority': 'STRING',
            'evidence': 'STRING'
        }
    ]
}
```

#### Table: `BetBudAI_AuditLog`

**Purpose**: Audit trail for all weight changes

```python
{
    'audit_id': 'STRING (HASH)',  # "weight_change_2026-05-20T21:35:00"
    'timestamp': 'STRING',
    'type': 'STRING',  # 'weight_adjustment', 'rollback', 'manual_override'
    'old_weights': 'MAP',
    'new_weights': 'MAP',
    'adjustments': {
        'weight_name': {
            'delta': 'NUMBER',
            'confidence': 'STRING',
            'frequency_7d': 'NUMBER'
        }
    },
    'approved_by': 'STRING',  # 'automated_learning', 'admin@betbudai.com'
    'reason': 'STRING',  # Optional
    'ttl': 'NUMBER'  # Auto-expire after 365 days
}
```

### 7.2 Storage Costs

Estimated storage costs (DynamoDB on-demand):

| Table | Items/Month | Size/Item | Total Size | Cost/Month |
|-------|-------------|-----------|------------|------------|
| LearningInsights | ~800 (20 losses/day * 30 days + TTL) | 2 KB | 1.6 MB | $0.01 |
| HistoricalReports | ~1 (monthly) | 50 KB | 50 KB | $0.00 |
| AuditLog | ~30 (daily adjustments) | 10 KB | 300 KB | $0.00 |
| **TOTAL** | | | **~2 MB** | **$0.01/month** |

---

## 8. Validation & Safety

### 8.1 A/B Testing Framework

```python
def enable_ab_testing(weight_name, new_value):
    """
    Enable A/B testing for weight change.
    
    Strategy:
    - 80% of picks use current weights (control group)
    - 20% of picks use new weights (test group)
    - Run for 7 days
    - Compare strike rates
    - Deploy to 100% if test group outperforms
    """
    
    ab_config = {
        'weight_name': weight_name,
        'control_value': get_current_weight(weight_name),
        'test_value': new_value,
        'test_percentage': 20,
        'start_date': datetime.utcnow().isoformat(),
        'end_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
        'status': 'running'
    }
    
    # Store A/B config
    ab_table = dynamodb.Table('BetBudAI_ABTests')
    ab_table.put_item(Item=ab_config)
    
    print(f"[A/B TEST] Started for {weight_name}: {ab_config['control_value']} vs {new_value}")


def get_weight_for_pick(weight_name, pick_id):
    """
    Get weight value for a pick based on A/B test assignment.
    
    Uses deterministic hashing to ensure same pick always gets same variant.
    """
    
    # Check if A/B test is running
    ab_config = get_active_ab_test(weight_name)
    
    if not ab_config:
        # No A/B test, use current weight
        return get_current_weight(weight_name)
    
    # Deterministic assignment based on pick_id hash
    import hashlib
    hash_val = int(hashlib.md5(pick_id.encode()).hexdigest(), 16)
    variant = hash_val % 100
    
    if variant < ab_config['test_percentage']:
        # Test group (20%)
        return ab_config['test_value']
    else:
        # Control group (80%)
        return ab_config['control_value']


def evaluate_ab_test(weight_name):
    """
    Evaluate A/B test results after 7 days.
    
    Compare:
    - Strike rate (control vs test)
    - ROI (control vs test)
    - Average odds (control vs test)
    
    Decision:
    - If test group strike rate >2% better: DEPLOY
    - If test group strike rate 0-2% better: CONTINUE MONITORING
    - If test group strike rate worse: ROLLBACK
    """
    
    ab_config = get_active_ab_test(weight_name)
    
    # Fetch picks from last 7 days
    picks = fetch_picks_last_n_days(7)
    
    control_picks = [p for p in picks if get_ab_variant(p['pick_id'], ab_config) == 'control']
    test_picks = [p for p in picks if get_ab_variant(p['pick_id'], ab_config) == 'test']
    
    control_wins = [p for p in control_picks if p.get('actual_result') == 'WIN']
    test_wins = [p for p in test_picks if p.get('actual_result') == 'WIN']
    
    control_sr = len(control_wins) / len(control_picks) if control_picks else 0
    test_sr = len(test_wins) / len(test_picks) if test_picks else 0
    
    improvement = (test_sr - control_sr) * 100
    
    print(f"[A/B TEST] {weight_name}: Control SR={control_sr:.1%}, Test SR={test_sr:.1%}, Δ={improvement:+.1f}%")
    
    if improvement > 2.0:
        # Test group significantly better
        deploy_weight(weight_name, ab_config['test_value'])
        print(f"[A/B TEST] ✓ DEPLOY: Test group {improvement:+.1f}% better")
        return 'deploy'
    elif improvement > 0:
        # Test group slightly better - continue monitoring
        extend_ab_test(weight_name, days=7)
        print(f"[A/B TEST] → CONTINUE: Test group {improvement:+.1f}% better (need more data)")
        return 'continue'
    else:
        # Test group worse - rollback
        rollback_weight(weight_name, ab_config['control_value'])
        print(f"[A/B TEST] ✗ ROLLBACK: Test group {improvement:.1f}% worse")
        return 'rollback'
```

### 8.2 Performance Monitoring

```python
def monitor_daily_performance():
    """
    Daily performance check.
    
    Triggers:
    - Strike rate drops >5% below 7-day average for 3 days
    - ROI drops >10% below 7-day average for 3 days
    - Pick volume drops <5 picks/day for 2 days
    """
    
    last_7_days = fetch_performance_last_n_days(7)
    last_3_days = fetch_performance_last_n_days(3)
    
    baseline_sr = last_7_days['strike_rate']
    recent_sr = last_3_days['strike_rate']
    
    baseline_roi = last_7_days['roi']
    recent_roi = last_3_days['roi']
    
    baseline_volume = last_7_days['picks_per_day']
    recent_volume = last_3_days['picks_per_day']
    
    alerts = []
    
    # Strike rate check
    if recent_sr < baseline_sr - 0.05:
        alerts.append({
            'type': 'strike_rate_drop',
            'severity': 'high',
            'message': f"Strike rate dropped {(baseline_sr - recent_sr) * 100:.1f}% in last 3 days",
            'action': 'Consider rollback if continues tomorrow'
        })
    
    # ROI check
    if recent_roi < baseline_roi - 0.10:
        alerts.append({
            'type': 'roi_drop',
            'severity': 'high',
            'message': f"ROI dropped {(baseline_roi - recent_roi) * 100:.1f}% in last 3 days",
            'action': 'Review weight changes'
        })
    
    # Volume check
    if recent_volume < 5:
        alerts.append({
            'type': 'low_volume',
            'severity': 'medium',
            'message': f"Pick volume dropped to {recent_volume:.1f} picks/day",
            'action': 'Check if weights too restrictive'
        })
    
    if alerts:
        send_performance_alerts(alerts)
    
    return alerts
```

### 8.3 Human Review Triggers

```python
HUMAN_REVIEW_TRIGGERS = {
    'extreme_weight_change': {
        'condition': lambda delta: abs(delta) > 15,
        'message': 'Weight change >15 points requires human approval',
        'action': 'notify_admin'
    },
    'too_many_changes': {
        'condition': lambda changes: len(changes) > 10,
        'message': '>10 weights changing simultaneously',
        'action': 'notify_admin'
    },
    'performance_degradation': {
        'condition': lambda metrics: metrics['strike_rate'] < metrics['baseline'] - 0.05,
        'message': 'Strike rate dropped >5% for 3 days',
        'action': 'auto_rollback_and_notify'
    },
    'critical_bias_detected': {
        'condition': lambda biases: any(b['priority'] == 'critical' for b in biases),
        'message': 'Critical systematic bias detected in monthly analysis',
        'action': 'notify_admin'
    }
}


def check_human_review_needed(context):
    """
    Check if human review is needed before deploying weight changes.
    """
    
    for trigger_name, trigger_config in HUMAN_REVIEW_TRIGGERS.items():
        if trigger_config['condition'](context):
            handle_trigger(trigger_name, trigger_config, context)
            return True
    
    return False


def handle_trigger(trigger_name, config, context):
    """Handle human review trigger."""
    
    if config['action'] == 'notify_admin':
        notify_admin(trigger_name, config['message'], context)
    elif config['action'] == 'auto_rollback_and_notify':
        rollback_weights()
        notify_admin(trigger_name, f"AUTO-ROLLBACK: {config['message']}", context)


def notify_admin(trigger, message, context):
    """Send SNS notification to admin."""
    sns = boto3.client('sns', region_name='eu-west-1')
    
    sns.publish(
        TopicArn='arn:aws:sns:eu-west-1:ACCOUNT:betbudai-admin-alerts',
        Subject=f'[BetBudAI] Human Review Required: {trigger}',
        Message=f"""
        Trigger: {trigger}
        Message: {message}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Action Required: Review and approve/reject in admin dashboard.
        """
    )
```

---

## 9. Implementation Plan

### Phase 1: Foundation (Week 1 - Days 1-3)

**Goal**: Build core loss analysis infrastructure

#### Day 1: Setup Tables & Schemas
- [ ] Create DynamoDB tables:
  - `BetBudAI_LearningInsights`
  - `BetBudAI_HistoricalReports`
  - `BetBudAI_AuditLog`
  - `BetBudAI_ABTests`
- [ ] Create GSIs for efficient querying
- [ ] Set TTL policies (90 days for insights, 365 days for audit)

#### Day 2: Loss Analysis Worker
- [ ] Create `learning-analyze-loss` Lambda
- [ ] Implement loss analysis logic:
  - Fetch Sporting Life result
  - Fetch racecard data
  - Compare our pick vs winner
  - Identify missing signals
  - Categorize loss type
  - Generate weight recommendations
- [ ] Test with 10 historical losses
- [ ] Deploy to dev environment

#### Day 3: Master Orchestrator
- [ ] Create `learning-master-orchestrator` Lambda
- [ ] Implement fan-out logic (5-10 workers)
- [ ] Implement aggregation logic
- [ ] Test end-to-end with 1 day of losses
- [ ] Deploy to dev environment

### Phase 2: Weight Optimization (Week 1 - Days 4-5)

**Goal**: Implement weight adjustment logic

#### Day 4: Weight Optimizer
- [ ] Create `learning-optimize-weights` Lambda
- [ ] Implement adjustment rules matrix
- [ ] Implement safety bounds
- [ ] Implement validation logic
- [ ] Test with mock pattern data
- [ ] Deploy to dev environment

#### Day 5: Validation & Deployment
- [ ] Create `learning-validate-weights` Lambda
- [ ] Create `learning-deploy-weights` Lambda
- [ ] Implement audit logging
- [ ] Implement CloudWatch metrics
- [ ] Create CloudWatch alarms
- [ ] Test full pipeline end-to-end

### Phase 3: Production Deployment (Week 1 - Days 6-7)

**Goal**: Deploy to production with monitoring

#### Day 6: Production Setup
- [ ] Create Step Functions state machine
- [ ] Create EventBridge rule (21:30 UTC daily)
- [ ] Set up SNS topics for alerts
- [ ] Create CloudWatch dashboard
- [ ] Configure Lambda concurrency limits
- [ ] Run dry-run on production data (no weight changes)

#### Day 7: Go Live
- [ ] Enable weight deployment (with human approval first)
- [ ] Monitor first run (21:30 UTC)
- [ ] Review first day results
- [ ] Enable auto-deployment (if first run successful)
- [ ] Document runbook for operations team

### Phase 4: A/B Testing (Week 2)

**Goal**: Add A/B testing framework for safe rollouts

#### Days 8-10: A/B Framework
- [ ] Create `BetBudAI_ABTests` table
- [ ] Implement A/B assignment logic
- [ ] Modify pick generation to use A/B variants
- [ ] Implement A/B evaluation logic
- [ ] Test with mock weight change
- [ ] Deploy to production

#### Days 11-14: First A/B Test
- [ ] Launch first A/B test (consistency weight +10)
- [ ] Monitor for 7 days
- [ ] Evaluate results
- [ ] Deploy winner variant

### Phase 5: Historical Analysis (Week 3)

**Goal**: Monthly deep analysis pipeline

#### Days 15-17: Historical Analyzer
- [ ] Create `learning-historical-analyzer` Lambda (15min timeout)
- [ ] Implement 30-day batch processing
- [ ] Implement bias detection logic
- [ ] Implement confidence scoring
- [ ] Test with last 30 days of data
- [ ] Deploy to production

#### Days 18-21: First Monthly Run
- [ ] Run first monthly analysis (1st of month)
- [ ] Review historical report
- [ ] Validate recommendations
- [ ] Apply recommended structural changes (if any)

### Phase 6: Monitoring & Optimization (Week 4)

**Goal**: Refine and optimize system

#### Days 22-25: Monitoring
- [ ] Add detailed CloudWatch metrics
- [ ] Create operational dashboard
- [ ] Implement rollback monitoring
- [ ] Test rollback trigger
- [ ] Document SOP for rollbacks

#### Days 26-30: Optimization
- [ ] Optimize Lambda performance (reduce cold starts)
- [ ] Add caching for Sporting Life fetches
- [ ] Optimize DynamoDB queries
- [ ] Add batch processing for historical data
- [ ] Performance testing (stress test with 100 losses)

---

## 10. Code Structure

### 10.1 Directory Layout

```
backend/
├── core/
│   ├── learning/                     # NEW: Learning system
│   │   ├── __init__.py
│   │   ├── loss_analyzer.py         # Core loss analysis logic
│   │   ├── pattern_aggregator.py    # Pattern detection across losses
│   │   ├── weight_optimizer.py      # Weight adjustment calculation
│   │   ├── historical_analyzer.py   # Monthly historical analysis
│   │   ├── ab_testing.py            # A/B testing framework
│   │   └── helpers.py               # Utility functions
│   ├── scoring/
│   ├── settlement/
│   └── ...
├── pipeline/
│   ├── learning/                     # NEW: Learning Lambda handlers
│   │   ├── fetch_settled.py         # Fetch settled picks
│   │   ├── analyze_loss.py          # Loss analysis worker
│   │   ├── aggregate.py             # Pattern aggregation
│   │   ├── optimize_weights.py      # Weight optimization
│   │   ├── validate_weights.py      # Validation
│   │   ├── deploy_weights.py        # Deployment
│   │   ├── publish_metrics.py       # CloudWatch metrics
│   │   ├── historical.py            # Monthly historical analysis
│   │   └── orchestrator.py          # Master orchestrator
│   └── ...
├── config/
│   └── weights.py                    # (Already exists - extended)
├── tests/
│   └── learning/                     # NEW: Learning system tests
│       ├── test_loss_analyzer.py
│       ├── test_pattern_aggregator.py
│       ├── test_weight_optimizer.py
│       └── fixtures/
│           ├── mock_losses.json
│           └── mock_results.json
└── ...
```

### 10.2 Key Modules

#### `backend/core/learning/loss_analyzer.py`

```python
"""
Core loss analysis logic.
"""

from typing import Dict, Any, List
from datetime import datetime
from .helpers import (
    calculate_consistency,
    calculate_form_velocity,
    get_jockey_rank,
    categorize_loss,
    calculate_confidence
)


class LossAnalyzer:
    """Analyzes individual race losses."""
    
    def __init__(self, sl_fetcher, racecard_fetcher):
        self.sl_fetcher = sl_fetcher
        self.racecard_fetcher = racecard_fetcher
    
    def analyze(self, bet_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze why our pick lost.
        
        Args:
            bet_record: Bet record from SureBetBets table
        
        Returns:
            Loss analysis with recommendations
        """
        # Implementation from Section 3.1
        pass
    
    def fetch_race_result(self, course: str, race_time: str, date: str) -> Dict[str, Any]:
        """Fetch race result from Sporting Life."""
        return self.sl_fetcher.fetch_result(course, race_time, date)
    
    def fetch_racecard(self, market_id: str, date: str) -> Dict[str, Any]:
        """Fetch full racecard data."""
        return self.racecard_fetcher.fetch(market_id, date)
    
    def compare_horses(self, our_pick: Dict, winner: Dict) -> Dict[str, Any]:
        """Compare our pick vs winner."""
        # Implementation from Section 3.1
        pass
    
    def identify_missing_signals(self, comparison: Dict) -> List[Dict[str, Any]]:
        """Identify which signals we missed."""
        # Implementation from Section 3.1
        pass
    
    def generate_recommendations(self, missing_signals: List) -> Dict[str, int]:
        """Generate weight adjustment recommendations."""
        # Implementation from Section 3.1
        pass
```

#### `backend/core/learning/weight_optimizer.py`

```python
"""
Weight optimization and deployment.
"""

from typing import Dict, Any, List
from config.weights import WeightManager, DEFAULT_WEIGHTS


class WeightOptimizer:
    """Optimizes weights based on loss patterns."""
    
    def __init__(self):
        self.manager = WeightManager()
        self.current_weights = self.manager.get_weights()
    
    def calculate_adjustments(
        self, 
        patterns: Dict[str, Any],
        historical_frequency: Dict[str, int]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate weight adjustments based on patterns.
        
        Args:
            patterns: Aggregated pattern data
            historical_frequency: Pattern frequency over last 7 days
        
        Returns:
            Dict of weight adjustments with confidence
        """
        # Implementation from Section 5.1
        pass
    
    def apply_safety_bounds(
        self, 
        weight_name: str, 
        current_value: float, 
        proposed_delta: float
    ) -> tuple[float, float]:
        """Apply safety bounds to adjustment."""
        # Implementation from Section 5.2
        pass
    
    def validate(self, adjustments: Dict) -> bool:
        """Validate adjustments are safe."""
        # Implementation from Section 4.1
        pass
    
    def deploy(self, adjustments: Dict) -> bool:
        """Deploy new weights to DynamoDB."""
        # Implementation from Section 4.1
        pass
```

### 10.3 Lambda Handler Templates

#### `backend/pipeline/learning/analyze_loss.py`

```python
"""
Lambda handler: Analyze single loss.
"""

import json
import os
from core.learning.loss_analyzer import LossAnalyzer
from core.enrichment.sporting_life import SportingLifeFetcher
from core.enrichment.racecard_fetcher import RacecardFetcher


def lambda_handler(event, context):
    """
    Analyze a single loss.
    
    Input:
        {
            "bet_id": "...",
            "horse": "...",
            "course": "...",
            "race_time": "...",
            "actual_result": "LOSS",
            "score_breakdown": {...}
        }
    
    Output:
        {
            "loss_id": "...",
            "loss_category": "...",
            "missing_signals": [...],
            "weight_recommendations": {...}
        }
    """
    
    bet_record = event
    
    # Initialize analyzer
    sl_fetcher = SportingLifeFetcher()
    racecard_fetcher = RacecardFetcher()
    analyzer = LossAnalyzer(sl_fetcher, racecard_fetcher)
    
    # Analyze loss
    analysis = analyzer.analyze(bet_record)
    
    # Store in DynamoDB
    import boto3
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('BetBudAI_LearningInsights')
    table.put_item(Item=analysis)
    
    return analysis
```

#### `backend/pipeline/learning/orchestrator.py`

```python
"""
Lambda handler: Master orchestrator.
"""

# Implementation from Section 4.1
```

---

## 11. Deployment Checklist

### Pre-Deployment

- [ ] **Code Review**: All learning modules peer-reviewed
- [ ] **Unit Tests**: >90% coverage for core learning logic
- [ ] **Integration Tests**: End-to-end pipeline tested in dev
- [ ] **Performance Tests**: Tested with 100+ concurrent losses
- [ ] **Security Review**: IAM roles follow least privilege
- [ ] **Cost Estimation**: Validated <$10/month additional cost
- [ ] **Documentation**: README and runbook complete

### Infrastructure

- [ ] **DynamoDB Tables**: Created with proper indexes and TTL
- [ ] **Lambda Functions**: Deployed to all environments (dev/prod)
- [ ] **Step Functions**: State machine deployed and tested
- [ ] **EventBridge**: Cron rules created (disabled initially)
- [ ] **SNS Topics**: Alert topics created with subscriptions
- [ ] **CloudWatch**: Alarms and dashboard created
- [ ] **IAM Roles**: Lambda execution roles with required permissions

### Configuration

- [ ] **Environment Variables**: Set for all Lambda functions
- [ ] **Secrets**: Stored in Secrets Manager (if needed)
- [ ] **Concurrency Limits**: Set on all Lambda functions
- [ ] **Timeouts**: Configured appropriately (60s workers, 10min orchestrator)
- [ ] **Memory**: Allocated (512MB workers, 1024MB orchestrator)

### Validation

- [ ] **Dry Run**: Run orchestrator with deployment disabled
- [ ] **Manual Test**: Trigger pipeline manually, verify output
- [ ] **Metrics Check**: Validate CloudWatch metrics publishing
- [ ] **Alert Check**: Validate SNS notifications working
- [ ] **Rollback Test**: Test rollback logic with mock degradation

### Go-Live

- [ ] **Enable EventBridge Rule**: Activate daily trigger (21:30 UTC)
- [ ] **Monitor First Run**: Watch CloudWatch logs during first execution
- [ ] **Verify Results**: Check DynamoDB for loss analyses
- [ ] **Verify Weights**: Confirm weights updated (if applicable)
- [ ] **Alert Check**: Confirm no unexpected alerts fired

### Post-Deployment

- [ ] **Performance Baseline**: Establish baseline metrics (day 1-7)
- [ ] **Strike Rate Tracking**: Monitor daily strike rate vs baseline
- [ ] **Cost Monitoring**: Track actual AWS costs vs estimate
- [ ] **Error Rate**: Monitor Lambda error rates
- [ ] **Documentation Update**: Update with any production learnings

### Week 1 Checklist

**Monday (Day 1)**:
- [ ] Deploy DynamoDB tables
- [ ] Deploy loss analysis worker Lambda
- [ ] Test worker with 5 historical losses
- [ ] Review test results

**Tuesday (Day 2)**:
- [ ] Deploy master orchestrator Lambda
- [ ] Deploy weight optimizer Lambda
- [ ] Test end-to-end with 1 day of data
- [ ] Fix any bugs found

**Wednesday (Day 3)**:
- [ ] Deploy validation & deployment Lambdas
- [ ] Create Step Functions state machine
- [ ] Create CloudWatch dashboard
- [ ] Create SNS alerts

**Thursday (Day 4)**:
- [ ] Dry run on production data (no deployment)
- [ ] Review dry run results
- [ ] Get stakeholder approval
- [ ] Enable EventBridge rule (disabled)

**Friday (Day 5)**:
- [ ] Enable EventBridge rule for 21:30 UTC run
- [ ] Monitor first production run
- [ ] Verify weights updated correctly
- [ ] Celebrate if successful!

**Weekend (Days 6-7)**:
- [ ] Monitor Saturday/Sunday runs
- [ ] Review first 3 days of data
- [ ] Adjust parameters if needed

### Success Metrics

**Week 1**:
- [ ] Pipeline runs successfully daily (7/7 days)
- [ ] >90% of losses analyzed successfully
- [ ] Weight adjustments validated correctly
- [ ] No manual interventions required

**Month 1**:
- [ ] Strike rate improves by +2-5%
- [ ] ROI improves or remains stable
- [ ] No rollbacks triggered
- [ ] <5 human review triggers

**Month 3**:
- [ ] Strike rate improves by +5-10%
- [ ] ROI improves by +5-10%
- [ ] System fully autonomous
- [ ] Monthly historical analysis providing insights

---

## Appendix A: CloudWatch Dashboard JSON

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Daily Losses Analyzed",
        "metrics": [
          ["BetBudAI/Learning", "DailyLossesAnalyzed"]
        ],
        "period": 86400,
        "stat": "Sum",
        "region": "eu-west-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Patterns Detected",
        "metrics": [
          ["BetBudAI/Learning", "PatternsDetected"]
        ],
        "period": 86400,
        "stat": "Sum"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Weights Adjusted",
        "metrics": [
          ["BetBudAI/Learning", "WeightsAdjusted"]
        ],
        "period": 86400,
        "stat": "Sum"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Lambda Duration (Orchestrator)",
        "metrics": [
          ["AWS/Lambda", "Duration", {"FunctionName": "learning-master-orchestrator"}]
        ],
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Lambda Errors",
        "metrics": [
          ["AWS/Lambda", "Errors", {"FunctionName": "learning-master-orchestrator"}],
          ["...", {"FunctionName": "learning-analyze-loss"}]
        ],
        "period": 300,
        "stat": "Sum"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Strike Rate Trend (7-day MA)",
        "metrics": [
          ["BetBudAI/Performance", "StrikeRate"]
        ],
        "period": 604800,
        "stat": "Average"
      }
    }
  ]
}
```

---

## Appendix B: IAM Policies

### Learning Pipeline Execution Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:eu-west-1:*:table/SureBetBets",
        "arn:aws:dynamodb:eu-west-1:*:table/BetBudAI_LearningInsights",
        "arn:aws:dynamodb:eu-west-1:*:table/BetBudAI_HistoricalReports",
        "arn:aws:dynamodb:eu-west-1:*:table/BetBudAI_AuditLog",
        "arn:aws:dynamodb:eu-west-1:*:table/BetBudAI_ABTests"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:eu-west-1:*:function:learning-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:sns:eu-west-1:*:betbudai-alerts",
        "arn:aws:sns:eu-west-1:*:betbudai-admin-alerts"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "BetBudAI/Learning"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:eu-west-1:*:log-group:/aws/lambda/learning-*"
    }
  ]
}
```

---

## Appendix C: Sample Loss Analysis Output

```json
{
  "loss_id": "20260520_1430_Ascot_GoldenMiller",
  "analyzed_at": "2026-05-20T21:32:15.123Z",
  "date": "2026-05-20",
  "race_id": "Ascot_14:30",
  "our_pick": {
    "name": "Golden Miller",
    "odds": 4.5,
    "score": 92,
    "score_breakdown": {
      "recent_win": 16,
      "consistency": 6,
      "form_velocity_bonus": 10,
      "course_bonus": 12,
      "jockey_quality": 12,
      "class_drop_bonus": 0,
      "going_suitability": 16,
      "trainer_form_bonus": 8,
      "distance_suitability": 12,
      "total": 92
    }
  },
  "actual_winner": {
    "name": "Silver Streak",
    "odds": 5.0,
    "reconstructed_score": 98,
    "form": "22321",
    "jockey": "Frankie Dettori",
    "trainer": "John Gosden"
  },
  "missing_signals": [
    {
      "signal": "consistency",
      "gap": 18,
      "description": "Winner (Silver Streak) had consistent form (2-2-3-2-1) vs our pick's volatile form (1-8-5-1-9)"
    },
    {
      "signal": "jockey_upgrade",
      "gap": 2,
      "description": "Winner had elite jockey (Frankie Dettori), our pick had apprentice"
    }
  ],
  "loss_category": "consistent_placer_missed",
  "score_gap": 6,
  "weight_recommendations": {
    "consistency": 8,
    "recent_win": -5,
    "jockey_quality": 6,
    "jockey_course_bonus": 8
  },
  "confidence_score": 85
}
```

---

## Summary

This automated learning system will:

1. **Analyze 100% of losses** within 30 minutes of settlement (21:30 UTC daily)
2. **Identify patterns** across 20-40 daily losses using parallel processing
3. **Auto-adjust weights** based on validated patterns (5+ occurrences = high confidence)
4. **Monthly deep analysis** of 150-200 races to catch systematic biases
5. **A/B test changes** before full deployment (80/20 split for 7 days)
6. **Auto-rollback** if performance degrades (>5% strike rate drop)
7. **Human oversight** for extreme changes (>15pt adjustments)

**Expected Impact**:
- Strike rate: 20-25% → 30-35% within 60 days
- ROI: Break-even → 10%+ within 90 days
- Continuous improvement via daily learning

**Cost**: <$10/month (DynamoDB + Lambda)

**Deployment**: Week 1 (production-ready)

---

**END OF DOCUMENT**
