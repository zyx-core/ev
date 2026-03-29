# IEVC-eco Simulation Package
"""
Multi-Agent Reinforcement Learning simulation for EV charging ecosystem

Modules:
- env: PettingZoo-based multi-agent environment
- agents: EV, CPO, and Grid agent implementations
- train: MARL training script
- stress_test: Scalability testing with 1000+ EVs
"""

from .env.charging_env import ChargingEnvironment, make_env
from .agents.ev_agent import EVAgent
from .agents.cpo_agent import CPOAgent
from .agents.grid_agent import GridAgent

__all__ = [
    'ChargingEnvironment',
    'make_env',
    'EVAgent',
    'CPOAgent',
    'GridAgent'
]
