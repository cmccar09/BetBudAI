"""
Signal Weights Configuration
============================
Centralized dynamic weight management with hot-reload support.
Loaded from DynamoDB (auto-updated by learning system) with fallback to defaults.
"""

from typing import Dict
import boto3
from datetime import datetime
import json

DEFAULT_WEIGHTS = {
    # Core form signals - REBALANCED 2026-05-20 (Expert Tipster Review)
    'recent_win': 14,  # ↓ REDUCED 16→14 (last win alone doesn't predict next)
    'total_wins': 8,
    'consistency': 12,  # ↑ INCREASED 6→12 (reliable form beats one-off brilliance)
    'form_exact_course_win': 20,
    'form_exact_distance_win': 20,
    'form_close_2nd': 14,
    'form_velocity_bonus': 18,  # ↑ INCREASED 10→18 (improving form > static recent win)
    'form_velocity_penalty': 10,  # ↑ INCREASED 6→10

    # Course & distance
    'course_bonus': 12,
    'distance_suitability': 16,
    'cd_bonus': 16,
    'graded_race_cd_bonus': 8,

    # Market signals - REDUCED (less trust in market)
    'sweet_spot': 8,  # ↓ REDUCED 10→8
    'optimal_odds': 8,
    'favorite_correction': 5,  # ↓ REDUCED 8→5 (market wrong 60% of time in our range)
    'market_steam_bonus': 10,
    'market_drift_penalty': 6,
    'market_divergence_penalty': 18,
    'score_gap_illusion_penalty': 12,

    # Trainer & jockey - STRENGTHEN COMBOS
    'trainer_reputation': 16,
    'trainer_tier2': 8,
    'trainer_tier3': 4,
    'trainer_combo_bonus': 8,
    'trainer_form_bonus': 8,
    'trainer_course_bonus': 12,  # ↑ INCREASED 8→12
    'same_trainer_rival_penalty': 10,
    'jockey_quality': 12,
    'jockey_tier2': 6,
    'jockey_course_bonus': 15,  # ↑ INCREASED 8→15 (elite combos like Dettori/Ascot)
    'meeting_focus_trainer': 10,
    'meeting_focus_jockey': 10,
    'meeting_focus_combo': 10,

    # Going & conditions
    'going_suitability': 16,
    'heavy_going_penalty': 12,
    'track_pattern_bonus': 8,

    # Race characteristics - REDUCE PENALTIES
    'weight_penalty': 10,
    'age_bonus': 7,
    'novice_race_penalty': 8,  # ↓ REDUCED 15→8 (over-penalizing inexperienced horses)
    'large_field_penalty': 10,
    'aw_evening_penalty': 12,
    'aw_low_class_penalty': 50,
    'irish_handicap_penalty': 10,

    # Ratings & class - STRENGTHEN (class drops win!)
    'official_rating_bonus': 8,
    'class_drop_bonus': 24,  # ↑ INCREASED 12→24 (class droppers win at 40%+ strike)
    'class_drop_rebound_bonus': 20,  # ↑ INCREASED 10→20 (dropping + bounce = near certainty)

    # Form patterns - STRENGTHEN
    'bounce_back_bonus': 14,  # ↑ INCREASED 8→14
    'pu_winner_bounce': 6,
    'short_form_improvement': 8,
    'unexposed_bonus': 12,

    # Timeform
    'timeform_5star_bonus': 12,
    'timeform_4star_bonus': 8,
    'timeform_3star_bonus': 4,
    'timeform_lowstar_penalty': 6,

    # Risk controls
    'recent_non_completion_penalty': 10,
    'current_form_edge_bonus': 8,
    'potential_hype_penalty': 10,
    'unknown_trainer_penalty': 8,
    'new_trainer_debut': 5,

    # Database knowledge
    'database_history': 15,
}

_weights_cache = {
    'weights': None,
    'timestamp': None,
    'ttl_seconds': 300,  # 5 minute cache
}


class WeightManager:
    """Centralized weight loading with caching and fallback."""
    
    def __init__(self, dynamodb_table_name: str = 'SureBetBets', region: str = 'eu-west-1'):
        self.table_name = dynamodb_table_name
        self.region = region
        self.dynamodb = None
        self.table = None
    
    def _get_dynamodb_table(self):
        """Lazy-load DynamoDB table."""
        if self.table is None:
            self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
            self.table = self.dynamodb.Table(self.table_name)
        return self.table
    
    def get_weights(self) -> Dict[str, float]:
        """Get current weights from cache, DynamoDB, or defaults.
        
        Returns:
            Dictionary of weight_name -> weight_value
        """
        global _weights_cache
        
        # Check cache validity
        if _weights_cache['weights'] and _weights_cache['timestamp']:
            age = (datetime.now() - _weights_cache['timestamp']).total_seconds()
            if age < _weights_cache['ttl_seconds']:
                return _weights_cache['weights']
        
        # Try DynamoDB
        try:
            table = self._get_dynamodb_table()
            response = table.get_item(
                Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'}
            )
            
            if 'Item' in response:
                weights = response['Item'].get('weights', {})
                # Convert Decimal to float
                weights_dict = {k: float(v) for k, v in weights.items()}
                _weights_cache['weights'] = weights_dict
                _weights_cache['timestamp'] = datetime.now()
                return weights_dict
        except Exception as e:
            print(f"[WeightManager] Error loading from DynamoDB: {e}")
        
        # Fallback to defaults
        _weights_cache['weights'] = DEFAULT_WEIGHTS.copy()
        _weights_cache['timestamp'] = datetime.now()
        return _weights_cache['weights']
    
    def save_weights(self, weights: Dict[str, float]) -> bool:
        """Save weights to DynamoDB for learning system."""
        try:
            table = self._get_dynamodb_table()
            from decimal import Decimal
            
            weights_decimal = {k: Decimal(str(v)) for k, v in weights.items()}
            
            table.put_item(
                Item={
                    'bet_id': 'SYSTEM_WEIGHTS',
                    'bet_date': 'CONFIG',
                    'weights': weights_decimal,
                    'updated_at': datetime.now().isoformat(),
                    'version': 1,
                }
            )
            
            # Clear cache to force reload
            _weights_cache['weights'] = None
            _weights_cache['timestamp'] = None
            return True
        except Exception as e:
            print(f"[WeightManager] Error saving weights: {e}")
            return False


# Global instance
_weight_manager = WeightManager()


def get_current_weights() -> Dict[str, float]:
    """Get current weights (convenience function)."""
    return _weight_manager.get_weights()
