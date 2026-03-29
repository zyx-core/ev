# ML - Federated Learning & Prediction Models

## Overview
Privacy-preserving machine learning components:
- LSTM model for battery SoC prediction
- Federated Learning server (Flower)
- Client simulation scripts

## Tech Stack
- TensorFlow 2.15+ / PyTorch 2.1+
- Flower (Federated Learning framework)
- NumPy, Pandas

## Setup
```bash
cd ml
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Components
- `models/lstm_soc.py` - LSTM architecture for SoC prediction
- `federated/server.py` - Flower aggregation server
- `federated/client.py` - Simulated client training
- `data/` - Mock battery usage data generators
