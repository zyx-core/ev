"""
LSTM Model for Battery State of Charge (SoC) Prediction

This module implements a privacy-preserving LSTM neural network for predicting
EV battery State of Charge based on time-series data (voltage, current, temperature).
"""

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from typing import Tuple, Optional
import os


# Input features for the LSTM model
FEATURE_NAMES = ['voltage', 'current', 'temperature', 'power', 'energy_consumed']
NUM_FEATURES = len(FEATURE_NAMES)
SEQUENCE_LENGTH = 60  # 60 timesteps (e.g., 1 minute at 1Hz sampling)


def create_lstm_model(
    sequence_length: int = SEQUENCE_LENGTH,
    num_features: int = NUM_FEATURES,
    lstm_units: Tuple[int, int] = (64, 32),
    dropout_rate: float = 0.2,
    learning_rate: float = 0.001
) -> Sequential:
    """
    Create an LSTM model for battery SoC prediction.
    
    Args:
        sequence_length: Number of timesteps in input sequence
        num_features: Number of input features per timestep
        lstm_units: Tuple of units for each LSTM layer
        dropout_rate: Dropout rate for regularization
        learning_rate: Learning rate for Adam optimizer
    
    Returns:
        Compiled Keras Sequential model
    """
    model = Sequential([
        # First LSTM layer with return sequences for stacking
        LSTM(
            units=lstm_units[0],
            input_shape=(sequence_length, num_features),
            return_sequences=True,
            kernel_regularizer=tf.keras.regularizers.l2(0.001)
        ),
        BatchNormalization(),
        Dropout(dropout_rate),
        
        # Second LSTM layer
        LSTM(
            units=lstm_units[1],
            return_sequences=False,
            kernel_regularizer=tf.keras.regularizers.l2(0.001)
        ),
        BatchNormalization(),
        Dropout(dropout_rate),
        
        # Dense layers for final prediction
        Dense(16, activation='relu'),
        Dropout(dropout_rate / 2),
        
        # Output layer: Two values (SoC and SoH percentages 0-1)
        Dense(2, activation='sigmoid')
    ])
    
    # Compile with MSE loss and additional metrics
    model.compile(
        optimizer=Adam(learning_rate=learning_rate),
        loss='mse',
        metrics=['mae']
    )
    
    return model


def get_model_weights(model: Sequential) -> list:
    """Extract model weights for federated learning."""
    return model.get_weights()


def set_model_weights(model: Sequential, weights: list) -> None:
    """Set model weights from federated learning aggregation."""
    model.set_weights(weights)


def train_model(
    model: Sequential,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    epochs: int = 50,
    batch_size: int = 32,
    checkpoint_path: Optional[str] = None,
    verbose: int = 1
) -> dict:
    """
    Train the LSTM model on local data.
    
    Args:
        model: LSTM model to train
        X_train: Training sequences (samples, timesteps, features)
        y_train: Training targets (SoC values)
        X_val: Optional validation sequences
        y_val: Optional validation targets
        epochs: Number of training epochs
        batch_size: Batch size for training
        checkpoint_path: Optional path to save best model
        verbose: Verbosity level
    
    Returns:
        Training history dictionary
    """
    callbacks = []
    
    # Early stopping to prevent overfitting
    if X_val is not None:
        callbacks.append(EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=verbose
        ))
    
    # Model checkpointing
    if checkpoint_path:
        callbacks.append(ModelCheckpoint(
            filepath=checkpoint_path,
            monitor='val_loss' if X_val is not None else 'loss',
            save_best_only=True,
            verbose=verbose
        ))
    
    # Prepare validation data
    validation_data = (X_val, y_val) if X_val is not None else None
    
    # Train the model
    history = model.fit(
        X_train, y_train,
        validation_data=validation_data,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=verbose
    )
    
    return history.history


def evaluate_model(
    model: Sequential,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> dict:
    """
    Evaluate model performance on test data.
    
    Args:
        model: Trained LSTM model
        X_test: Test sequences
        y_test: Test targets
    
    Returns:
        Dictionary with evaluation metrics
    """
    results = model.evaluate(X_test, y_test, verbose=0)
    
    # Get predictions for additional metrics
    y_pred = model.predict(X_test, verbose=0)
    
    # Calculate additional metrics mapped over both outputs
    mse = np.mean((y_test - y_pred) ** 2, axis=0)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(y_test - y_pred), axis=0)
    
    # MAPE with handling for zero values
    mask = y_test != 0
    mape = np.zeros(2)
    for i in range(2):
        m = mask[:, i]
        if m.sum() > 0:
            mape[i] = np.mean(np.abs((y_test[m, i] - y_pred[m, i]) / y_test[m, i])) * 100
        else:
            mape[i] = float('inf')
    
    return {
        'loss': results[0],
        'keras_mae': results[1],
        'soc_rmse': float(rmse[0]),
        'soh_rmse': float(rmse[1]),
        'soc_mae': float(mae[0]),
        'soh_mae': float(mae[1]),
        'soc_mape': float(mape[0]),
        'soh_mape': float(mape[1])
    }


def save_model(model: Sequential, path: str) -> None:
    """Save model to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    model.save(path)


def load_trained_model(path: str) -> Sequential:
    """Load a trained model from disk."""
    return load_model(path)


# Model summary for debugging
if __name__ == "__main__":
    # Create and display model architecture
    model = create_lstm_model()
    model.summary()
    
    # Test with dummy data
    batch_size = 16
    X_dummy = np.random.randn(batch_size, SEQUENCE_LENGTH, NUM_FEATURES)
    y_dummy = np.random.rand(batch_size)  # SoC values between 0 and 1
    
    # Quick training test
    history = train_model(model, X_dummy, y_dummy, epochs=2, verbose=1)
    print(f"\nTraining completed. Final loss: {history['loss'][-1]:.4f}")
