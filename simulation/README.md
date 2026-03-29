# Simulation - MARL Environment

## Overview
Multi-Agent Reinforcement Learning simulation for:
- Dynamic pricing optimization
- Load balancing
- Nash equilibrium discovery

## Tech Stack
- Python 3.10+
- OpenAI Gym / PettingZoo
- Ray RLLib / Stable Baselines3
- NumPy, Matplotlib

## Setup
```bash
cd simulation
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Components
- `env/charging_env.py` - Gym environment for EV charging ecosystem
- `agents/` - EV, CPO, and Grid Aggregator agents
- `train.py` - MARL training script
- `stress_test.py` - 1,000 EV simulation

## Run Training
```bash
python train.py --episodes 1000 --agents 100
```
