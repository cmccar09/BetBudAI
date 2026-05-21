"""
Unit tests for API routes
"""

import pytest
import json
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from api.app import app, decimal_to_float


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test /api/health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'timestamp' in data


def test_decimal_to_float():
    """Test Decimal conversion helper"""
    from decimal import Decimal
    
    test_data = {
        'amount': Decimal('100.50'),
        'nested': {
            'value': Decimal('25.75')
        },
        'items': [Decimal('1.1'), Decimal('2.2')]
    }
    
    result = decimal_to_float(test_data)
    
    assert result['amount'] == 100.50
    assert result['nested']['value'] == 25.75
    assert result['items'] == [1.1, 2.2]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
