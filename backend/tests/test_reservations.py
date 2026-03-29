"""
Test Reservations API
Unit tests for reservation and session endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import (
    ChargingStation, 
    Connector, 
    User,
    ChargingSession,
    ConnectorType, 
    ConnectorStatus,
    SessionStatus
)


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
def station_with_connector(client):
    """Create a station with available connector"""
    db = TestingSessionLocal()
    
    station = ChargingStation(
        id="station-001",
        name="Downtown Charger",
        latitude=40.7128,
        longitude=-74.0060,
        operator_id="operator-001",
        base_rate=0.40,
        dynamic_multiplier=1.0,
        is_active=True
    )
    db.add(station)
    
    connector = Connector(
        id="connector-001",
        station_id=station.id,
        connector_type=ConnectorType.CCS2,
        power_kw=150,
        status=ConnectorStatus.AVAILABLE
    )
    db.add(connector)
    
    db.commit()
    
    # Store IDs before closing session
    result = {"station_id": station.id, "connector_id": connector.id}
    db.close()
    
    return result


class TestReservationsAPI:
    """Test cases for reservations endpoints"""
    
    def test_create_reservation(self, client, station_with_connector):
        """Test creating a new reservation"""
        response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "test@example.com",
                "user_name": "Test User"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["station_id"] == station_with_connector["station_id"]
        assert data["status"] == "reserved"
        assert "id" in data
        assert "escrow_amount" in data
    
    def test_create_reservation_invalid_station(self, client):
        """Test creating reservation for non-existent station"""
        response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": "non-existent-station",
                "user_email": "test@example.com"
            }
        )
        assert response.status_code == 404
        assert "Station not found" in response.json()["detail"]
    
    def test_get_reservation(self, client, station_with_connector):
        """Test getting reservation details"""
        # First create a reservation
        create_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "test@example.com"
            }
        )
        reservation_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(f"/api/v1/reservations/{reservation_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == reservation_id
        assert data["status"] == "reserved"
    
    def test_cancel_reservation(self, client, station_with_connector):
        """Test canceling a reservation"""
        # Create reservation
        create_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "cancel@example.com"
            }
        )
        reservation_id = create_response.json()["id"]
        
        # Cancel it
        response = client.delete(f"/api/v1/reservations/{reservation_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Reservation cancelled successfully"
    
    def test_no_available_connectors(self, client, station_with_connector):
        """Test reservation when no connectors available"""
        # Create first reservation (takes the only connector)
        client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "first@example.com"
            }
        )
        
        # Try to create second reservation
        response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "second@example.com"
            }
        )
        assert response.status_code == 400
        assert "No available connectors" in response.json()["detail"]


class TestSessionsAPI:
    """Test cases for session management endpoints"""
    
    def test_start_session(self, client, station_with_connector):
        """Test starting a charging session"""
        # Create reservation first
        create_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "session@example.com"
            }
        )
        reservation_id = create_response.json()["id"]
        
        # Start session
        response = client.post(
            "/api/v1/sessions/start",
            json={"reservation_id": reservation_id}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "active"
        assert data["start_time"] is not None
    
    def test_end_session(self, client, station_with_connector):
        """Test ending a charging session"""
        # Create and start session
        create_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "complete@example.com"
            }
        )
        reservation_id = create_response.json()["id"]
        
        client.post(
            "/api/v1/sessions/start",
            json={"reservation_id": reservation_id}
        )
        
        # End session
        response = client.post(
            f"/api/v1/sessions/{reservation_id}/end",
            json={"energy_delivered_kwh": 25.5}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "completed"
        assert data["energy_delivered_kwh"] == 25.5
        assert data["cost"] > 0
    
    def test_get_session(self, client, station_with_connector):
        """Test getting session details"""
        # Create and start session
        create_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "view@example.com"
            }
        )
        session_id = create_response.json()["id"]
        
        # Get session
        response = client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["id"] == session_id
    
    def test_cannot_end_inactive_session(self, client, station_with_connector):
        """Test that non-active sessions cannot be ended"""
        # Create reservation but don't start it
        create_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "inactive@example.com"
            }
        )
        reservation_id = create_response.json()["id"]
        
        # Try to end without starting
        response = client.post(
            f"/api/v1/sessions/{reservation_id}/end",
            json={"energy_delivered_kwh": 10.0}
        )
        assert response.status_code == 400


class TestFullChargingFlow:
    """End-to-end test for complete charging flow"""
    
    def test_complete_charging_flow(self, client, station_with_connector):
        """Test full flow: reserve -> start -> charge -> end"""
        # Step 1: Create reservation
        reserve_response = client.post(
            "/api/v1/reservations/",
            json={
                "station_id": station_with_connector["station_id"],
                "user_email": "flow@example.com",
                "user_name": "Flow Test User"
            }
        )
        assert reserve_response.status_code == 200
        reservation = reserve_response.json()
        assert reservation["status"] == "reserved"
        
        session_id = reservation["id"]
        
        # Step 2: Start session
        start_response = client.post(
            "/api/v1/sessions/start",
            json={"reservation_id": session_id}
        )
        assert start_response.status_code == 200
        session = start_response.json()
        assert session["status"] == "active"
        
        # Step 3: End session
        end_response = client.post(
            f"/api/v1/sessions/{session_id}/end",
            json={"energy_delivered_kwh": 45.0}
        )
        assert end_response.status_code == 200
        final_session = end_response.json()
        
        assert final_session["status"] == "completed"
        assert final_session["energy_delivered_kwh"] == 45.0
        assert final_session["cost"] == 45.0 * 0.40  # base_rate * energy
