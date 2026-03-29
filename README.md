# IEVC-eco: Integrated AIoT Intelligent EV Charging Ecosystem

## Overview
A decentralized software platform that optimizes EV charging/discharging slots using:
- **Multi-Agent Reinforcement Learning (MARL)** for dynamic pricing and load balancing
- **Federated Learning** for privacy-preserving battery prediction
- **Blockchain** for secure, trustless billing and reservation management

## Target Stakeholders
- **EV Drivers**: Find cost-effective charging slots without compromising privacy
- **Charging Point Operators (CPOs)**: Maximize station profit through dynamic pricing
- **Grid Aggregators**: Predict energy demand and prevent overloads

## Project Structure
```
ievc-eco/
├── frontend/           # Flutter App (Driver) & React Dashboard (CPO)
├── backend/            # FastAPI (Orchestration, MARL Interface)
├── ml/                 # Federated Learning & LSTM Models
├── blockchain/         # Smart Contracts & Tests
├── simulation/         # MARL Environment & Stress Tests
└── docs/               # Documentation & Architecture Diagrams
```

## Tech Stack
- **Frontend**: Flutter (Mobile), React.js (Dashboard)
- **Backend**: Python, FastAPI
- **AI/ML**: TensorFlow/PyTorch, Flower (Federated Learning)
- **Blockchain**: Ethereum (Solidity) or Hyperledger
- **Simulation**: Python, OpenAI Gym/PettingZoo, Ray RLLib

## Development Roadmap
1. **Phase 1 (Weeks 1-3)**: Smart Discovery & Recommendation
2. **Phase 2 (Weeks 4-6)**: Privacy-Preserving AI (Federated Learning)
3. **Phase 3 (Weeks 7-9)**: Secure Transaction Management (Blockchain)
4. **Phase 4 (Weeks 10-12)**: System Coordination (MARL) & Stress Testing

## Getting Started
See individual component READMEs in each directory for setup instructions.

## License
TBD
