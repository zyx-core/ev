"""
Reservations and Sessions Router
Handles charging reservations and session management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import ChargingStation, ChargingSession, User, Connector, SessionStatus, ConnectorStatus
from ..services.blockchain import get_blockchain_service
from ..schemas import (
    ReservationCreate,
    ReservationResponse,
    SessionStart,
    SessionEnd,
    SessionResponse,
    SessionStatusEnum
)

router = APIRouter(prefix="/reservations", tags=["reservations"])


def get_or_create_user(db: Session, email: str, name: str) -> User:
    """Get existing user or create new one"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("/", response_model=ReservationResponse)
async def create_reservation(
    request: ReservationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new charging reservation
    
    - **station_id**: UUID of the charging station
    - **connector_type**: Optional preferred connector type
    - **scheduled_start**: Optional scheduled start time
    - **user_email**: User email for identification
    """
    # Get station
    station = db.query(ChargingStation).filter(
        ChargingStation.id == request.station_id
    ).first()
    
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    if not station.is_active:
        raise HTTPException(status_code=400, detail="Station is not active")
    
    # Find available connector
    connector = None
    for c in station.connectors:
        if c.status == ConnectorStatus.AVAILABLE:
            if request.connector_type is None or c.connector_type.value == request.connector_type.value:
                connector = c
                break
    
    if not connector:
        raise HTTPException(
            status_code=400, 
            detail="No available connectors at this station"
        )
    
    # Get or create user
    user = get_or_create_user(db, request.user_email, request.user_name)
    
    # Create reservation (as a session with RESERVED status)
    session = ChargingSession(
        user_id=user.id,
        station_id=station.id,
        connector_id=connector.id,
        status=SessionStatus.RESERVED,
        start_time=request.scheduled_start
    )
    
    # Reserve the connector
    connector.status = ConnectorStatus.RESERVED
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Calculate escrow amount (estimate based on 30 min charging)
    escrow_amount = station.base_rate * station.dynamic_multiplier * connector.power_kw * 0.5
    
    return ReservationResponse(
        id=session.id,
        station_id=station.id,
        station_name=station.name,
        user_id=user.id,
        status=SessionStatusEnum(session.status.value),
        scheduled_start=session.start_time,
        created_at=session.created_at,
        blockchain_tx_hash=session.blockchain_tx_hash,
        escrow_amount=round(escrow_amount, 2)
    )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: str,
    db: Session = Depends(get_db)
):
    """Get reservation details"""
    session = db.query(ChargingSession).filter(
        ChargingSession.id == reservation_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    station = db.query(ChargingStation).filter(
        ChargingStation.id == session.station_id
    ).first()
    
    return ReservationResponse(
        id=session.id,
        station_id=session.station_id,
        station_name=station.name if station else "Unknown",
        user_id=session.user_id,
        status=SessionStatusEnum(session.status.value),
        scheduled_start=session.start_time,
        created_at=session.created_at,
        blockchain_tx_hash=session.blockchain_tx_hash,
        escrow_amount=0.0
    )


@router.delete("/{reservation_id}")
async def cancel_reservation(
    reservation_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a reservation"""
    session = db.query(ChargingSession).filter(
        ChargingSession.id == reservation_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if session.status != SessionStatus.RESERVED:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel reservation with status: {session.status.value}"
        )
    
    # Release connector
    if session.connector_id:
        connector = db.query(Connector).filter(
            Connector.id == session.connector_id
        ).first()
        if connector:
            connector.status = ConnectorStatus.AVAILABLE
    
    session.status = SessionStatus.CANCELLED
    db.commit()
    
    return {"message": "Reservation cancelled successfully", "id": reservation_id}


# Session endpoints
session_router = APIRouter(prefix="/sessions", tags=["sessions"])


@session_router.post("/start", response_model=SessionResponse)
async def start_session(
    request: SessionStart,
    db: Session = Depends(get_db)
):
    """Start a charging session from a reservation"""
    session = db.query(ChargingSession).filter(
        ChargingSession.id == request.reservation_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if session.status != SessionStatus.RESERVED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start session with status: {session.status.value}"
        )
    
    # Update connector status
    if session.connector_id:
        connector = db.query(Connector).filter(
            Connector.id == session.connector_id
        ).first()
        if connector:
            connector.status = ConnectorStatus.OCCUPIED
    
    session.status = SessionStatus.ACTIVE
    session.start_time = datetime.utcnow()
    db.commit()
    db.refresh(session)
    
    station = db.query(ChargingStation).filter(
        ChargingStation.id == session.station_id
    ).first()

    # Blockchain integration
    blockchain = get_blockchain_service()
    if blockchain and blockchain.is_connected:
        try:
            # Calculate escrow amount
            rate = station.base_rate * station.dynamic_multiplier
            # Convert to Wei (assuming rate is in ETH/tokens)
            rate_wei = int(rate * 1e18)
            escrow_wei = int(rate * connector.power_kw * 1.0 * 1e18) # 1 hour escrow
            
            # Use station address as operator if available, else a default
            operator_address = station.blockchain_address or blockchain.account
            
            if operator_address:
                tx_hash = blockchain.start_blockchain_session(
                    session_id=session.id,
                    station_id=station.id,
                    operator_address=operator_address,
                    rate_per_kwh_wei=rate_wei,
                    escrow_amount_wei=escrow_wei
                )
                session.blockchain_tx_hash = tx_hash
                db.commit()
        except Exception as e:
            print(f"Blockchain start session error: {e}")
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        station_id=session.station_id,
        station_name=station.name if station else "Unknown",
        connector_id=session.connector_id,
        status=SessionStatusEnum(session.status.value),
        start_time=session.start_time,
        end_time=session.end_time,
        energy_delivered_kwh=session.energy_delivered_kwh,
        cost=session.cost,
        blockchain_tx_hash=session.blockchain_tx_hash,
        created_at=session.created_at
    )


@session_router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    request: SessionEnd,
    db: Session = Depends(get_db)
):
    """End a charging session and calculate cost"""
    session = db.query(ChargingSession).filter(
        ChargingSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot end session with status: {session.status.value}"
        )
    
    station = db.query(ChargingStation).filter(
        ChargingStation.id == session.station_id
    ).first()
    
    # Release connector
    if session.connector_id:
        connector = db.query(Connector).filter(
            Connector.id == session.connector_id
        ).first()
        if connector:
            connector.status = ConnectorStatus.AVAILABLE
    
    # Calculate cost
    effective_rate = station.base_rate * station.dynamic_multiplier if station else 1.0
    cost = request.energy_delivered_kwh * effective_rate
    
    session.status = SessionStatus.COMPLETED
    session.end_time = datetime.utcnow()
    session.energy_delivered_kwh = request.energy_delivered_kwh
    session.cost = round(cost, 2)
    
    # Blockchain integration
    blockchain = get_blockchain_service()
    if blockchain and blockchain.is_connected:
        try:
            energy_wh = int(request.energy_delivered_kwh * 1000)
            tx_hash = blockchain.complete_blockchain_session(
                session_id=session.id,
                energy_wh=energy_wh
            )
            # Update tx hash to the completion hash or log it
            # Ideally we'd have start_tx_hash and end_tx_hash
            # For now, updating to the latest action hash
            session.blockchain_tx_hash = tx_hash
        except Exception as e:
            print(f"Blockchain complete session error: {e}")
    
    db.commit()
    db.refresh(session)
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        station_id=session.station_id,
        station_name=station.name if station else "Unknown",
        connector_id=session.connector_id,
        status=SessionStatusEnum(session.status.value),
        start_time=session.start_time,
        end_time=session.end_time,
        energy_delivered_kwh=session.energy_delivered_kwh,
        cost=session.cost,
        blockchain_tx_hash=session.blockchain_tx_hash,
        created_at=session.created_at
    )


@session_router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get session details"""
    session = db.query(ChargingSession).filter(
        ChargingSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    station = db.query(ChargingStation).filter(
        ChargingStation.id == session.station_id
    ).first()
    
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        station_id=session.station_id,
        station_name=station.name if station else "Unknown",
        connector_id=session.connector_id,
        status=SessionStatusEnum(session.status.value),
        start_time=session.start_time,
        end_time=session.end_time,
        energy_delivered_kwh=session.energy_delivered_kwh,
        cost=session.cost,
        blockchain_tx_hash=session.blockchain_tx_hash,
        created_at=session.created_at
    )


@session_router.post("/{session_id}/slash", tags=["sessions"])
async def slash_no_show(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Slash escrow for a no-show reservation.

    Called by station operators when a user reserved a charger but never
    initiated the charging session within the 15-minute window.
    Sends 20% of escrow to the operator and refunds 80% to the user.
    Triggers the `slashNoShow` function on the TransactionManager smart contract.
    """
    session = db.query(ChargingSession).filter(
        ChargingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != SessionStatus.RESERVED and session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot slash session with status: {session.status.value}"
        )

    # Check that the reservation window has expired (15 minutes)
    if session.start_time:
        elapsed_seconds = (datetime.utcnow() - session.start_time).total_seconds()
        if elapsed_seconds < 900:  # 900 seconds = 15 minutes
            minutes_left = int((900 - elapsed_seconds) / 60) + 1
            raise HTTPException(
                status_code=400,
                detail=f"Reservation window has not expired yet. Wait {minutes_left} more minute(s)."
            )

    # Attempt to call the blockchain contract
    blockchain = get_blockchain_service()
    tx_hash = None
    if blockchain and blockchain.is_connected:
        try:
            tx_hash = blockchain.slash_no_show_session(session_id=session.id)
        except Exception as e:
            print(f"Blockchain slash_no_show error: {e}")

    # Update local DB state regardless (blockchain is the source of truth for funds)
    session.status = SessionStatus.CANCELLED
    session.end_time = datetime.utcnow()

    # Free the connector
    if session.connector_id:
        connector = db.query(Connector).filter(
            Connector.id == session.connector_id
        ).first()
        if connector:
            connector.status = ConnectorStatus.AVAILABLE

    db.commit()

    return {
        "message": "No-show penalty applied. 20% of escrow sent to operator, 80% refunded to user.",
        "session_id": session_id,
        "blockchain_tx_hash": tx_hash
    }

