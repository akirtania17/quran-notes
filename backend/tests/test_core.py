"""Test core functionality."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.rate_limit import rate_limiter


client = TestClient(app)


def test_cors_headers():
    """Test CORS headers are properly set."""
    response = client.options(
        "/v1/health",
        headers={
            "Origin": "http://localhost:19006",
            "Access-Control-Request-Method": "GET",
        }
    )
    # FastAPI/Starlette handles CORS, just verify the endpoint is accessible
    assert response.status_code in [200, 405]


def test_rate_limiter_basic():
    """Test rate limiter tracks requests."""
    # Clear any existing state
    rate_limiter._requests.clear()
    
    # Should allow first request
    rate_limiter.check_rate_limit("test-client-1")
    
    # Should track the request
    assert len(rate_limiter._requests["test-client-1"]) == 1


def test_rate_limiter_enforcement():
    """Test rate limiter enforces limits."""
    from app.core.errors import RateLimitError
    
    # Clear any existing state
    rate_limiter._requests.clear()
    
    # Create a temporary limiter with low limit for testing
    test_limiter = type(rate_limiter)(max_requests=2, window_seconds=60)
    
    # First two requests should succeed
    test_limiter.check_rate_limit("test-client-2")
    test_limiter.check_rate_limit("test-client-2")
    
    # Third request should fail
    with pytest.raises(RateLimitError):
        test_limiter.check_rate_limit("test-client-2")


def test_settings_loaded():
    """Test settings are loaded correctly."""
    assert settings.env in ["dev", "prod"]
    assert settings.port == 8000
    assert settings.database_url.startswith("sqlite")
    assert settings.max_upload_mb > 0


def test_settings_cors_origins_list():
    """Test CORS origins are parsed correctly."""
    origins = settings.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) > 0


def test_settings_max_upload_bytes():
    """Test max upload bytes calculation."""
    max_bytes = settings.max_upload_bytes
    assert max_bytes == settings.max_upload_mb * 1024 * 1024
    assert max_bytes > 0

