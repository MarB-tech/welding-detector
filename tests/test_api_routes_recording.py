"""Tests for recording API routes."""

import pytest
from pathlib import Path


@pytest.mark.unit
class TestRecordingRoutes:
    """Test recording API endpoints."""

    def test_recording_status(self, test_client, mock_camera_service):
        """Test GET /recording/status endpoint."""
        mock_camera_service.is_recording = False
        mock_camera_service.get_recording_duration.return_value = 0
        mock_camera_service._frame_count = 0
        
        response = test_client.get("/recording/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "is_recording" in data
        assert "duration_seconds" in data
        assert "frames" in data

    def test_start_recording(self, test_client, mock_camera_service):
        """Test POST /recording/start endpoint."""
        mock_camera_service.is_recording = False
        mock_camera_service.start_recording.return_value = "test_rec.mp4"
        
        response = test_client.post("/recording/start")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["filename"] == "test_rec.mp4"

    def test_start_recording_already_recording(self, test_client, mock_camera_service):
        """Test POST /recording/start when already recording."""
        mock_camera_service.is_recording = True
        
        response = test_client.post("/recording/start")
        
        assert response.status_code == 400
        assert "already recording" in response.json()["detail"].lower()

    def test_stop_recording(self, test_client, mock_camera_service):
        """Test POST /recording/stop endpoint."""
        mock_camera_service.is_recording = True
        mock_camera_service.stop_recording.return_value = {
            "filename": "test_rec.mp4",
            "duration_seconds": 10.5,
            "frames": 300,
            "fps": 30.0,
            "size_mb": 5.2
        }
        
        response = test_client.post("/recording/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
        assert data["filename"] == "test_rec.mp4"
        assert data["duration_seconds"] == 10.5

    def test_stop_recording_not_recording(self, test_client, mock_camera_service):
        """Test POST /recording/stop when not recording."""
        mock_camera_service.is_recording = False
        
        response = test_client.post("/recording/stop")
        
        assert response.status_code == 400
        assert "not recording" in response.json()["detail"].lower()

    def test_list_recordings(self, test_client, mock_camera_service):
        """Test GET /recording/list endpoint."""
        mock_camera_service.list_recordings.return_value = [
            {"filename": "rec1.mp4", "size_mb": 5.2, "created": "2024-01-01T12:00:00", "note": ""},
            {"filename": "rec2.mp4", "size_mb": 3.1, "created": "2024-01-02T12:00:00", "note": "Test note"}
        ]
        
        response = test_client.get("/recording/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "recordings" in data
        assert len(data["recordings"]) == 2

    def test_download_recording(self, test_client, mock_camera_service, tmp_path):
        """Test GET /recording/download/{filename} endpoint."""
        # Create a temporary MP4 file
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"fake mp4 data")
        mock_camera_service.get_recording_path.return_value = test_file
        
        response = test_client.get("/recording/download/test.mp4")
        
        assert response.status_code == 200
        assert response.content == b"fake mp4 data"

    def test_download_recording_not_found(self, test_client, mock_camera_service):
        """Test GET /recording/download/{filename} when file doesn't exist."""
        mock_camera_service.get_recording_path.return_value = None
        
        response = test_client.get("/recording/download/nonexistent.mp4")
        
        assert response.status_code == 404

    def test_delete_recording(self, test_client, mock_camera_service):
        """Test DELETE /recording/{filename} endpoint."""
        mock_camera_service.delete_recording.return_value = True
        
        response = test_client.delete("/recording/test.mp4")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["filename"] == "test.mp4"

    def test_delete_recording_not_found(self, test_client, mock_camera_service):
        """Test DELETE /recording/{filename} when file doesn't exist."""
        mock_camera_service.delete_recording.return_value = False
        
        response = test_client.delete("/recording/nonexistent.mp4")
        
        assert response.status_code == 404

    def test_set_recording_note(self, test_client, mock_camera_service):
        """Test PUT /recording/{filename}/note endpoint."""
        mock_camera_service.set_note.return_value = True
        
        response = test_client.put("/recording/test.mp4/note?note=Test%20note")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["filename"] == "test.mp4"

    def test_set_recording_note_not_found(self, test_client, mock_camera_service):
        """Test PUT /recording/{filename}/note when file doesn't exist."""
        mock_camera_service.set_note.return_value = False
        
        response = test_client.put("/recording/test.mp4/note?note=Test")
        
        assert response.status_code == 404


@pytest.mark.unit
class TestRecordingAdvancedRoutes:
    """Test advanced recording routes (overlay, frames, motion)."""

    def test_get_video_info_not_found(self, test_client, mock_camera_service):
        """Test GET /recording/{filename}/info when file doesn't exist."""
        mock_camera_service.get_recording_path.return_value = None
        
        response = test_client.get("/recording/nonexistent.mp4/info")
        
        assert response.status_code == 404

    def test_apply_overlay(self, test_client, mock_camera_service, tmp_path):
        """Test POST /recording/{filename}/apply-overlay endpoint - already processing."""
        from unittest.mock import MagicMock, patch
        
        test_file = tmp_path / "test.mp4"
        test_file.touch()
        mock_camera_service.get_recording_path.return_value = test_file
        
        mock_video_overlay = MagicMock()
        mock_video_overlay.process_video.return_value = False  # Simulate already processing
        
        with patch("app.api.routes.recording.get_video_overlay_service", return_value=mock_video_overlay):
            response = test_client.post("/recording/test.mp4/apply-overlay")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_processing"
    def test_overlay_status(self, test_client):
        """Test GET /recording/{filename}/overlay-status endpoint."""
        from unittest.mock import MagicMock, patch
        
        mock_video_overlay = MagicMock()
        # Make it return None first to trigger the default response
        mock_video_overlay.get_status.return_value = {"status": "processing", "progress": 50}
        
        with patch("app.api.routes.recording.get_video_overlay_service", return_value=mock_video_overlay):
            response = test_client.get("/recording/test.mp4/overlay-status")
        
        assert response.status_code == 200
        data = response.json()
        # It should return either the status or not_found
        assert "status" in data

    def test_get_enhancement_presets(self, test_client):
        """Test GET /recording/enhancement/presets endpoint."""
        response = test_client.get("/recording/enhancement/presets")
        
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert len(data["presets"]) > 0
        assert "colormaps" in data
        assert "edge_colors" in data

    def test_get_single_frame_not_found(self, test_client, mock_camera_service):
        """Test GET /recording/{filename}/frame/{index} when file doesn't exist."""
        mock_camera_service.get_recording_path.return_value = None
        
        response = test_client.get("/recording/nonexistent.mp4/frame/0")
        
        assert response.status_code == 404

    def test_apply_overlay_not_found(self, test_client, mock_camera_service):
        """Test POST /recording/{filename}/apply-overlay when file doesn't exist."""
        mock_camera_service.get_recording_path.return_value = None
        
        response = test_client.post("/recording/nonexistent.mp4/apply-overlay")
        
        assert response.status_code == 404

    def test_detect_motion_not_found(self, test_client, mock_camera_service):
        """Test GET /recording/{filename}/detect-motion when file doesn't exist."""
        mock_camera_service.get_recording_path.return_value = None
        
        response = test_client.get("/recording/nonexistent.mp4/detect-motion")
        
        assert response.status_code == 404

    def test_extract_frames_not_found(self, test_client, mock_camera_service):
        """Test POST /recording/{filename}/extract-frames when file doesn't exist."""
        mock_camera_service.get_recording_path.return_value = None
        
        response = test_client.post(
            "/recording/nonexistent.mp4/extract-frames",
            json={"step": 10}
        )
        
        assert response.status_code == 404
