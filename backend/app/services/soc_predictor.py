"""
SoC Prediction Service

Provides battery State of Charge predictions using the trained FL model.
Integrates with the backend API for real-time predictions.
"""

import numpy as np
from typing import List, Optional
import os

# Try to import TensorFlow (may not be available in all environments)
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class SoCPredictor:
    """
    Battery State of Charge Predictor.
    
    Uses the trained LSTM model from federated learning
    to predict battery SoC from time-series data.
    """
    
    # Default model path
    DEFAULT_MODEL_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "ml", "checkpoints", "best_model.keras"
    )
    
    # Input configuration
    SEQUENCE_LENGTH = 60
    FEATURE_NAMES = ['voltage', 'current', 'temperature', 'power', 'energy_consumed']
    NUM_FEATURES = len(FEATURE_NAMES)
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the predictor.
        
        Args:
            model_path: Path to the trained model file
        """
        self.model = None
        self.model_path = model_path or self.DEFAULT_MODEL_PATH
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the trained model from disk."""
        if not TF_AVAILABLE:
            print("Warning: TensorFlow not available. Using mock predictions.")
            return
        
        if not os.path.exists(self.model_path):
            print(f"Warning: Model not found at {self.model_path}")
            print("Run FL training first: python ml/run_demo.py")
            return
        
        try:
            self.model = load_model(self.model_path)
            print(f"Model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
    
    def predict(
        self,
        voltage: List[float],
        current: List[float],
        temperature: List[float],
        power: List[float],
        energy_consumed: List[float]
    ) -> dict:
        """
        Predict battery SoC and SoH from time-series data.
        
        Args:
            voltage: Voltage readings (V)
            current: Current readings (A)
            temperature: Temperature readings (C)
            power: Power readings (kW)
            energy_consumed: Cumulative energy consumed (kWh)
        
        Returns:
            Dictionary with 'soc' (%) and 'soh' (%)
        """
        # Validate input lengths
        min_len = min(len(voltage), len(current), len(temperature), 
                      len(power), len(energy_consumed))
        
        if min_len < self.SEQUENCE_LENGTH:
            # Pad with last values if not enough data
            pad_len = self.SEQUENCE_LENGTH - min_len
            voltage = [voltage[0]] * pad_len + voltage
            current = [current[0]] * pad_len + current
            temperature = [temperature[0]] * pad_len + temperature
            power = [power[0]] * pad_len + power
            energy_consumed = [energy_consumed[0]] * pad_len + energy_consumed
        
        # Take last SEQUENCE_LENGTH samples
        voltage = voltage[-self.SEQUENCE_LENGTH:]
        current = current[-self.SEQUENCE_LENGTH:]
        temperature = temperature[-self.SEQUENCE_LENGTH:]
        power = power[-self.SEQUENCE_LENGTH:]
        energy_consumed = energy_consumed[-self.SEQUENCE_LENGTH:]
        
        # Create feature array
        features = np.array([
            voltage, current, temperature, power, energy_consumed
        ]).T  # Shape: (SEQUENCE_LENGTH, NUM_FEATURES)
        
        # Normalize features
        features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
        
        # Add batch dimension
        features = features.reshape(1, self.SEQUENCE_LENGTH, self.NUM_FEATURES)
        
        # Make prediction
        if self.model is not None:
            prediction = self.model.predict(features, verbose=0)[0]
            soc = float(prediction[0]) * 100
            soh = float(prediction[1]) * 100 if len(prediction) > 1 else 95.0
            return {"soc": soc, "soh": soh}
        else:
            # Mock prediction based on energy consumed trend
            return self._mock_predict(energy_consumed)
    
    def _mock_predict(self, energy_consumed: List[float]) -> dict:
        """
        Mock prediction when model is not available.
        Uses simple heuristics based on energy consumption.
        """
        base_soh = 95.0  # Default mock SoH
        if not energy_consumed:
            return {"soc": 50.0, "soh": base_soh}
        
        # Estimate based on energy consumption rate
        consumption_rate = (energy_consumed[-1] - energy_consumed[0]) / len(energy_consumed)
        
        # Assume starting from 80% with 60kWh battery
        battery_capacity = 60.0
        initial_soc = 80.0
        estimated_soc = initial_soc - (energy_consumed[-1] / battery_capacity * 100)
        
        return {
            "soc": max(0.0, min(100.0, estimated_soc)),
            "soh": base_soh
        }
    
    def predict_from_dict(self, data: dict) -> dict:
        """
        Predict from a dictionary of time-series arrays.
        
        Args:
            data: Dictionary with keys 'voltage', 'current', 'temperature', 
                  'power', 'energy_consumed'
        
        Returns:
            Dictionary with 'soc' and 'soh' percentages
        """
        return self.predict(
            voltage=data.get('voltage', []),
            current=data.get('current', []),
            temperature=data.get('temperature', []),
            power=data.get('power', []),
            energy_consumed=data.get('energy_consumed', [])
        )


# Singleton instance for API usage
_predictor_instance = None


def get_predictor() -> SoCPredictor:
    """Get or create the SoC predictor singleton."""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = SoCPredictor()
    return _predictor_instance


# Quick test
if __name__ == "__main__":
    predictor = SoCPredictor()
    
    # Generate sample data
    import random
    n = 60
    sample_data = {
        'voltage': [350 + random.gauss(0, 5) for _ in range(n)],
        'current': [50 + random.gauss(0, 5) for _ in range(n)],
        'temperature': [30 + random.gauss(0, 2) for _ in range(n)],
        'power': [20 + random.gauss(0, 3) for _ in range(n)],
        'energy_consumed': [i * 0.01 for i in range(n)]
    }
    
    result = predictor.predict_from_dict(sample_data)
    print(f"Predicted SoC: {result['soc']:.1f}%")
    print(f"Predicted SoH: {result['soh']:.1f}%")
