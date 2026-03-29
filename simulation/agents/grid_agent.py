"""
Grid Aggregator Agent
Reinforcement learning agent for grid load balancing
"""
import numpy as np
from typing import Dict, List, Tuple


class GridAgent:
    """
    Grid Aggregator RL Agent
    
    Goal: Balance grid load by sending signals to encourage/discourage charging
    
    Observation:
    - Station occupancy rates
    - Current prices
    - Total grid load
    - Time of day
    - Day of week
    
    Action:
    - Load signal [-1, 1] where:
      -1 = Discourage charging (high load)
       0 = Neutral
      +1 = Encourage charging (low load)
    """
    
    def __init__(
        self,
        agent_id: str = "grid_0",
        observation_dim: int = 15,
        learning_rate: float = 1e-3,
        gamma: float = 0.99
    ):
        """
        Initialize Grid Aggregator agent
        
        Args:
            agent_id: Unique agent identifier
            observation_dim: Dimension of observation space
            learning_rate: Learning rate
            gamma: Discount factor
        """
        self.agent_id = agent_id
        self.observation_dim = observation_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        
        # Grid parameters
        self.max_load = 10000  # kW
        self.target_load = 0.6  # Target 60% utilization
        self.danger_threshold = 0.85
        self.low_threshold = 0.3
        
        # Load history for forecasting
        self.load_history = []
        self.signal_history = []
        
        # Learning state
        self.episode_rewards = []
        self.total_imbalance = 0.0
        
        # Simple policy parameters
        self.theta = np.random.randn(observation_dim) * 0.01
        
    def select_action(
        self, 
        observation: np.ndarray, 
        explore: bool = True
    ) -> np.ndarray:
        """
        Select grid signal based on observation
        
        Args:
            observation: Current environment observation
            explore: Whether to add exploration noise
            
        Returns:
            Grid signal array [-1, 1]
        """
        # Extract grid load from observation (last element before the extra obs)
        grid_load = observation[-1]  # Assuming grid_load is appended
        
        # Rule-based signal generation
        if grid_load > self.danger_threshold:
            # Critical: strong signal to reduce load
            signal = -1.0
        elif grid_load > 0.7:
            # High: moderate signal to reduce
            signal = -0.5
        elif grid_load < self.low_threshold:
            # Low: signal to increase load
            signal = 0.8
        elif grid_load < 0.5:
            # Below target: slight increase signal
            signal = 0.3
        else:
            # Near target: neutral
            signal = 0.0
        
        # Add exploration noise
        if explore:
            noise = np.random.normal(0, 0.1)
            signal += noise
        
        # Clip to valid range
        signal = np.clip(signal, -1.0, 1.0)
        
        self.load_history.append(grid_load)
        self.signal_history.append(signal)
        
        return np.array([signal], dtype=np.float32)
    
    def update(
        self, 
        observation: np.ndarray, 
        action: np.ndarray, 
        reward: float,
        next_observation: np.ndarray, 
        done: bool
    ):
        """Update agent's learning state"""
        self.episode_rewards.append(reward)
        
        # Track load imbalance
        grid_load = observation[-1]
        imbalance = abs(grid_load - self.target_load)
        self.total_imbalance += imbalance
    
    def predict_load(self, horizon: int = 12) -> np.ndarray:
        """
        Predict future load based on history
        
        Args:
            horizon: Number of steps to predict (default 1 hour at 5-min intervals)
            
        Returns:
            Predicted load values
        """
        if len(self.load_history) < 24:  # Need at least 2 hours of data
            return np.full(horizon, self.target_load)
        
        # Simple moving average prediction
        recent = np.array(self.load_history[-24:])
        trend = np.mean(np.diff(recent))
        
        predictions = []
        last_value = recent[-1]
        
        for i in range(horizon):
            next_value = last_value + trend
            next_value = np.clip(next_value, 0, 1)
            predictions.append(next_value)
            last_value = next_value
        
        return np.array(predictions)
    
    def get_load_status(self, current_load: float) -> str:
        """Get human-readable load status"""
        if current_load > self.danger_threshold:
            return "CRITICAL"
        elif current_load > 0.7:
            return "HIGH"
        elif current_load < self.low_threshold:
            return "LOW"
        elif current_load < 0.5:
            return "MODERATE"
        else:
            return "OPTIMAL"
    
    def calculate_load_balancing_reward(
        self, 
        prev_load: float, 
        current_load: float
    ) -> float:
        """
        Calculate reward based on load balancing performance
        
        Rewards:
        - Moving towards target load
        - Avoiding critical load levels
        - Smooth load transitions
        """
        reward = 0.0
        
        # Distance to target
        prev_distance = abs(prev_load - self.target_load)
        curr_distance = abs(current_load - self.target_load)
        
        # Reward for moving towards target
        if curr_distance < prev_distance:
            reward += 0.5
        else:
            reward -= 0.3
        
        # Penalty for critical load
        if current_load > self.danger_threshold:
            reward -= 2.0
        
        # Bonus for maintaining optimal range
        if 0.5 <= current_load <= 0.7:
            reward += 0.5
        
        # Penalty for high variance (smooth transitions preferred)
        if len(self.load_history) > 1:
            variance = abs(current_load - self.load_history[-1])
            reward -= variance * 0.5
        
        return reward
    
    def reset(self):
        """Reset agent for new episode"""
        self.load_history = []
        self.signal_history = []
        self.episode_rewards = []
        
    def get_stats(self) -> Dict[str, float]:
        """Get agent statistics"""
        return {
            "agent_id": self.agent_id,
            "total_imbalance": self.total_imbalance,
            "avg_load": np.mean(self.load_history) if self.load_history else 0.0,
            "max_load": max(self.load_history) if self.load_history else 0.0,
            "min_load": min(self.load_history) if self.load_history else 0.0,
            "avg_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0.0
        }


class GridBalancingPolicy:
    """
    Neural network policy for grid load balancing
    Outputs continuous signal in [-1, 1]
    """
    
    def __init__(
        self,
        observation_dim: int,
        hidden_dims: tuple = (32, 16),
        learning_rate: float = 1e-3
    ):
        self.observation_dim = observation_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        
        # Policy network weights
        self.weights = {
            'w1': np.random.randn(observation_dim, hidden_dims[0]) * 0.1,
            'b1': np.zeros(hidden_dims[0]),
            'w2': np.random.randn(hidden_dims[0], hidden_dims[1]) * 0.1,
            'b2': np.zeros(hidden_dims[1]),
            'w_out': np.random.randn(hidden_dims[1], 1) * 0.1,
            'b_out': np.zeros(1)
        }
    
    def forward(self, observation: np.ndarray) -> float:
        """Forward pass - returns signal value"""
        # Hidden layers
        h1 = np.tanh(observation @ self.weights['w1'] + self.weights['b1'])
        h2 = np.tanh(h1 @ self.weights['w2'] + self.weights['b2'])
        
        # Output (tanh to bound to [-1, 1])
        out = np.tanh(h2 @ self.weights['w_out'] + self.weights['b_out'])
        
        return float(out[0])
    
    def sample_action(self, observation: np.ndarray) -> np.ndarray:
        """Sample action with noise"""
        signal = self.forward(observation)
        noise = np.random.normal(0, 0.1)
        action = np.clip(signal + noise, -1.0, 1.0)
        return np.array([action], dtype=np.float32)
    
    def get_action(self, observation: np.ndarray) -> np.ndarray:
        """Get deterministic action"""
        signal = self.forward(observation)
        return np.array([signal], dtype=np.float32)
