from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Database
    database_url: str = "sqlite:///./ievc_eco.db"
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "IEVC-eco API"
    version: str = "1.0.0"
    
    # CORS - allow all origins for development
    cors_origins: list[str] = [
        "*",  # Allow all origins for development
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]
    
    # Map API Keys (optional for Phase 1)
    google_maps_api_key: Optional[str] = None
    mapbox_token: Optional[str] = None
    
    # Blockchain
    registry_contract_address: Optional[str] = None
    tx_manager_contract_address: Optional[str] = None
    blockchain_private_key: Optional[str] = None
    web3_provider_uri: str = "http://127.0.0.1:8545"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
