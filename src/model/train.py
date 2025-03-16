import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, LSTM, Input, Bidirectional, Conv1D, MaxPooling1D, Flatten, concatenate
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import yaml
import pickle
import sys

sys.path.append('../../')
from src.data_processing.preprocess import OTDRDataProcessor

class OTDRFaultDetectionModel:
    """
    Class for building, training and evaluating OTDR fault detection models
    """
    def __init__(self, config_path='../../config.yaml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Create model directory if it doesn't exist
        os.makedirs(self.config['model']['model_save_path'], exist_ok=True)
        
        # Set random seeds for reproducibility
        np.random.seed(self.config['data']['random_seed'])
        tf.random.set_seed(self.config['data']['random_seed'])
    
    def load_processed_data(self):
        """Load the processed data for model training"""
        processed_dir = self.config['data']['processed_data_path']
        
        self.X_train = pd.read_csv(f"{processed_dir}/X_train.csv")
        self.y_train = pd.read_csv(f"{processed_dir}/y_train.csv").values.ravel()
        self.X_val = pd.read_csv(f"{processed_dir}/X_val.csv")
        self.y_val = pd.read_csv(f"{processed_dir}/y_val.csv").values.ravel()
        self.X_test = pd.read_csv(f"{processed_dir}/X_test.csv")
        self.y_test = pd.read_csv(f"{processed_dir}/y_test.csv").values.ravel()
        
        print(f"Loaded processed data:")
        print(f"Train set: {self.X_train.shape}, Validation set: {self.X_val.shape}, Test set: {self.X_test.shape}")
        
        return self.X_train, self.y_train, self.X_val, self.y_val, self.X_test, self.y_test
    
    def build_model(self, model_type=None):
        """Build the neural network model based on configuration"""
        if model_type is None:
            model_type = self.config['model']['model_type']
        
        num_classes = len(np.unique(self.y_train))
        input_dim = self.X_train.shape[1]
        
        if model_type == 'lstm':
            # Reshape data for LSTM
            # Extract only the OTDR trace points (P1-P30)
            trace_columns = [col for col in self.X_train.columns if col.startswith('P') and len(col) <= 3]
            
            # Create sequence data for LSTM
            X_train_seq = self.X_train[trace_columns].values.reshape(self.X_train.shape[0], len(trace_columns), 1)
            X_val_seq = self.X_val[trace_columns].values.reshape(self.X_val.shape[0], len(trace_columns), 1)
            X_test_seq = self.X_test[trace_columns].values.reshape(self.X_test.shape[0], len(trace_columns), 1)
            
            # Create additional features input
            other_columns = [col for col in self.X_train.columns if col not in trace_columns]
            X_train_other = self.X_train[other_columns].values
            X_val_other = self.X_val[other_columns].values
            X_test_other = self.X_test[other_columns].values
            
            # LSTM input
            sequence_input = Input(shape=(len(trace_columns), 1), name='sequence_input')
            lstm_layer = Bidirectional(LSTM(128, return_sequences=True))(sequence_input)
            lstm_layer = Dropout(0.3)(lstm_layer)
            lstm_layer = Bidirectional(LSTM(64))(lstm_layer)
            lstm_layer = Dropout(0.3)(lstm_layer)
            
            # Other features input
            other_input = Input(shape=(len(other_columns),), name='other_input')
            other_layer = Dense(64, activation='relu')(other_input)
            other_layer = Dropout(0.3)(other_layer)
            
            # Combine both inputs
            combined = concatenate([lstm_layer, other_layer])
            
            # Output layers
            dense_layer = Dense(64, activation='relu')(combined)
            dense_layer = Dropout(0.3)(dense_layer)
            output_layer = Dense(num_classes, activation='softmax')(dense_layer)
            
            # Create model
            model = Model(inputs=[sequence_input, other_input], outputs=output_layer)
            
            # Compile model
            model.compile(
                loss='sparse_categorical_crossentropy',
                optimizer=Adam(learning_rate=self.config['model']['learning_rate']),
                metrics=['accuracy']
            )
            
            self.model = model
            self.X_train_prepared = [X_train_seq, X_train_other]
            self.X_val_prepared = [X_val_seq, X_val_other]
            self.X_test_prepared = [X_test_seq, X_test_other]
            
        elif model_type == 'cnn':
            # Reshape data for CNN
            trace_columns = [col for col in self.X_train.columns if col.startswith('P') and len(col) <= 3]
            
            # Create sequence data for CNN
            X_train_seq = self.X_train[trace_columns].values.reshape(self.X_train.shape[0], len(trace_columns), 1)
            X_val_seq = self.X_val[trace_columns].values.reshape(self.X_val.shape[0], len(trace_columns), 1)
            X_test_seq = self.X_test[trace_columns].values.reshape(self.X_test.shape[0], len(trace_columns), 1)
            
            # Create additional features input
            other_columns = [col for col in self.X_train.columns if col not in trace_columns]
            X_train_other = self.X_train[other_columns].values
            X_val_other = self.X_val[other_columns].values
            X_test_other = self.X_test[other_columns].values
            
            # CNN input
            sequence_input = Input(shape=(len(trace_columns), 1), name='sequence_input')
            conv_layer = Conv1D(filters=64, kernel_size=3, activation='relu')(sequence_input)
            conv_layer = MaxPooling1D(pool_size=2)(conv_layer)
            conv_layer = Conv1D(filters=128, kernel_size=3, activation='relu')(conv_layer)
            conv_layer = MaxPooling1D(pool_size=2)(conv_layer)
            conv_layer = Flatten()(conv_layer)
            conv_layer = Dropout(0.3)(conv_layer)
            
            # Other features input
            other_input = Input(shape=(len(other_columns),), name='other_input')
            other_layer = Dense(64, activation='relu')(other_input)
            other_layer = Dropout(0.3)(other_layer)
            
            # Combine both inputs
            combined = concatenate([conv_layer, other_layer])
            
            # Output layers
            dense_layer = Dense(64, activation='relu')(combined)
            dense_layer = Dropout(0.3)(dense_layer)
            output_layer = Dense(num_classes, activation='softmax')(dense_layer)
            
            # Create model
            model = Model(inputs=[sequence_input, other_input], outputs=output_layer)
            
            # Compile model
            model.compile(
                loss='sparse_categorical_crossentropy',
                optimizer=Adam(learning_rate=self.config['model']['learning_rate']),
                metrics=['accuracy']
            )
            
            self.model = model
            self.X_train_prepared = [X_train_seq, X_train_other]
            self.X_val_prepared = [X_val_seq, X_val_other]
            self.X_test_prepared = [X_test_seq, X_test_other]
            
        else:  # Default to a simple dense neural network
            model = Sequential()
            model.add(Dense(128, input_dim=input_dim, activation='relu'))
            model.add(Dropout(0.3))
            model.add(Dense(64, activation='relu'))
            model.add(Dropout(0.3))
            model.add(Dense(num_classes, activation='softmax'))
            
            model.compile(
                loss='sparse_categorical_crossentropy',
                optimizer=Adam(learning_rate=self.config['model']['learning_rate']),
                metrics=['accuracy']
            )
            
            self.model = model
            self.X_train_prepared = self.X_train
            self.X_val_prepared = self.X_val
            self.X_test_prepared = self.X_test
        
        print(f"Built {model_type} model:")
        self.model.summary()
        
        return self.model
    
    def train_model(self):
        """Train the model with early stopping and model checkpointing"""
        # Define callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=self.config['model']['early_stopping_patience'],
            restore_best_weights=True
        )
        
        model_checkpoint = ModelCheckpoint(
            filepath=os.path.join(self.config['model']['model_save_path'], 'best_model.h5'),
            monitor='val_loss',
            save_best_only=True
        )
        
        # Train the model
        history = self.model.fit(
            self.X_train_prepared,
            self.y_train,
            validation_data=(self.X_val_prepared, self.y_val),
            epochs=self.config['model']['epochs'],
            batch_size=self.config['model']['batch_size'],
            callbacks=[early_stopping, model_checkpoint],
            verbose=1
        )
        
        # Save training history
        with open(os.path.join(self.config['model']['model_save_path'], 'training_history.pkl'), 'wb') as f:
            pickle.dump(history.history, f)
        
        return history
    
    def evaluate_model(self):
        """Evaluate the model on test data and generate performance metrics"""
        # Evaluate on test data
        test_loss, test_accuracy = self.model.evaluate(self.X_test_prepared, self.y_test, verbose=0)
        print(f"Test Loss: {test_loss:.4f}")
        print(f"Test Accuracy: {test_accuracy:.4f}")
        
        # Generate predictions
        y_pred = self.model.predict(self.X_test_prepared)
        y_pred_classes = np.argmax(y_pred, axis=1)
        
        # Classification report
        class_names = ['Normal', 'Fiber Tapping', 'Bad Splice', 'Bending Event', 
                       'Dirty Connector', 'Fiber Cut', 'PC Connector', 'Reflector']
        report = classification_report(self.y_test, y_pred_classes, target_names=class_names)
        print("Classification Report:")
        print(report)
        
        # Save classification report to file
        with open(os.path.join(self.config['model']['model_save_path'], 'classification_report.txt'), 'w') as f:
            f.write(report)
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, y_pred_classes)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig(os.path.join(self.config['model']['model_save_path'], 'confusion_matrix.png'))
        
        # Plot training history if available
        try:
            with open(os.path.join(self.config['model']['model_save_path'], 'training_history.pkl'), 'rb') as f:
                history = pickle.load(f)
            
            # Plot accuracy
            plt.figure(figsize=(12, 5))
            plt.subplot(1, 2, 1)
            plt.plot(history['accuracy'], label='Training Accuracy')
            plt.plot(history['val_accuracy'], label='Validation Accuracy')
            plt.xlabel('Epoch')
            plt.ylabel('Accuracy')
            plt.title('Training and Validation Accuracy')
            plt.legend()
            
            # Plot loss
            plt.subplot(1, 2, 2)
            plt.plot(history['loss'], label='Training Loss')
            plt.plot(history['val_loss'], label='Validation Loss')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.title('Training and Validation Loss')
            plt.legend()
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.config['model']['model_save_path'], 'training_history.png'))
        except:
            print("Could not plot training history.")
        
        return test_accuracy, report
    
    def save_model(self):
        """Save the trained model for deployment"""
        # Save the model architecture and weights
        model_path = os.path.join(self.config['model']['model_save_path'], 'best_model.h5')
        self.model.save(model_path)
        
        # Save as pickle for easier loading in production
        model_pkl_path = os.path.join(self.config['model']['model_save_path'], 'best_model.pkl')
        with open(model_pkl_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"Model saved to {model_path} and {model_pkl_path}")
        
        return model_path, model_pkl_path

if __name__ == "__main__":
    # Process data if not already processed
    if not os.path.exists(os.path.join('../../data/processed', 'X_train.csv')):
        processor = OTDRDataProcessor(config_path='../../config.yaml')
        processor.load_data()
        processor.preprocess_data()
    
    # Initialize model
    model = OTDRFaultDetectionModel(config_path='../../config.yaml')
    
    # Load processed data
    model.load_processed_data()
    
    # Build model
    model.build_model()
    
    # Train model
    history = model.train_model()
    
    # Evaluate model
    accuracy, report = model.evaluate_model()
    
    # Save model
    model_path, model_pkl_path = model.save_model()
    
    print(f"Model training and evaluation completed successfully!")
    print(f"Final test accuracy: {accuracy:.4f}")
