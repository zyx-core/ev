"""
Flower Federated Learning Server

Aggregation server for privacy-preserving LSTM model training.
Uses FedAvg strategy to combine model updates from distributed clients.
"""

import flwr as fl
from flwr.server.strategy import FedAvg
from flwr.common import Metrics
from typing import List, Tuple, Dict, Optional
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.lstm_soc import create_lstm_model, save_model


def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    """
    Weighted average of metrics from multiple clients.
    
    Args:
        metrics: List of (num_examples, metrics_dict) tuples
    
    Returns:
        Weighted average metrics
    """
    # Extract metric values
    total_examples = sum(num_examples for num_examples, _ in metrics)
    
    if total_examples == 0:
        return {}
    
    # Calculate weighted averages for common metrics
    weighted_metrics = {}
    metric_names = ['loss', 'mae', 'mape'] if metrics else []
    
    for name in metric_names:
        values = [
            num_examples * m.get(name, 0) 
            for num_examples, m in metrics 
            if name in m
        ]
        if values:
            weighted_metrics[name] = sum(values) / total_examples
    
    return weighted_metrics


class SoCPredictionStrategy(FedAvg):
    """
    Custom FedAvg strategy for SoC prediction model.
    
    Extends the standard FedAvg with model checkpointing
    and custom aggregation logic.
    """
    
    def __init__(
        self,
        fraction_fit: float = 0.3,
        fraction_evaluate: float = 0.2,
        min_fit_clients: int = 2,
        min_evaluate_clients: int = 2,
        min_available_clients: int = 2,
        checkpoint_dir: str = "checkpoints",
        **kwargs
    ):
        """
        Initialize the strategy.
        
        Args:
            fraction_fit: Fraction of clients for training
            fraction_evaluate: Fraction of clients for evaluation
            min_fit_clients: Minimum clients for training round
            min_evaluate_clients: Minimum clients for evaluation
            min_available_clients: Minimum available clients to start
            checkpoint_dir: Directory to save model checkpoints
        """
        super().__init__(
            fraction_fit=fraction_fit,
            fraction_evaluate=fraction_evaluate,
            min_fit_clients=min_fit_clients,
            min_evaluate_clients=min_evaluate_clients,
            min_available_clients=min_available_clients,
            evaluate_metrics_aggregation_fn=weighted_average,
            fit_metrics_aggregation_fn=weighted_average,
            **kwargs
        )
        
        self.checkpoint_dir = checkpoint_dir
        self.best_loss = float('inf')
        self.round_losses = []
        
        # Create checkpoint directory
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Create initial model for weight shapes
        self.model = create_lstm_model()
    
    def aggregate_fit(self, server_round, results, failures):
        """
        Aggregate model updates after training round.
        
        Also saves checkpoints when loss improves.
        """
        aggregated = super().aggregate_fit(server_round, results, failures)
        
        if aggregated is not None:
            parameters, metrics = aggregated
            
            # Track loss for this round
            if metrics and 'loss' in metrics:
                current_loss = metrics['loss']
                self.round_losses.append(current_loss)
                
                print(f"\n[Round {server_round}] Aggregated loss: {current_loss:.6f}")
                
                # Save checkpoint if loss improved
                if current_loss < self.best_loss:
                    self.best_loss = current_loss
                    self._save_checkpoint(parameters, server_round)
                    print(f"[Round {server_round}] New best model saved!")
        
        return aggregated
    
    def _save_checkpoint(self, parameters, round_num):
        """Save model checkpoint."""
        # Convert parameters to weights
        weights = fl.common.parameters_to_ndarrays(parameters)
        
        # Create model and set weights
        model = create_lstm_model()
        model.set_weights(weights)
        
        # Save model
        checkpoint_path = os.path.join(
            self.checkpoint_dir, f"model_round_{round_num}.keras"
        )
        save_model(model, checkpoint_path)
        
        # Also save as best model
        best_path = os.path.join(self.checkpoint_dir, "best_model.keras")
        save_model(model, best_path)


def start_server(
    server_address: str = "[::]:8080",
    num_rounds: int = 10,
    min_clients: int = 2,
    fraction_fit: float = 0.5,
    checkpoint_dir: str = "checkpoints"
) -> None:
    """
    Start the Flower FL server.
    
    Args:
        server_address: Server address and port
        num_rounds: Number of FL training rounds
        min_clients: Minimum clients required
        fraction_fit: Fraction of clients per round
        checkpoint_dir: Directory for model checkpoints
    """
    print("=" * 60)
    print("    IEVC-eco Federated Learning Server")
    print("    Privacy-Preserving SoC Prediction Model Training")
    print("=" * 60)
    print(f"\nServer address: {server_address}")
    print(f"Training rounds: {num_rounds}")
    print(f"Minimum clients: {min_clients}")
    print(f"Client fraction per round: {fraction_fit}")
    print(f"Checkpoint directory: {checkpoint_dir}")
    print("=" * 60)
    
    # Create initial model to get weight shapes
    initial_model = create_lstm_model()
    initial_weights = initial_model.get_weights()
    initial_parameters = fl.common.ndarrays_to_parameters(initial_weights)
    
    # Create strategy
    strategy = SoCPredictionStrategy(
        fraction_fit=fraction_fit,
        fraction_evaluate=0.3,
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
        checkpoint_dir=checkpoint_dir,
        initial_parameters=initial_parameters
    )
    
    # Start server
    print("\nWaiting for clients to connect...")
    
    fl.server.start_server(
        server_address=server_address,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy
    )
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print(f"Best model saved to: {checkpoint_dir}/best_model.keras")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FL Server for SoC Prediction")
    parser.add_argument("--address", type=str, default="[::]:8080",
                        help="Server address")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of training rounds")
    parser.add_argument("--min-clients", type=int, default=2,
                        help="Minimum clients required")
    parser.add_argument("--fraction-fit", type=float, default=0.5,
                        help="Fraction of clients per round")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints",
                        help="Checkpoint directory")
    
    args = parser.parse_args()
    
    start_server(
        server_address=args.address,
        num_rounds=args.rounds,
        min_clients=args.min_clients,
        fraction_fit=args.fraction_fit,
        checkpoint_dir=args.checkpoint_dir
    )
