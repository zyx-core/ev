"""
EV Driver Agent
Reinforcement learning agent for EV charging station selection
"""
import numpy as np
from typing import Dict, Any, Optional
from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy


class EVAgent:
    """
    EV Driver RL Agent
    
    Goal: Minimize charging cost + wait time while reaching desired SoC
    
    Observation:
    - Station occupancy rates
    - Station prices
    - Current grid load
    - Time of day
    - Day of week
    
    Action:
    - Select charging station (discrete)
    """
    
    def __init__(
        self,
        agent_id: str,
        num_stations: int,
        observation_dim: int,
        learning_rate: float = 3e-4,
        gamma: float = 0.99
    ):
        """
        Initialize EV agent
        
        Args:
            agent_id: Unique agent identifier
            num_stations: Number of stations to choose from
            observation_dim: Dimension of observation space
            learning_rate: Learning rate for policy optimization
            gamma: Discount factor
        """
        self.agent_id = agent_id
        self.num_stations = num_stations
        self.observation_dim = observation_dim
        self.learning_rate = learning_rate
        self.gamma = gamma
        
        # Agent state
        self.current_soc = 50.0  # State of charge (0-100)
        self.target_soc = 80.0
        self.battery_capacity = 75.0  # kWh
        
        # Preferences (can be personalized per agent)
        self.price_sensitivity = np.random.uniform(0.3, 0.7)
        self.time_sensitivity = np.random.uniform(0.3, 0.7)
        self.location = np.random.rand(2)  # Random location
        
        # Learning state
        self.episode_rewards = []
        self.total_cost = 0.0
        self.total_wait_time = 0.0
        
    def select_action(self, observation: np.ndarray, explore: bool = True) -> int:
        """
        Select a charging station based on observation
        
        Args:
            observation: Current environment observation
            explore: Whether to explore or exploit
            
        Returns:
            Station index to charge at
        """
        # Parse observation
        occupancy_rates = observation[:self.num_stations]
        prices = observation[self.num_stations:2*self.num_stations]
        grid_load = observation[2*self.num_stations]
        
        # Calculate utility for each station
        utilities = np.zeros(self.num_stations)
        
        for i in range(self.num_stations):
            # Lower price = higher utility
            price_utility = 1.0 - prices[i]
            
            # Lower occupancy = higher utility (less wait time)
            wait_utility = 1.0 - occupancy_rates[i]
            
            # Combine utilities based on preferences
            utilities[i] = (
                self.price_sensitivity * price_utility +
                self.time_sensitivity * wait_utility
            )
        
        if explore and np.random.random() < 0.1:
            # Epsilon-greedy exploration
            return np.random.randint(self.num_stations)
        else:
            return int(np.argmax(utilities))
    
    def update(self, observation: np.ndarray, action: int, reward: float, 
               next_observation: np.ndarray, done: bool):
        """Update agent's learning state"""
        self.episode_rewards.append(reward)
        
    def get_energy_needed(self) -> float:
        """Calculate energy needed to reach target SoC"""
        energy_kwh = (self.target_soc - self.current_soc) / 100 * self.battery_capacity
        return max(0, energy_kwh)
    
    def simulate_charging(self, power_kw: float, duration_minutes: float, price_per_kwh: float):
        """
        Simulate a charging session
        
        Args:
            power_kw: Charging power in kW
            duration_minutes: Charging duration
            price_per_kwh: Price per kWh
        """
        energy_kwh = power_kw * (duration_minutes / 60)
        cost = energy_kwh * price_per_kwh
        
        # Update SoC
        soc_increase = (energy_kwh / self.battery_capacity) * 100
        self.current_soc = min(100, self.current_soc + soc_increase)
        
        self.total_cost += cost
        
        return energy_kwh, cost
    
    def reset(self):
        """Reset agent for new episode"""
        self.current_soc = np.random.uniform(20, 50)
        self.episode_rewards = []
        
    def get_stats(self) -> Dict[str, float]:
        """Get agent statistics"""
        return {
            "agent_id": self.agent_id,
            "current_soc": self.current_soc,
            "total_cost": self.total_cost,
            "total_wait_time": self.total_wait_time,
            "avg_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0.0
        }


class EVAgentPolicy:
    """
    Neural network policy for EV agent
    Uses PPO algorithm from Stable Baselines3
    """
    
    def __init__(
        self,
        observation_dim: int,
        action_dim: int,
        hidden_dims: tuple = (64, 64),
        learning_rate: float = 3e-4
    ):
        self.observation_dim = observation_dim
        self.action_dim = action_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        
        # Policy network weights (simplified)
        self.weights = {
            'w1': np.random.randn(observation_dim, hidden_dims[0]) * 0.1,
            'b1': np.zeros(hidden_dims[0]),
            'w2': np.random.randn(hidden_dims[0], hidden_dims[1]) * 0.1,
            'b2': np.zeros(hidden_dims[1]),
            'w_out': np.random.randn(hidden_dims[1], action_dim) * 0.1,
            'b_out': np.zeros(action_dim)
        }
    
    def forward(self, observation: np.ndarray) -> np.ndarray:
        """Forward pass through the policy network"""
        # Hidden layer 1
        h1 = np.tanh(observation @ self.weights['w1'] + self.weights['b1'])
        
        # Hidden layer 2
        h2 = np.tanh(h1 @ self.weights['w2'] + self.weights['b2'])
        
        # Output layer (logits)
        logits = h2 @ self.weights['w_out'] + self.weights['b_out']
        
        # Softmax to get action probabilities
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        return probs
    
    def sample_action(self, observation: np.ndarray) -> int:
        """Sample action from policy"""
        probs = self.forward(observation)
        return np.random.choice(self.action_dim, p=probs)
    
    def get_action(self, observation: np.ndarray) -> int:
        """Get greedy action"""
        probs = self.forward(observation)
        return int(np.argmax(probs))
