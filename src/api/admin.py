from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any
import logging
import yaml
import os
import sys

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
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)

# Models
class ModelInfo(BaseModel):
    """Model for model information"""
    model_type: str = Field(..., description="Type of model (lstm, cnn, etc.)")
    input_features: int = Field(..., description="Number of input features")
    hidden_layers: list = Field(..., description="Hidden layer configuration")
    model_path: str = Field(..., description="Path to the model file")

class SystemInfo(BaseModel):
    """Model for system information"""
    api_version: str = Field(..., description="API version")
    model_info: ModelInfo = Field(..., description="Model information")
    config: Dict[str, Any] = Field(..., description="System configuration")

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

@router.get("/system-info", response_model=SystemInfo)
def get_system_info(detector: OTDRFaultDetector = Depends(get_detector)):
    """
    Get system information
    """
    try:
        # Create model info
        model_info = ModelInfo(
            model_type=config["model"]["model_type"],
            input_features=config["model"]["input_features"],
            hidden_layers=config["model"]["hidden_layers"],
            model_path=config["api"]["model_path"]
        )
        
        # Create system info
        system_info = SystemInfo(
            api_version="1.0.0",
            model_info=model_info,
            config={
                "data": config["data"],
                "model": {k: v for k, v in config["model"].items() if k != "model_save_path"},
                "api": {k: v for k, v in config["api"].items() if k != "model_path"}
            }
        )
        
        return system_info
    
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system info: {str(e)}")

@router.get("/model-status")
def get_model_status(detector: OTDRFaultDetector = Depends(get_detector)):
    """
    Get model status
    """
    try:
        # Check if model is loaded
        if detector.model is None:
            return {"status": "error", "message": "Model not loaded"}
        
        return {
            "status": "active",
            "model_type": config["model"]["model_type"],
            "model_path": config["api"]["model_path"],
            "class_names": detector.class_names
        }
    
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting model status: {str(e)}")
