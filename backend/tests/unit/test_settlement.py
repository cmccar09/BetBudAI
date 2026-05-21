"""
Unit tests for settlement calculator
"""

import pytest
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from core.settlement.calculator import calculate_pnl, reconcile_result


def test_calculate_pnl_win():
    """Test P&L calculation for winning pick"""
    pick = {
        'horse_name': 'Frankie',
        'stake': 10,
        'odds': 3.5,
        'bet_type': 'win'
    }
    
    outcome, profit = calculate_pnl(pick, 'Frankie', [], {})
    
    assert outcome == 'WIN'
    assert profit == Decimal('35')  # 10 * 3.5


def test_calculate_pnl_place():
    """Test P&L calculation for place bet"""
    pick = {
        'horse_name': 'Frankie',
        'stake': 10,
        'odds': 4.0,
        'bet_type': 'place'
    }
    
    outcome, profit = calculate_pnl(pick, 'Other', ['Frankie', 'Third'], {})
    
    assert outcome == 'PLACE'
    assert float(profit) == 10.0  # 10 * (4.0/4)


def test_calculate_pnl_loss():
    """Test P&L calculation for losing pick"""
    pick = {
        'horse_name': 'Frankie',
        'stake': 10,
        'odds': 3.5,
        'bet_type': 'win'
    }
    
    outcome, profit = calculate_pnl(pick, 'Winner', [], {})
    
    assert outcome == 'LOSS'
    assert profit == Decimal('-10')


def test_reconcile_result():
    """Test result reconciliation"""
    result = reconcile_result(
        'pick_123',
        {'winner': 'Frankie', 'placed': ['Second', 'Third']},
        existing_outcome='WIN'
    )
    
    assert result['pick_id'] == 'pick_123'
    assert result['verified'] is True
    assert result['confidence'] == 0.95


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
