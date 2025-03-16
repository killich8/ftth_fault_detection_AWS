import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import yaml

class OTDRDataProcessor:
    """
    Class for processing OTDR data for fault detection model
    """
    def __init__(self, config_path='../../config.yaml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Create processed data directory if it doesn't exist
        os.makedirs(self.config['data']['processed_data_path'], exist_ok=True)
    
    def load_data(self):
        """Load the raw OTDR data"""
        self.data = pd.read_csv(self.config['data']['raw_data_path'])
        print(f"Loaded data with shape: {self.data.shape}")
        return self.data
    
    def preprocess_data(self):
        """Preprocess the OTDR data for model training"""
        # Extract features and target
        X = self.data.drop(['Class', 'Position', 'Reflectance', 'loss'], axis=1)
        y = self.data['Class']
        
        # Add engineered features
        X = self._add_engineered_features(X)
        
        # Split data into train, validation, and test sets
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, 
            test_size=self.config['data']['train_test_split'] + self.config['data']['validation_split'],
            random_state=self.config['data']['random_seed'],
            stratify=y
        )
        
        # Further split temp data into validation and test sets
        test_size_adjusted = self.config['data']['train_test_split'] / (self.config['data']['train_test_split'] + self.config['data']['validation_split'])
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, 
            test_size=test_size_adjusted,
            random_state=self.config['data']['random_seed'],
            stratify=y_temp
        )
        
        # Save processed datasets
        self._save_datasets(X_train, y_train, X_val, y_val, X_test, y_test)
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def _add_engineered_features(self, X):
        """Add engineered features to improve model performance"""
        # Calculate statistical features from OTDR trace points
        trace_columns = [col for col in X.columns if col.startswith('P')]
        
        # Add max, min, mean, std, and range of trace points
        X['trace_max'] = X[trace_columns].max(axis=1)
        X['trace_min'] = X[trace_columns].min(axis=1)
        X['trace_mean'] = X[trace_columns].mean(axis=1)
        X['trace_std'] = X[trace_columns].std(axis=1)
        X['trace_range'] = X['trace_max'] - X['trace_min']
        
        # Add first and second derivatives to capture rate of change
        for i in range(1, len(trace_columns)):
            X[f'derivative_P{i}'] = X[f'P{i}'] - X[f'P{i-1}']
        
        for i in range(2, len(trace_columns)):
            X[f'second_derivative_P{i}'] = X[f'derivative_P{i}'] - X[f'derivative_P{i-1}']
        
        # Add SNR-related features
        X['snr_to_mean_ratio'] = X['SNR'] / X['trace_mean']
        
        return X
    
    def _save_datasets(self, X_train, y_train, X_val, y_val, X_test, y_test):
        """Save processed datasets to disk"""
        # Create directories
        processed_dir = self.config['data']['processed_data_path']
        
        # Save datasets
        X_train.to_csv(f"{processed_dir}/X_train.csv", index=False)
        y_train.to_csv(f"{processed_dir}/y_train.csv", index=False)
        X_val.to_csv(f"{processed_dir}/X_val.csv", index=False)
        y_val.to_csv(f"{processed_dir}/y_val.csv", index=False)
        X_test.to_csv(f"{processed_dir}/X_test.csv", index=False)
        y_test.to_csv(f"{processed_dir}/y_test.csv", index=False)
        
        print(f"Saved processed datasets to {processed_dir}")
        print(f"Train set: {X_train.shape}, Validation set: {X_val.shape}, Test set: {X_test.shape}")

if __name__ == "__main__":
    # Initialize data processor
    processor = OTDRDataProcessor(config_path='../../config.yaml')
    
    # Load and preprocess data
    processor.load_data()
    X_train, y_train, X_val, y_val, X_test, y_test = processor.preprocess_data()
    
    print("Data preprocessing completed successfully!")
