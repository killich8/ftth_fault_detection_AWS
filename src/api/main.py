from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import yaml
import os
import sys
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.predict import OTDRFaultDetector

# Get logger
logger = logging.getLogger("ftth-api")

# Load configuration
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Create router
router = APIRouter(
    tags=["prediction"],
    responses={404: {"description": "Not found"}},
)

# Initialize fault detector
detector = None

# Input data models
class OTDRPoint(BaseModel):
    """Model for a single OTDR trace point"""
    value: float = Field(..., description="Normalized value of the OTDR trace point")

class OTDRTrace(BaseModel):
    """Model for OTDR trace data"""
    snr: float = Field(..., description="Signal-to-noise ratio")
    trace_points: List[float] = Field(..., min_items=30, max_items=30, description="30 normalized OTDR trace points [P1...P30]")

class BatchOTDRTraces(BaseModel):
    """Model for batch OTDR trace data"""
    traces: List[OTDRTrace] = Field(..., description="List of OTDR traces")

# Output data models
class FaultPrediction(BaseModel):
    """Model for fault prediction result"""
    fault_type: int = Field(..., description="Predicted fault type code (0-7)")
    fault_name: str = Field(..., description="Name of the predicted fault type")
    confidence: float = Field(..., description="Confidence score for the prediction")
    all_probabilities: Dict[str, float] = Field(..., description="Probabilities for all fault types")
    location: Optional[float] = Field(None, description="Estimated location of the fault (if applicable)")
    reflectance: Optional[float] = Field(None, description="Estimated reflectance of the fault (if applicable)")
    loss: Optional[float] = Field(None, description="Estimated loss of the fault (if applicable)")

class BatchFaultPredictions(BaseModel):
    """Model for batch fault prediction results"""
    predictions: List[FaultPrediction] = Field(..., description="List of fault predictions")

# Dependency to get the detector
def get_detector():
    global detector
    if detector is None:
        try:
            model_path = config["api"]["model_path"]
            detector = OTDRFaultDetector(config_path="config.yaml", model_path=model_path)
            logger.info(f"Initialized fault detector with model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to initialize fault detector: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize fault detector")
    return detector

# These endpoints are now in __init__.py

@router.post("/predict", response_model=FaultPrediction)
def predict(trace: OTDRTrace, detector: OTDRFaultDetector = Depends(get_detector)):
    """
    Predict fault type from OTDR trace
    """
    try:
        # Convert input data to the format expected by the model
        input_data = {
            'SNR': trace.snr
        }
        
        # Add trace points
        for i, point in enumerate(trace.trace_points, 1):
            input_data[f'P{i}'] = point
        
        # Make prediction
        result = detector.predict(input_data)
        
        # Create response
        prediction = FaultPrediction(
            fault_type=result['fault_type'],
            fault_name=result['fault_name'],
            confidence=result['confidence'],
            all_probabilities=result['all_probabilities'],
            # Optional fields are set to None by default
        )
        
        logger.info(f"Prediction made: {prediction.fault_name} with confidence {prediction.confidence:.4f}")
        
        return prediction
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@router.post("/batch-predict", response_model=BatchFaultPredictions)
def batch_predict(batch_traces: BatchOTDRTraces, detector: OTDRFaultDetector = Depends(get_detector)):
    """
    Predict fault types from a batch of OTDR traces
    """
    try:
        # Convert input data to the format expected by the model
        input_data_list = []
        
        for trace in batch_traces.traces:
            input_data = {
                'SNR': trace.snr
            }
            
            # Add trace points
            for i, point in enumerate(trace.trace_points, 1):
                input_data[f'P{i}'] = point
            
            input_data_list.append(input_data)
        
        # Make batch prediction
        results = detector.batch_predict(input_data_list)
        
        # Create response
        predictions = []
        for result in results:
            prediction = FaultPrediction(
                fault_type=result['fault_type'],
                fault_name=result['fault_name'],
                confidence=result['confidence'],
                all_probabilities=result['all_probabilities'],
                # Optional fields are set to None by default
            )
            predictions.append(prediction)
        
        logger.info(f"Batch prediction made for {len(predictions)} traces")
        
        return BatchFaultPredictions(predictions=predictions)
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction error: {str(e)}")

@router.get("/fault-types")
def get_fault_types():
    """
    Get information about fault types
    """
    fault_types = [
        {"code": 0, "name": "Normal", "description": "No fault detected"},
        {"code": 1, "name": "Fiber Tapping", "description": "Unauthorized access to the fiber"},
        {"code": 2, "name": "Bad Splice", "description": "Poor quality fiber splice"},
        {"code": 3, "name": "Bending Event", "description": "Excessive bending of the fiber"},
        {"code": 4, "name": "Dirty Connector", "description": "Contaminated fiber connector"},
        {"code": 5, "name": "Fiber Cut", "description": "Complete break in the fiber"},
        {"code": 6, "name": "PC Connector", "description": "Physical Contact connector"},
        {"code": 7, "name": "Reflector", "description": "Reflective event in the fiber"}
    ]
    
    return {"fault_types": fault_types}

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "main:app",
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=True
    )
