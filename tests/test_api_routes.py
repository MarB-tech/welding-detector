"""
Testy API Routes - FastAPI endpoints.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path


class TestCameraEndpoints:
    """Testy dla endpointów /camera/*."""
    
    @pytest.mark.unit
    def test_camera_health_healthy(self, test_client, mock_camera_service):
        """Sprawdza czy /camera/health zwraca status healthy."""
        response = test_client.get("/camera/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "camera_url" in data
    
    @pytest.mark.unit
    def test_camera_health_disconnected(self, test_client, mock_camera_service):
        """Sprawdza czy /camera/health zwraca disconnected gdy kamera niedostępna."""
        mock_camera_service.health_check = AsyncMock(return_value={
            "status": "disconnected",
            "camera_url": "http://test:8001",
            "error": "Connection refused",
            "has_cached_frame": False
        })
        
        response = test_client.get("/camera/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disconnected"
    
    @pytest.mark.unit
    def test_camera_capture_returns_jpeg(self, test_client, valid_jpeg_bytes):
        """Sprawdza czy /camera/capture zwraca JPEG."""
        response = test_client.get("/camera/capture")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        
        # Sprawdź czy to prawidłowy JPEG
        assert response.content[:2] == b'\xff\xd8'
    
    @pytest.mark.unit
    def test_camera_capture_no_frame_503(self, test_client, mock_camera_service):
        """Sprawdza czy /camera/capture zwraca 503 gdy brak klatki."""
        mock_camera_service.get_single_frame = AsyncMock(return_value=None)
        
        response = test_client.get("/camera/capture")
        
        assert response.status_code == 503
    
    @pytest.mark.unit
    def test_camera_capture_overlay_param(self, test_client, mock_overlay_service, valid_jpeg_bytes):
        """Sprawdza czy parametr overlay=false wyłącza overlay."""
        # Z overlay
        response_with = test_client.get("/camera/capture?overlay=true")
        assert response_with.status_code == 200
        
        # Bez overlay
        response_without = test_client.get("/camera/capture?overlay=false")
        assert response_without.status_code == 200
    
    @pytest.mark.unit
    def test_camera_stream_returns_mjpeg(self, test_client):
        """Sprawdza czy /camera/stream zwraca MJPEG stream."""
        response = test_client.get("/camera/stream", timeout=2)
        
        assert response.status_code == 200
        assert "multipart/x-mixed-replace" in response.headers["content-type"]


class TestEdgeEndpoints:
    """Testy dla endpointów /edge/*."""
    
    @pytest.mark.unit
    def test_edge_detect_not_implemented(self, test_client):
        """Sprawdza czy /edge/detect zwraca not_implemented."""
        response = test_client.get("/edge/detect")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_implemented"


class TestRecordingEndpoints:
    """Testy dla endpointów /recording/*."""
    
    @pytest.mark.unit
    def test_recording_status_not_recording(self, test_client):
        """Sprawdza czy /recording/status zwraca is_recording=false."""
        response = test_client.get("/recording/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_recording"] is False
    
    @pytest.mark.unit
    def test_recording_start_success(self, test_client, mock_recorder_service):
        """Sprawdza czy POST /recording/start startuje nagrywanie."""
        response = test_client.post("/recording/start")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert "filename" in data
    
    @pytest.mark.unit
    def test_recording_start_already_recording_400(self, test_client, mock_overlay_service):
        """Sprawdza czy POST /recording/start zwraca 400 gdy już nagrywa."""
        mock_overlay_service.is_recording = True
        
        response = test_client.post("/recording/start")
        
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_recording_stop_success(self, test_client, mock_overlay_service, mock_recorder_service):
        """Sprawdza czy POST /recording/stop zatrzymuje nagrywanie."""
        mock_overlay_service.is_recording = True
        
        response = test_client.post("/recording/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        assert "filename" in data
        assert "duration_seconds" in data
        assert "frames" in data
        assert "size_mb" in data
    
    @pytest.mark.unit
    def test_recording_stop_not_recording_400(self, test_client, mock_overlay_service):
        """Sprawdza czy POST /recording/stop zwraca 400 gdy nie nagrywa."""
        mock_overlay_service.is_recording = False
        
        response = test_client.post("/recording/stop")
        
        assert response.status_code == 400
    
    @pytest.mark.unit
    def test_recording_list_empty(self, test_client, mock_recorder_service):
        """Sprawdza czy GET /recording/list zwraca pustą listę."""
        mock_recorder_service.list_files.return_value = []
        
        response = test_client.get("/recording/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["recordings"] == []
    
    @pytest.mark.unit
    def test_recording_list_with_files(self, test_client, mock_recorder_service):
        """Sprawdza czy GET /recording/list zwraca listę nagrań."""
        mock_recorder_service.list_files.return_value = [
            {"filename": "rec_001.mp4", "size_mb": 1.5, "created": "2024-01-01T12:00:00"}
        ]
        
        response = test_client.get("/recording/list")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recordings"]) == 1
        assert data["recordings"][0]["filename"] == "rec_001.mp4"
    
    @pytest.mark.unit
    def test_recording_download_not_found(self, test_client, mock_recorder_service):
        """Sprawdza czy GET /recording/download/{file} zwraca 404 dla nieistniejącego pliku."""
        mock_recorder_service.get_path.return_value = None
        
        response = test_client.get("/recording/download/nonexistent.mp4")
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_recording_download_success(self, test_client, mock_recorder_service, tmp_path):
        """Sprawdza czy GET /recording/download/{file} zwraca plik."""
        # Utwórz testowy plik
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"fake mp4 content")
        
        mock_recorder_service.get_path.return_value = test_file
        
        response = test_client.get("/recording/download/test.mp4")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
    
    @pytest.mark.unit
    def test_recording_delete_not_found(self, test_client, mock_recorder_service):
        """Sprawdza czy DELETE /recording/{file} zwraca 404 dla nieistniejącego pliku."""
        mock_recorder_service.get_path.return_value = None
        
        response = test_client.delete("/recording/nonexistent.mp4")
        
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_recording_delete_success(self, test_client, mock_recorder_service, tmp_path):
        """Sprawdza czy DELETE /recording/{file} usuwa plik."""
        # Utwórz testowy plik
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"fake mp4 content")
        
        mock_recorder_service.get_path.return_value = test_file
        
        response = test_client.delete("/recording/test.mp4")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert not test_file.exists()  # Plik usunięty


class TestRecordingFlow:
    """Testy E2E - pełny flow nagrywania."""
    
    @pytest.mark.integration
    def test_full_recording_flow(self, test_client_real_services, valid_jpeg_bytes, patch_recordings_dir):
        """Test pełnego cyklu: start -> status -> stop -> list -> download -> delete."""
        from app.services.video_recorder_service import VideoRecorderService
        
        # Reset i patch
        VideoRecorderService._instance = None
        
        with patch('app.services.video_recorder_service.RECORDINGS_DIR', patch_recordings_dir):
            # 1. Start recording
            response = test_client_real_services.post("/recording/start")
            assert response.status_code == 200
            filename = response.json()["filename"]
            
            # 2. Check status
            response = test_client_real_services.get("/recording/status")
            assert response.status_code == 200
            assert response.json()["is_recording"] is True
            
            # 3. Symuluj dodanie klatek (przez serwis bezpośrednio)
            from app.services.video_recorder_service import get_recorder_service
            recorder = get_recorder_service()
            for _ in range(10):
                recorder.add_frame(valid_jpeg_bytes)
            
            # 4. Stop recording
            response = test_client_real_services.post("/recording/stop")
            assert response.status_code == 200
            assert response.json()["frames"] == 10
            
            # 5. List recordings
            response = test_client_real_services.get("/recording/list")
            assert response.status_code == 200
            recordings = response.json()["recordings"]
            assert len(recordings) >= 1
            assert any(r["filename"] == filename for r in recordings)
            
            # 6. Download
            response = test_client_real_services.get(f"/recording/download/{filename}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "video/mp4"
            
            # 7. Delete
            response = test_client_real_services.delete(f"/recording/{filename}")
            assert response.status_code == 200
            
            # 8. Verify deleted
            response = test_client_real_services.get(f"/recording/download/{filename}")
            assert response.status_code == 404
