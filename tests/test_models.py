"""Tests for models.py - Pydantic models."""

import pytest
from datetime import datetime
from app.api.models import (
    LabelType,
    DefectType,
    AddLabelRequest,
    FrameLabelResponse,
    HealthStatus,
    CameraHealthResponse,
    RecordingStatusResponse,
    RecordingStartResponse,
    RecordingStopResponse
)


class TestEnums:
    """Test enums."""
    
    @pytest.mark.unit
    def test_label_type_values(self):
        assert LabelType.OK.value == "ok"
        assert LabelType.NOK.value == "nok"
        assert LabelType.SKIP.value == "skip"
    
    @pytest.mark.unit
    def test_defect_type_values(self):
        assert DefectType.POROSITY.value == "porosity"
        assert DefectType.CRACK.value == "crack"
        assert DefectType.UNDERCUT.value == "undercut"
        assert DefectType.BURN_THROUGH.value == "burn_through"
    
    @pytest.mark.unit
    def test_health_status_values(self):
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestModels:
    """Test Pydantic models."""
    
    @pytest.mark.unit
    def test_add_label_request(self):
        req = AddLabelRequest(label=LabelType.OK)
        assert req.label == LabelType.OK
    
    @pytest.mark.unit
    def test_add_label_request_with_defect(self):
        req = AddLabelRequest(
            label=LabelType.NOK,
            defect_type=DefectType.POROSITY,
            notes="Test defect"
        )
        assert req.label == LabelType.NOK
        assert req.defect_type == DefectType.POROSITY
        assert req.notes == "Test defect"
    
    @pytest.mark.unit
    def test_camera_health_response(self):
        resp = CameraHealthResponse(
            status=HealthStatus.HEALTHY,
            camera_index=0,
            fps=30.0,
            resolution="1920x1080",
            is_recording=False
        )
        assert resp.status == HealthStatus.HEALTHY
        assert resp.camera_index == 0
        assert resp.fps == 30.0
    
    @pytest.mark.unit
    def test_recording_status_response(self):
        resp = RecordingStatusResponse(is_recording=True, duration_seconds=10.5, frames=315)
        assert resp.is_recording is True
        assert resp.duration_seconds == 10.5
        assert resp.frames == 315
    
    @pytest.mark.unit
    def test_recording_start_response(self):
        resp = RecordingStartResponse(status="started", filename="test.mp4")
        assert resp.status == "started"
        assert resp.filename == "test.mp4"
    
    @pytest.mark.unit
    def test_recording_stop_response(self):
        resp = RecordingStopResponse(
            status="stopped",
            filename="test.mp4",
            duration_seconds=10.0,
            frames=300,
            size_mb=5.0
        )
        assert resp.status == "stopped"
        assert resp.duration_seconds == 10.0
