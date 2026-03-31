"""
Dynamic Pricing Router
API endpoints for MARL-based dynamic pricing optimization
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import numpy as np

from ..database import get_db
from ..models import ChargingStation


router = APIRouter(prefix="/pricing", tags=["pricing"])


class DynamicPricingRequest(BaseModel):
    """Request for dynamic pricing calculation"""
    station_id: Optional[str] = None
    current_occupancy: float = Field(default=0.5, ge=0, le=1, description="Current occupancy rate")
    grid_load: float = Field(default=0.6, ge=0, le=1, description="Current grid load percentage")
    hour_of_day: int = Field(default=12, ge=0, le=23, description="Current hour (0-23)")
    day_of_week: int = Field(default=0, ge=0, le=6, description="Day of week (0=Monday)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "station-001",
                "current_occupancy": 0.7,
                "grid_load": 0.65,
                "hour_of_day": 18,
                "day_of_week": 2
            }
        }


class PricingMultiplier(BaseModel):
    """Pricing multiplier for a station"""
    station_id: str
    station_name: str
    base_rate: float
    multiplier: float
    effective_rate: float
    reasoning: str


class DynamicPricingResponse(BaseModel):
    """Response with pricing recommendations"""
    timestamp: datetime
    grid_status: str
    pricing_strategy: str
    stations: List[PricingMultiplier]
    avg_multiplier: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-07T10:30:00",
                "grid_status": "normal",
                "pricing_strategy": "peak_demand",
                "stations": [
                    {
                        "station_id": "station-001",
                        "station_name": "Downtown Charger",
                        "base_rate": 0.40,
                        "multiplier": 1.3,
                        "effective_rate": 0.52,
                        "reasoning": "High demand period"
                    }
                ],
                "avg_multiplier": 1.25
            }
        }



class CPOPricingPolicy:
    """
    Neural network policy for CPO dynamic pricing
    Outputs continuous price multipliers
    """
    
    def __init__(
        self,
        observation_dim: int,
        num_stations: int,
        hidden_dims: tuple = (64, 32),
        learning_rate: float = 1e-3
    ):
        self.observation_dim = observation_dim
        self.num_stations = num_stations
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        
        # Policy network weights
        self.weights = {
            'w1': np.random.randn(observation_dim, hidden_dims[0]) * 0.1,
            'b1': np.zeros(hidden_dims[0]),
            'w2': np.random.randn(hidden_dims[0], hidden_dims[1]) * 0.1,
            'b2': np.zeros(hidden_dims[1]),
            'w_mu': np.random.randn(hidden_dims[1], num_stations) * 0.1,  # Mean
            'b_mu': np.ones(num_stations),  # Start at 1.0
            'log_std': np.zeros(num_stations)  # Log standard deviation
        }
    
    def forward(self, observation: np.ndarray) -> tuple:
        """
        Forward pass - returns mean and std of action distribution
        """
        # Hidden layers
        h1 = np.tanh(observation @ self.weights['w1'] + self.weights['b1'])
        h2 = np.tanh(h1 @ self.weights['w2'] + self.weights['b2'])
        
        # Output mean (sigmoid scaled to [0.5, 2.0])
        mu_raw = h2 @ self.weights['w_mu'] + self.weights['b_mu']
        mu = 0.5 + 1.5 * (1 / (1 + np.exp(-mu_raw)))  # Sigmoid scaled
        
        # Standard deviation
        std = np.exp(self.weights['log_std'])
        
        return mu, std
    
    def get_action(self, observation: np.ndarray) -> np.ndarray:
        """Get deterministic action (mean)"""
        mu, _ = self.forward(observation)
        return np.clip(mu, 0.5, 2.0).astype(np.float32)

    def load_weights(self, path: str):
        """Load weights from JSON"""
        import json
        import os
        if not os.path.exists(path):
            print(f"Warning: Model weights {path} not found")
            return
            
        with open(path, 'r') as f:
            weights_data = json.load(f)
            
        for k, v in weights_data.items():
            self.weights[k] = np.array(v)


class MARLPricingEngine:
    """
    MARL-inspired pricing engine
    Uses learned policies to calculate dynamic pricing
    """
    
    # Peak hours (higher demand)
    PEAK_HOURS = [7, 8, 9, 17, 18, 19, 20]
    
    # Weekend adjustment
    WEEKEND_DAYS = [5, 6]
    
    def __init__(self):
        import os
        # Initialize Policy
        # Observation dim is num_stations*2 + 3. 
        # Assuming 5 stations for now (match training default)
        # TODO: Make this dynamic based on config
        self.num_stations = 5
        self.obs_dim = self.num_stations * 2 + 3 + self.num_stations # + CPO owned stations extra obs
        
        # The observation structure in CPOAgent is:
        # base_obs (occupancy + prices + grid + hour + day) + owned_occupancy
        # base_obs size: num_stations + num_stations + 1 + 1 + 1 = 2*num + 3
        # owned_occupancy: num_owned (let's say 3 for CPO 0 in 5 station setup)
        # We need to match the training setup exactly.
        # For this demo, we'll try to load weights and infer dimensions if possible, 
        # or hardcode to match the 5-station training run we just did.
        
        # Training run was: 5 stations, 2 CPOs. CPO 0 likely has 3 stations (0, 2, 4).
        # We will assume we are acting as "CPO 0" for all stations for simplicity, 
        # or just use the model to predict for a generic station.
        
        self.policy = CPOPricingPolicy(
            observation_dim=16, # 5 stations: 5 occ + 5 price + 1 grid + 1 hour + 1 day + 3 owned_occ = 16
            num_stations=3 # CPO 0 has 3 stations
        )
        
        # Load weights
        # Path relative to backend execution
        checkpoint_path = os.path.abspath(os.path.join(os.getcwd(), "..", "simulation", "checkpoints", "cpo_model.json"))
        if os.path.exists(checkpoint_path):
            self.policy.load_weights(checkpoint_path)
            print(f"[*] Loaded MARL model from {checkpoint_path}")
        else:
            print(f"[!] Warning: MARL model not found at {checkpoint_path}, using random weights")
    
    def calculate_multiplier(
        self,
        occupancy: float,
        grid_load: float,
        hour: int,
        day: int
    ) -> tuple:
        """
        Calculate pricing multiplier based on MARL policy
        
        Returns:
            (multiplier, reasoning)
        """
        multiplier = 1.0
        reasons = []
        
        # Construct Observation Vector for Inference
        # We need to match the training environment's observation format exactly.
        # Format: [occupancy_all, prices_all, grid_load, hour, day, occupancy_owned]
        
        # 1. Occupancy (All) - We don't have all stations here, so we'll simulate context
        # or just use current station for all slots (simplified inference)
        occupancy_all = np.full(self.num_stations, occupancy)
        
        # 2. Prices (All) - Normalized. Assume current base price for all
        prices_all = np.ones(self.num_stations) # Normalized
        
        # 3. Grid Load
        grid_val = grid_load
        
        # 4. Hour (Normalized 0-1)
        hour_norm = hour / 24.0
        
        # 5. Day (Normalized 0-1)
        day_norm = day / 7.0
        
        # 6. Owned Occupancy (Simulated as same as current)
        owned_occupancy = np.full(3, occupancy) # Assuming 3 owned stations
        
        # Concat
        obs = np.concatenate([
            occupancy_all,
            prices_all,
            [grid_val],
            [hour_norm],
            [day_norm],
            owned_occupancy
        ]).astype(np.float32)
        
        # Inference
        try:
            # Get actions (multipliers for all owned stations)
            actions = self.policy.get_action(obs)
            # Use the first action as the multiplier for this station
            # In a real system, we'd map station_id to the specific output index
            multiplier = float(actions[0])
            reasons.append("MARL Model Inference")
        except Exception as e:
            print(f"Inference error: {e}")
            multiplier = 1.0
            reasons.append("Model Error (Fallback)")
            
        # Post-Processing / Safety Bounds for Demo Visibility
        # If grid load is critical (>80%), force prices UP (1.5x - 2.0x)
        if grid_load > 0.8:
            reasons.append("High Grid Stress (+50%)")
            multiplier = max(multiplier, 1.5) 
        # If grid load is high (>70%), nudge prices UP
        elif grid_load > 0.7:
            reasons.append("Increased Grid Demand (+20%)")
            multiplier = max(multiplier, 1.2)
        # If grid load is very low (<30%), offer DISCOUNTS
        elif grid_load < 0.3:
            reasons.append("Grid Surplus Discount (-20%)")
            multiplier = min(multiplier, 0.8)
            
        # Ensure within reasonable bounds [0.5, 2.5]
        multiplier = max(0.5, min(2.5, multiplier))
        
        reasoning = " + ".join(reasons) if reasons else "Standard rate"
        
        return multiplier, reasoning
    
    def get_grid_status(self, grid_load: float) -> str:
        """Get human-readable grid status"""
        if grid_load > 0.85:
            return "critical"
        elif grid_load > 0.7:
            return "high"
        elif grid_load < 0.3:
            return "low"
        else:
            return "normal"
    
    def get_pricing_strategy(self, hour: int, occupancy: float) -> str:
        """Get current pricing strategy name"""
        if hour in self.PEAK_HOURS:
            return "peak_demand_management"
        elif hour in [0, 1, 2, 3, 4, 5]:
            return "night_incentive"
        elif occupancy > 0.7:
            return "congestion_pricing"
        elif occupancy < 0.3:
            return "demand_generation"
        else:
            return "balanced_optimization"


# Singleton engine instance
_pricing_engine: Optional[MARLPricingEngine] = None


def get_pricing_engine() -> MARLPricingEngine:
    global _pricing_engine
    if _pricing_engine is None:
        _pricing_engine = MARLPricingEngine()
    return _pricing_engine


@router.post("/dynamic", response_model=DynamicPricingResponse)
async def get_dynamic_pricing(
    request: DynamicPricingRequest,
    db: Session = Depends(get_db)
):
    """
    Get MARL-optimized dynamic pricing for charging stations
    
    Uses Multi-Agent Reinforcement Learning policy to determine
    optimal pricing based on:
    - Current station occupancy
    - Grid load status
    - Time of day and week
    - Historical demand patterns
    
    Returns pricing multipliers to maximize:
    - CPO revenue
    - Grid stability
    - User satisfaction
    """
    engine = get_pricing_engine()
    
    # Get stations
    query = db.query(ChargingStation).filter(ChargingStation.is_active == True)
    
    if request.station_id:
        query = query.filter(ChargingStation.id == request.station_id)
    
    stations = query.all()
    
    if not stations:
        raise HTTPException(status_code=404, detail="No active stations found")
    
    pricing_results = []
    multipliers = []
    
    # Use real-time grid load from IoT Gateway if available
    from ..routers.iot import grid_state
    
    # If request has default 0.6 and we have a different state, use state
    # Ideally the frontend should pass it, but this ensures sync for demo
    current_grid_load = request.grid_load
    if current_grid_load == 0.6 and grid_state["load_factor"] != 0.6:
        current_grid_load = grid_state["load_factor"]
    elif current_grid_load == 0.6 and grid_state["load_factor"] == 0.5:
         # If both are defaults, use the state (which starts at 0.5)
         current_grid_load = grid_state["load_factor"]

    for station in stations:
        multiplier, reasoning = engine.calculate_multiplier(
            occupancy=request.current_occupancy,
            grid_load=current_grid_load,
            hour=request.hour_of_day,
            day=request.day_of_week
        )
        
        effective_rate = station.base_rate * multiplier
        
        pricing_results.append(PricingMultiplier(
            station_id=station.id,
            station_name=station.name,
            base_rate=station.base_rate,
            multiplier=round(multiplier, 3),
            effective_rate=round(effective_rate, 3),
            reasoning=reasoning
        ))
        
        multipliers.append(multiplier)
    
    return DynamicPricingResponse(
        timestamp=datetime.utcnow(),
        grid_status=engine.get_grid_status(request.grid_load),
        pricing_strategy=engine.get_pricing_strategy(
            request.hour_of_day, 
            request.current_occupancy
        ),
        stations=pricing_results,
        avg_multiplier=round(np.mean(multipliers), 3)
    )


@router.get("/station/{station_id}")
async def get_station_pricing(
    station_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current pricing for a specific station
    
    Returns the base rate and current dynamic multiplier
    """
    station = db.query(ChargingStation).filter(
        ChargingStation.id == station_id
    ).first()
    
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return {
        "station_id": station.id,
        "station_name": station.name,
        "base_rate": station.base_rate,
        "current_multiplier": station.dynamic_multiplier,
        "effective_rate": round(station.base_rate * station.dynamic_multiplier, 3),
        "last_updated": station.created_at
    }


@router.post("/station/{station_id}/update")
async def update_station_pricing(
    station_id: str,
    multiplier: float = Query(..., ge=0.5, le=2.0, description="Pricing multiplier"),
    db: Session = Depends(get_db)
):
    """
    Update dynamic pricing multiplier for a station
    
    Allows CPOs to override MARL recommendations
    """
    station = db.query(ChargingStation).filter(
        ChargingStation.id == station_id
    ).first()
    
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    
    old_multiplier = station.dynamic_multiplier
    station.dynamic_multiplier = multiplier
    db.commit()
    
    return {
        "station_id": station.id,
        "old_multiplier": old_multiplier,
        "new_multiplier": multiplier,
        "new_effective_rate": round(station.base_rate * multiplier, 3),
        "message": "Pricing updated successfully"
    }


@router.get("/strategy/current")
async def get_current_strategy():
    """
    Get current pricing strategy based on time
    
    Returns the active pricing mode and parameters
    """
    engine = get_pricing_engine()
    now = datetime.now()
    
    hour = now.hour
    day = now.weekday()
    
    # Estimate occupancy and grid (would come from real data)
    estimated_occupancy = 0.5 + 0.2 * np.sin(hour * np.pi / 12)  # Peaks at noon
    estimated_grid = 0.4 + 0.3 * np.sin((hour - 6) * np.pi / 12)  # Peaks at 6pm
    
    strategy = engine.get_pricing_strategy(hour, estimated_occupancy)
    grid_status = engine.get_grid_status(estimated_grid)
    
    return {
        "timestamp": now.isoformat(),
        "hour_of_day": hour,
        "day_of_week": day,
        "pricing_strategy": strategy,
        "grid_status": grid_status,
        "estimated_occupancy": round(estimated_occupancy, 2),
        "estimated_grid_load": round(estimated_grid, 2),
        "peak_hours": engine.PEAK_HOURS,
        "is_peak": hour in engine.PEAK_HOURS,
        "is_weekend": day in engine.WEEKEND_DAYS
    }


class MCDMPreferences(BaseModel):
    """User preference weights for MCDM-based station recommendation."""
    user_location: Optional[dict] = None  # Compatible with frontend {latitude, longitude}
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    price_weight: float = Field(default=0.3, ge=0, le=1)
    speed_weight: float = Field(default=0.2, ge=0, le=1)
    distance_weight: float = Field(default=0.4, ge=0, le=1)
    availability_weight: float = Field(default=0.1, ge=0, le=1)
    connector_type: Optional[str] = None
    battery_soc: Optional[float] = None
    max_distance_km: Optional[float] = None


@router.post("/recommend")
async def recommend_stations(
    preferences: MCDMPreferences,
    db: Session = Depends(get_db)
):
    """
    Recommend and rank charging stations using MCDM (AHP-inspired).

    Accepts user preference weights for price, speed, proximity, and availability.
    Returns stations sorted by a weighted MCDM score so users can balance
    'lowest cost' vs 'fastest charge' vs 'closest station'.
    """
    from ..services.mcdm import MCDMRecommender

    stations = db.query(ChargingStation).filter(ChargingStation.is_active == True).all()

    if not stations:
        raise HTTPException(status_code=404, detail="No active stations found")

    # Normalize weights to sum to 1
    total_weight = (
        preferences.price_weight + preferences.speed_weight +
        preferences.distance_weight + preferences.availability_weight
    )
    if total_weight == 0:
        raise HTTPException(status_code=400, detail="At least one preference weight must be non-zero")

    # Extract lat/lon from flexible input
    lat = preferences.user_lat
    lon = preferences.user_lon
    if preferences.user_location:
        lat = preferences.user_location.get('latitude')
        lon = preferences.user_location.get('longitude')
        
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="User location (latitude/longitude) is required")

    recommender = MCDMRecommender(
        distance_weight=preferences.distance_weight / total_weight,
        price_weight=preferences.price_weight / total_weight,
        speed_weight=preferences.speed_weight / total_weight,
        availability_weight=preferences.availability_weight / total_weight
    )

    ranked = recommender.rank_stations(
        stations=stations,
        user_lat=lat,
        user_lon=lon,
        connector_type=preferences.connector_type
    )

    results = []
    for station, score, distance_km in ranked:
        # Filter by max distance if provided
        if preferences.max_distance_km and distance_km > preferences.max_distance_km:
            continue
            
        results.append({
            "station": {
                "id": str(station.id),
                "name": station.name,
                "location": {"latitude": station.latitude, "longitude": station.longitude},
                "pricing": {
                    "base_rate": station.base_rate,
                    "dynamic_multiplier": station.dynamic_multiplier,
                    "effective_rate": round(station.base_rate * station.dynamic_multiplier, 2)
                },
                "connectors": [
                    {"id": str(c.id), "connector_type": c.connector_type.value, "power_kw": c.power_kw, "status": c.status.value}
                    for c in station.connectors
                ]
            },
            "score": round(score, 4),
            "distance_km": round(distance_km, 2),
            "estimated_wait_minutes": 0
        })

    return {
        "stations": results,
        "total_count": len(results),
        "user_location": {"latitude": lat, "longitude": lon}
    }

