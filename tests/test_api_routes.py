"""Testy API Routes."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


class TestCameraEndpoints:
    @pytest.mark.unit
    def test_camera_health(self, test_client):
        response = test_client.get("/camera/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.unit
    def test_camera_capture(self, test_client):
        response = test_client.get("/camera/capture")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content[:2] == b'\xff\xd8'
    
    @pytest.mark.unit
    def test_camera_capture_no_frame(self, test_client, mock_camera_service):
        mock_camera_service.get_single_frame = AsyncMock(return_value=None)
        response = test_client.get("/camera/capture")
        assert response.status_code == 503
    
    @pytest.mark.unit
    def test_camera_stream(self, test_client):
        response = test_client.get("/camera/stream", timeout=2)
        assert response.status_code == 200
        assert "multipart/x-mixed-replace" in response.headers["content-type"]
    
    @pytest.mark.unit
    def test_camera_settings_get(self, test_client):
        response = test_client.get("/camera/settings")
        assert response.status_code == 200
        data = response.json()
        assert "fps" in data
        assert "jpeg_quality" in data
    
    @pytest.mark.unit
    def test_camera_monochrome(self, test_client):
        response = test_client.get("/camera/monochrome")
        assert response.status_code == 200
        assert "monochrome" in response.json()


class TestRecordingEndpoints:
    @pytest.mark.unit
    def test_recording_status(self, test_client):
        response = test_client.get("/recording/status")
        assert response.status_code == 200
        assert "is_recording" in response.json()
    
    @pytest.mark.unit
    def test_recording_start(self, test_client, mock_camera_service):
        mock_camera_service.is_recording = False
        response = test_client.post("/recording/start")
        assert response.status_code == 200
        assert response.json()["status"] == "started"
    
    @pytest.mark.unit
    def test_recording_start_already_recording(self, test_client, mock_camera_service):
        mock_camera_service.is_recording = True
        response = test_client.post("/recording/start")
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_recording_stop_not_recording(self, test_client, mock_camera_service):
        mock_camera_service.is_recording = False
        response = test_client.post("/recording/stop")
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_recording_list(self, test_client):
        response = test_client.get("/recording/list")
        assert response.status_code == 200
        assert "recordings" in response.json()
    
    @pytest.mark.unit
    def test_recording_download_not_found(self, test_client, mock_camera_service):
        mock_camera_service.get_recording_path.return_value = None
        response = test_client.get("/recording/download/nonexistent.mp4")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_recording_delete_not_found(self, test_client, mock_camera_service):
        mock_camera_service.delete_recording.return_value = False
        response = test_client.delete("/recording/nonexistent.mp4")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_recording_stop_success(self, test_client, mock_camera_service):
        mock_camera_service.is_recording = True
        response = test_client.post("/recording/stop")
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_recording_info_not_found(self, test_client, mock_camera_service):
        mock_camera_service.get_recording_path.return_value = None
        response = test_client.get("/recording/info/test.mp4")
        assert response.status_code == 404
    
    @pytest.mark.unit  
    def test_recording_note_not_found(self, test_client, mock_camera_service):
        mock_camera_service.set_note.return_value = False
        response = test_client.put("/recording/test.mp4/note?note=Test")
        assert response.status_code == 404


class TestLabelingEndpoints:
    """Test labeling endpoints."""
    
    @pytest.mark.unit
    def test_get_label_not_found(self, test_client):
        from app.services.labeling_service import get_labeling_service
        mock_labeling = MagicMock()
        mock_labeling.get_label.return_value = None
        
        from app.main import app
        app.dependency_overrides[get_labeling_service] = lambda: mock_labeling
        
        response = test_client.get("/labeling/test.mp4/frame/0")
        assert response.status_code == 200
        assert response.json() is None
        
        app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_remove_label_not_found(self, test_client):
        from app.services.labeling_service import get_labeling_service
        mock_labeling = MagicMock()
        mock_labeling.remove_label.return_value = False
        
        from app.main import app
        app.dependency_overrides[get_labeling_service] = lambda: mock_labeling
        
        response = test_client.delete("/labeling/test.mp4/frame/0")
        assert response.status_code == 404
        
        app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_get_video_labels(self, test_client):
        from app.services.labeling_service import get_labeling_service
        mock_labeling = MagicMock()
        mock_label = MagicMock()
        mock_label.frame_index = 0
        mock_label.label = "ok"
        mock_label.defect_type = None
        mock_label.timestamp = datetime.now()
        mock_labeling.get_labels_for_video.return_value = [mock_label]
        
        from app.main import app
        app.dependency_overrides[get_labeling_service] = lambda: mock_labeling
        
        response = test_client.get("/labeling/test.mp4/labels")
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "labels" in data
        
        app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_add_label_video_not_found(self, test_client, mock_camera_service):
        from app.services.labeling_service import get_labeling_service
        mock_labeling = MagicMock()
        mock_camera_service.get_recording_path.return_value = None
        
        from app.main import app
        app.dependency_overrides[get_labeling_service] = lambda: mock_labeling
        
        response = test_client.post(
            "/labeling/nonexistent.mp4/frame/0",
            json={"label": "ok"}
        )
        assert response.status_code == 404
        
        app.dependency_overrides.clear()

    @pytest.mark.unit
    def test_get_labeling_stats(self, test_client):
        """Test GET /labeling/stats endpoint."""
        from app.services.labeling_service import get_labeling_service
        mock_labeling = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_labeled = 100
        mock_stats.ok_count = 70
        mock_stats.nok_count = 30
        mock_stats.skip_count = 0
        mock_stats.videos_labeled = 5
        mock_stats.defect_counts = {}
        mock_labeling.get_stats.return_value = mock_stats
        
        from app.main import app
        app.dependency_overrides[get_labeling_service] = lambda: mock_labeling
        
        response = test_client.get("/labeling/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_labeled"] == 100
        
        app.dependency_overrides.clear()

    @pytest.mark.unit
    def test_export_training_data(self, test_client):
        """Test GET /labeling/training-data endpoint."""
        from app.services.labeling_service import get_labeling_service
        mock_labeling = MagicMock()
        mock_labeling.export_for_training.return_value = {
            "training_data_path": "labels/training_data",
            "ok_count": 50,
            "nok_count": 40,
            "total": 90,
            "ready_for_training": True,
            "defect_counts": {}
        }
        
        from app.main import app
        app.dependency_overrides[get_labeling_service] = lambda: mock_labeling
        
        response = test_client.get("/labeling/training-data")
        assert response.status_code == 200
        data = response.json()
        assert data["ok_count"] == 50
        
        app.dependency_overrides.clear()


class TestMLEndpoints:
    """Test ML endpoints."""
    
    @pytest.mark.unit
    def test_ml_info(self, test_client):
        from app.services.ml_classification_service import get_ml_service
        mock_ml = MagicMock()
        mock_ml.get_model_info.return_value = {"model_loaded": True}
        mock_ml.get_training_data_stats.return_value = {
            "ok_samples": 20,
            "nok_samples": 20,
            "ready_for_training": True
        }
        
        from app.main import app
        app.dependency_overrides[get_ml_service] = lambda: mock_ml
        
        response = test_client.get("/ml/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        assert "training_status" in data
        
        app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_training_status(self, test_client):
        response = test_client.get("/ml/training-status")
        assert response.status_code == 200
    
    @pytest.mark.unit
    def test_train_insufficient_data(self, test_client):
        from app.services.ml_classification_service import get_ml_service
        mock_ml = MagicMock()
        mock_ml.get_training_data_stats.return_value = {
            "ok_samples": 10,
            "nok_samples": 10,
            "ready_for_training": False
        }
        
        from app.main import app
        app.dependency_overrides[get_ml_service] = lambda: mock_ml
        
        response = test_client.post("/ml/train")
        assert response.status_code == 400
        
        app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_ml_training_already_in_progress(self, test_client):
        # Test że nie można wystartować drugiego treningu
        from app.api.routes import ml as ml_module
        ml_module._training_status["in_progress"] = True
        
        from app.services.ml_classification_service import get_ml_service
        mock_ml = MagicMock()
        mock_ml.get_training_data_stats.return_value = {
            "ok_samples": 30,
            "nok_samples": 30,
            "ready_for_training": True
        }
        
        from app.main import app
        app.dependency_overrides[get_ml_service] = lambda: mock_ml
        
        response = test_client.post("/ml/train")
        assert response.status_code == 400
        
        # Cleanup
        ml_module._training_status["in_progress"] = False
        app.dependency_overrides.clear()


class TestDefectEndpoints:
    """Test defect endpoints."""
    
    @pytest.mark.unit
    def test_defect_info(self, test_client):
        from app.services.defect_classifier_service import get_defect_classifier_service
        mock_defect = MagicMock()
        mock_defect.get_model_info.return_value = {"model_loaded": False}
        mock_defect.get_training_data_stats.return_value = {
            "total_samples": 0,
            "ready_for_training": False
        }
        
        from app.main import app
        app.dependency_overrides[get_defect_classifier_service] = lambda: mock_defect
        
        response = test_client.get("/defects/info")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        assert "training_status" in data
        
        app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_defect_train_insufficient_data(self, test_client):
        from app.services.defect_classifier_service import get_defect_classifier_service
        mock_defect = MagicMock()
        mock_defect.get_training_data_stats.return_value = {
            "total_samples": 10,
            "ready_for_training": False,
            "class_counts": {}
        }
        
        from app.main import app
        app.dependency_overrides[get_defect_classifier_service] = lambda: mock_defect
        
        response = test_client.post("/defects/train")
        assert response.status_code == 400
        
        app.dependency_overrides.clear()


class TestAdditionalCameraEndpoints:
    """Additional camera endpoint tests for coverage."""
    
    @pytest.mark.unit
    def test_camera_settings_get(self, test_client):
        """Test GET /camera/settings endpoint."""
        response = test_client.get("/camera/settings")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.unit
    def test_camera_settings_partial_update(self, test_client):
        """Test PUT /camera/settings with partial data."""
        response = test_client.put(
            "/camera/settings",
            json={"jpeg_quality": 85}
        )
        
        assert response.status_code == 200

    @pytest.mark.unit
    def test_camera_capture(self, test_client, mock_camera_service, valid_jpeg_bytes):
        """Test GET /camera/capture endpoint."""
        mock_camera_service.get_single_frame = AsyncMock(return_value=valid_jpeg_bytes)
        response = test_client.get("/camera/capture")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    @pytest.mark.unit
    def test_camera_capture_unavailable(self, test_client, mock_camera_service):
        """Test GET /camera/capture when camera unavailable."""
        mock_camera_service.get_single_frame = AsyncMock(return_value=None)
        response = test_client.get("/camera/capture")
        
        assert response.status_code == 503

    @pytest.mark.unit
    def test_camera_monochrome_get(self, test_client, mock_camera_service):
        """Test GET /camera/monochrome endpoint."""
        mock_camera_service.monochrome = False
        response = test_client.get("/camera/monochrome")
        
        assert response.status_code == 200
        data = response.json()
        assert "monochrome" in data

    @pytest.mark.unit
    def test_camera_monochrome_set(self, test_client):
        """Test POST /camera/monochrome endpoint."""
        response = test_client.post("/camera/monochrome?enabled=true")
        
        assert response.status_code == 200
        data = response.json()
        assert "monochrome" in data
