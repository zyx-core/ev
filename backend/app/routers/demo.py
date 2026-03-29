from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from ..services.demo_service import run_demo_scenario

router = APIRouter(
    prefix="/demo",
    tags=["demo"]
)

class DemoResponse(BaseModel):
    demo_id: str
    logs: List[str]

@router.post("/run/{demo_id}", response_model=DemoResponse)
async def run_demo(demo_id: str):
    """
    Run a specific demo scenario and return the logs.
    """
    valid_ids = ["1", "2", "3", "4", "5"]
    if demo_id not in valid_ids:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    logs = await run_demo_scenario(demo_id)
    return DemoResponse(demo_id=demo_id, logs=logs)
