"""
Test Dynamic Pricing API
Unit tests for MARL-based dynamic pricing endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import ChargingStation, Connector, ConnectorType, ConnectorStatus


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def client(db_override):
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_stations(client):
    """Create sample stations for pricing tests"""
    db = TestingSessionLocal()
    
    for i in range(3):
        station = ChargingStation(
            id=f"pricing-station-{i}",
            name=f"Pricing Station {i}",
            latitude=40.7 + i * 0.01,
            longitude=-74.0 + i * 0.01,
            operator_id="test-operator",
            base_rate=0.35 + i * 0.05,
            dynamic_multiplier=1.0,
            is_active=True
        )
        db.add(station)
        
        connector = Connector(
            id=f"pricing-conn-{i}",
            station_id=station.id,
            connector_type=ConnectorType.CCS2,
            power_kw=150,
            status=ConnectorStatus.AVAILABLE
        )
        db.add(connector)
    
    db.commit()
    db.close()


class TestDynamicPricingAPI:
    """Test cases for dynamic pricing endpoints"""
    
    def test_get_dynamic_pricing(self, client, sample_stations):
        """Test getting dynamic pricing for all stations"""
        response = client.post(
            "/api/v1/pricing/dynamic",
            json={
                "current_occupancy": 0.6,
                "grid_load": 0.5,
                "hour_of_day": 14,
                "day_of_week": 2
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "grid_status" in data
        assert "pricing_strategy" in data
        assert "stations" in data
        assert len(data["stations"]) == 3
    
    def test_peak_hour_pricing(self, client, sample_stations):
        """Test that peak hours have higher multipliers"""
        # Peak hour request
        peak_response = client.post(
            "/api/v1/pricing/dynamic",
            json={
                "current_occupancy": 0.5,
                "grid_load": 0.8,  # High grid load during peak
                "hour_of_day": 18,  # Peak hour
                "day_of_week": 1
            }
        )
        
        # Off-peak request
        offpeak_response = client.post(
            "/api/v1/pricing/dynamic",
            json={
                "current_occupancy": 0.5,
                "grid_load": 0.3,  # Low grid load off-peak
                "hour_of_day": 3,  # Off-peak
                "day_of_week": 1
            }
        )
        
        assert peak_response.status_code == 200
        assert offpeak_response.status_code == 200
        
        peak_data = peak_response.json()
        offpeak_data = offpeak_response.json()
        
        # Peak multiplier should be higher
        assert peak_data["avg_multiplier"] > offpeak_data["avg_multiplier"]
    
    def test_current_pricing_strategy(self, client):
        """Test getting current pricing strategy"""
        response = client.get("/api/v1/pricing/strategy/current")
        assert response.status_code == 200
        
        data = response.json()
        assert "pricing_strategy" in data
        assert "grid_status" in data
        assert "peak_hours" in data
        assert "is_peak" in data
    
    def test_station_specific_pricing(self, client, sample_stations):
        """Test getting pricing for specific station"""
        response = client.get("/api/v1/pricing/station/pricing-station-0")
        assert response.status_code == 200
        
        data = response.json()
        assert data["station_id"] == "pricing-station-0"
        assert "base_rate" in data
        assert "current_multiplier" in data
        assert "effective_rate" in data


class TestDashboardAPI:
    """Test cases for dashboard endpoints"""
    
    def test_dashboard_overview(self, client, sample_stations):
        """Test dashboard overview endpoint"""
        response = client.get("/api/v1/dashboard/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "stations" in data
        assert "connectors" in data
        assert "sessions_24h" in data
        assert "revenue_24h" in data
    
    def test_stations_status(self, client, sample_stations):
        """Test stations status endpoint"""
        response = client.get("/api/v1/dashboard/stations/status")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 3
        assert "utilization" in data[0]
    
    def test_grid_load(self, client):
        """Test grid load simulation endpoint"""
        response = client.get("/api/v1/dashboard/grid/load")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_load" in data
        assert "status" in data
        assert "forecast" in data
        assert len(data["forecast"]) == 24
    
    def test_pricing_overview(self, client, sample_stations):
        """Test pricing overview endpoint"""
        response = client.get("/api/v1/dashboard/pricing/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "avg_effective_rate" in data
        assert data["stations_count"] == 3
    
    def test_analytics_trends(self, client, sample_stations):
        """Test analytics trends endpoint"""
        response = client.get("/api/v1/dashboard/analytics/trends?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert "daily_trends" in data
        assert len(data["daily_trends"]) == 7
