# Backend - FastAPI Service

## Overview
The backend orchestrates the entire IEVC-eco system, providing:
- REST APIs for mobile/web clients
- MCDM-based station ranking
- Integration with Federated Learning aggregator
- Blockchain transaction coordination
- MARL agent interface

## Tech Stack
- Python 3.10+
- FastAPI
- SQLite (development) / PostgreSQL (production)
- Web3.py (blockchain integration)
- Pydantic (data validation)

## Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```

## API Endpoints (Planned)
- `GET /stations` - List all charging stations
- `POST /recommend` - Get ranked station recommendations
- `POST /reserve` - Create charging reservation
- `GET /session/{id}` - Get session status
