import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models import ChargingStation, Connector, ConnectorType, ConnectorStatus
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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

@pytest.fixture
def client(db_override):
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Drop tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_blockchain_service():
    with patch("app.routers.reservations.get_blockchain_service") as mock_get_service:
        mock_service = MagicMock()
        mock_service.is_connected = True
        mock_service.account = "0xTestAccount"
        mock_service.start_blockchain_session.return_value = "0xStartTxHash"
        mock_service.complete_blockchain_session.return_value = "0xEndTxHash"
        
        mock_get_service.return_value = mock_service
        yield mock_service

def test_start_session_blockchain_call(client, mock_blockchain_service):
    # Seed DB
    db = TestingSessionLocal()
    station = ChargingStation(
        id="station-1",
        name="Test Station",
        latitude=0.0,
        longitude=0.0,
        base_rate=0.5,
        dynamic_multiplier=1.2,
        is_active=True,
        blockchain_address="0xStationAddress"
    )
    connector = Connector(
        id="conn-1",
        station_id="station-1",
        connector_type=ConnectorType.CCS2,
        power_kw=50.0,
        status=ConnectorStatus.AVAILABLE
    )
    db.add(station)
    db.add(connector)
    db.commit()
    
    # Create reservation via API
    res_response = client.post("/api/v1/reservations/", json={
        "station_id": "station-1",
        "connector_type": "CCS2",
        "user_email": "test@example.com",
        "user_name": "Test User"
    })
    assert res_response.status_code == 200
    reservation_id = res_response.json()["id"]
    
    # Start Session
    start_response = client.post("/api/v1/sessions/start", json={
        "reservation_id": reservation_id
    })
    assert start_response.status_code == 200
    data = start_response.json()
    assert data["status"] == "active"
    assert data["blockchain_tx_hash"] == "0xStartTxHash"
    
    # Verify mock call
    mock_blockchain_service.start_blockchain_session.assert_called_once()
    call_args = mock_blockchain_service.start_blockchain_session.call_args[1]
    assert call_args["station_id"] == "station-1"
    # rate_wei = 0.5 * 1.2 * 1e18 = 0.6 * 1e18
    assert call_args["rate_per_kwh_wei"] == int(0.6 * 1e18)
    # escrow = 0.6 * 50.0 * 1.0 * 1e18 = 30.0 * 1e18
    assert call_args["escrow_amount_wei"] == int(30.0 * 1e18)

def test_end_session_blockchain_call(client, mock_blockchain_service):
    # Setup - reusing station logic effectively by continuing flow
    # Since fixtures reset DB, we need to redo seed
    db = TestingSessionLocal()
    station = ChargingStation(
        id="station-1",
        name="Test Station",
        latitude=0.0,
        longitude=0.0,
        base_rate=0.5,
        dynamic_multiplier=1.0,
        is_active=True,
        blockchain_address="0xStationAddress"
    )
    connector = Connector(
        id="conn-1",
        station_id="station-1",
        connector_type=ConnectorType.CCS2,
        power_kw=50.0,
        status=ConnectorStatus.AVAILABLE
    )
    db.add(station)
    db.add(connector)
    db.commit()
    
    # Create reservation
    res_response = client.post("/api/v1/reservations/", json={
        "station_id": "station-1",
        "connector_type": "CCS2",
        "user_email": "test@example.com",
        "user_name": "Test User"
    })
    reservation_id = res_response.json()["id"]
    
    # Start Session
    client.post("/api/v1/sessions/start", json={"reservation_id": reservation_id})
    
    # End Session
    end_response = client.post(f"/api/v1/sessions/{reservation_id}/end", json={
        "energy_delivered_kwh": 10.5
    })
    
    assert end_response.status_code == 200
    data = end_response.json()
    assert data["status"] == "completed"
    assert data["blockchain_tx_hash"] == "0xEndTxHash"
    
    # Verify mock call
    mock_blockchain_service.complete_blockchain_session.assert_called_once()
    call_args = mock_blockchain_service.complete_blockchain_session.call_args[1]
    assert call_args["session_id"] == reservation_id
    assert call_args["energy_wh"] == 10500 # 10.5 * 1000
