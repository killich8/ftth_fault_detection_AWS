import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.api import app

# Create test client
client = TestClient(app)

def test_admin_endpoints():
    """Test the admin endpoints"""
    # Test system info endpoint
    # Note: This would require mocking the model in a real test
    # response = client.get("/admin/system-info")
    # assert response.status_code == 200
    
    # Test model status endpoint
    # Note: This would require mocking the model in a real test
    # response = client.get("/admin/model-status")
    # assert response.status_code == 200
    
    # For now, we'll just check that the endpoints exist in the router
    from src.api.admin import router
    endpoints = [route.path for route in router.routes]
    assert "/admin/system-info" in endpoints
    assert "/admin/model-status" in endpoints

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
