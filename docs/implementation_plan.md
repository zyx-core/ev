# Implementation Plan - Run IEVC-eco Platform

The goal is to run the IEVC-eco platform's backend and then execute a demonstration script to verify its functionality.

## Proposed Changes

### Backend Service
Start the FastAPI backend service to provide the necessary API endpoints for the demo.

- **Action**: Run `python -m uvicorn app.main:app` in the `backend` directory.
- **Port**: 8000 (Static)

### Web Dashboard
Start the React-based CPO/Grid dashboard.

- **Action**: Run `npm run dev` in the `frontend/web` directory.
- **Expected Port**: 5173 (Default Vite)

### Driver Web App
Start the React-based Driver frontend.

- **Action**: Run `npm run dev` in the `frontend/driver-web` directory.
- **Expected Port**: 5174 (Auto-incremented Vite)

### Demo Script
Run the `demo_for_judges.py` script to simulate user interactions and system features.

- **Action**: Run `python demo_for_judges.py` from the root directory.

## Verification Plan

### Automated Tests
- Monitor the output of `demo_for_judges.py` for successful API calls and simulated flows.
- Check backend console logs for any tracebacks or errors.

### Manual Verification
- None required beyond monitoring script output.
