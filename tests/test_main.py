"""
Tests for the main application.
"""

import pytest
from fastapi.testclient import TestClient

from smeflow.main import create_app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    
    Returns:
        TestClient: Test client instance.
    """
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    """
    Test the health check endpoint.
    
    Args:
        client: FastAPI test client.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_api_health_endpoint(client):
    """
    Test the API health check endpoint.
    
    Args:
        client: FastAPI test client.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_api_tenants_endpoint(client):
    """
    Test the tenants endpoint (placeholder).
    
    Args:
        client: FastAPI test client.
    """
    response = client.get("/api/v1/tenants")
    assert response.status_code == 200
    
    data = response.json()
    assert "tenants" in data
    assert "message" in data


def test_api_agents_endpoint(client):
    """
    Test the agents endpoint (placeholder).
    
    Args:
        client: FastAPI test client.
    """
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    
    data = response.json()
    assert "agents" in data
    assert "message" in data


def test_api_workflows_endpoint(client):
    """
    Test the workflows endpoint (placeholder).
    
    Args:
        client: FastAPI test client.
    """
    response = client.get("/api/v1/workflows")
    assert response.status_code == 200
    
    data = response.json()
    assert "workflows" in data
    assert "message" in data
