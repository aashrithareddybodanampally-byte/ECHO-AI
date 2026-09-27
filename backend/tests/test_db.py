import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from app.main import app

client = TestClient(app)

def test_db_health_check_success():
    with patch("app.api.v1.health.Session") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        
        # Override the dependency
        from app.api.v1.health import get_db
        
        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        mock_db.execute.assert_called_once()
        
        # Clean up override
        app.dependency_overrides.clear()

def test_db_health_check_failure():
    with patch("app.api.v1.health.Session") as mock_session:
        mock_db = MagicMock()
        mock_db.execute.side_effect = SQLAlchemyError("Connection failed")
        mock_session.return_value = mock_db
        
        # Override the dependency
        from app.api.v1.health import get_db
        
        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        
        response = client.get("/api/v1/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        
        # Clean up override
        app.dependency_overrides.clear()
