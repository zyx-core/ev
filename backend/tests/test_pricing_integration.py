
import sys
import os
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.routers.pricing import get_dynamic_pricing, DynamicPricingRequest, get_pricing_engine

def test_marl_pricing_integration():
    # Setup
    engine = get_pricing_engine()
    
    # Check if policy is loaded
    # We can't easily check internal state without peering, but we can check if weights are not all zeros/random if we knew orig state
    # But mainly we want to ensure calculate_multiplier runs without error
    
    req = DynamicPricingRequest(
        station_id="test-station",
        current_occupancy=0.5,
        grid_load=0.6,
        hour_of_day=12,
        day_of_week=0
    )
    
    # Mock DB
    mock_db = MagicMock()
    mock_station = MagicMock()
    mock_station.id = "test-station"
    mock_station.name = "Test Station"
    mock_station.base_rate = 0.5
    mock_station.dynamic_multiplier = 1.0
    mock_station.is_active = True
    
    # Setup chain
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_station]
    
    # Run
    import asyncio
    response = asyncio.run(get_dynamic_pricing(req, mock_db))
    
    print(f"\nResponse: {response}")
    
    assert response.avg_multiplier > 0
    assert len(response.stations) == 1
    assert "MARL" in response.stations[0].reasoning or "Standard" in response.stations[0].reasoning
    
if __name__ == "__main__":
    test_marl_pricing_integration()
