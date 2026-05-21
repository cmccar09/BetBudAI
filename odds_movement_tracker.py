#!/usr/bin/env python3
"""
Odds Movement Tracker
Monitors Betfair odds changes over time to detect:
- Steam moves (sudden odds drops = insider money)
- Drift (odds lengthening = lack of confidence)
- Market confidence signals
- Volume patterns

Stores historical snapshots and calculates movement metrics.
"""

import json
import os
from datetime import datetime, timedelta, timezone
import boto3
from decimal import Decimal

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
odds_table = dynamodb.Table('SureBetOddsHistory')  # New table for odds tracking


class OddsMovementTracker:
    """Track and analyze odds movements for betting signals"""
    
    def __init__(self):
        self.snapshot_dir = os.path.join(os.path.dirname(__file__), 'odds_snapshots')
        os.makedirs(self.snapshot_dir, exist_ok=True)
    
    def capture_snapshot(self, snapshot_data, label='live'):
        """
        Save a snapshot of current odds with timestamp
        Args:
            snapshot_data: JSON data from betfair_delayed_snapshots.py
            label: Identifier for this snapshot run
        """
        timestamp = datetime.now(timezone.utc)
        
        # Save local copy
        filename = timestamp.strftime(f'odds_{label}_%Y%m%d_%H%M%S.json')
        filepath = os.path.join(self.snapshot_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2)
        
        print(f"[OK] Snapshot saved: {filename}")
        
        # Store in DynamoDB for querying
        self._store_in_dynamodb(snapshot_data, timestamp)
        
        return filepath
    
    def _store_in_dynamodb(self, snapshot_data, timestamp):
        """Store odds snapshot in DynamoDB for historical analysis"""
        
        for race in snapshot_data.get('races', []):
            market_id = race.get('market_id')
            course = race.get('course', 'Unknown')
            race_time = race.get('time', '')
            
            for runner in race.get('runners', []):
                selection_id = str(runner.get('selection_id'))
                horse_name = runner.get('name')
                odds = runner.get('odds', 0)
                
                # Create composite key
                pk = f"{market_id}#{selection_id}"
                sk = timestamp.isoformat()
                
                try:
                    odds_table.put_item(
                        Item={
                            'market_selection': pk,
                            'timestamp': sk,
                            'market_id': market_id,
                            'selection_id': selection_id,
                            'horse_name': horse_name,
                            'course': course,
                            'race_time': race_time,
                            'odds': Decimal(str(odds)),
                            'captured_at': timestamp.isoformat()
                        }
                    )
                except Exception as e:
                    print(f"  ⚠️ Error storing odds for {horse_name}: {e}")
    
    def get_odds_movement(self, market_id, selection_id, hours_back=6):
        """
        Get odds movement history for a specific runner
        Returns list of (timestamp, odds) tuples
        """
        pk = f"{market_id}#{selection_id}"
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()
        
        try:
            response = odds_table.query(
                KeyConditionExpression='market_selection = :pk AND #ts >= :cutoff',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':pk': pk,
                    ':cutoff': cutoff_time
                }
            )
            
            items = response.get('Items', [])
            
            # Convert to (timestamp, odds) tuples
            movements = [
                (item['timestamp'], float(item['odds']))
                for item in sorted(items, key=lambda x: x['timestamp'])
            ]
            
            return movements
        
        except Exception as e:
            print(f"Error fetching odds movement: {e}")
            return []
    
    def analyze_movement(self, movements):
        """
        Analyze odds movement patterns
        Returns: {
            'opening_odds': float,
            'current_odds': float,
            'drift_pct': float,  # Positive = drifted out, negative = steamed in
            'movement_type': str,  # 'STEAM', 'DRIFT', 'STABLE'
            'confidence_signal': str  # 'STRONG_BACKING', 'WEAK', 'NEUTRAL'
        }
        """
        if not movements or len(movements) < 2:
            return None
        
        opening_odds = movements[0][1]
        current_odds = movements[-1][1]
        
        # Calculate drift percentage
        # Negative = odds shortened (backed), Positive = odds lengthened (drifted)
        drift_pct = ((current_odds - opening_odds) / opening_odds) * 100
        
        # Classify movement
        if drift_pct < -15:
            movement_type = 'STRONG_STEAM'
            confidence_signal = 'STRONG_BACKING'
        elif drift_pct < -5:
            movement_type = 'STEAM'
            confidence_signal = 'MODERATE_BACKING'
        elif drift_pct > 15:
            movement_type = 'STRONG_DRIFT'
            confidence_signal = 'WEAK'
        elif drift_pct > 5:
            movement_type = 'DRIFT'
            confidence_signal = 'MODERATE_WEAK'
        else:
            movement_type = 'STABLE'
            confidence_signal = 'NEUTRAL'
        
        # Calculate volatility (how much odds fluctuated)
        odds_values = [m[1] for m in movements]
        max_odds = max(odds_values)
        min_odds = min(odds_values)
        volatility = ((max_odds - min_odds) / min_odds) * 100
        
        return {
            'opening_odds': opening_odds,
            'current_odds': current_odds,
            'drift_pct': round(drift_pct, 2),
            'movement_type': movement_type,
            'confidence_signal': confidence_signal,
            'volatility_pct': round(volatility, 2),
            'snapshots_count': len(movements)
        }
    
    def enrich_with_movement_data(self, snapshot_file, output_file=None):
        """
        Enrich a snapshot with odds movement analysis
        Adds historical movement data to each runner
        """
        print("\n=== Enriching Snapshot with Odds Movement Data ===\n")
        
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        enriched_count = 0
        
        for race in snapshot.get('races', []):
            market_id = race.get('market_id')
            
            for runner in race.get('runners', []):
                selection_id = str(runner.get('selection_id'))
                
                # Get odds movement
                movements = self.get_odds_movement(market_id, selection_id, hours_back=6)
                
                if movements:
                    analysis = self.analyze_movement(movements)
                    
                    if analysis:
                        runner['odds_movement'] = analysis
                        enriched_count += 1
                        
                        # Flag significant movements
                        if analysis['movement_type'] in ['STRONG_STEAM', 'STEAM']:
                            print(f"  [STEAM] {runner['name']} - {analysis['drift_pct']}% move")
                        elif analysis['movement_type'] in ['STRONG_DRIFT', 'DRIFT']:
                            print(f"  [DRIFT] {runner['name']} - {analysis['drift_pct']}% move")
        
        # Save enriched snapshot
        if not output_file:
            output_file = snapshot_file.replace('.json', '_with_movement.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2)
        
        print(f"\n[OK] Added movement data to {enriched_count} runners")
        print(f"   Saved to: {output_file}")
        
        return output_file
    
    def get_steam_moves(self, snapshot_file, threshold=-10):
        """
        Identify horses with significant steam (odds shortening)
        threshold: Negative percentage (e.g., -10 = 10% odds drop)
        """
        with open(snapshot_file, 'r', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        steam_horses = []
        
        for race in snapshot.get('races', []):
            for runner in race.get('runners', []):
                movement = runner.get('odds_movement', {})
                
                if movement.get('drift_pct', 0) <= threshold:
                    steam_horses.append({
                        'horse': runner['name'],
                        'course': race['course'],
                        'time': race['time'],
                        'current_odds': movement['current_odds'],
                        'opening_odds': movement['opening_odds'],
                        'drift_pct': movement['drift_pct'],
                        'signal': movement['confidence_signal']
                    })
        
        # Sort by strongest steam
        steam_horses.sort(key=lambda x: x['drift_pct'])
        
        return steam_horses


def setup_dynamodb_table():
    """Create DynamoDB table for odds history (run once)"""
    print("Creating SureBetOddsHistory table...")
    
    try:
        table = dynamodb.create_table(
            TableName='SureBetOddsHistory',
            KeySchema=[
                {'AttributeName': 'market_selection', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'market_selection', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        table.wait_until_exists()
        print("✅ Table created successfully")
    
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("ℹ️  Table already exists")
    except Exception as e:
        print(f"❌ Error creating table: {e}")


def main():
    """Test odds movement tracking"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Track and analyze odds movements')
    parser.add_argument('--snapshot', default='response_live.json', help='Betfair snapshot file')
    parser.add_argument('--setup', action='store_true', help='Create DynamoDB table')
    parser.add_argument('--capture', action='store_true', help='Capture current snapshot')
    parser.add_argument('--analyze', action='store_true', help='Analyze movement and flag steam')
    
    args = parser.parse_args()
    
    tracker = OddsMovementTracker()
    
    if args.setup:
        setup_dynamodb_table()
        return
    
    if not os.path.exists(args.snapshot):
        print(f"❌ Snapshot file not found: {args.snapshot}")
        return
    
    if args.capture:
        with open(args.snapshot, 'r') as f:
            snapshot = json.load(f)
        tracker.capture_snapshot(snapshot)
    
    if args.analyze:
        output = tracker.enrich_with_movement_data(args.snapshot)
        
        # Show steam moves
        print("\n[STEAM MOVES] Strong Backing:")
        steam = tracker.get_steam_moves(output, threshold=-10)
        
        for i, horse in enumerate(steam[:10], 1):
            print(f"{i}. {horse['horse']} @ {horse['course']} ({horse['time']})")
            print(f"   {horse['opening_odds']:.2f} → {horse['current_odds']:.2f} ({horse['drift_pct']:.1f}%)")
            print(f"   Signal: {horse['signal']}")


if __name__ == '__main__':
    main()
