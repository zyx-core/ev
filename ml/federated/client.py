"""
Flower Federated Learning Client

Client for local model training without sharing raw battery data.
Only model weight updates are sent to the aggregation server.
"""

import flwr as fl
from flwr.client import NumPyClient
import numpy as np
import sys
import os
from typing import Tuple, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.lstm_soc import create_lstm_model, train_model, evaluate_model
from data.data_generator import generate_client_dataset


class SoCPredictionClient(NumPyClient):
    """
    Federated Learning client for SoC prediction.
    
    Performs local training on private battery data and
    sends only model weight updates to the server.
    """
    
    def __init__(
        self,
        client_id: int,
        num_sessions: int = 20,
        sequence_length: int = 60,
        local_epochs: int = 5,
        batch_size: int = 32
    ):
        """
        Initialize the FL client.
        
        Args:
            client_id: Unique identifier for this client
            num_sessions: Number of driving sessions to simulate
            sequence_length: Input sequence length
            local_epochs: Epochs for local training per round
            batch_size: Batch size for local training
        """
        self.client_id = client_id
        self.local_epochs = local_epochs
        self.batch_size = batch_size
        
        print(f"[Client {client_id}] Initializing...")
        
        # Create local model
        self.model = create_lstm_model()
        
        # Generate local dataset (privacy-preserving: data stays local)
        print(f"[Client {client_id}] Generating local battery data...")
        X, y = generate_client_dataset(
            client_id, num_sessions, sequence_length
        )
        
        # Split into train/validation/test
        n = len(X)
        train_end = int(0.7 * n)
        val_end = int(0.85 * n)
        
        self.X_train = X[:train_end]
        self.y_train = y[:train_end]
        self.X_val = X[train_end:val_end]
        self.y_val = y[train_end:val_end]
        self.X_test = X[val_end:]
        self.y_test = y[val_end:]
        
        print(f"[Client {client_id}] Dataset ready: "
              f"train={len(self.X_train)}, val={len(self.X_val)}, test={len(self.X_test)}")
    
    def get_parameters(self, config: Dict) -> list:
        """Return current model weights."""
        return self.model.get_weights()
    
    def set_parameters(self, parameters: list) -> None:
        """Set model weights from server."""
        self.model.set_weights(parameters)
    
    def fit(
        self, 
        parameters: list, 
        config: Dict
    ) -> Tuple[list, int, Dict]:
        """
        Train model on local data.
        
        Args:
            parameters: Model weights from server
            config: Training configuration from server
        
        Returns:
            Tuple of (updated_weights, num_samples, metrics)
        """
        # Set weights from server
        self.set_parameters(parameters)
        
        # Get training config
        epochs = config.get("local_epochs", self.local_epochs)
        batch_size = config.get("batch_size", self.batch_size)
        
        print(f"[Client {self.client_id}] Training for {epochs} epochs...")
        
        # Local training (data never leaves the client!)
        history = train_model(
            self.model,
            self.X_train, self.y_train,
            self.X_val, self.y_val,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0
        )
        
        # Get final metrics
        final_loss = history['loss'][-1]
        final_mae = history['mae'][-1] if 'mae' in history else 0
        
        print(f"[Client {self.client_id}] Training complete. "
              f"Loss: {final_loss:.4f}, MAE: {final_mae:.4f}")
        
        # Return updated weights and metrics (NOT the data!)
        return (
            self.get_parameters({}),
            len(self.X_train),
            {
                "loss": float(final_loss),
                "mae": float(final_mae)
            }
        )
    
    def evaluate(
        self, 
        parameters: list, 
        config: Dict
    ) -> Tuple[float, int, Dict]:
        """
        Evaluate model on local test data.
        
        Args:
            parameters: Model weights from server
            config: Evaluation configuration
        
        Returns:
            Tuple of (loss, num_samples, metrics)
        """
        # Set weights from server
        self.set_parameters(parameters)
        
        # Evaluate on local test set
        metrics = evaluate_model(self.model, self.X_test, self.y_test)
        
        print(f"[Client {self.client_id}] Evaluation - "
              f"Loss: {metrics['loss']:.4f}, MAE: {metrics['mae']:.4f}, "
              f"MAPE: {metrics['mape']:.2f}%")
        
        return (
            float(metrics['loss']),
            len(self.X_test),
            {
                "mae": float(metrics['mae']),
                "mape": float(metrics['mape']),
                "rmse": float(metrics['rmse'])
            }
        )


def start_client(
    server_address: str = "127.0.0.1:8080",
    client_id: int = 0,
    num_sessions: int = 20,
    local_epochs: int = 5
) -> None:
    """
    Start a Flower FL client.
    
    Args:
        server_address: FL server address
        client_id: Unique client identifier
        num_sessions: Driving sessions to simulate
        local_epochs: Epochs per FL round
    """
    print("=" * 50)
    print(f"    IEVC-eco FL Client {client_id}")
    print(f"    Connecting to: {server_address}")
    print("=" * 50)
    
    # Create client
    client = SoCPredictionClient(
        client_id=client_id,
        num_sessions=num_sessions,
        local_epochs=local_epochs
    )
    
    # Start client
    print(f"\n[Client {client_id}] Connecting to server...")
    fl.client.start_client(
        server_address=server_address,
        client=client
    )
    
    print(f"\n[Client {client_id}] Training complete!")


def simulate_clients(
    server_address: str = "127.0.0.1:8080",
    num_clients: int = 5,
    num_sessions: int = 20,
    local_epochs: int = 5
) -> None:
    """
    Simulate multiple FL clients in sequence.
    Useful for testing without multi-processing.
    
    Note: In production, each client would run on a separate device.
    """
    import multiprocessing
    import time
    
    print(f"\nStarting {num_clients} simulated clients...")
    
    processes = []
    
    for client_id in range(num_clients):
        p = multiprocessing.Process(
            target=start_client,
            args=(server_address, client_id, num_sessions, local_epochs)
        )
        p.start()
        processes.append(p)
        time.sleep(1)  # Stagger client starts
    
    # Wait for all clients to complete
    for p in processes:
        p.join()
    
    print("\nAll clients completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FL Client for SoC Prediction")
    parser.add_argument("--server", type=str, default="127.0.0.1:8080",
                        help="Server address")
    parser.add_argument("--client-id", type=int, default=0,
                        help="Client ID")
    parser.add_argument("--sessions", type=int, default=20,
                        help="Number of driving sessions")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Local epochs per round")
    parser.add_argument("--simulate", type=int, default=0,
                        help="Simulate N clients (0 = single client)")
    
    args = parser.parse_args()
    
    if args.simulate > 0:
        simulate_clients(
            server_address=args.server,
            num_clients=args.simulate,
            num_sessions=args.sessions,
            local_epochs=args.epochs
        )
    else:
        start_client(
            server_address=args.server,
            client_id=args.client_id,
            num_sessions=args.sessions,
            local_epochs=args.epochs
        )
