"""Tests for ML and Defects API routes."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestMLRoutes:
    """Test ML classification API routes."""

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)

    def test_ml_info(self, test_client):
        """Test GET /ml/info endpoint."""
        from app.services.ml_classification_service import get_ml_service
        from app.main import app
        
        mock_service = Mock()
        mock_service.get_model_info.return_value = {
            "model_loaded": True,
            "device": "cpu",
            "class_names": ["OK", "NOK"]
        }
        mock_service.get_training_data_stats.return_value = {
            "ok_samples": 50,
            "nok_samples": 50,
            "total_samples": 100,
            "ready_for_training": True
        }
        
        app.dependency_overrides[get_ml_service] = lambda: mock_service
        
        response = test_client.get("/ml/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        
        app.dependency_overrides.clear()

    def test_ml_train_insufficient_data(self, test_client):
        """Test POST /ml/train with insufficient data."""
        from app.services.ml_classification_service import get_ml_service
        from app.main import app
        
        mock_service = Mock()
        mock_service.get_training_data_stats.return_value = {
            "ok_samples": 5,
            "nok_samples": 5,
            "total_samples": 10,
            "ready_for_training": False
        }
        
        app.dependency_overrides[get_ml_service] = lambda: mock_service
        
        response = test_client.post("/ml/train")
        assert response.status_code == 400
        
        app.dependency_overrides.clear()

    def test_defect_info(self, test_client):
        """Test GET /defects/info endpoint."""
        from app.services.defect_classifier_service import get_defect_classifier_service
        from app.main import app
        
        mock_service = Mock()
        mock_service.get_model_info.return_value = {
            "model_loaded": True,
            "device": "cpu"
        }
        mock_service.get_training_data_stats.return_value = {
            "total_samples": 100,
            "ready_for_training": True,
            "class_counts": {"porosity": 50, "crack": 50}
        }
        
        app.dependency_overrides[get_defect_classifier_service] = lambda: mock_service
        
        response = test_client.get("/defects/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        
        app.dependency_overrides.clear()

    def test_defect_train_insufficient_data(self, test_client):
        """Test POST /defects/train with insufficient data."""
        from app.services.defect_classifier_service import get_defect_classifier_service
        from app.main import app
        
        mock_service = Mock()
        mock_service.get_training_data_stats.return_value = {
            "total_samples": 10,
            "ready_for_training": False,
            "class_counts": {"porosity": 10}
        }
        
        app.dependency_overrides[get_defect_classifier_service] = lambda: mock_service
        
        response = test_client.post("/defects/train")
        assert response.status_code == 400
        
        app.dependency_overrides.clear()
