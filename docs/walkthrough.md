# Walkthrough - IEVC-eco Platform Demo

I have successfully started the IEVC-eco backend and verified its functionality using the `demo_for_judges.py` script. All core features are operational.

## System Components Started
- **Backend Service**: FastAPI server running at `http://127.0.0.1:8000`.
- **Web Dashboard**: React/Vite application running at `http://localhost:5173`.
- **Driver Web App**: React/Vite application running at `http://localhost:5174`.

## Verified Features

### 1. Station Discovery
The system successfully identified 8 charging stations with real-time status and pricing.
- **EcoCharge Downtown Hub**: Rs.12.00/kWh, 2/3 available.
- **GreenPower Mall Station**: Rs.10.50/kWh, 2/2 available.

### 2. Dynamic Pricing Engine
The MARL-based pricing model calculated dynamic rates based on demand, grid load, and time of day.
- **Scenario**: Peak demand management at 9:00 AM.
- **Result**: Prices adjusted from base rates (e.g., Rs.12.00 -> Rs.18.81) with reasoning provided by the AI model.

### 3. Load Simulation
Simulated 20 EVs simultaneously requesting recommendations.
- **Success Rate**: 100% (20/20).
- **Avg Response Time**: 275ms.

### 4. Complete Charging Flow
Verified the end-to-end user journey:
1. **Station Selection**: EcoCharge Downtown Hub.
2. **Reservation**: Created reservation `29ef2dd2...` with Rs.900 escrow.
3. **Session Start**: Initialized charging session.
4. **Session End**: Completed with 31.93 kWh delivered at a cost of Rs.383.18.

### 5. Grid Monitoring Dashboard
Verified platform-wide metrics and grid status.
- **Grid Load**: 50.0% (Normal).
- **Platform Revenue (24h)**: Rs.383.18.
- **Energy Distributed (24h)**: 31.93 kWh.

## Validation Results
All API calls returned `200 OK` and the internal logic (pricing multipliers, escrow calculations, state transitions) behaved as expected.
