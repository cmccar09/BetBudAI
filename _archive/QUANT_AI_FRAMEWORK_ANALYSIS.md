# Quantitative Betting AI Framework Analysis

## Executive Summary
Review of proposed quant framework vs existing SureBet system. **Most features already implemented**, some gaps identified for enhancement.

---

## ✅ ALREADY IMPLEMENTED

### 1. **Probabilistic Modeling**
- **Status:** ✅ ACTIVE
- **Location:** `enhanced_analysis.py`, `save_selections_to_dynamodb.py`
- **Implementation:**
  - Predicts `p_win` and `p_place` for each runner
  - Uses AWS Bedrock Claude for multi-pass analysis
  - Outputs probabilities (not binary picks)
  - Example: `p_win: 0.28` (28% chance to win)

### 2. **Expected Value (EV) Calculation**
- **Status:** ✅ ACTIVE
- **Location:** `save_selections_to_dynamodb.py` lines 328-350
- **Formula:**
  ```python
  # WIN bets
  ev = (implied_odds * p_win) - 1
  
  # EW bets (split stake)
  place_odds = 1 + ((implied_odds - 1) * ew_fraction)
  total_return = (p_win * win_scenario_return) + (place_only_prob * place_scenario_return)
  ev = total_return - 1
  ```
- **ROI Calculation:** `roi_pct = ev * 100`

### 3. **Positive EV Filtering**
- **Status:** ✅ ACTIVE (but with lower threshold than proposed)
- **Current Thresholds:**
  - Horses: **0% ROI minimum** (breakeven)
  - Greyhounds: **-15% ROI minimum** (adjusted for lower odds structure)
- **Proposed:** +5% EV minimum
- **Gap:** Current system accepts breakeven/slightly negative EV bets

### 4. **Market Odds Comparison**
- **Status:** ✅ ACTIVE
- **Location:** `save_selections_to_dynamodb.py` lines 306-312
- **Implementation:**
  - Loads actual Betfair market odds from snapshots
  - Compares AI probabilities vs market implied probabilities
  - Calculates market edge in combined confidence score
  - Formula: `edge = p_win - (1 / market_odds)`

### 5. **Self-Learning Loop**
- **Status:** ✅ ACTIVE
- **Components:**
  - `evaluate_performance.py` - Compares predictions vs actual results
  - `generate_learning_insights.py` - Extracts patterns from historical data
  - `analyze_losing_bets()` - Analyzes what actual winners had vs our picks
  - `learning_insights.json` - Stores learnings
- **Metrics Tracked:**
  - Win rate vs predicted
  - Calibration error (Brier score analog)
  - Tag-based performance
  - ROI by strategy
- **Auto-Updates:** After every race via `scheduled_workflow.ps1`

### 6. **Separate Models by Sport**
- **Status:** ✅ ACTIVE
- **Implementation:**
  - Horses: Standard ROI threshold (0%)
  - Greyhounds: Adjusted ROI threshold (-15%)
  - Sport-specific ROI calculation (5% boost for greyhounds with odds < 2.5)
  - Venue-based sport detection

### 7. **Kelly Criterion Bankroll Management**
- **Status:** ✅ IMPLEMENTED (not currently used in production)
- **Location:** `learning_engine.py` lines 268-330
- **Features:**
  ```python
  kelly_fraction = 0.25  # Quarter Kelly for safety
  max_stake_pct = 0.05   # Never more than 5% of bankroll
  
  # Kelly formula: f = (bp - q) / b
  kelly_full = (b * p_win - q) / b
  fractional_kelly = max(0, kelly_full * kelly_fraction)
  stake = min(fractional_kelly * bankroll, bankroll * max_stake_pct)
  ```
- **Gap:** Not integrated into DynamoDB picks or UI

### 8. **Combined Confidence Scoring**
- **Status:** ✅ ACTIVE
- **Location:** `save_selections_to_dynamodb.py` lines 163-272
- **Components:**
  - Win Probability (40% weight)
  - Place Probability (20% weight)
  - Value Edge (20% weight)
  - Consistency Score (20% weight)
- **Output:** 0-100 score with grades (EXCELLENT, GOOD, FAIR, POOR)

### 9. **Data Processing & Weighting**
- **Status:** ✅ ACTIVE
- **Data Sources:**
  - Betfair market data (odds, volumes)
  - Racing Post form data (when available)
  - Historical results
  - Odds movement tracking
  - Track/venue conditions
- **Location:** `enhanced_racing_data_fetcher.py`, `odds_movement_tracker.py`

---

## ⚠️ GAPS TO ADDRESS

### 1. **EV Threshold Too Low**
- **Current:** 0% (horses), -15% (greyhounds)
- **Proposed:** +5% minimum
- **Recommendation:** 
  ```python
  # Update in save_selections_to_dynamodb.py
  horse_min_roi = 5.0  # Increase from 0.0
  greyhound_min_roi = 0.0  # Increase from -15.0
  ```
- **Impact:** Fewer bets, but higher quality

### 2. **Ensemble Methods Not Implemented**
- **Current:** Single AWS Bedrock Claude model
- **Proposed:** Multiple models voting
- **Recommendation:**
  - Add secondary model (e.g., XGBoost trained on historical data)
  - Compare AI predictions vs statistical model
  - Average or weight the two predictions
  - Increase confidence when models agree
- **New File:** `ensemble_predictions.py`

### 3. **Brier Score Not Tracked**
- **Current:** Calibration error tracked but not Brier score
- **Proposed:** Formal Brier score calculation
- **Recommendation:**
  ```python
  # Add to evaluate_performance.py
  def calculate_brier_score(predictions, outcomes):
      """Brier Score = mean((prediction - outcome)^2)"""
      return sum((p - o)**2 for p, o in zip(predictions, outcomes)) / len(predictions)
  ```

### 4. **Recency Weighting Not Explicit**
- **Current:** Learning uses all historical data equally
- **Proposed:** Recent races weighted more heavily
- **Recommendation:**
  ```python
  # Add to generate_learning_insights.py
  def apply_recency_weights(df):
      df['days_ago'] = (datetime.now() - pd.to_datetime(df['date'])).dt.days
      df['recency_weight'] = 1 / (1 + (df['days_ago'] / 7))  # Decay weekly
      return df
  ```

### 5. **Bayesian Updating Not Implemented**
- **Current:** AI learns from aggregate patterns
- **Proposed:** Bayesian probability updating after each race
- **Recommendation:**
  - Track prior beliefs (e.g., "trainer X has 20% win rate")
  - Update posterior after each result
  - Use Beta distribution for win rates
  - **New File:** `bayesian_updater.py`

### 6. **Daily Risk Limit Not Enforced**
- **Current:** No maximum daily exposure
- **Proposed:** 5% max daily risk
- **Recommendation:**
  ```python
  # Add to save_selections_to_dynamodb.py
  def enforce_daily_risk_limit(picks, bankroll=1000, max_daily_risk=0.05):
      total_exposure = sum(p.get('stake', 0) for p in picks)
      max_exposure = bankroll * max_daily_risk
      
      if total_exposure > max_exposure:
          # Scale down all stakes proportionally
          scale_factor = max_exposure / total_exposure
          for pick in picks:
              pick['stake'] = pick.get('stake', 0) * scale_factor
      
      return picks
  ```

### 7. **Stop-Loss Rules Not Implemented**
- **Current:** No automatic stopping after drawdowns
- **Proposed:** Pause betting after losing streaks
- **Recommendation:**
  ```python
  # Add to scheduled_workflow.ps1
  def check_drawdown():
      recent_results = get_last_n_days_results(7)
      total_pnl = sum(r['profit_loss'] for r in recent_results)
      
      if total_pnl < -50:  # Lost more than 50 units in 7 days
          print("STOP-LOSS TRIGGERED: Pausing betting for 24 hours")
          return False  # Don't generate new picks
      return True
  ```

### 8. **Kelly Stakes Not Applied to Actual Bets**
- **Current:** Kelly calculation exists but not used in production
- **Proposed:** Add stake sizes to all picks
- **Recommendation:**
  ```python
  # Add to format_bet_for_dynamodb()
  from learning_engine import calculate_bet_stake
  
  stake = calculate_bet_stake(
      odds=implied_odds,
      p_win=p_win,
      bankroll=1000,  # Make configurable
      bet_type=bet_type,
      p_place=p_place,
      ew_fraction=ew_fraction
  )
  
  bet_item['stake'] = round(stake, 2)
  bet_item['stake_units'] = round(stake / 10, 2)  # Convert to unit stakes
  ```

---

## 📋 IMPLEMENTATION PRIORITY

### HIGH PRIORITY (Implement Now)
1. **Increase EV threshold to +5%** (1 hour)
   - Update `horse_min_roi` and `greyhound_min_roi` in save_selections_to_dynamodb.py
   
2. **Add Kelly stakes to picks** (2 hours)
   - Integrate `learning_engine.calculate_bet_stake()` into `format_bet_for_dynamodb()`
   - Add `stake` and `stake_units` fields to DynamoDB items
   - Display stake in UI

3. **Implement daily risk limit** (2 hours)
   - Add `enforce_daily_risk_limit()` before saving to database
   - Track daily total exposure

### MEDIUM PRIORITY (Next Sprint)
4. **Add Brier score tracking** (3 hours)
   - Update `evaluate_performance.py` with formal Brier score
   - Track improvement over time
   
5. **Implement recency weighting** (4 hours)
   - Update `generate_learning_insights.py` to weight recent races more
   - Exponential decay (e.g., last 7 days = 1.0, 14 days = 0.5, 30 days = 0.25)

6. **Add stop-loss protection** (3 hours)
   - Track 7-day rolling P&L
   - Pause betting after -5% drawdown
   - Resume after 24-48 hours

### LOW PRIORITY (Future Enhancement)
7. **Ensemble modeling** (20+ hours)
   - Train XGBoost model on historical data
   - Compare AI vs statistical predictions
   - Weighted ensemble voting

8. **Bayesian updating** (15+ hours)
   - Implement Beta distribution tracking
   - Update trainer/jockey priors after each race
   - Feed updated priors into AI analysis

---

## 🎯 RECOMMENDED NEXT STEPS

1. **Quick Win:** Update ROI thresholds to +5% (horses), +2% (greyhounds)
   - More selective, higher quality bets
   - Better long-term ROI

2. **Activate Kelly Staking:** Integrate existing Kelly code into production
   - Optimal bet sizing
   - Better bankroll growth

3. **Add Risk Management:** Daily limits and stop-loss
   - Protect capital during losing streaks
   - Sustainable long-term operation

4. **Track Brier Score:** Add formal calibration metric
   - Measure prediction accuracy improvement
   - Identify when model needs retraining

---

## 📊 CURRENT SYSTEM STRENGTHS

- ✅ **Probabilistic predictions** (not binary)
- ✅ **EV-based selection** (ROI calculated)
- ✅ **Self-learning system** (evaluates every race)
- ✅ **Market comparison** (edge detection)
- ✅ **Combined confidence** (multi-signal weighting)
- ✅ **Loser analysis** (learns from mistakes)
- ✅ **Sport-specific logic** (horses vs greyhounds)
- ✅ **Kelly Criterion code exists** (just not integrated)

**Bottom Line:** Your SureBet system already implements ~70% of the proposed quant framework. The main gaps are:
1. Stricter EV thresholds
2. Kelly stake sizing in production
3. Risk management (daily limits, stop-loss)
4. Ensemble methods

Would you like me to implement the HIGH PRIORITY items now?
