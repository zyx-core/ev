"""
Federated Learning Demo

Quick demonstration of the FL training pipeline:
1. Starts the FL server
2. Launches multiple simulated clients
3. Trains the LSTM model in a privacy-preserving manner
4. Saves the trained model
"""

import subprocess
import sys
import time
import os
import threading
import signal


def run_demo(
    num_clients: int = 5,
    num_rounds: int = 3,
    sessions_per_client: int = 10,
    local_epochs: int = 3
):
    """
    Run a complete FL training demo.
    
    Args:
        num_clients: Number of simulated clients
        num_rounds: Number of FL training rounds
        sessions_per_client: Driving sessions per client
        local_epochs: Local epochs per round
    """
    print("=" * 60)
    print("    IEVC-eco Federated Learning Demo")
    print("    Privacy-Preserving Battery SoC Prediction")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  - Clients: {num_clients}")
    print(f"  - FL Rounds: {num_rounds}")
    print(f"  - Sessions per client: {sessions_per_client}")
    print(f"  - Local epochs per round: {local_epochs}")
    print("=" * 60)
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    federated_dir = os.path.join(script_dir, "federated")
    
    server_script = os.path.join(federated_dir, "server.py")
    client_script = os.path.join(federated_dir, "client.py")
    
    # Check if scripts exist
    if not os.path.exists(server_script):
        print(f"Error: Server script not found at {server_script}")
        return
    
    if not os.path.exists(client_script):
        print(f"Error: Client script not found at {client_script}")
        return
    
    # Start the server
    print("\n[Demo] Starting FL server...")
    server_process = subprocess.Popen(
        [
            sys.executable, server_script,
            "--rounds", str(num_rounds),
            "--min-clients", str(min(2, num_clients)),
            "--fraction-fit", "0.8"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Give server time to start
    time.sleep(3)
    
    # Function to print server output
    def print_server_output():
        for line in server_process.stdout:
            print(f"[Server] {line}", end="")
    
    # Start server output thread
    server_thread = threading.Thread(target=print_server_output, daemon=True)
    server_thread.start()
    
    # Start clients
    print(f"\n[Demo] Starting {num_clients} simulated clients...")
    client_processes = []
    
    for client_id in range(num_clients):
        print(f"[Demo] Starting client {client_id}...")
        client_process = subprocess.Popen(
            [
                sys.executable, client_script,
                "--server", "127.0.0.1:8080",
                "--client-id", str(client_id),
                "--sessions", str(sessions_per_client),
                "--epochs", str(local_epochs)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        client_processes.append(client_process)
        time.sleep(0.5)  # Stagger client starts
    
    # Wait for clients to complete
    print("\n[Demo] Training in progress...")
    for i, p in enumerate(client_processes):
        exit_code = p.wait()
        print(f"[Demo] Client {i} finished (exit code: {exit_code})")
    
    # Wait for server to finish
    print("\n[Demo] Waiting for server to complete aggregation...")
    server_process.wait(timeout=30)
    
    print("\n" + "=" * 60)
    print("    Demo Complete!")
    print("=" * 60)
    print("\nTrained model saved to: ml/checkpoints/best_model.keras")
    print("\nTo use the model for predictions:")
    print("  from models.lstm_soc import load_trained_model")
    print("  model = load_trained_model('checkpoints/best_model.keras')")
    print("  prediction = model.predict(battery_sequence)")


def quick_test():
    """
    Quick test without full FL training.
    Tests model creation and data generation.
    """
    print("=" * 60)
    print("    Quick Test: Model & Data Generation")
    print("=" * 60)
    
    # Test model creation
    print("\n1. Testing LSTM model creation...")
    from models.lstm_soc import create_lstm_model
    model = create_lstm_model()
    print(f"   Model created with {model.count_params():,} parameters")
    
    # Test data generation
    print("\n2. Testing battery data generation...")
    from data.data_generator import generate_client_dataset
    X, y = generate_client_dataset(client_id=0, num_sessions=3)
    print(f"   Generated {len(X)} samples")
    print(f"   Input shape: {X.shape}")
    print(f"   Target range: [{y.min():.2f}, {y.max():.2f}]")
    
    # Quick training test
    print("\n3. Testing model training (2 epochs)...")
    from models.lstm_soc import train_model, evaluate_model
    
    # Split data
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    history = train_model(model, X_train, y_train, epochs=2, verbose=1)
    print(f"   Final loss: {history['loss'][-1]:.4f}")
    
    # Evaluate
    print("\n4. Testing model evaluation...")
    metrics = evaluate_model(model, X_test, y_test)
    print(f"   SoC RMSE: {metrics['soc_rmse']:.4f}")
    print(f"   SoH RMSE: {metrics['soh_rmse']:.4f}")
    print(f"   SoC MAE:  {metrics['soc_mae']:.4f}")
    print(f"   SoH MAE:  {metrics['soh_mae']:.4f}")
    
    print("\n" + "=" * 60)
    print("    All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FL Demo")
    parser.add_argument("--quick", action="store_true",
                        help="Run quick test only")
    parser.add_argument("--clients", type=int, default=3,
                        help="Number of clients")
    parser.add_argument("--rounds", type=int, default=3,
                        help="FL rounds")
    
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    else:
        run_demo(
            num_clients=args.clients,
            num_rounds=args.rounds
        )
