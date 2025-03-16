import pytest
from fastapi.testclient import TestClient
import sys
import os
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import app

# Create test client
client = TestClient(app)

def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_fault_types():
    """Test the fault types endpoint"""
    response = client.get("/fault-types")
    assert response.status_code == 200
    assert "fault_types" in response.json()
    fault_types = response.json()["fault_types"]
    assert len(fault_types) == 8  # 8 fault types (0-7)

def test_validate_trace():
    """Test the trace validation endpoint"""
    # Valid trace
    valid_trace = {
        "snr": 15.0,
        "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                         0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                         0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
    }
    response = client.post("/validation/trace", json=valid_trace)
    assert response.status_code == 200
    assert response.json()["is_valid"] == True
    
    # Invalid trace (too few points)
    invalid_trace = {
        "snr": 15.0,
        "trace_points": [0.8, 0.7, 0.6]
    }
    response = client.post("/validation/trace", json=invalid_trace)
    assert response.status_code == 422  # Validation error
    
    # Invalid trace (negative SNR)
    invalid_trace = {
        "snr": -5.0,
        "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                         0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                         0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
    }
    response = client.post("/validation/trace", json=invalid_trace)
    assert response.status_code == 422  # Validation error

def test_check_range():
    """Test the check range endpoint"""
    response = client.get("/validation/check-range?min_value=0&max_value=10&actual_value=5")
    assert response.status_code == 200
    assert response.json()["is_valid"] == True
    
    response = client.get("/validation/check-range?min_value=0&max_value=10&actual_value=15")
    assert response.status_code == 200
    assert response.json()["is_valid"] == False
    assert len(response.json()["errors"]) > 0

# Mock the model prediction for testing
@pytest.fixture
def mock_prediction(monkeypatch):
    def mock_predict(*args, **kwargs):
        return {
            "fault_type": 2,
            "fault_name": "Bad Splice",
            "confidence": 0.95,
            "all_probabilities": {
                "Normal": 0.01,
                "Fiber Tapping": 0.02,
                "Bad Splice": 0.95,
                "Bending Event": 0.01,
                "Dirty Connector": 0.005,
                "Fiber Cut": 0.001,
                "PC Connector": 0.002,
                "Reflector": 0.002
            }
        }
    
    # This is a simplified mock - in a real test you would need to properly mock the detector
    # and its dependencies
    from unittest.mock import MagicMock
    mock_detector = MagicMock()
    mock_detector.predict.return_value = mock_predict()
    monkeypatch.setattr("api.main.get_detector", lambda: mock_detector)
    
    return mock_predict

# Note: The following tests would require mocking the model, which is complex
# In a real implementation, you would use dependency injection to mock the model
# For now, these are commented out as they would require more setup

"""
def test_predict(mock_prediction):
    # Test the prediction endpoint
    trace = {
        "snr": 15.0,
        "trace_points": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1,
                         0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9,
                         0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1]
    }
    response = client.post("/predict", json=trace)
    assert response.status_code == 200
    assert response.json()["fault_type"] == 2
    assert response.json()["fault_name"] == "Bad Splice"
    assert response.json()["confidence"] > 0.9
"""

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
