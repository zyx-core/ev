"""
Test Stations API
Unit tests for charging station endpoints
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
    """Override database dependency for tests"""
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
    """Create test client with fresh database"""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_station(client):
    """Create a sample station in the database"""
    db = TestingSessionLocal()
    
    station = ChargingStation(
        id="test-station-1",
        name="Test Station",
        latitude=40.7128,
        longitude=-74.0060,
        operator_id="test-operator",
        base_rate=0.35,
        dynamic_multiplier=1.0,
        is_active=True
    )
    db.add(station)
    
    connector = Connector(
        id="test-connector-1",
        station_id=station.id,
        connector_type=ConnectorType.CCS2,
        power_kw=150,
        status=ConnectorStatus.AVAILABLE
    )
    db.add(connector)
    
    db.commit()
    station_id = station.id
    db.close()
    
    return station_id


class TestStationsAPI:
    """Test cases for stations endpoints"""
    
    def test_health_check(self, client):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_list_stations_empty(self, client):
        """Test listing stations when database is empty"""
        response = client.get("/api/v1/stations/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_stations(self, client, sample_station):
        """Test listing stations with data"""
        response = client.get("/api/v1/stations/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Station"
        assert data[0]["location"]["latitude"] == 40.7128
    
    def test_get_station_not_found(self, client):
        """Test getting non-existent station"""
        response = client.get("/api/v1/stations/nonexistent-id")
        assert response.status_code == 404
    
    def test_get_station(self, client, sample_station):
        """Test getting specific station"""
        response = client.get(f"/api/v1/stations/{sample_station}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == sample_station
        assert data["name"] == "Test Station"
        assert len(data["connectors"]) == 1
        assert data["connectors"][0]["connector_type"] == "CCS2"
    
    def test_recommend_stations(self, client, sample_station):
        """Test station recommendations"""
        response = client.post(
            "/api/v1/stations/recommend",
            json={
                "user_location": {
                    "latitude": 40.7128,
                    "longitude": -74.0060
                },
                "battery_soc": 50.0,
                "max_distance_km": 50.0,
                "preferences": {
                    "distance_weight": 0.4,
                    "price_weight": 0.3,
                    "speed_weight": 0.2,
                    "availability_weight": 0.1
                }
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "stations" in data
        assert data["total_count"] >= 0
    
    def test_filter_by_connector_type(self, client, sample_station):
        """Test filtering stations by connector type"""
        response = client.get("/api/v1/stations/?connector_type=CCS2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        
        # Filter by non-matching type
        response = client.get("/api/v1/stations/?connector_type=CHAdeMO")
        assert response.status_code == 200
        assert response.json() == []


class TestRecommendationAlgorithm:
    """Test cases for MCDM recommendation algorithm"""
    
    def test_preferences_validation(self, client):
        """Test that preferences must sum to 1.0"""
        response = client.post(
            "/api/v1/stations/recommend",
            json={
                "user_location": {"latitude": 40.0, "longitude": -74.0},
                "preferences": {
                    "distance_weight": 0.5,
                    "price_weight": 0.5,
                    "speed_weight": 0.5,
                    "availability_weight": 0.5
                }
            }
        )
        # Should fail validation
        assert response.status_code == 422
    
    def test_valid_preferences(self, client, sample_station):
        """Test valid preference weights"""
        response = client.post(
            "/api/v1/stations/recommend",
            json={
                "user_location": {"latitude": 40.0, "longitude": -74.0},
                "preferences": {
                    "distance_weight": 0.25,
                    "price_weight": 0.25,
                    "speed_weight": 0.25,
                    "availability_weight": 0.25
                }
            }
        )
        assert response.status_code == 200
