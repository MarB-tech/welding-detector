"""
Testy jednostkowe - FrameOverlayService.
"""

import pytest
import cv2 # type: ignore
import numpy as np
import time
from unittest.mock import patch


class TestFrameOverlayService:
    """Testy dla FrameOverlayService."""
    
    # ============== OVERLAY TESTS ==============
    
    @pytest.mark.unit
    def test_overlay_adds_timestamp(self, valid_jpeg_bytes: bytes):
        """Sprawdza czy timestamp jest dodawany do obrazu."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        
        # Wynik powinien być bajtami JPEG
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Sprawdź czy to prawidłowy JPEG (zaczyna się od FFD8)
        assert result[:2] == b'\xff\xd8', "Wynik powinien być prawidłowym JPEG"
    
    @pytest.mark.unit
    def test_overlay_preserves_image_dimensions(self, valid_jpeg_bytes: bytes):
        """Sprawdza czy wymiary obrazu nie zmieniają się po overlay."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        # Dekoduj oryginał
        original = cv2.imdecode(np.frombuffer(valid_jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
        orig_h, orig_w = original.shape[:2]
        
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        
        # Dekoduj wynik
        processed = cv2.imdecode(np.frombuffer(result, np.uint8), cv2.IMREAD_COLOR)
        proc_h, proc_w = processed.shape[:2]
        
        assert orig_h == proc_h, f"Wysokość zmieniona: {orig_h} -> {proc_h}"
        assert orig_w == proc_w, f"Szerokość zmieniona: {orig_w} -> {proc_w}"
    
    @pytest.mark.unit
    def test_overlay_handles_invalid_jpeg(self, invalid_jpeg_bytes: bytes):
        """Sprawdza czy nieprawidłowy JPEG nie crashuje serwisu."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(invalid_jpeg_bytes)
        
        # Powinien zwrócić oryginał bez zmian
        assert result == invalid_jpeg_bytes
    
    @pytest.mark.unit
    def test_overlay_modifies_image(self, valid_jpeg_bytes: bytes):
        """Sprawdza czy obraz jest faktycznie modyfikowany (timestamp dodany)."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        service = FrameOverlayService()
        result = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        
        # Obrazy powinny być różne (timestamp zmienia piksele)
        original = cv2.imdecode(np.frombuffer(valid_jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
        processed = cv2.imdecode(np.frombuffer(result, np.uint8), cv2.IMREAD_COLOR)
        
        # Sprawdź różnicę w lewym górnym rogu (gdzie jest timestamp)
        diff = cv2.absdiff(original[:50, :300], processed[:50, :300])
        assert np.sum(diff) > 0, "Timestamp powinien zmienić piksele w lewym górnym rogu"
    
    # ============== RECORDING STATE TESTS ==============
    
    @pytest.mark.unit
    def test_start_stop_recording(self):
        """Sprawdza czy start/stop zmieniają stan is_recording."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        service = FrameOverlayService()
        
        assert service.is_recording is False, "Domyślnie nie powinno nagrywać"
        
        service.start_recording()
        assert service.is_recording is True, "Po start powinno nagrywać"
        
        duration = service.stop_recording()
        assert service.is_recording is False, "Po stop nie powinno nagrywać"
        assert duration is not None, "Stop powinien zwrócić duration"
        assert duration >= 0, "Duration powinno być >= 0"
    
    @pytest.mark.unit
    def test_recording_duration(self):
        """Sprawdza czy czas nagrywania jest prawidłowo liczony."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        service = FrameOverlayService()
        
        # Przed startem - None
        assert service.get_recording_duration() is None
        
        service.start_recording()
        time.sleep(0.1)  # 100ms
        
        duration = service.get_recording_duration()
        assert duration is not None
        assert duration >= 0.1, f"Duration powinno być >= 0.1s, jest {duration}"
        
        service.stop_recording()
        
        # Po stop - None
        assert service.get_recording_duration() is None
    
    @pytest.mark.unit
    def test_stop_without_start_returns_none(self):
        """Sprawdza czy stop bez start zwraca None."""
        from app.services.frame_overlay_service import FrameOverlayService
        
        service = FrameOverlayService()
        result = service.stop_recording()
        
        assert result is None, "Stop bez start powinien zwrócić None"
    
    # ============== REC INDICATOR TESTS ==============
    
    @pytest.mark.unit
    def test_rec_indicator_visible_when_recording(self, valid_jpeg_bytes: bytes):
        """Sprawdza czy REC indicator jest widoczny podczas nagrywania."""
        from app.services.frame_overlay_service import FrameOverlayService
        import time as time_module
        
        service = FrameOverlayService()
        
        # Klatka bez nagrywania
        no_rec = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
        
        # Klatka z nagrywaniem - testujemy wiele razy z opóźnieniem bo REC miga co 0.5s
        service.start_recording()
        
        # Zbierz kilka klatek z opóźnieniem - przynajmniej jedna powinna mieć REC
        frames_with_rec = []
        for _ in range(6):
            frame = service.apply_overlay_to_jpeg(valid_jpeg_bytes)
            frames_with_rec.append(frame)
            time_module.sleep(0.2)  # 200ms opóźnienia między klatkami
        
        service.stop_recording()
        
        # Dekoduj obraz bez nagrywania
        img_no_rec = cv2.imdecode(np.frombuffer(no_rec, np.uint8), cv2.IMREAD_COLOR)
        
        # Sprawdź czy przynajmniej jedna klatka ma różnicę w prawym górnym rogu
        any_diff = False
        for frame_bytes in frames_with_rec:
            img_with_rec = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            diff = cv2.absdiff(img_no_rec[:50, -100:], img_with_rec[:50, -100:])
            if np.sum(diff) > 0:
                any_diff = True
                break
        
        assert any_diff, "REC indicator powinien być widoczny przynajmniej w jednej klatce"
    
    # ============== SINGLETON TESTS ==============
    
    @pytest.mark.unit
    def test_singleton_pattern(self):
        """Sprawdza czy get_overlay_service zwraca tę samą instancję."""
        from app.services.frame_overlay_service import get_overlay_service
        
        service1 = get_overlay_service()
        service2 = get_overlay_service()
        
        assert service1 is service2, "Singleton powinien zwracać tę samą instancję"
    
    @pytest.mark.unit
    def test_singleton_state_persists(self):
        """Sprawdza czy stan singletona jest zachowany."""
        from app.services.frame_overlay_service import get_overlay_service
        
        service1 = get_overlay_service()
        service1.start_recording()
        
        service2 = get_overlay_service()
        assert service2.is_recording is True, "Stan powinien być zachowany między wywołaniami"
        
        service2.stop_recording()
