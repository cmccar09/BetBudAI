"""
generate_learning_insights.py - Extract learnings from performance data

Analyzes historical betting results to generate insights that improve
future selections. Creates learning_insights.json that enhanced_analysis.py
can load to adapt its strategy.
"""

import json
import pandas as pd
import glob
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict


def load_all_results(days_back: int = 30) -> List[Dict]:
    """Load all results from history folder"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    results = []
    history_path = Path(__file__).parent / "history"
    
    for results_file in history_path.glob("results_*.json"):
        # Extract date from filename (results_20260104.json)
        date_str = results_file.stem.replace("results_", "")
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date >= cutoff_date:
                with open(results_file, 'r') as f:
                    data = json.load(f)
                    results.append({
                        'date': date_str,
                        'data': data
                    })
        except (ValueError, json.JSONDecodeError) as e:
            print(f"Skipping {results_file}: {e}")
            continue
    
    return results


def merge_all_selections_with_results(days_back: int = 30) -> pd.DataFrame:
    """Merge selections with results across all days"""
    
    history_path = Path(__file__).parent / "history"
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    all_data = []
    
    # Find all selection files
    for selections_file in sorted(history_path.glob("selections_*.csv")):
        # Extract date from filename
        date_str = selections_file.stem.split('_')[1]  # selections_20260104_hhmmss.csv
        
        try:
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < cutoff_date:
                continue
            
            # Load selections
            selections_df = pd.read_csv(selections_file)
            
            # Find corresponding results file
            results_file = history_path / f"results_{date_str}.json"
            
            if not results_file.exists():
                print(f"No results for {date_str} yet")
                continue
            
            with open(results_file, 'r') as f:
                results_data = json.load(f)
            
            # Results can be either:
            # 1. Flat list of runners with market_id/selection_id
            # 2. Nested dict with 'markets' key containing runners
            if isinstance(results_data, list):
                # Check if it's a flat list (new format)
                if results_data and 'market_id' in results_data[0]:
                    # Flat format: convert to dict for easier lookup
                    results_lookup = {
                        (str(r.get('market_id')), str(r.get('selection_id'))): r 
                        for r in results_data
                    }
                else:
                    # Old nested format
                    markets = results_data
                    results_lookup = None
            else:
                markets = results_data.get('markets', [])
                results_lookup = None
            
            # Merge selections with results
            for _, row in selections_df.iterrows():
                selection_id = str(row.get('selection_id', ''))
                market_id = str(row.get('market_id', ''))
                
                # Find result for this selection
                result = None
                
                # Use flat lookup if available
                if results_lookup is not None:
                    result = results_lookup.get((market_id, selection_id))
                else:
                    # Old nested format
                    for market in markets:
                        if str(market.get('market_id')) == market_id:
                            for runner in market.get('runners', []):
                                if str(runner.get('selection_id')) == selection_id:
                                    result = runner
                                    break
                            break
                
                if result:
                    # Handle both old and new status formats
                    status = result.get('status', 'UNKNOWN')
                    is_winner = result.get('is_winner', False) or status == 'WINNER'
                    is_placed = result.get('is_placed', False) or status in ['WINNER', 'PLACED']
                    
                    # Extract odds (try multiple field names)
                    odds = None
                    for odds_field in ['odds', 'last_price_traded', 'sp']:
                        if odds_field in row:
                            try:
                                odds = float(row[odds_field])
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    # If no odds in row, try result
                    if odds is None and result:
                        for odds_field in ['odds', 'last_price_traded', 'sp']:
                            if odds_field in result:
                                try:
                                    odds = float(result[odds_field])
                                    break
                                except (ValueError, TypeError):
                                    continue
                    
                    merged = {
                        'date': date_str,
                        'runner_name': row.get('runner_name', ''),
                        'venue': row.get('venue', ''),
                        'market_name': row.get('market_name', ''),
                        'odds': odds if odds else 0.0,
                        'p_win': float(row.get('p_win', 0)),
                        'p_place': float(row.get('p_place', 0)),
                        'bet_type': row.get('bet_type', 'EW'),
                        'tags': row.get('tags', ''),
                        'why_now': row.get('why_now', ''),
                        'status': status,
                        'won': is_winner,
                        'placed': is_placed
                    }
                    all_data.append(merged)
        
        except Exception as e:
            print(f"Error processing {selections_file}: {e}")
            continue
    
    if not all_data:
        return pd.DataFrame()
    
    return pd.DataFrame(all_data)


def analyze_tag_performance(df: pd.DataFrame) -> Dict[str, Dict]:
    """Analyze which selection strategies work best"""
    
    tag_stats = defaultdict(lambda: {'wins': 0, 'places': 0, 'total': 0, 'p_win_avg': []})
    
    for _, row in df.iterrows():
        tags = str(row.get('tags', '')).split(',')
        
        for tag in tags:
            tag = tag.strip()
            if not tag or tag == 'enhanced_analysis':
                continue
            
            tag_stats[tag]['total'] += 1
            tag_stats[tag]['p_win_avg'].append(row.get('p_win', 0))
            
            if row.get('won', False):
                tag_stats[tag]['wins'] += 1
            if row.get('placed', False):
                tag_stats[tag]['places'] += 1
    
    # Calculate rates
    results = {}
    for tag, stats in tag_stats.items():
        if stats['total'] >= 3:  # Minimum sample size
            win_rate = stats['wins'] / stats['total']
            place_rate = stats['places'] / stats['total']
            avg_p_win = sum(stats['p_win_avg']) / len(stats['p_win_avg'])
            
            results[tag] = {
                'win_rate': win_rate,
                'place_rate': place_rate,
                'expected_win_rate': avg_p_win,
                'calibration': win_rate - avg_p_win,
                'sample_size': stats['total'],
                'verdict': 'WORKING' if win_rate >= avg_p_win * 0.8 else 'FAILING'
            }
    
    return results


def analyze_odds_ranges(df: pd.DataFrame) -> Dict[str, Dict]:
    """Analyze performance by odds ranges - KEY FOR SWEET SPOT OPTIMIZATION"""
    
    if 'odds' not in df.columns or len(df) == 0:
        return {}
    
    # Filter out invalid odds
    df_valid = df[df['odds'] > 0].copy()
    
    if len(df_valid) == 0:
        return {}
    
    # Define sweet spot ranges
    ranges = {
        'ultimate_sweet_spot': (3.5, 6.0),  # Perfect range
        'sweet_spot': (3.0, 9.0),           # Target range  
        'short_odds': (1.0, 3.0),           # Favorites
        'medium_odds': (9.0, 15.0),         # Long shots
        'long_odds': (15.0, 50.0),          # Very long
        'extreme_odds': (50.0, 1000.0)      # Avoid
    }
    
    odds_stats = {}
    
    for range_name, (min_odds, max_odds) in ranges.items():
        range_df = df_valid[(df_valid['odds'] >= min_odds) & (df_valid['odds'] < max_odds)]
        
        if len(range_df) == 0:
            continue
        
        total_bets = len(range_df)
        wins = range_df['won'].sum()
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        # Calculate ROI (simple: assume €1 stake per bet)
        total_stake = total_bets
        total_return = 0
        
        for _, row in range_df.iterrows():
            if row['won']:
                total_return += row['odds']  # Return includes stake
        
        profit = total_return - total_stake
        roi = (profit / total_stake * 100) if total_stake > 0 else 0
        
        odds_stats[range_name] = {
            'range': f"{min_odds:.1f}-{max_odds:.1f}",
            'total_bets': int(total_bets),
            'wins': int(wins),
            'win_rate': float(win_rate),
            'roi': float(roi),
            'avg_odds': float(range_df['odds'].mean()),
            'verdict': 'PROFITABLE' if roi > 0 else 'LOSING'
        }
    
    return odds_stats


def extract_pattern_learnings(df: pd.DataFrame, tag_performance: Dict, odds_performance: Dict) -> Dict[str, Any]:
    """Extract specific learnings from the data"""
    
    learnings = {
        'generated_at': datetime.now().isoformat(),
        'sample_size': len(df),
        'date_range': f"{df['date'].min()} to {df['date'].max()}" if len(df) > 0 else "No data",
        'overall_stats': {},
        'odds_performance': odds_performance,
        'sweet_spot_analysis': {},
        'winning_patterns': [],
        'failing_patterns': [],
        'recommendations': []
    }
    
    if len(df) == 0:
        learnings['recommendations'].append("Insufficient data - need at least 30 days of results")
        return learnings
    
    # Overall stats
    learnings['overall_stats'] = {
        'total_bets': len(df),
        'wins': int(df['won'].sum()),
        'win_rate': float(df['won'].mean()),
        'places': int(df['placed'].sum()),
        'place_rate': float(df['placed'].mean()),
        'avg_p_win': float(df['p_win'].mean())
    }
    
    # Sweet spot specific analysis
    if 'odds' in df.columns:
        df_valid = df[df['odds'] > 0].copy()
        sweet_spot_df = df_valid[(df_valid['odds'] >= 3.0) & (df_valid['odds'] < 9.0)]
        ultimate_sweet_df = df_valid[(df_valid['odds'] >= 3.5) & (df_valid['odds'] < 6.0)]
        
        if len(sweet_spot_df) > 0:
            ss_wins = sweet_spot_df['won'].sum()
            ss_total = len(sweet_spot_df)
            ss_win_rate = ss_wins / ss_total if ss_total > 0 else 0
            
            # Calculate ROI for sweet spot
            ss_stake = ss_total
            ss_return = sum(row['odds'] for _, row in sweet_spot_df.iterrows() if row['won'])
            ss_profit = ss_return - ss_stake
            ss_roi = (ss_profit / ss_stake * 100) if ss_stake > 0 else 0
            
            learnings['sweet_spot_analysis'] = {
                'range': '3.0-9.0 (2/1 to 8/1)',
                'total_bets': int(ss_total),
                'wins': int(ss_wins),
                'win_rate': float(ss_win_rate),
                'roi': float(ss_roi),
                'percentage_of_portfolio': float(ss_total / len(df_valid) * 100) if len(df_valid) > 0 else 0,
                'verdict': 'PROFITABLE' if ss_roi > 0 else 'NEEDS_IMPROVEMENT'
            }
            
            # Ultimate sweet spot
            if len(ultimate_sweet_df) > 0:
                uss_wins = ultimate_sweet_df['won'].sum()
                uss_total = len(ultimate_sweet_df)
                uss_win_rate = uss_wins / uss_total if uss_total > 0 else 0
                uss_stake = uss_total
                uss_return = sum(row['odds'] for _, row in ultimate_sweet_df.iterrows() if row['won'])
                uss_profit = uss_return - uss_stake
                uss_roi = (uss_profit / uss_stake * 100) if uss_stake > 0 else 0
                
                learnings['sweet_spot_analysis']['ultimate'] = {
                    'range': '3.5-6.0 (5/2 to 5/1)',
                    'total_bets': int(uss_total),
                    'wins': int(uss_wins),
                    'win_rate': float(uss_win_rate),
                    'roi': float(uss_roi)
                }
    
    # Winning patterns (tags that outperform)
    for tag, stats in tag_performance.items():
        if stats['verdict'] == 'WORKING' and stats['sample_size'] >= 5:
            learnings['winning_patterns'].append({
                'pattern': tag,
                'win_rate': f"{stats['win_rate']:.1%}",
                'expected': f"{stats['expected_win_rate']:.1%}",
                'sample_size': stats['sample_size'],
                'action': 'KEEP - this strategy is working'
            })
    
    # Failing patterns (tags that underperform)
    for tag, stats in tag_performance.items():
        if stats['verdict'] == 'FAILING' and stats['sample_size'] >= 5:
            learnings['failing_patterns'].append({
                'pattern': tag,
                'win_rate': f"{stats['win_rate']:.1%}",
                'expected': f"{stats['expected_win_rate']:.1%}",
                'sample_size': stats['sample_size'],
                'action': 'REDUCE - underperforming expectations'
            })
    
    # Generate recommendations - SWEET SPOT FOCUS
    overall_win_rate = learnings['overall_stats']['win_rate']
    avg_p_win = learnings['overall_stats']['avg_p_win']
    
    # Priority 1: Sweet spot performance
    if learnings.get('sweet_spot_analysis'):
        ss_data = learnings['sweet_spot_analysis']
        ss_percentage = ss_data.get('percentage_of_portfolio', 0)
        ss_roi = ss_data.get('roi', 0)
        ss_win_rate = ss_data.get('win_rate', 0)
        
        if ss_percentage < 60:
            learnings['recommendations'].append(
                f"🎯 CRITICAL: Only {ss_percentage:.1f}% of bets in SWEET SPOT (3.0-9.0 odds). "
                f"TARGET: 80%+ in this range. This is where winners are!"
            )
        
        if ss_roi > 10:
            learnings['recommendations'].append(
                f"✅ SWEET SPOT WORKING: {ss_roi:.1f}% ROI with {ss_win_rate:.1%} win rate. "
                f"DOUBLE DOWN on 3.0-9.0 odds range!"
            )
        elif ss_roi < -10:
            learnings['recommendations'].append(
                f"⚠️ Sweet spot underperforming: {ss_roi:.1f}% ROI. "
                f"Review selection criteria WITHIN the range - need better winners at 3-9 odds."
            )
        
        # Ultimate sweet spot guidance
        if 'ultimate' in ss_data:
            uss_data = ss_data['ultimate']
            if uss_data['total_bets'] >= 5:
                if uss_data['roi'] > ss_roi:
                    learnings['recommendations'].append(
                        f"🏆 ULTIMATE SWEET SPOT (3.5-6.0) is BEST: {uss_data['roi']:.1f}% ROI. "
                        f"Prioritize this sub-range within sweet spot!"
                    )
    
    # Calibration
    if overall_win_rate < avg_p_win * 0.7:
        learnings['recommendations'].append(
            f"Calibration issue: Win rate ({overall_win_rate:.1%}) well below predictions ({avg_p_win:.1%}). "
            "Focus on PROVEN WINNERS in sweet spot, not hopefuls."
        )
    
    # Odds range comparison
    if odds_performance:
        # Find best performing range
        best_range = None
        best_roi = -999
        for range_name, stats in odds_performance.items():
            if stats['total_bets'] >= 5 and stats['roi'] > best_roi:
                best_roi = stats['roi']
                best_range = (range_name, stats)
        
        if best_range and best_range[0] in ['sweet_spot', 'ultimate_sweet_spot']:
            learnings['recommendations'].append(
                f"✅ BEST RANGE CONFIRMED: {best_range[1]['range']} odds with {best_roi:.1f}% ROI. Stay focused here!"
            )
        elif best_range:
            learnings['recommendations'].append(
                f"⚠️ WARNING: {best_range[1]['range']} odds performing best, but SWEET SPOT (3-9) should be target. "
                f"Need better horse selection within sweet spot."
            )
    
    # Win vs EW performance
    if 'bet_type' in df.columns:
        win_bets = df[df['bet_type'] == 'WIN']
        ew_bets = df[df['bet_type'] == 'EW']
        
        if len(win_bets) >= 5:
            win_strike_rate = win_bets['won'].mean()
            if win_strike_rate < 0.15:  # Less than 15%
                learnings['recommendations'].append(
                    f"Win bet strike rate low ({win_strike_rate:.1%}). "
                    f"Need more CONFIDENT selections in sweet spot - look for recent WINNERS."
                )
        
        if len(ew_bets) >= 5:
            ew_place_rate = ew_bets['placed'].mean()
            learnings['recommendations'].append(
                f"EW bets: {len(ew_bets)} bets, {ew_place_rate:.1%} place rate"
            )
    
    return learnings


def analyze_prediction_calibration(df: pd.DataFrame) -> Dict[str, Any]:
    """V2.2: Analyze prediction calibration - are we accurate?"""
    
    if len(df) == 0 or 'p_win' not in df.columns:
        return {}
    
    # Define calibration bins
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
    
    df['confidence_bin'] = pd.cut(df['p_win'], bins=bins, labels=labels, include_lowest=True)
    
    calibration_results = {}
    
    for bin_name in labels:
        bin_df = df[df['confidence_bin'] == bin_name]
        
        if len(bin_df) == 0:
            continue
        
        predicted_avg = bin_df['p_win'].mean()
        actual_rate = bin_df['won'].mean()
        calibration_error = actual_rate - predicted_avg
        
        calibration_results[bin_name] = {
            'predicted': round(predicted_avg, 3),
            'actual': round(actual_rate, 3),
            'error': round(calibration_error, 3),
            'sample_size': len(bin_df),
            'verdict': 'OVERCONFIDENT' if calibration_error < -0.1 else 
                      'UNDERCONFIDENT' if calibration_error > 0.1 else 'CALIBRATED'
        }
    
    return calibration_results


def analyze_systematic_failures(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """V2.2: Find patterns in high-confidence losses"""
    
    if len(df) == 0:
        return []
    
    # High confidence losses (40%+ predicted, but lost)
    high_conf_losses = df[(df['p_win'] >= 0.4) & (df['won'] == 0)]
    
    if len(high_conf_losses) == 0:
        return []
    
    recommendations = []
    
    # Pattern 1: Failing trainers
    if 'trainer' in high_conf_losses.columns:
        trainer_failures = high_conf_losses.groupby('trainer').size()
        for trainer, count in trainer_failures.items():
            if count >= 3:  # 3+ failures = pattern
                recommendations.append({
                    'type': 'TRAINER_ISSUE',
                    'pattern': f"Trainer {trainer}: {count} high-conf losses",
                    'action': f"Reduce confidence for {trainer} by 25%"
                })
    
    # Pattern 2: Problematic courses
    if 'course' in high_conf_losses.columns:
        course_failures = high_conf_losses.groupby('course').size()
        for course, count in course_failures.items():
            if count >= 3:
                recommendations.append({
                    'type': 'COURSE_ISSUE',
                    'pattern': f"Course {course}: {count} high-conf losses",
                    'action': f"Review course-specific factors at {course}"
                })
    
    # Pattern 3: Failing in specific odds ranges
    if 'odds' in high_conf_losses.columns:
        high_conf_losses['odds_bin'] = pd.cut(
            high_conf_losses['odds'],
            bins=[0, 4, 6, 9, 20],
            labels=['<4.0', '4-6', '6-9', '9+']
        )
        odds_failures = high_conf_losses.groupby('odds_bin').size()
        for odds_range, count in odds_failures.items():
            if count >= 4:
                recommendations.append({
                    'type': 'ODDS_ISSUE',
                    'pattern': f"Odds {odds_range}: {count} high-conf losses",
                    'action': f"Recalibrate predictions in {odds_range} range"
                })
    
    return recommendations


def analyze_successful_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """V2.2: Find what's working - reinforce successful predictions"""
    
    if len(df) == 0:
        return []
    
    # Successful predictions (30%+ predicted and won)
    successes = df[(df['p_win'] >= 0.3) & (df['won'] == 1)]
    
    if len(successes) == 0:
        return []
    
    reinforcements = []
    
    # Pattern 1: Winning trainers
    if 'trainer' in successes.columns:
        trainer_wins = successes.groupby('trainer').size()
        for trainer, count in trainer_wins.items():
            if count >= 2:  # 2+ wins = pattern
                reinforcements.append({
                    'type': 'TRAINER_SUCCESS',
                    'pattern': f"Trainer {trainer}: {count} wins",
                    'action': f"Maintain/increase confidence for {trainer}"
                })
    
    # Pattern 2: Winning courses
    if 'course' in successes.columns:
        course_wins = successes.groupby('course').size()
        for course, count in course_wins.items():
            if count >= 2:
                reinforcements.append({
                    'type': 'COURSE_SUCCESS',
                    'pattern': f"Course {course}: {count} wins",
                    'action': f"Track patterns at {course} - understanding it well"
                })
    
    # Pattern 3: Sweet spot validation
    if 'odds' in successes.columns:
        sweet_spot_wins = successes[(successes['odds'] >= 3.0) & (successes['odds'] <= 9.0)]
        if len(sweet_spot_wins) >= len(successes) * 0.6:  # 60%+ in sweet spot
            reinforcements.append({
                'type': 'SWEET_SPOT_CONFIRMED',
                'pattern': f"{len(sweet_spot_wins)}/{len(successes)} wins in 3-9 odds",
                'action': "Continue focusing on sweet spot - strategy validated"
            })
    
    return reinforcements


def generate_prompt_guidance(learnings: Dict) -> str:
    """Generate guidance text to add to AI prompts - SWEET SPOT FOCUSED"""
    
    if learnings['sample_size'] < 10:
        return "INSUFFICIENT DATA - Focus on SWEET SPOT (3.0-9.0 odds) with recent WINNERS."
    
    guidance = f"""
=== PERFORMANCE-DRIVEN INSIGHTS ({learnings['sample_size']} bets analyzed) ===

🎯 SWEET SPOT PERFORMANCE (3.0-9.0 odds / 2/1-8/1):
"""
    
    # Sweet spot analysis first - THIS IS PRIORITY
    if learnings.get('sweet_spot_analysis'):
        ss = learnings['sweet_spot_analysis']
        guidance += f"""
Range: {ss['range']}
Bets in range: {ss['total_bets']} ({ss['percentage_of_portfolio']:.1f}% of portfolio)
Win rate: {ss['win_rate']:.1%}
ROI: {ss['roi']:.1f}%
Status: {ss['verdict']}
"""
        
        if 'ultimate' in ss:
            uss = ss['ultimate']
            guidance += f"""
🏆 ULTIMATE SWEET SPOT ({uss['range']}):
  - Bets: {uss['total_bets']} | Wins: {uss['wins']} | Win rate: {uss['win_rate']:.1%} | ROI: {uss['roi']:.1f}%
"""
    
    # Odds range breakdown
    if learnings.get('odds_performance'):
        guidance += "\n📊 ODDS RANGE BREAKDOWN:\n"
        # Sort by ROI descending
        sorted_ranges = sorted(
            learnings['odds_performance'].items(),
            key=lambda x: x[1]['roi'],
            reverse=True
        )
        for range_name, stats in sorted_ranges[:5]:  # Top 5
            symbol = "✅" if stats['roi'] > 0 else "❌"
            guidance += f"{symbol} {stats['range']}: {stats['total_bets']} bets, {stats['win_rate']:.1%} win rate, {stats['roi']:.1f}% ROI\n"
    
    # Winning patterns
    if learnings['winning_patterns']:
        guidance += "\n✅ WORKING STRATEGIES:\n"
        for pattern in learnings['winning_patterns'][:5]:  # Top 5
            guidance += f"  • {pattern['pattern']}: {pattern['win_rate']} actual vs {pattern['expected']} expected (n={pattern['sample_size']})\n"
    
    # Failing patterns
    if learnings['failing_patterns']:
        guidance += "\n❌ UNDERPERFORMING STRATEGIES (AVOID):\n"
        for pattern in learnings['failing_patterns'][:5]:
            guidance += f"  • {pattern['pattern']}: {pattern['win_rate']} actual vs {pattern['expected']} expected (n={pattern['sample_size']})\n"
    
    # Key recommendations
    guidance += "\n🔑 KEY ACTIONS:\n"
    for rec in learnings['recommendations'][:7]:  # Top 7 most important
        guidance += f"  • {rec}\n"
    
    # V2.2: Add calibration insights
    if learnings.get('calibration_analysis'):
        guidance += "\n📊 PREDICTION CALIBRATION:\n"
        for bin_name, stats in learnings['calibration_analysis'].items():
            if stats['sample_size'] >= 3:
                guidance += f"  {bin_name}: Predicted {stats['predicted']:.1%} vs Actual {stats['actual']:.1%} ({stats['verdict']})\n"
    
    # V2.2: Add systematic failures
    if learnings.get('systematic_failures'):
        guidance += "\n❌ SYSTEMATIC FAILURES TO FIX:\n"
        for failure in learnings['systematic_failures'][:3]:
            guidance += f"  • {failure['pattern']} → {failure['action']}\n"
    
    # V2.2: Add success patterns
    if learnings.get('success_patterns'):
        guidance += "\n✅ SUCCESS PATTERNS TO REINFORCE:\n"
        for success in learnings['success_patterns'][:3]:
            guidance += f"  • {success['pattern']} → {success['action']}\n"
    
    guidance += """
⚡ FOCUS MANDATE: 
  - Prioritize 3.0-9.0 odds range (especially 3.5-6.0)
  - Look for RECENT WINNERS (won in last 3 races)
  - In-form trainers/jockeys
  - Value quality over quantity - better 3 great picks than 10 mediocre
"""
    
    return guidance


def main():
    """Generate learning insights from historical data"""
    
    print("="*60)
    print("Generating Learning Insights")
    print("="*60)
    
    # Load and merge all data
    print("\nLoading historical data (last 30 days)...")
    df = merge_all_selections_with_results(days_back=30)
    
    if len(df) == 0:
        print("No historical data found yet")
        
        # Create empty insights file
        empty_insights = {
            'generated_at': datetime.now().isoformat(),
            'sample_size': 0,
            'message': 'Insufficient data - need settled results from at least 5 days',
            'prompt_guidance': 'INSUFFICIENT DATA - Continue with standard analysis approach.'
        }
        
        output_file = Path(__file__).parent / "learning_insights.json"
        with open(output_file, 'w') as f:
            json.dump(empty_insights, f, indent=2)
        
        print(f"Created placeholder: {output_file}")
        return
    
    print(f"Loaded {len(df)} historical bets")
    
    # Analyze performance
    print("\nAnalyzing tag performance...")
    tag_performance = analyze_tag_performance(df)
    print(f"Found {len(tag_performance)} distinct strategies")
    
    # Analyze odds ranges - CRITICAL FOR SWEET SPOT
    print("\nAnalyzing odds range performance...")
    odds_performance = analyze_odds_ranges(df)
    print(f"Analyzed {len(odds_performance)} odds ranges")
    
    # Extract learnings
    print("\nGenerating insights...")
    learnings = extract_pattern_learnings(df, tag_performance, odds_performance)
    
    # Generate prompt guidance
    prompt_guidance = generate_prompt_guidance(learnings)
    learnings['prompt_guidance'] = prompt_guidance
    
    # V2.2: Add prediction calibration analysis
    print("\nAnalyzing prediction calibration...")
    calibration_analysis = analyze_prediction_calibration(df)
    learnings['calibration_analysis'] = calibration_analysis
    
    # V2.2: Analyze systematic failures
    print("Identifying systematic failures...")
    failure_patterns = analyze_systematic_failures(df)
    learnings['systematic_failures'] = failure_patterns
    
    # V2.2: Analyze successful patterns
    print("Validating successful patterns...")
    success_patterns = analyze_successful_patterns(df)
    learnings['success_patterns'] = success_patterns
    
    # Save to file
    output_file = Path(__file__).parent / "learning_insights.json"
    with open(output_file, 'w') as f:
        json.dump(learnings, f, indent=2)
    
    print(f"\n[OK] Saved insights to: {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Sample size: {learnings['sample_size']} bets")
    print(f"Win rate: {learnings['overall_stats']['win_rate']:.1%}")
    print(f"Expected: {learnings['overall_stats']['avg_p_win']:.1%}")
    print(f"\nWorking patterns: {len(learnings['winning_patterns'])}")
    print(f"Failing patterns: {len(learnings['failing_patterns'])}")
    print(f"\nRecommendations: {len(learnings['recommendations'])}")
    
    print("\n" + "="*60)
    print("PROMPT GUIDANCE")
    print("="*60)
    print(prompt_guidance)


if __name__ == "__main__":
    main()
