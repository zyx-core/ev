"""
Prediction Router

API endpoints for battery SoC prediction using the FL-trained model.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from ..services.soc_predictor import get_predictor
from ..services.anomaly_detector import get_anomaly_detector


router = APIRouter(prefix="/predictions", tags=["predictions"])


class BatteryDataRequest(BaseModel):
    """Request model for SoC prediction."""
    voltage: List[float] = Field(..., description="Voltage readings (V)")
    current: List[float] = Field(..., description="Current readings (A)")
    temperature: List[float] = Field(..., description="Temperature readings (C)")
    power: List[float] = Field(..., description="Power readings (kW)")
    energy_consumed: List[float] = Field(..., description="Cumulative energy (kWh)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "voltage": [350.0] * 60,
                "current": [50.0] * 60,
                "temperature": [30.0] * 60,
                "power": [20.0] * 60,
                "energy_consumed": [i * 0.01 for i in range(60)]
            }
        }


class SoCPredictionResponse(BaseModel):
    """Response model for SoC and SoH prediction."""
    predicted_soc: float = Field(..., description="Predicted State of Charge (%)")
    predicted_soh: float = Field(..., description="Predicted State of Health (%)")
    confidence: float = Field(default=0.85, description="Prediction confidence")
    model_version: str = Field(default="fl-lstm-v1", description="Model version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "predicted_soc": 72.5,
                "predicted_soh": 95.0,
                "confidence": 0.85,
                "model_version": "fl-lstm-v1"
            }
        }


class QuickPredictionRequest(BaseModel):
    """Simplified request for quick SoC estimation."""
    current_soc: float = Field(..., ge=0, le=100, description="Current SoC (%)")
    power_consumption_kw: float = Field(..., ge=0, description="Avg power (kW)")
    duration_minutes: float = Field(..., ge=0, description="Duration (min)")
    battery_capacity_kwh: float = Field(default=60.0, description="Battery capacity")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_soc": 80.0,
                "power_consumption_kw": 15.0,
                "duration_minutes": 30.0,
                "battery_capacity_kwh": 60.0
            }
        }


@router.post("/soc", response_model=SoCPredictionResponse)
async def predict_soc(request: BatteryDataRequest):
    """
    Predict battery State of Charge and Health from time-series data.
    
    Uses the LSTM model trained via Federated Learning.
    All input data is processed locally - no raw data is stored.
    Includes Anomaly Detection to prevent False Data Injection.
    """
    try:
        # Check for False Data Injection (Anomalies)
        detector = get_anomaly_detector()
        anomaly_check = detector.detect_anomalies(
            voltage=request.voltage,
            current=request.current,
            temperature=request.temperature,
            power=request.power,
            energy_consumed=request.energy_consumed
        )
        
        if anomaly_check["is_anomalous"]:
            raise ValueError(f"False Data Injection detected: {'; '.join(anomaly_check['reasons'])}")
            
        predictor = get_predictor()
        prediction = predictor.predict(
            voltage=request.voltage,
            current=request.current,
            temperature=request.temperature,
            power=request.power,
            energy_consumed=request.energy_consumed
        )
        
        return SoCPredictionResponse(
            predicted_soc=round(prediction["soc"], 2),
            predicted_soh=round(prediction["soh"], 2),
            confidence=0.85,
            model_version="fl-lstm-v1"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/soc/quick", response_model=SoCPredictionResponse)
async def quick_soc_prediction(request: QuickPredictionRequest):
    """
    Quick SoC estimation based on simple parameters.
    
    Uses a direct calculation based on power consumption
    without requiring full time-series data.
    """
    # Calculate energy consumed
    energy_consumed = request.power_consumption_kw * (request.duration_minutes / 60)
    
    # Calculate SoC drop
    soc_drop = (energy_consumed / request.battery_capacity_kwh) * 100
    
    # Predicted SoC
    predicted_soc = max(0, request.current_soc - soc_drop)
    
    return SoCPredictionResponse(
        predicted_soc=round(predicted_soc, 2),
        predicted_soh=95.0, # Mock SoH for quick path
        confidence=0.75,  # Lower confidence for simple estimation
        model_version="simple-calc-v1"
    )


@router.get("/model/status")
async def get_model_status():
    """
    Get the status of the prediction model.
    
    Returns information about model availability and version.
    """
    predictor = get_predictor()
    model_available = predictor.model is not None
    
    return {
        "model_available": model_available,
        "model_path": predictor.model_path,
        "model_version": "fl-lstm-v1" if model_available else None,
        "sequence_length": predictor.SEQUENCE_LENGTH,
        "features": predictor.FEATURE_NAMES,
        "status": "ready" if model_available else "model_not_loaded"
    }
