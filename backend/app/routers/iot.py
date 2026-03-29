from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..database import get_db
from ..models import ChargingStation, Connector, ConnectorStatus

router = APIRouter(prefix="/iot", tags=["iot-simulation"])

class ConnectorUpdate(BaseModel):
    connector_id: str
    status: ConnectorStatus

class StationUpdate(BaseModel):
    station_id: str
    is_active: bool
    dynamic_multiplier: float

class GridUpdate(BaseModel):
    load_factor: float

# In-memory grid state for simulation
grid_state = {"load_factor": 0.5}

@router.post("/connector/status")
async def update_connector_status(update: ConnectorUpdate, db: Session = Depends(get_db)):
    connector = db.query(Connector).filter(Connector.id == update.connector_id).first()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    connector.status = update.status
    db.commit()
    return {"status": "success", "connector_id": update.connector_id, "new_status": update.status}

@router.post("/station/status")
async def update_station_status(update: StationUpdate, db: Session = Depends(get_db)):
    station = db.query(ChargingStation).filter(ChargingStation.id == update.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    station.is_active = update.is_active
    station.dynamic_multiplier = update.dynamic_multiplier
    db.commit()
    return {"status": "success", "station_id": update.station_id}

from datetime import datetime
from ..routers.pricing import get_pricing_engine

@router.post("/grid/load")
async def update_grid_load(update: GridUpdate, db: Session = Depends(get_db)):
    # 1. Update In-Memory State
    grid_state["load_factor"] = update.load_factor
    
    # 2. Trigger MARL Engine Recalculation
    engine = get_pricing_engine()
    stations = db.query(ChargingStation).filter(ChargingStation.is_active == True).all()
    
    updated_count = 0
    
    # Simulate current time context
    now = datetime.now()
    hour = now.hour
    day = now.weekday()
    
    for station in stations:
        # Get simulated occupancy (random variance for demo)
        occupancy = 0.5  # Default
        
        # Calculate new multiplier based on new grid load
        multiplier, _ = engine.calculate_multiplier(
            occupancy=occupancy,
            grid_load=update.load_factor,
            hour=hour,
            day=day
        )
        
        # Update station in DB
        station.dynamic_multiplier = multiplier
        updated_count += 1
        
    db.commit()
    
    return {
        "status": "success", 
        "new_load": update.load_factor,
        "stations_updated": updated_count,
        "message": f"Grid load set to {update.load_factor*100}%. Prices updated for {updated_count} stations."
    }

@router.get("/grid/load")
async def get_grid_load():
    return grid_state

# OCPP 2.0.1 request models
class BootNotificationRequest(BaseModel):
    charge_point_model: str
    charge_point_vendor: str
    firmware_version: str | None = None

class StatusNotificationRequest(BaseModel):
    connector_id: str
    error_code: str
    status: str
    timestamp: str

# OCPP endpoints
@router.post("/ocpp/boot_notification")
async def boot_notification(request: BootNotificationRequest):
    # Process boot notification (e.g., register charge point)
    return {"status": "Accepted", "message": "Boot notification received"}

@router.post("/ocpp/status_notification")
async def status_notification(request: StatusNotificationRequest):
    # Process status update (e.g., update connector status)
    return {"status": "Accepted", "message": "Status notification received"}

# OCPP MeterValues request model
class MeterValuesRequest(BaseModel):
    connector_id: str
    transaction_id: str
    meter_value: float
    timestamp: str

@router.post("/ocpp/meter_values")
async def meter_values(request: MeterValuesRequest):
    # Process meter values (e.g., store or forward to backend)
    return {"status": "Accepted", "message": "Meter values received"}

# OCPP TransactionEvent request model
class TransactionEventRequest(BaseModel):
    event_type: str  # Started, Updated, Ended
    transaction_id: str
    connector_id: str
    id_tag: str | None = None
    timestamp: str

@router.post("/ocpp/transaction_event")
async def transaction_event(request: TransactionEventRequest):
    # Process transaction event (e.g., start/end charging session)
    return {"status": "Accepted", "message": f"Transaction event {request.event_type} received"}
