# Betting Prompt Integration - Quick Start

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements-prompt.txt
   ```

2. **Set up API key** (choose one):
   
   For Anthropic Claude:
   ```bash
   $env:ANTHROPIC_API_KEY = "your-api-key-here"
   ```
   
   For OpenAI GPT:
   ```bash
   $env:OPENAI_API_KEY = "your-api-key-here"
   ```

## Usage

### Option 1: Standalone (Test the prompt logic)

Run the prompt against existing snapshot data:

```bash
python run_saved_prompt.py --snapshot ./snapshots/run_20241216_143000_once.csv --out ./test_selections.csv
```

Options:
- `--prompt ./prompt.txt` - Your betting logic prompt (default: ./prompt.txt)
- `--snapshot <path>` - Market data CSV/JSON (auto-discovers latest if omitted)
- `--out <path>` - Output CSV for selections (default: ./my_probs.csv)
- `--provider anthropic|openai|auto` - LLM provider (default: auto)
- `--max_races <n>` - Limit to first N races (useful for testing)

### Option 2: Integrated (Full workflow with live data)

Run the complete pipeline: fetch Betfair data → apply prompt → generate Top 5:

```bash
python run_prompt_with_betfair.py --use_saved_prompt --auto --once
```

Key flags:
- `--use_saved_prompt` - Enables prompt.txt logic
- `--auto` - Fetch fresh Betfair snapshots first
- `--once` - Single snapshot now (vs scheduled snapshots)
- `--window_hours 4.0` - Race window (default: 4 hours)
- `--countries GB,IE` - Restrict to UK & Ireland

Full example:
```bash
python run_prompt_with_betfair.py \
    --use_saved_prompt \
    --auto \
    --once \
    --window_hours 4.0 \
    --countries GB,IE \
    --out_csv ./today_top5.csv \
    --analysis_report ./today_analysis.md
```

## What It Does

The integration:

1. **Loads your prompt** from [prompt.txt](prompt.txt) containing:
   - Bradley-Terry + Plackett-Luce modeling logic
   - Each-Way analysis rules
   - Portfolio ROI thresholds (≥20%)
   - Staking (fractional Kelly)
   - Selection gating criteria

2. **Fetches live Betfair data** (if --auto):
   - UK & Ireland races in next 4 hours
   - WIN and PLACE markets
   - Current odds/liquidity

3. **Calls LLM for each race** with:
   - Your full prompt logic
   - Race-specific market data
   - Runner names, IDs, and odds

4. **Parses selections** back to structured CSV:
   - `p_win`, `p_place` probabilities
   - EW terms and EV calculations
   - Edge tags and rationale
   - Recommended stakes

5. **Generates Top 5** based on:
   - Overlay thresholds
   - Portfolio diversification
   - ROI requirements

## Example Output

The script creates `my_probs.csv` with columns:
```
runner_name,selection_id,market_id,market_name,venue,start_time_dublin,
p_win,p_place,ew_places,ew_fraction,tags,why_now
```

Example row:
```
"Red Rum",12345,1.234567,"Win","Cheltenham","2024-12-16 14:30:00",
0.25,0.45,3,0.2,"pace/draw edge, EW value","Lone early pace, draw 1 advantage"
```

## Troubleshooting

**No API key found:**
- Make sure you set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` environment variable

**No snapshot file found:**
- Run with `--auto` flag to fetch fresh data
- Or point to existing snapshot with `--snapshot <path>`

**Empty selections:**
- Normal if no races meet ROI threshold (>+20%)
- Try `--max_races 1` to test on single race first
- Check LLM response in console output

**Module not found:**
- Run `pip install -r requirements-prompt.txt`

## Cost Estimation

- Anthropic Claude Sonnet: ~$0.003 per race (input) + $0.015 per race (output)
- OpenAI GPT-4: ~$0.01 per race (input) + $0.03 per race (output)

Example: 20 races = $0.36 (Claude) or $0.80 (GPT-4)

## Self-Learning System

**NEW**: The system now learns from results and improves itself daily!

### How It Works:

1. **Track**: Each day's selections are saved with predictions
2. **Fetch**: Actual race results from Betfair API
3. **Analyze**: Compare predictions vs outcomes
   - Win/Place rates by edge tag type
   - Probability calibration errors
   - ROI by odds range
4. **Learn**: Identify what's working and what's not
5. **Update**: Automatically adjust prompt.txt thresholds

### Daily Learning Workflow:

```bash
# Full automated learning loop
python daily_learning_workflow.py --apply_updates --run_today
```

This will:
1. Fetch yesterday's race results
2. Evaluate prediction accuracy
3. Update prompt.txt with learned adjustments
4. Generate today's selections with improved logic

Or run steps manually:

```bash
# 1. Fetch results for yesterday
python fetch_race_results.py --date 2024-12-15 --selections ./history/selections_20241215.csv --out ./history/results_20241215.json

# 2. Evaluate performance and suggest adjustments
python evaluate_performance.py --selections ./history/selections_20241215.csv --results ./history/results_20241215.json --report ./history/performance_20241215.md

# 3. Review report and apply updates
python evaluate_performance.py --selections ./history/selections_20241215.csv --results ./history/results_20241215.json --apply

# 4. Generate today's picks with updated logic
python run_prompt_with_betfair.py --use_saved_prompt --auto --once
```

### What Gets Adjusted:

The system automatically adjusts:
- **Overlay thresholds** (if strike rate too low/high)
- **Probability calibration** (if predictions consistently over/under)
- **Edge tag weights** (boost what's working, reduce what's not)
- **Staking multipliers** (for different edge types)
- **Portfolio constraints** (based on actual ROI)

Example adjustments:
```
1. HIGH_PRIORITY: Calibration error is 15%. Consider adjusting 
   isotonic regression parameters.

2. OPPORTUNITY: Tag 'pace/draw edge' performing well (28% win rate 
   from 18 bets). Consider increasing allocation.

3. MEDIUM_PRIORITY: Tag 'class-drop sanity' has poor win rate 
   (8% from 12 bets). Consider tightening criteria.
```

## Files Created

- `run_saved_prompt.py` - Main prompt integration script
- `fetch_race_results.py` - Fetch actual Betfair results
- `evaluate_performance.py` - Analyze accuracy & generate adjustments
- `daily_learning_workflow.py` - Automated daily learning loop
- `requirements-prompt.txt` - Python dependencies
- `my_probs.csv` - Selection probabilities output
- `top5.csv` - Final Top 5 selections
- `top5_analysis.md` - Human-readable analysis report
- `history/` - Daily selections, results, and performance reports
