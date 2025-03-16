import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
import yaml
import pickle
import json

class OTDRFaultDetector:
    """
    Class for making predictions on OTDR traces for fault detection
    """
    def __init__(self, config_path='../../config.yaml', model_path=None):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Set default model path if not provided
        if model_path is None:
            model_path = os.path.join(self.config['model']['model_save_path'], 'best_model.h5')
        
        # Load the model
        self.model = self.load_model(model_path)
        
        # Class names for reference
        self.class_names = ['Normal', 'Fiber Tapping', 'Bad Splice', 'Bending Event', 
                           'Dirty Connector', 'Fiber Cut', 'PC Connector', 'Reflector']
    
    def load_model(self, model_path):
        """Load the trained model"""
        try:
            model = load_model(model_path)
            print(f"Model loaded from {model_path}")
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            # Try loading as pickle if h5 fails
            try:
                model_pkl_path = model_path.replace('.h5', '.pkl')
                with open(model_pkl_path, 'rb') as f:
                    model = pickle.load(f)
                print(f"Model loaded from {model_pkl_path}")
                return model
            except Exception as e2:
                print(f"Error loading model from pickle: {e2}")
                return None
    
    def preprocess_input(self, data):
        """Preprocess input data for prediction"""
        # Check if data is a dictionary or DataFrame
        if isinstance(data, dict):
            # Convert dictionary to DataFrame
            df = pd.DataFrame([data])
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Input data must be a dictionary or DataFrame")
        
        # Ensure all required columns are present
        required_columns = ['SNR'] + [f'P{i}' for i in range(1, 31)]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Add engineered features (similar to preprocessing in training)
        trace_columns = [col for col in df.columns if col.startswith('P')]
        
        # Add statistical features
        df['trace_max'] = df[trace_columns].max(axis=1)
        df['trace_min'] = df[trace_columns].min(axis=1)
        df['trace_mean'] = df[trace_columns].mean(axis=1)
        df['trace_std'] = df[trace_columns].std(axis=1)
        df['trace_range'] = df['trace_max'] - df['trace_min']
        
        # Add derivatives
        for i in range(1, len(trace_columns)):
            df[f'derivative_P{i}'] = df[f'P{i}'] - df[f'P{i-1}']
        
        for i in range(2, len(trace_columns)):
            df[f'second_derivative_P{i}'] = df[f'derivative_P{i}'] - df[f'derivative_P{i-1}']
        
        # Add SNR-related features
        df['snr_to_mean_ratio'] = df['SNR'] / df['trace_mean']
        
        # Prepare data based on model type
        model_type = self.config['model']['model_type']
        
        if model_type in ['lstm', 'cnn']:
            # Extract OTDR trace points for sequence input
            trace_cols = [col for col in df.columns if col.startswith('P') and len(col) <= 3]
            X_seq = df[trace_cols].values.reshape(df.shape[0], len(trace_cols), 1)
            
            # Extract other features
            other_cols = [col for col in df.columns if col not in trace_cols]
            X_other = df[other_cols].values
            
            return [X_seq, X_other]
        else:
            # For dense neural network, return the entire DataFrame
            return df
    
    def predict(self, data):
        """Make prediction on input data"""
        # Preprocess input data
        X = self.preprocess_input(data)
        
        # Make prediction
        y_pred = self.model.predict(X)
        
        # Get predicted class and probability
        pred_class = np.argmax(y_pred, axis=1)[0]
        pred_prob = float(y_pred[0][pred_class])
        
        # Create prediction result
        result = {
            'fault_type': int(pred_class),
            'fault_name': self.class_names[pred_class],
            'confidence': pred_prob,
            'all_probabilities': {
                self.class_names[i]: float(y_pred[0][i]) for i in range(len(self.class_names))
            }
        }
        
        return result
    
    def batch_predict(self, data_list):
        """Make predictions on a batch of input data"""
        results = []
        
        for data in data_list:
            result = self.predict(data)
            results.append(result)
        
        return results

# Example usage
if __name__ == "__main__":
    # Initialize detector
    detector = OTDRFaultDetector(config_path='../../config.yaml')
    
    # Example input data (replace with actual OTDR trace)
    example_data = {
        'SNR': 15.0,
        'P1': 0.8, 'P2': 0.7, 'P3': 0.6, 'P4': 0.5, 'P5': 0.4,
        'P6': 0.3, 'P7': 0.2, 'P8': 0.1, 'P9': 0.0, 'P10': 0.1,
        'P11': 0.2, 'P12': 0.3, 'P13': 0.4, 'P14': 0.5, 'P15': 0.6,
        'P16': 0.7, 'P17': 0.8, 'P18': 0.9, 'P19': 1.0, 'P20': 0.9,
        'P21': 0.8, 'P22': 0.7, 'P23': 0.6, 'P24': 0.5, 'P25': 0.4,
        'P26': 0.3, 'P27': 0.2, 'P28': 0.1, 'P29': 0.0, 'P30': 0.1
    }
    
    # Make prediction
    result = detector.predict(example_data)
    
    # Print result
    print(json.dumps(result, indent=2))
