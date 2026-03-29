"""
ML Training Router

Exposes endpoints to trigger Federated Learning training and check model status.
Training runs as a background subprocess so the API remains responsive.
"""
import subprocess
import sys
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Optional

router = APIRouter(prefix="/ml", tags=["ml-training"])

# Global training state
_training_state = {
    "status": "idle",      # idle | running | done | failed
    "pid": None,
    "last_run_log": None
}

ML_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ml")
)
CHECKPOINT_PATH = os.path.join(ML_DIR, "checkpoints", "best_model.keras")


def _run_fl_training(clients: int, rounds: int):
    """Background task that runs the FL demo script."""
    global _training_state
    _training_state["status"] = "running"
    try:
        result = subprocess.run(
            [sys.executable, "run_demo.py", "--clients", str(clients), "--rounds", str(rounds)],
            cwd=ML_DIR,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute max
        )
        _training_state["last_run_log"] = result.stdout[-3000:]  # keep last 3k chars
        if result.returncode == 0:
            _training_state["status"] = "done"
        else:
            _training_state["status"] = "failed"
            _training_state["last_run_log"] += "\n\nSTDERR:\n" + result.stderr[-1000:]
    except subprocess.TimeoutExpired:
        _training_state["status"] = "failed"
        _training_state["last_run_log"] = "Training timed out after 10 minutes."
    except Exception as e:
        _training_state["status"] = "failed"
        _training_state["last_run_log"] = str(e)


@router.post("/train")
async def trigger_fl_training(
    background_tasks: BackgroundTasks,
    clients: int = 5,
    rounds: int = 5
):
    """
    Trigger Federated Learning training in the background.

    Launches the FL demo script with the specified number of simulated
    client vehicles and server aggregation rounds. The resulting model
    checkpoint (`best_model.keras`) is used by the `/predictions/soc` endpoint.

    Args:
        clients: Number of simulated EV clients (default 5).
        rounds:  Number of FL aggregation rounds (default 5).
    """
    if _training_state["status"] == "running":
        raise HTTPException(
            status_code=409,
            detail="Training is already running. Check /api/v1/ml/status for updates."
        )

    background_tasks.add_task(_run_fl_training, clients, rounds)
    _training_state["status"] = "running"
    _training_state["pid"] = None

    return {
        "message": f"Federated Learning training started with {clients} clients and {rounds} rounds.",
        "status": "running",
        "check_status_at": "/api/v1/ml/status"
    }


@router.get("/status")
async def get_training_status():
    """
    Get the current status of the Federated Learning training job.

    Returns training state (idle/running/done/failed), whether the
    model checkpoint exists, and the last training log snippet.
    """
    model_exists = os.path.exists(CHECKPOINT_PATH)
    return {
        "training_status": _training_state["status"],
        "model_available": model_exists,
        "model_path": CHECKPOINT_PATH if model_exists else None,
        "last_run_log": _training_state.get("last_run_log")
    }
