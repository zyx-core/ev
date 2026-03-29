from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, List, Optional
import uuid
import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

from ..schemas import SimulationConfig, SimulationResult

router = APIRouter(
    prefix="/simulation",
    tags=["simulation"]
)

# Store simulation results in memory
simulations: Dict[str, dict] = {}

def run_simulation_task(sim_id: str, config: SimulationConfig):
    """Background task to run the simulation script"""
    try:
        simulations[sim_id]["status"] = "running"
        
        # Resolve path relative to this file
        # backend/app/routers/simulation.py -> backend/app/routers -> backend/app -> backend -> root
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        script_path = base_dir / "simulation" / "stress_test.py"
        results_path = f"sim_results_{sim_id}.json"
        
        # Build command
        cmd = [
            sys.executable,
            str(script_path),
            "--evs", str(config.evs),
            "--stations", str(config.stations),
            "--cpos", str(config.cpos),
            "--steps", str(config.steps),
            "--save-results", results_path
        ]
        
        # Run command
        process = subprocess.run(cmd, capture_output=True, text=True, cwd=str(base_dir))
        
        if process.returncode == 0 and os.path.exists(results_path):
             # ... rest of function
            with open(results_path, 'r') as f:
                results_data = json.load(f)
            
            simulations[sim_id]["status"] = "completed"
            simulations[sim_id]["results"] = results_data
            
            # Clean up
            os.remove(results_path)
        else:
            simulations[sim_id]["status"] = "failed"
            simulations[sim_id]["error"] = process.stderr or "Simulation failed to produce results"
            
    except Exception as e:
        simulations[sim_id]["status"] = "failed"
        simulations[sim_id]["error"] = str(e)

@router.post("/run", response_model=Dict)
async def start_simulation(config: SimulationConfig, background_tasks: BackgroundTasks):
    """Start a new simulation in the background"""
    sim_id = str(uuid.uuid4())
    
    simulations[sim_id] = {
        "id": sim_id,
        "status": "pending",
        "config": config,
        "created_at": datetime.utcnow(),
        "results": None,
        "error": None
    }
    
    background_tasks.add_task(run_simulation_task, sim_id, config)
    
    return {"id": sim_id, "status": "pending"}

@router.get("/status/{sim_id}", response_model=SimulationResult)
async def get_simulation_status(sim_id: str):
    """Get the status and results of a simulation"""
    if sim_id not in simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return simulations[sim_id]

@router.get("/history", response_model=List[SimulationResult])
async def get_simulation_history():
    """Get history of all simulations"""
    # Sort by created_at desc
    return sorted(simulations.values(), key=lambda x: x["created_at"], reverse=True)
