from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import ChargingStation, ConnectorType
from ..schemas import (
    StationResponse,
    RecommendationRequest,
    RecommendationResponse,
    RankedStation,
    LocationSchema
)
from ..services.mcdm import MCDMRecommender

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/", response_model=List[StationResponse])
async def list_stations(
    lat: Optional[float] = Query(None, description="User latitude for filtering"),
    lon: Optional[float] = Query(None, description="User longitude for filtering"),
    radius_km: Optional[float] = Query(None, ge=0, description="Search radius in km"),
    connector_type: Optional[str] = Query(None, description="Filter by connector type"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    List all charging stations with optional filters
    
    - **lat, lon, radius_km**: Filter stations within radius of location
    - **connector_type**: Filter by connector type (CCS2, CHAdeMO, Type2, Type1)
    - **is_active**: Filter by active status
    """
    query = db.query(ChargingStation).filter(ChargingStation.is_active == is_active)
    
    stations = query.all()
    
    # Filter by connector type if specified
    if connector_type:
        stations = [
            s for s in stations
            if any(c.connector_type.value == connector_type for c in s.connectors)
        ]
    
    # Filter by radius if location provided
    if lat is not None and lon is not None and radius_km is not None:
        from ..services.mcdm import haversine_distance
        stations = [
            s for s in stations
            if haversine_distance(lat, lon, s.latitude, s.longitude) <= radius_km
        ]
    
    return [StationResponse.from_db_model(s) for s in stations]


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific charging station
    
    - **station_id**: UUID of the charging station
    """
    station = db.query(ChargingStation).filter(ChargingStation.id == station_id).first()
    
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return StationResponse.from_db_model(station)


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_stations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Get personalized station recommendations using MCDM algorithm
    
    - **user_location**: Current user location (lat, lon)
    - **battery_soc**: Battery state of charge (0-100)
    - **connector_type**: Preferred connector type
    - **max_distance_km**: Maximum search distance
    - **preferences**: Weights for distance, price, speed, availability
    """
    # Get all active stations
    stations = db.query(ChargingStation).filter(
        ChargingStation.is_active == True
    ).all()
    
    if not stations:
        return RecommendationResponse(
            stations=[],
            total_count=0,
            user_location=request.user_location
        )
    
    # Initialize MCDM recommender with user preferences
    recommender = MCDMRecommender(
        distance_weight=request.preferences.distance_weight,
        price_weight=request.preferences.price_weight,
        speed_weight=request.preferences.speed_weight,
        availability_weight=request.preferences.availability_weight
    )
    
    # Get ranked stations
    ranked = recommender.rank_stations(
        stations=stations,
        user_lat=request.user_location.latitude,
        user_lon=request.user_location.longitude,
        connector_type=request.connector_type.value if request.connector_type else None
    )
    
    # Filter by max distance
    ranked = [
        (station, score, distance)
        for station, score, distance in ranked
        if distance <= request.max_distance_km
    ]
    
    # Convert to response format
    ranked_stations = [
        RankedStation(
            station=StationResponse.from_db_model(station),
            score=round(score, 3),
            distance_km=round(distance, 2),
            estimated_wait_minutes=0  # TODO: Implement wait time estimation
        )
        for station, score, distance in ranked
    ]
    
    return RecommendationResponse(
        stations=ranked_stations,
        total_count=len(ranked_stations),
        user_location=request.user_location
    )
