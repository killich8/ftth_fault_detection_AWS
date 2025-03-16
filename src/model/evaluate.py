import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
import yaml
import pickle
import sys

sys.path.append('../../')
from src.data_processing.preprocess import OTDRDataProcessor

class OTDRModelEvaluator:
    """
    Class for evaluating the trained OTDR fault detection model
    """
    def __init__(self, config_path='../../config.yaml'):
        # Load configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        # Set random seeds for reproducibility
        np.random.seed(self.config['data']['random_seed'])
        tf.random.set_seed(self.config['data']['random_seed'])
    
    def load_model(self, model_path=None):
        """Load the trained model"""
        if model_path is None:
            model_path = os.path.join(self.config['model']['model_save_path'], 'best_model.h5')
        
        try:
            self.model = load_model(model_path)
            print(f"Model loaded from {model_path}")
            return self.model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    
    def load_test_data(self):
        """Load the test data for evaluation"""
        processed_dir = self.config['data']['processed_data_path']
        
        self.X_test = pd.read_csv(f"{processed_dir}/X_test.csv")
        self.y_test = pd.read_csv(f"{processed_dir}/y_test.csv").values.ravel()
        
        print(f"Loaded test data with shape: {self.X_test.shape}")
        
        # Prepare test data based on model type
        model_type = self.config['model']['model_type']
        
        if model_type in ['lstm', 'cnn']:
            # Extract OTDR trace points
            trace_columns = [col for col in self.X_test.columns if col.startswith('P') and len(col) <= 3]
            
            # Create sequence data
            X_test_seq = self.X_test[trace_columns].values.reshape(self.X_test.shape[0], len(trace_columns), 1)
            
            # Create additional features input
            other_columns = [col for col in self.X_test.columns if col not in trace_columns]
            X_test_other = self.X_test[other_columns].values
            
            self.X_test_prepared = [X_test_seq, X_test_other]
        else:
            self.X_test_prepared = self.X_test
        
        return self.X_test_prepared, self.y_test
    
    def evaluate(self):
        """Evaluate the model on test data"""
        # Evaluate on test data
        test_loss, test_accuracy = self.model.evaluate(self.X_test_prepared, self.y_test, verbose=1)
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
        with open(os.path.join(self.config['model']['model_save_path'], 'evaluation_report.txt'), 'w') as f:
            f.write(f"Test Loss: {test_loss:.4f}\n")
            f.write(f"Test Accuracy: {test_accuracy:.4f}\n\n")
            f.write("Classification Report:\n")
            f.write(report)
        
        # Confusion matrix
        cm = confusion_matrix(self.y_test, y_pred_classes)
        plt.figure(figsize=(12, 10))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
        plt.xlabel('Predicted')
        plt.ylabel('True')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig(os.path.join(self.config['model']['model_save_path'], 'evaluation_confusion_matrix.png'))
        
        # Calculate per-class metrics
        precision, recall, f1, _ = precision_recall_fscore_support(self.y_test, y_pred_classes)
        
        # Plot per-class metrics
        plt.figure(figsize=(15, 6))
        x = np.arange(len(class_names))
        width = 0.25
        
        plt.bar(x - width, precision, width, label='Precision')
        plt.bar(x, recall, width, label='Recall')
        plt.bar(x + width, f1, width, label='F1-Score')
        
        plt.xlabel('Fault Type')
        plt.ylabel('Score')
        plt.title('Per-Class Performance Metrics')
        plt.xticks(x, class_names, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.config['model']['model_save_path'], 'per_class_metrics.png'))
        
        # Return evaluation metrics
        return {
            'accuracy': test_accuracy,
            'loss': test_loss,
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'f1': f1.tolist(),
            'confusion_matrix': cm.tolist()
        }
    
    def analyze_misclassifications(self):
        """Analyze misclassified examples to understand model weaknesses"""
        # Generate predictions
        y_pred = self.model.predict(self.X_test_prepared)
        y_pred_classes = np.argmax(y_pred, axis=1)
        
        # Find misclassified examples
        misclassified_indices = np.where(y_pred_classes != self.y_test)[0]
        
        if len(misclassified_indices) == 0:
            print("No misclassifications found.")
            return
        
        # Sample a few misclassified examples
        sample_size = min(10, len(misclassified_indices))
        sample_indices = np.random.choice(misclassified_indices, sample_size, replace=False)
        
        # Class names for reference
        class_names = ['Normal', 'Fiber Tapping', 'Bad Splice', 'Bending Event', 
                       'Dirty Connector', 'Fiber Cut', 'PC Connector', 'Reflector']
        
        # Analyze each misclassified example
        misclassification_analysis = []
        
        for idx in sample_indices:
            true_class = self.y_test[idx]
            pred_class = y_pred_classes[idx]
            confidence = y_pred[idx][pred_class]
            
            # Extract OTDR trace for plotting
            trace_columns = [col for col in self.X_test.columns if col.startswith('P') and len(col) <= 3]
            trace_values = self.X_test.iloc[idx][trace_columns].values
            
            # Create analysis entry
            analysis = {
                'index': idx,
                'true_class': int(true_class),
                'true_class_name': class_names[int(true_class)],
                'pred_class': int(pred_class),
                'pred_class_name': class_names[int(pred_class)],
                'confidence': float(confidence),
                'trace_values': trace_values.tolist()
            }
            
            misclassification_analysis.append(analysis)
        
        # Save misclassification analysis to file
        with open(os.path.join(self.config['model']['model_save_path'], 'misclassification_analysis.txt'), 'w') as f:
            f.write(f"Analysis of {sample_size} misclassified examples:\n\n")
            
            for analysis in misclassification_analysis:
                f.write(f"Example {analysis['index']}:\n")
                f.write(f"  True class: {analysis['true_class_name']} (class {analysis['true_class']})\n")
                f.write(f"  Predicted class: {analysis['pred_class_name']} (class {analysis['pred_class']})\n")
                f.write(f"  Confidence: {analysis['confidence']:.4f}\n\n")
        
        # Plot misclassified examples
        plt.figure(figsize=(15, 10))
        
        for i, analysis in enumerate(misclassification_analysis):
            plt.subplot(3, 4, i + 1)
            plt.plot(analysis['trace_values'])
            plt.title(f"True: {analysis['true_class_name']}\nPred: {analysis['pred_class_name']}")
            plt.tight_layout()
        
        plt.savefig(os.path.join(self.config['model']['model_save_path'], 'misclassified_examples.png'))
        
        return misclassification_analysis

if __name__ == "__main__":
    # Initialize evaluator
    evaluator = OTDRModelEvaluator(config_path='../../config.yaml')
    
    # Load model
    model = evaluator.load_model()
    
    if model is not None:
        # Load test data
        X_test, y_test = evaluator.load_test_data()
        
        # Evaluate model
        metrics = evaluator.evaluate()
        
        # Analyze misclassifications
        misclassification_analysis = evaluator.analyze_misclassifications()
        
        print(f"Model evaluation completed successfully!")
        print(f"Evaluation results saved to {evaluator.config['model']['model_save_path']}")
    else:
        print("Model evaluation failed due to error loading model.")
