from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConnectorTypeEnum(str, Enum):
    """Connector types"""
    CCS2 = "CCS2"
    CHADEMO = "CHAdeMO"
    TYPE2 = "Type2"
    TYPE1 = "Type1"


class ConnectorStatusEnum(str, Enum):
    """Connector status"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    FAULTED = "faulted"
    RESERVED = "reserved"


class LocationSchema(BaseModel):
    """Location coordinates"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class ConnectorSchema(BaseModel):
    """Connector information"""
    id: str
    connector_type: ConnectorTypeEnum
    power_kw: float
    status: ConnectorStatusEnum
    
    class Config:
        from_attributes = True


class PricingSchema(BaseModel):
    """Pricing information"""
    base_rate: float
    dynamic_multiplier: float
    effective_rate: float


class StationResponse(BaseModel):
    """Charging station response"""
    id: str
    name: str
    location: LocationSchema
    operator_id: str
    pricing: PricingSchema
    connectors: List[ConnectorSchema]
    is_active: bool
    blockchain_address: Optional[str] = None
    
    @classmethod
    def from_db_model(cls, station):
        """Convert database model to response schema"""
        return cls(
            id=station.id,
            name=station.name,
            location=LocationSchema(
                latitude=station.latitude,
                longitude=station.longitude
            ),
            operator_id=station.operator_id,
            pricing=PricingSchema(
                base_rate=station.base_rate,
                dynamic_multiplier=station.dynamic_multiplier,
                effective_rate=station.base_rate * station.dynamic_multiplier
            ),
            connectors=[
                ConnectorSchema.from_orm(c) for c in station.connectors
            ],
            is_active=station.is_active,
            blockchain_address=station.blockchain_address
        )
    
    class Config:
        from_attributes = True


class UserPreferences(BaseModel):
    """User preferences for recommendation"""
    distance_weight: float = Field(default=0.4, ge=0, le=1)
    price_weight: float = Field(default=0.3, ge=0, le=1)
    speed_weight: float = Field(default=0.2, ge=0, le=1)
    availability_weight: float = Field(default=0.1, ge=0, le=1)
    
    @validator('availability_weight')
    def weights_sum_to_one(cls, v, values):
        """Ensure weights sum to 1.0"""
        total = (
            values.get('distance_weight', 0) +
            values.get('price_weight', 0) +
            values.get('speed_weight', 0) +
            v
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f'Weights must sum to 1.0, got {total}')
        return v


class RecommendationRequest(BaseModel):
    """Request for station recommendations"""
    user_location: LocationSchema
    battery_soc: Optional[float] = Field(default=50.0, ge=0, le=100)
    connector_type: Optional[ConnectorTypeEnum] = None
    max_distance_km: Optional[float] = Field(default=50.0, gt=0)
    preferences: UserPreferences = UserPreferences()


class RankedStation(BaseModel):
    """Station with ranking score"""
    station: StationResponse
    score: float
    distance_km: float
    estimated_wait_minutes: int = 0
    
    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    """Response with ranked stations"""
    stations: List[RankedStation]
    total_count: int
    user_location: LocationSchema


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime


class SessionStatusEnum(str, Enum):
    """Session status"""
    RESERVED = "reserved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReservationCreate(BaseModel):
    """Request to create a reservation"""
    station_id: str
    connector_type: Optional[ConnectorTypeEnum] = None
    scheduled_start: Optional[datetime] = None
    user_email: str = Field(..., description="User email for identification")
    user_name: str = Field(default="Guest", description="User name")


class ReservationResponse(BaseModel):
    """Reservation response"""
    id: str
    station_id: str
    station_name: str
    user_id: str
    status: SessionStatusEnum
    scheduled_start: Optional[datetime] = None
    created_at: datetime
    blockchain_tx_hash: Optional[str] = None
    escrow_amount: float = 0.0
    
    class Config:
        from_attributes = True


class SessionStart(BaseModel):
    """Request to start a charging session"""
    reservation_id: str
    connector_id: Optional[str] = None


class SessionEnd(BaseModel):
    """Request to end a charging session"""
    energy_delivered_kwh: float = Field(..., ge=0)


class SessionResponse(BaseModel):
    """Charging session response"""
    id: str
    user_id: str
    station_id: str
    station_name: str
    connector_id: Optional[str] = None
    status: SessionStatusEnum
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    energy_delivered_kwh: float
    cost: float
    blockchain_tx_hash: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SimulationConfig(BaseModel):
    """Configuration for running a simulation"""
    evs: int = Field(default=100, ge=1)
    stations: int = Field(default=10, ge=1)
    cpos: int = Field(default=3, ge=1)
    steps: int = Field(default=100, ge=1)


class SimulationResult(BaseModel):
    """Result of a simulation run"""
    id: str
    status: str
    config: SimulationConfig
    created_at: datetime
    results: Optional[dict] = None
    error: Optional[str] = None

