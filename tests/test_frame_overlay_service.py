"""Testy jednostkowe - FrameOverlayService."""

import pytest
import cv2
import numpy as np
import time
from app.services.frame_overlay_service import FrameOverlayService, get_overlay_service


class TestOverlay:
    """Testy nakładki timestamp/REC na obraz."""
    
    @pytest.mark.unit
    def test_returns_valid_jpeg(self, valid_jpeg_bytes):
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        
        assert isinstance(result, bytes) and len(result) > 0
        assert result[:2] == b'\xff\xd8'
    
    @pytest.mark.unit
    def test_preserves_dimensions(self, valid_jpeg_bytes):
        service = FrameOverlayService()
        original = cv2.imdecode(np.frombuffer(valid_jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
        result = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        processed = cv2.imdecode(np.frombuffer(result, np.uint8), cv2.IMREAD_COLOR)
        
        assert original is not None and processed is not None, "Failed to decode images"
        assert original.shape == processed.shape
    
    @pytest.mark.unit
    def test_handles_invalid_jpeg(self, invalid_jpeg_bytes):
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(invalid_jpeg_bytes)
        assert result == invalid_jpeg_bytes
    
    @pytest.mark.unit
    def test_modifies_image_with_timestamp(self, valid_jpeg_bytes):
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        
        original = cv2.imdecode(np.frombuffer(valid_jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
        processed = cv2.imdecode(np.frombuffer(result, np.uint8), cv2.IMREAD_COLOR)
        
        assert original is not None and processed is not None, "Failed to decode images"
        diff = cv2.absdiff(original[:50, :300], processed[:50, :300])
        assert np.sum(diff) > 0


class TestRecordingState:
    """Testy stanu nagrywania."""
    
    @pytest.mark.unit
    def test_start_stop_recording(self):
        service = FrameOverlayService()
        
        assert not service.is_recording
        service.start_recording()
        assert service.is_recording
        
        duration = service.stop_recording()
        assert not service.is_recording
        assert duration is not None and duration >= 0
    
    @pytest.mark.unit
    def test_recording_duration(self):
        service = FrameOverlayService()
        
        assert service.get_recording_duration() is None
        
        service.start_recording()
        time.sleep(0.1)
        duration = service.get_recording_duration()
        
        assert duration is not None and duration >= 0.1
        service.stop_recording()
        assert service.get_recording_duration() is None
    
    @pytest.mark.unit
    def test_stop_without_start(self):
        service = FrameOverlayService()
        assert service.stop_recording() is None


class TestSingleton:
    """Testy wzorca singleton."""
    
    @pytest.mark.unit
    def test_returns_same_instance(self):
        assert get_overlay_service() is get_overlay_service()
    
    @pytest.mark.unit
    def test_state_persists(self):
        service1 = get_overlay_service()
        service1.start_recording()
        
        service2 = get_overlay_service()
        assert service2.is_recording
        service2.stop_recording()
