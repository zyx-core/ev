"""
Dashboard Router
API endpoints for the web dashboard data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import numpy as np
import asyncio
import json
from fastapi.responses import StreamingResponse

from ..database import get_db
from ..models import ChargingStation, ChargingSession, Connector, SessionStatus


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Get dashboard overview data
    
    Returns aggregated statistics for the main dashboard
    """
    # Station statistics
    total_stations = db.query(ChargingStation).count()
    active_stations = db.query(ChargingStation).filter(
        ChargingStation.is_active == True
    ).count()
    
    # Connector statistics
    total_connectors = db.query(Connector).count()
    available_connectors = db.query(Connector).filter(
        Connector.status == "available"
    ).count()
    
    # Session statistics (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    sessions_today = db.query(ChargingSession).filter(
        ChargingSession.created_at >= yesterday
    ).count()
    
    completed_sessions = db.query(ChargingSession).filter(
        ChargingSession.created_at >= yesterday,
        ChargingSession.status == SessionStatus.COMPLETED
    ).count()
    
    # Revenue calculation
    revenue_result = db.query(func.sum(ChargingSession.cost)).filter(
        ChargingSession.created_at >= yesterday,
        ChargingSession.status == SessionStatus.COMPLETED
    ).scalar()
    
    revenue_24h = float(revenue_result) if revenue_result else 0.0
    
    # Energy delivered
    energy_result = db.query(func.sum(ChargingSession.energy_delivered_kwh)).filter(
        ChargingSession.created_at >= yesterday,
        ChargingSession.status == SessionStatus.COMPLETED
    ).scalar()
    
    energy_24h = float(energy_result) if energy_result else 0.0
    
    # Calculate current utilization
    utilization = (total_connectors - available_connectors) / max(total_connectors, 1)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "stations": {
            "total": total_stations,
            "active": active_stations,
            "inactive": total_stations - active_stations
        },
        "connectors": {
            "total": total_connectors,
            "available": available_connectors,
            "in_use": total_connectors - available_connectors,
            "utilization": round(utilization * 100, 1)
        },
        "sessions_24h": {
            "total": sessions_today,
            "completed": completed_sessions,
            "active": sessions_today - completed_sessions
        },
        "revenue_24h": round(revenue_24h, 2),
        "energy_24h_kwh": round(energy_24h, 2),
        "avg_session_value": round(revenue_24h / max(completed_sessions, 1), 2)
    }


    return result

@router.get("/stations/status")
async def get_stations_status(db: Session = Depends(get_db)):
    """
    Get real-time status of all stations
    
    Returns list of stations with current status
    """
    stations = db.query(ChargingStation).filter(
        ChargingStation.is_active == True
    ).all()
    
    result = []
    for station in stations:
        available = sum(1 for c in station.connectors if c.status.value == "available")
        total = len(station.connectors)
        
        # Calculate reasoning for the demo
        reason = "Base rate active"
        if station.dynamic_multiplier > 1.1:
            reason = "MARL: High occupancy & Peak Demand"
        elif station.dynamic_multiplier < 0.9:
            reason = "Grid Stability: Low Load Incentive"
        elif 0.9 <= station.dynamic_multiplier <= 1.1:
            reason = "Stable Grid: Optimized Balanced Pricing"

        result.append({
            "id": station.id,
            "name": station.name,
            "location": {
                "latitude": station.latitude,
                "longitude": station.longitude
            },
            "connectors_available": available,
            "connectors_total": total,
            "utilization": round((total - available) / max(total, 1) * 100, 1),
            "current_rate": round(station.base_rate * station.dynamic_multiplier, 3),
            "price_multiplier": round(station.dynamic_multiplier, 2),
            "reasoning": reason
        })
    
    return result


@router.get("/stream")
async def stream_station_updates():
    """
    Server-Sent Events (SSE) stream for real-time station updates
    """
    from sqlalchemy.orm import joinedload
    from ..database import SessionLocal
    
    async def event_generator():
        while True:
            db = SessionLocal()
            try:
                stations = db.query(ChargingStation).options(
                    joinedload(ChargingStation.connectors)
                ).filter(ChargingStation.is_active == True).all()
                
                result = []
                for s in stations:
                    available = sum(1 for c in s.connectors if c.status.value == "available")
                    total = len(s.connectors)
                    result.append({
                        "id": str(s.id),
                        "name": s.name,
                        "location": {"latitude": s.latitude, "longitude": s.longitude},
                        "pricing": {
                            "base_rate": s.base_rate,
                            "dynamic_multiplier": s.dynamic_multiplier,
                            "effective_rate": round(base_rate * multiplier, 2) if (base_rate := s.base_rate) and (multiplier := s.dynamic_multiplier) else 0.0
                        },
                        "connectors_available": available,
                        "connectors_total": total,
                        "connectors": [
                            {"connector_type": c.connector_type.value, "status": c.status.value, "power_kw": float(c.power_kw or 0)}
                            for c in s.connectors
                        ]
                    })
                
                yield f"data: {json.dumps(result)}\n\n"
            finally:
                db.close()
                
            await asyncio.sleep(1) # Stream every 1 second
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/sessions/recent")
async def get_recent_sessions(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get recent charging sessions
    
    Returns list of most recent sessions for monitoring
    """
    sessions = db.query(ChargingSession).order_by(
        ChargingSession.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "station_id": s.station_id,
            "station_name": s.station.name if s.station else "Unknown Station",
            "status": s.status.value,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "energy_kwh": s.energy_delivered_kwh,
            "cost": s.cost,
            "created_at": s.created_at.isoformat()
        }
        for s in sessions
    ]


from ..routers.iot import grid_state

@router.get("/grid/load")
async def get_grid_load_data():
    """
    Get simulated grid load data
    
    Returns estimated grid load and recommendations
    """
    now = datetime.now()
    
    # Use real-time state from IoT Gateway
    current_load = grid_state["load_factor"]
    
    # Determine grid status
    
    # Determine grid status
    if current_load > 0.85:
        status = "critical"
        recommendation = "Reduce charging load - consider scheduling for off-peak"
    elif current_load > 0.7:
        status = "high"
        recommendation = "Monitor load - prefer lower power charging"
    elif current_load < 0.4:
        status = "low"
        recommendation = "Good time for high-power charging"
    else:
        status = "normal"
        recommendation = "Normal operations"
    
    # Generate hourly forecast
    forecast = []
    base_load = 0.5
    for h in range(24):
        future_load = base_load + 0.3 * np.exp(-((h - 18) ** 2) / 20) + 0.15 * np.exp(-((h - 8) ** 2) / 10)
        forecast.append({
            "hour": h,
            "predicted_load": round(future_load, 2),
            "is_peak": h in [7, 8, 9, 17, 18, 19, 20]
        })
    
    return {
        "timestamp": now.isoformat(),
        "current_load": round(current_load, 3),
        "status": status,
        "recommendation": recommendation,
        "forecast": forecast,
        "optimal_charging_hours": [0, 1, 2, 3, 4, 5, 11, 12, 13, 14]
    }


@router.get("/pricing/overview")
async def get_pricing_overview(db: Session = Depends(get_db)):
    """
    Get pricing overview for dashboard
    
    Returns current pricing statistics
    """
    stations = db.query(ChargingStation).filter(
        ChargingStation.is_active == True
    ).all()
    
    if not stations:
        return {
            "avg_base_rate": 0,
            "avg_multiplier": 1.0,
            "avg_effective_rate": 0,
            "min_rate": 0,
            "max_rate": 0,
            "stations_count": 0
        }
    
    base_rates = [s.base_rate for s in stations]
    multipliers = [s.dynamic_multiplier for s in stations]
    effective_rates = [s.base_rate * s.dynamic_multiplier for s in stations]
    
    return {
        "avg_base_rate": round(np.mean(base_rates), 3),
        "avg_multiplier": round(np.mean(multipliers), 3),
        "avg_effective_rate": round(np.mean(effective_rates), 3),
        "min_rate": round(min(effective_rates), 3),
        "max_rate": round(max(effective_rates), 3),
        "stations_count": len(stations),
        "pricing_distribution": {
            "below_avg": sum(1 for r in effective_rates if r < np.mean(effective_rates)),
            "at_avg": sum(1 for r in effective_rates if abs(r - np.mean(effective_rates)) < 0.01),
            "above_avg": sum(1 for r in effective_rates if r > np.mean(effective_rates))
        }
    }


@router.get("/analytics/trends")
async def get_analytics_trends(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get analytics trends for specified days
    
    Returns daily aggregated metrics
    """
    trends = []
    
    for i in range(days - 1, -1, -1):
        day_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        sessions = db.query(ChargingSession).filter(
            ChargingSession.created_at >= day_start,
            ChargingSession.created_at < day_end
        ).all()
        
        completed = [s for s in sessions if s.status == SessionStatus.COMPLETED]
        
        trends.append({
            "date": day_start.date().isoformat(),
            "sessions": len(sessions),
            "completed": len(completed),
            "revenue": round(sum(s.cost for s in completed), 2),
            "energy_kwh": round(sum(s.energy_delivered_kwh for s in completed), 2)
        })
    
    return {
        "period_days": days,
        "daily_trends": trends,
        "total_sessions": sum(t["sessions"] for t in trends),
        "total_revenue": round(sum(t["revenue"] for t in trends), 2),
        "total_energy_kwh": round(sum(t["energy_kwh"] for t in trends), 2)
    }
