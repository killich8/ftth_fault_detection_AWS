from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import logging

# Get logger
logger = logging.getLogger("ftth-api")

# Create router
router = APIRouter(
    prefix="/validation",
    tags=["validation"],
    responses={404: {"description": "Not found"}},
)

# Models
class ValidationResult(BaseModel):
    """Model for validation result"""
    is_valid: bool = Field(..., description="Whether the data is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Statistical information about the data")

class OTDRTrace(BaseModel):
    """Model for OTDR trace data"""
    snr: float = Field(..., description="Signal-to-noise ratio")
    trace_points: List[float] = Field(..., min_items=30, max_items=30, description="30 normalized OTDR trace points [P1...P30]")
    
    @validator('snr')
    def validate_snr(cls, v):
        if v < 0:
            raise ValueError("SNR must be non-negative")
        if v > 30:
            raise ValueError("SNR is unusually high (>30)")
        return v
    
    @validator('trace_points')
    def validate_trace_points(cls, v):
        if len(v) != 30:
            raise ValueError("Must provide exactly 30 trace points")
        if any(point < 0 or point > 1 for point in v):
            raise ValueError("All trace points must be normalized between 0 and 1")
        return v

@router.post("/trace", response_model=ValidationResult)
def validate_trace(trace: OTDRTrace):
    """
    Validate OTDR trace data
    """
    try:
        errors = []
        warnings = []
        stats = {}
        
        # Check SNR
        if trace.snr < 3:
            warnings.append(f"Low SNR ({trace.snr}) may affect detection accuracy")
        
        # Calculate statistics
        trace_array = np.array(trace.trace_points)
        stats["trace_min"] = float(np.min(trace_array))
        stats["trace_max"] = float(np.max(trace_array))
        stats["trace_mean"] = float(np.mean(trace_array))
        stats["trace_std"] = float(np.std(trace_array))
        stats["trace_range"] = stats["trace_max"] - stats["trace_min"]
        
        # Check for flat sections
        diff = np.diff(trace_array)
        if np.all(np.abs(diff) < 0.01):
            errors.append("Trace appears to be flat, which is unusual for OTDR data")
        
        # Check for sudden drops
        if np.any(diff < -0.5):
            drop_indices = np.where(diff < -0.5)[0]
            for idx in drop_indices:
                warnings.append(f"Sudden drop detected at position {idx+1} to {idx+2}")
        
        # Check for sudden spikes
        if np.any(diff > 0.5):
            spike_indices = np.where(diff > 0.5)[0]
            for idx in spike_indices:
                warnings.append(f"Sudden spike detected at position {idx+1} to {idx+2}")
        
        # Determine if valid
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@router.get("/check-range", response_model=ValidationResult)
def check_value_range(
    min_value: float = Query(..., description="Minimum expected value"),
    max_value: float = Query(..., description="Maximum expected value"),
    actual_value: float = Query(..., description="Actual value to check")
):
    """
    Check if a value is within the expected range
    """
    errors = []
    warnings = []
    stats = {"min": min_value, "max": max_value, "value": actual_value}
    
    if actual_value < min_value:
        errors.append(f"Value {actual_value} is below minimum {min_value}")
    elif actual_value > max_value:
        errors.append(f"Value {actual_value} is above maximum {max_value}")
    
    # Add warnings for values close to limits
    buffer = (max_value - min_value) * 0.1
    if min_value <= actual_value <= min_value + buffer:
        warnings.append(f"Value {actual_value} is close to minimum {min_value}")
    elif max_value - buffer <= actual_value <= max_value:
        warnings.append(f"Value {actual_value} is close to maximum {max_value}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        stats=stats
    )
