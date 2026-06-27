"""Test health check endpoint."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint returns 200."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


def test_root_endpoint():
    """Test root endpoint returns basic info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Quran Notes API"
    assert data["version"] == "1.0.0"

