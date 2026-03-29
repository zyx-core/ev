from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os
from pathlib import Path

from .config import settings
from .database import init_db
from .routers import stations, predictions
from .routers.reservations import router as reservations_router, session_router
from .routers.pricing import router as pricing_router
from .routers.dashboard import router as dashboard_router
from .routers.simulation import router as simulation_router
from .routers.iot import router as iot_router
from .routers import demo
from .routers.ml_training import router as ml_training_router
from .services.blockchain import init_blockchain_service
from .schemas import HealthResponse


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="""
    IEVC-eco API - Integrated AIoT Intelligent EV Charging Ecosystem
    
    ## Features
    - **Station Discovery**: Find nearby charging stations with real-time availability
    - **Personalized Recommendations**: MCDM-based station ranking with user preferences
    - **Smart Filtering**: Filter by connector type, distance, and availability
    - **SoC Prediction**: Privacy-preserving battery state prediction (Phase 2)
    - **Reservations**: Book charging slots and manage sessions (Phase 3)
    - **Dynamic Pricing**: MARL-optimized real-time pricing (Phase 4)
    
    ## Phase 1 Endpoints
    - Stations listing and details
    - MCDM-based recommendations
    
    ## Phase 2 Endpoints
    - Battery SoC prediction using FL-trained LSTM model
    
    ## Phase 3 Endpoints
    - Charging reservations and session management
    
    ## Phase 4 Endpoints
    - Dynamic pricing optimization
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stations.router, prefix=settings.api_v1_prefix)
app.include_router(predictions.router, prefix=settings.api_v1_prefix)
app.include_router(reservations_router, prefix=settings.api_v1_prefix)
app.include_router(session_router, prefix=settings.api_v1_prefix)
app.include_router(pricing_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(simulation_router, prefix=settings.api_v1_prefix)
app.include_router(iot_router, prefix=settings.api_v1_prefix)
app.include_router(demo.router, prefix=settings.api_v1_prefix)
app.include_router(ml_training_router, prefix=settings.api_v1_prefix)

# Serve IoT Simulation Gateway
BASE_DIR = Path(__file__).resolve().parent.parent.parent
IOT_DIR = os.path.join(BASE_DIR, "frontend", "iot_gateway")
app.mount("/iot", StaticFiles(directory=IOT_DIR, html=True), name="iot")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    init_blockchain_service()
    print(f"[*] {settings.project_name} v{settings.version} started")
    print(f"[*] API docs available at /docs")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.utcnow()
    )
