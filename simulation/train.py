"""
MARL Training Script
Train multi-agent reinforcement learning agents for EV charging ecosystem
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import os
import json
from datetime import datetime

from env.charging_env import ChargingEnvironment, make_env
from agents.ev_agent import EVAgent
from agents.cpo_agent import CPOAgent
from agents.grid_agent import GridAgent


class MARLTrainer:
    """
    Multi-Agent RL Trainer for IEVC-eco
    
    Trains EV, CPO, and Grid agents in the charging environment
    """
    
    def __init__(
        self,
        num_evs: int = 10,
        num_stations: int = 5,
        num_cpos: int = 2,
        max_steps: int = 288,
        seed: int = 42
    ):
        """
        Initialize trainer
        
        Args:
            num_evs: Number of EV agents
            num_stations: Number of charging stations
            num_cpos: Number of CPO agents
            max_steps: Max steps per episode
            seed: Random seed
        """
        np.random.seed(seed)
        
        self.num_evs = num_evs
        self.num_stations = num_stations
        self.num_cpos = num_cpos
        self.max_steps = max_steps
        
        # Create environment
        self.env = make_env(
            num_evs=num_evs,
            num_stations=num_stations,
            num_cpos=num_cpos,
            max_steps=max_steps
        )
        
        # Initialize agents
        self._init_agents()
        
        # Training metrics
        self.episode_rewards: Dict[str, List[float]] = {
            agent: [] for agent in self.env.possible_agents
        }
        self.episode_lengths: List[int] = []
        self.grid_loads: List[float] = []
        
    def _init_agents(self):
        """Initialize all agent instances"""
        obs_dim = self.num_stations * 2 + 3  # Base observation size
        
        # EV agents
        self.ev_agents = {}
        for i in range(self.num_evs):
            agent_id = f"ev_{i}"
            self.ev_agents[agent_id] = EVAgent(
                agent_id=agent_id,
                num_stations=self.num_stations,
                observation_dim=obs_dim
            )
        
        # CPO agents
        self.cpo_agents = {}
        for i in range(self.num_cpos):
            agent_id = f"cpo_{i}"
            station_indices = [
                s for s, c in self.env.station_cpo_map.items() if c == i
            ]
            self.cpo_agents[agent_id] = CPOAgent(
                agent_id=agent_id,
                num_stations=self.num_stations,
                station_indices=station_indices,
                observation_dim=obs_dim + len(station_indices)
            )
        
        # Grid agent
        self.grid_agent = GridAgent(
            agent_id="grid_0",
            observation_dim=obs_dim + 1
        )
        
    def get_action(self, agent_id: str, observation: np.ndarray, explore: bool = True):
        """Get action for an agent"""
        if agent_id.startswith("ev_"):
            return self.ev_agents[agent_id].select_action(observation, explore)
        elif agent_id.startswith("cpo_"):
            return self.cpo_agents[agent_id].select_action(observation, explore)
        elif agent_id.startswith("grid_"):
            return self.grid_agent.select_action(observation, explore)
        else:
            raise ValueError(f"Unknown agent: {agent_id}")
    
    def update_agent(
        self, 
        agent_id: str, 
        obs: np.ndarray, 
        action, 
        reward: float,
        next_obs: np.ndarray, 
        done: bool
    ):
        """Update an agent with experience"""
        if agent_id.startswith("ev_"):
            self.ev_agents[agent_id].update(obs, action, reward, next_obs, done)
        elif agent_id.startswith("cpo_"):
            self.cpo_agents[agent_id].update(obs, action, reward, next_obs, done)
        elif agent_id.startswith("grid_"):
            self.grid_agent.update(obs, action, reward, next_obs, done)
    
    def train(
        self, 
        num_episodes: int = 100, 
        verbose: bool = True,
        save_interval: int = 50
    ) -> Dict:
        """
        Train all agents for specified episodes
        
        Args:
            num_episodes: Number of training episodes
            verbose: Print progress
            save_interval: Episodes between saving checkpoints
            
        Returns:
            Training statistics
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Starting MARL Training")
            print(f"EVs: {self.num_evs}, Stations: {self.num_stations}, CPOs: {self.num_cpos}")
            print(f"Episodes: {num_episodes}, Max Steps: {self.max_steps}")
            print(f"{'='*60}\n")
        
        for episode in range(num_episodes):
            observations, _ = self.env.reset(seed=episode)
            
            # Reset agent states
            for agent in self.ev_agents.values():
                agent.reset()
            for agent in self.cpo_agents.values():
                agent.reset()
            self.grid_agent.reset()
            
            episode_reward = {agent: 0.0 for agent in self.env.possible_agents}
            step = 0
            
            while self.env.agents:
                # Collect actions from all agents
                actions = {}
                for agent_id in self.env.agents:
                    if agent_id in observations:
                        actions[agent_id] = self.get_action(
                            agent_id, 
                            observations[agent_id],
                            explore=True
                        )
                
                # Step environment
                next_observations, rewards, terminated, truncated, infos = self.env.step(actions)
                
                # Update agents
                for agent_id in self.env.possible_agents:
                    if agent_id in observations and agent_id in next_observations:
                        self.update_agent(
                            agent_id,
                            observations[agent_id],
                            actions.get(agent_id),
                            rewards.get(agent_id, 0.0),
                            next_observations[agent_id],
                            terminated.get(agent_id, False) or truncated.get(agent_id, False)
                        )
                        episode_reward[agent_id] += rewards.get(agent_id, 0.0)
                
                observations = next_observations
                step += 1
                
                # Track grid load
                if "grid_0" in infos:
                    self.grid_loads.append(infos["grid_0"].get("grid_load", 0.5))
            
            # Record episode metrics
            self.episode_lengths.append(step)
            for agent_id, total_reward in episode_reward.items():
                self.episode_rewards[agent_id].append(total_reward)
            
            # Progress logging
            if verbose and (episode + 1) % 10 == 0:
                avg_ev_reward = np.mean([
                    self.episode_rewards[f"ev_{i}"][-1] 
                    for i in range(self.num_evs)
                ])
                avg_cpo_reward = np.mean([
                    self.episode_rewards[f"cpo_{i}"][-1] 
                    for i in range(self.num_cpos)
                ])
                grid_reward = self.episode_rewards["grid_0"][-1]
                
                print(f"Episode {episode + 1:4d} | "
                      f"EV: {avg_ev_reward:7.2f} | "
                      f"CPO: {avg_cpo_reward:7.2f} | "
                      f"Grid: {grid_reward:7.2f} | "
                      f"Steps: {step}")
            
            # Save checkpoint
            if save_interval > 0 and (episode + 1) % save_interval == 0:
                self.save_checkpoint(f"checkpoint_ep{episode+1}")
        
        if verbose:
            print(f"\n{'='*60}")
            print("Training Complete!")
            print(f"{'='*60}")
        
        # Save final model
        self.save_checkpoint("final_model")
        
        return self.get_training_stats()
    
    def get_training_stats(self) -> Dict:
        """Get training statistics"""
        stats = {
            "total_episodes": len(self.episode_lengths),
            "avg_episode_length": np.mean(self.episode_lengths),
            "avg_grid_load": np.mean(self.grid_loads) if self.grid_loads else 0.0,
            "agents": {}
        }
        
        for agent_id, rewards in self.episode_rewards.items():
            if rewards:
                stats["agents"][agent_id] = {
                    "avg_reward": np.mean(rewards),
                    "max_reward": np.max(rewards),
                    "min_reward": np.min(rewards),
                    "final_reward": rewards[-1]
                }
        
        return stats
    
    def save_checkpoint(self, name: str):
        """Save training checkpoint"""
        checkpoint_dir = "checkpoints"
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        checkpoint = {
            "episode_rewards": self.episode_rewards,
            "episode_lengths": self.episode_lengths,
            "grid_loads": self.grid_loads,
            "timestamp": datetime.now().isoformat()
        }
        
        path = os.path.join(checkpoint_dir, f"{name}.json")
        with open(path, 'w') as f:
            json.dump(checkpoint, f)
        
        print(f"[*] Saved checkpoint to {path}")
        
        # Also save CPO agent weights for backend integration
        # Save the first CPO agent's weights as the canonical model for the API
        if self.cpo_agents:
            cpo_agent = list(self.cpo_agents.values())[0]
            weights_path = os.path.join(checkpoint_dir, "cpo_model.json")
            cpo_agent.save(weights_path)
            print(f"[*] Saved CPO model weights to {weights_path}")
    
    def plot_training_curves(self, save_path: str = None):
        """Plot training curves"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # EV rewards
        ax = axes[0, 0]
        for i in range(min(3, self.num_evs)):  # Plot first 3 EVs
            rewards = self.episode_rewards[f"ev_{i}"]
            ax.plot(rewards, alpha=0.7, label=f"EV {i}")
        ax.set_title("EV Agent Rewards")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Total Reward")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # CPO rewards
        ax = axes[0, 1]
        for i in range(self.num_cpos):
            rewards = self.episode_rewards[f"cpo_{i}"]
            ax.plot(rewards, label=f"CPO {i}")
        ax.set_title("CPO Agent Rewards (Revenue)")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Total Revenue")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Grid rewards
        ax = axes[1, 0]
        ax.plot(self.episode_rewards["grid_0"], color='green')
        ax.set_title("Grid Agent Rewards (Load Balancing)")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Total Reward")
        ax.grid(True, alpha=0.3)
        
        # Grid load over time
        ax = axes[1, 1]
        ax.plot(self.grid_loads[-1000:], alpha=0.7)  # Last 1000 steps
        ax.axhline(y=0.6, color='r', linestyle='--', label='Target (60%)')
        ax.axhline(y=0.85, color='orange', linestyle='--', label='Danger (85%)')
        ax.set_title("Grid Load (Last 1000 steps)")
        ax.set_xlabel("Step")
        ax.set_ylabel("Load %")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"[*] Saved training curves to {save_path}")
        else:
            plt.show()


def main():
    parser = argparse.ArgumentParser(description="Train MARL agents for EV charging")
    parser.add_argument("--episodes", type=int, default=100, help="Number of episodes")
    parser.add_argument("--evs", type=int, default=10, help="Number of EV agents")
    parser.add_argument("--stations", type=int, default=5, help="Number of stations")
    parser.add_argument("--cpos", type=int, default=2, help="Number of CPOs")
    parser.add_argument("--max-steps", type=int, default=288, help="Max steps per episode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--plot", action="store_true", help="Plot training curves")
    parser.add_argument("--save-plot", type=str, default=None, help="Save plot to path")
    
    args = parser.parse_args()
    
    # Create trainer
    trainer = MARLTrainer(
        num_evs=args.evs,
        num_stations=args.stations,
        num_cpos=args.cpos,
        max_steps=args.max_steps,
        seed=args.seed
    )
    
    # Train
    stats = trainer.train(
        num_episodes=args.episodes,
        verbose=True,
        save_interval=50
    )
    
    # Print final stats
    print("\nFinal Training Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Plot if requested
    if args.plot or args.save_plot:
        trainer.plot_training_curves(args.save_plot)


if __name__ == "__main__":
    main()
