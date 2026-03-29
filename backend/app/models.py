from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from .database import Base


def generate_uuid():
    """Generate UUID as string"""
    return str(uuid.uuid4())


class ConnectorType(str, enum.Enum):
    """Connector types for EV charging"""
    CCS2 = "CCS2"
    CHADEMO = "CHAdeMO"
    TYPE2 = "Type2"
    TYPE1 = "Type1"


class ConnectorStatus(str, enum.Enum):
    """Status of charging connector"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    FAULTED = "faulted"
    RESERVED = "reserved"


class SessionStatus(str, enum.Enum):
    """Charging session status"""
    RESERVED = "reserved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChargingStation(Base):
    """Charging station model"""
    __tablename__ = "charging_stations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    operator_id = Column(String, default="default-operator")
    base_rate = Column(Float, nullable=False)  # Base price per kWh
    dynamic_multiplier = Column(Float, default=1.0)  # Dynamic pricing multiplier
    is_active = Column(Boolean, default=True)
    blockchain_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    connectors = relationship("Connector", back_populates="station", cascade="all, delete-orphan")
    sessions = relationship("ChargingSession", back_populates="station")


class Connector(Base):
    """Charging connector model"""
    __tablename__ = "connectors"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    station_id = Column(String, ForeignKey("charging_stations.id"), nullable=False)
    connector_type = Column(Enum(ConnectorType), nullable=False)
    power_kw = Column(Float, nullable=False)  # Charging power in kW
    status = Column(Enum(ConnectorStatus), default=ConnectorStatus.AVAILABLE)
    
    # Relationships
    station = relationship("ChargingStation", back_populates="connectors")


class User(Base):
    """User model (basic for Phase 1)"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = relationship("ChargingSession", back_populates="user")


class ChargingSession(Base):
    """Charging session model"""
    __tablename__ = "charging_sessions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    station_id = Column(String, ForeignKey("charging_stations.id"), nullable=False)
    connector_id = Column(String, ForeignKey("connectors.id"), nullable=True)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    energy_delivered_kwh = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    
    status = Column(Enum(SessionStatus), default=SessionStatus.RESERVED)
    blockchain_tx_hash = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    station = relationship("ChargingStation", back_populates="sessions")
