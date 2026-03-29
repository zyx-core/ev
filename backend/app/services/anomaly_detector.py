import numpy as np
from typing import List, Dict, Union

class AnomalyDetector:
    """
    Detects anomalous patterns (False Data Injection) in incoming
    Battery Management System (BMS) telemetry.
    
    Uses statistical boundaries and Rate-of-Change (RoC) analysis
    to identify spoofed data without requiring heavy ML dependencies.
    """
    
    # Plausible physical boundaries for standard EV profiles
    BOUNDs = {
        "voltage": (200.0, 1000.0),    # V
        "current": (-500.0, 500.0),    # A
        "temperature": (-20.0, 80.0),  # C
        "power": (-350.0, 350.0),      # kW
    }
    
    # Maximum allowed change between consecutive readings (per second)
    MAX_ROC = {
        "voltage": 50.0,      # Max 50V jump per sample
        "current": 100.0,     # Max 100A jump
        "temperature": 5.0,   # Max 5C jump
    }

    def detect_anomalies(
        self,
        voltage: List[float],
        current: List[float],
        temperature: List[float],
        power: List[float],
        energy_consumed: List[float]
    ) -> Dict[str, Union[bool, str, list]]:
        """
        Analyze time-series BMS data for anomalies.
        
        Args:
            voltage: List of voltage readings.
            current: List of current readings.
            temperature: List of temperature readings.
            power: List of power readings.
            energy_consumed: List of cumulative energy.
            
        Returns:
            Dict containing 'is_anomalous' (bool) and 'reasons' (list).
        """
        reasons = []
        
        data_streams = {
            "voltage": voltage,
            "current": current,
            "temperature": temperature,
            "power": power
        }
        
        # 1. Check absolute boundaries (Out-of-Bounds FDI)
        for name, stream in data_streams.items():
            if not stream:
                continue
            min_val, max_val = self.BOUNDs[name]
            stream_min = min(stream)
            stream_max = max(stream)
            
            if stream_min < min_val or stream_max > max_val:
                reasons.append(f"{name.capitalize()} out of physical bounds [{min_val}, {max_val}]. Got [{stream_min:.1f}, {stream_max:.1f}].")
                
        # 2. Check Rate of Change (Spike/Step FDI)
        for name, max_roc in self.MAX_ROC.items():
            stream = data_streams.get(name)
            if not stream or len(stream) < 2:
                continue
                
            stream_arr = np.array(stream)
            roc = np.abs(np.diff(stream_arr))
            max_actual_roc = np.max(roc)
            
            if max_actual_roc > max_roc:
                reasons.append(f"{name.capitalize()} spike detected. Max allowed change: {max_roc}, Got: {max_actual_roc:.1f}.")
                
        # 3. Check for Statistical Variance (Noise Injection)
        # e.g., if temperature fluctuates too randomly, which physically shouldn't happen quickly
        if len(temperature) >= 10:
            temp_std = np.std(temperature)
            if temp_std > 10.0:  # Temp shouldn't have a 10 degree standard deviation in a 60-second window
                reasons.append(f"Temperature variance too high (std: {temp_std:.1f}), indicating possible noise injection.")
                
        # 4. Logical consistencies
        # Energy consumed should technically never decrease significantly
        if len(energy_consumed) > 1:
            energy_diff = np.diff(energy_consumed)
            if np.min(energy_diff) < -0.1:  # Allow tiny floating point errors but no major drop
                reasons.append("Cumulative energy consumed decreased, which is physically impossible.")

        is_anomalous = len(reasons) > 0
        
        return {
            "is_anomalous": is_anomalous,
            "reasons": reasons
        }

# Singleton accessor
_detector_instance = None

def get_anomaly_detector() -> AnomalyDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = AnomalyDetector()
    return _detector_instance
