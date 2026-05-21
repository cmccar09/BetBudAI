"""
Continuous Learning System - 2 Week UK/Ireland Race Analysis
Automatically analyzes all races, compares with results, and optimizes selection logic
"""

import json
import boto3
import time
from datetime import datetime, timedelta
from decimal import Decimal
import subprocess
import os

# Initialize DynamoDB
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

class ContinuousLearningSystem:
    def __init__(self):
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=14)
        self.races_analyzed = 0
        self.results_processed = 0
        self.learnings_generated = 0
        
    def run_learning_cycle(self):
        """Main continuous learning loop"""
        
        print(f"\n{'='*80}")
        print(f"CONTINUOUS LEARNING SYSTEM STARTED")
        print(f"Duration: 2 weeks ({self.start_date.date()} to {self.end_date.date()})")
        print(f"{'='*80}\n")
        
        cycle_count = 0
        
        while datetime.now() < self.end_date:
            cycle_count += 1
            print(f"\n{'='*80}")
            print(f"LEARNING CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*80}\n")
            
            try:
                # Step 1: Fetch today's races
                print("📥 Step 1: Fetching race data...")
                self.fetch_race_data()
                
                # Step 2: Analyze ALL horses in ALL UK/Ireland races
                print("\n🔍 Step 2: Analyzing all races...")
                new_analyses = self.analyze_all_races()
                
                # Step 3: Fetch and process results for completed races
                print("\n🏁 Step 3: Checking for completed races...")
                new_results = self.process_completed_races()
                
                # Step 4: Generate learnings from results
                if new_results > 0:
                    print("\n📚 Step 4: Generating learnings...")
                    self.generate_learnings()
                    
                    # Step 4a: Auto-adjust weights based on results
                    print("\n🎯 Step 4a: Auto-adjusting scoring weights...")
                    self.auto_adjust_weights()
                
                # Step 5: Update selection logic if enough data
                if self.results_processed > 0 and self.results_processed % 20 == 0:
                    print("\n⚙️ Step 5: Updating selection logic...")
                    self.optimize_selection_logic()
                
                # Step 6: Generate daily report
                self.generate_daily_report()
                
                # Wait before next cycle (run every 30 minutes)
                wait_time = 1800  # 30 minutes
                print(f"\n⏳ Waiting {wait_time//60} minutes until next cycle...")
                print(f"   Next run: {(datetime.now() + timedelta(seconds=wait_time)).strftime('%H:%M:%S')}")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Learning system stopped by user")
                self.generate_final_report()
                break
            except Exception as e:
                print(f"\n❌ Error in cycle: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(300)  # Wait 5 minutes on error
    
    def fetch_race_data(self):
        """Fetch current race data from Betfair"""
        try:
            result = subprocess.run(
                ['python', 'betfair_odds_fetcher.py'],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print("   ✓ Race data fetched successfully")
                return True
            else:
                print(f"   ✗ Failed to fetch race data: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ✗ Error fetching data: {str(e)}")
            return False
    
    def analyze_all_races(self):
        """Analyze all horses in all UK/Ireland races"""
        try:
            with open('response_horses.json', 'r') as f:
                data = json.load(f)
            
            # Filter UK/Ireland races only
            uk_ireland_venues = [
                'Leopardstown', 'Kempton', 'Cheltenham', 'Ascot', 'Newmarket',
                'York', 'Doncaster', 'Aintree', 'Sandown', 'Haydock',
                'Newcastle', 'Southwell', 'Lingfield', 'Wolverhampton',
                'Fairyhouse', 'Punchestown', 'Navan', 'Gowran', 'Cork',
                'Naas', 'Tipperary', 'Dundalk', 'Market Rasen', 'Ludlow'
            ]
            
            races = [r for r in data.get('races', []) 
                    if any(venue in r.get('venue', '') for venue in uk_ireland_venues)]
            
            if not races:
                print("   ℹ️  No UK/Ireland races found")
                return 0
            
            analyses_saved = 0
            
            for race in races:
                market_id = race.get('marketId', 'unknown')
                venue = race.get('venue', 'Unknown')
                start_time = race.get('start_time', 'Unknown')
                runners = race.get('runners', [])
                
                # Check if already analyzed
                existing = table.scan(
                    FilterExpression='market_id = :mid AND analysis_type = :type',
                    ExpressionAttributeValues={
                        ':mid': market_id,
                        ':type': 'PRE_RACE_COMPLETE'
                    }
                )
                
                if existing.get('Items'):
                    continue  # Already analyzed
                
                print(f"   📊 Analyzing: {venue} {start_time} ({len(runners)} runners)")
                
                for runner in runners:
                    analysis = self.create_horse_analysis(race, runner)
                    if analysis:
                        table.put_item(Item=analysis)
                        analyses_saved += 1
                
                self.races_analyzed += 1
            
            print(f"   ✓ Analyzed {analyses_saved} horses in {len(races)} races")
            return analyses_saved
            
        except Exception as e:
            print(f"   ✗ Error analyzing races: {str(e)}")
            return 0
    
    def create_horse_analysis(self, race, runner):
        """Create detailed pre-race analysis for a horse"""
        try:
            horse_name = runner.get('name', runner.get('runnerName', 'Unknown'))
            selection_id = runner.get('selectionId', 0)
            market_id = race.get('marketId', 'unknown')
            
            return {
                'bet_id': f'ANALYSIS_{market_id}_{selection_id}',
                'bet_date': datetime.now().strftime('%Y-%m-%d'),
                'analysis_type': 'PRE_RACE_COMPLETE',
                'venue': race.get('venue', 'Unknown'),
                'race_time': race.get('start_time', 'Unknown'),
                'market_id': market_id,
                'market_name': race.get('marketName', 'Unknown'),
                'horse': horse_name,
                'selection_id': str(selection_id),
                
                # Odds and probability
                'odds': self.to_decimal(runner.get('odds', 0)),
                'implied_probability': self.to_decimal(runner.get('implied_probability', 0)),
                
                # Form data
                'form': str(runner.get('form', 'Unknown')),
                'trainer': self.get_string_value(runner.get('trainer', 'Unknown')),
                'jockey': self.get_string_value(runner.get('jockey', 'Unknown')),
                'weight': str(runner.get('weight', 'Unknown')),
                'age': str(runner.get('age', 'Unknown')),
                
                # Analysis timestamp
                'analyzed_at': datetime.now().isoformat(),
                'analysis_purpose': 'CONTINUOUS_LEARNING'
            }
        except Exception as e:
            print(f"      ✗ Error creating analysis: {str(e)}")
            return None
    
    def process_completed_races(self):
        """Fetch results for races that have finished"""
        try:
            # Run results fetcher
            result = subprocess.run(
                ['python', 'betfair_results_fetcher_v2.py'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print("   ℹ️  No new results available")
                return 0
            
            # Process new results
            new_results = self.compare_predictions_vs_results()
            
            if new_results > 0:
                print(f"   ✓ Processed {new_results} race results")
                self.results_processed += new_results
            
            return new_results
            
        except Exception as e:
            print(f"   ✗ Error processing results: {str(e)}")
            return 0
    
    def compare_predictions_vs_results(self):
        """Compare our pre-race analysis with actual results"""
        # This will be implemented to read results and compare
        # For now, placeholder
        return 0
    
    def generate_learnings(self):
        """Analyze patterns from race results"""
        print("   🧠 Analyzing winning patterns...")
        
        # Query all results from today
        response = table.scan(
            FilterExpression='learning_type = :type AND bet_date = :date',
            ExpressionAttributeValues={
                ':type': 'RACE_RESULT_ANALYSIS',
                ':date': datetime.now().strftime('%Y-%m-%d')
            }
        )
        
        results = response.get('Items', [])
        
        if len(results) < 5:
            print(f"   ℹ️  Only {len(results)} results - need more data")
            return
        
        # Analyze patterns
        patterns = self.identify_patterns(results)
        
        # Save learning insights
        learning_summary = {
            'bet_id': f'LEARNING_SUMMARY_{datetime.now().strftime("%Y%m%d_%H%M")}',
            'bet_date': datetime.now().strftime('%Y-%m-%d'),
            'learning_type': 'PATTERN_ANALYSIS',
            'total_races': len(results),
            'patterns': patterns,
            'analyzed_at': datetime.now().isoformat()
        }
        
        table.put_item(Item=learning_summary)
        self.learnings_generated += 1
        
        print(f"   ✓ Generated learning from {len(results)} races")
    
    def identify_patterns(self, results):
        """Identify winning patterns from results"""
        patterns = {
            'sweet_spot_wins': 0,
            'favorite_wins': 0,
            'longshot_wins': 0,
            'form_1_wins': 0,
            'total': len(results)
        }
        
        for result in results:
            insights = result.get('insights', [])
            
            if any('SWEET SPOT' in i for i in insights):
                patterns['sweet_spot_wins'] += 1
            if result.get('favorite_won'):
                patterns['favorite_wins'] += 1
            if any('LONGSHOT' in i for i in insights):
                patterns['longshot_wins'] += 1
            if any('LTO winner' in i for i in insights):
                patterns['form_1_wins'] += 1
        
        return patterns
    
    def optimize_selection_logic(self):
        """Update prompt.txt based on learnings"""
        print("   ⚙️  Optimizing selection logic based on data...")
        
        # Query all learnings
        response = table.scan(
            FilterExpression='learning_type = :type',
            ExpressionAttributeValues={
                ':type': 'PATTERN_ANALYSIS'
            }
        )
        
        learnings = response.get('Items', [])
        
        if len(learnings) < 3:
            print(f"   ℹ️  Need more learnings (have {len(learnings)}, need 3+)")
            return
        
        # Aggregate patterns
        total_patterns = {
            'sweet_spot_wins': 0,
            'favorite_wins': 0,
            'longshot_wins': 0,
            'form_1_wins': 0,
            'total': 0
        }
        
        for learning in learnings:
            patterns = learning.get('patterns', {})
            for key in total_patterns:
                if key in patterns:
                    total_patterns[key] += patterns[key]
        
        # Calculate percentages
        if total_patterns['total'] > 0:
            sweet_spot_pct = 100 * total_patterns['sweet_spot_wins'] / total_patterns['total']
            favorite_pct = 100 * total_patterns['favorite_wins'] / total_patterns['total']
            form_1_pct = 100 * total_patterns['form_1_wins'] / total_patterns['total']
            
            print(f"   📊 Pattern Analysis ({total_patterns['total']} races):")
            print(f"      Sweet spot wins: {sweet_spot_pct:.1f}%")
            print(f"      Favorites won: {favorite_pct:.1f}%")
            print(f"      LTO winners: {form_1_pct:.1f}%")
        
        # Save optimization report
        with open('learning_optimization_log.txt', 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Optimization Update: {datetime.now().isoformat()}\n")
            f.write(f"Races analyzed: {total_patterns['total']}\n")
            f.write(f"Sweet spot success: {sweet_spot_pct:.1f}%\n")
            f.write(f"Favorite success: {favorite_pct:.1f}%\n")
            f.write(f"LTO winner success: {form_1_pct:.1f}%\n")
            f.write(f"{'='*80}\n")
    
    def auto_adjust_weights(self):
        """Auto-adjust scoring weights based on recent results"""
        try:
            result = subprocess.run(
                ['python', 'auto_adjust_weights.py'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("   ✓ Weights automatically adjusted based on results")
                # Print key output lines
                for line in result.stdout.split('\n'):
                    if 'optimal_odds' in line or 'recent_win' in line or 'WEIGHTS UPDATED' in line:
                        print(f"      {line.strip()}")
                return True
            else:
                print(f"   ℹ️  Weight adjustment: {result.stdout}")
                return False
        except Exception as e:
            print(f"   ⚠️  Could not adjust weights: {str(e)}")
            return False
    
    def generate_daily_report(self):
        """Generate summary of today's learning"""
        print(f"\n   📊 Daily Summary:")
        print(f"      Races analyzed: {self.races_analyzed}")
        print(f"      Results processed: {self.results_processed}")
        print(f"      Learnings generated: {self.learnings_generated}")
    
    def generate_final_report(self):
        """Generate final 2-week learning report"""
        print(f"\n{'='*80}")
        print(f"FINAL 2-WEEK LEARNING REPORT")
        print(f"{'='*80}\n")
        print(f"Total races analyzed: {self.races_analyzed}")
        print(f"Total results processed: {self.results_processed}")
        print(f"Total learnings: {self.learnings_generated}")
        print(f"\nDuration: {datetime.now() - self.start_date}")
        print(f"\n{'='*80}\n")
    
    def to_decimal(self, value):
        """Convert to Decimal for DynamoDB"""
        try:
            return Decimal(str(value)) if value else Decimal('0')
        except:
            return Decimal('0')
    
    def get_string_value(self, value):
        """Get string value safely"""
        if isinstance(value, str):
            return value
        elif isinstance(value, dict):
            return value.get('name', 'Unknown')
        else:
            return 'Unknown'

def main():
    """Start the continuous learning system"""
    system = ContinuousLearningSystem()
    system.run_learning_cycle()

if __name__ == "__main__":
    main()
