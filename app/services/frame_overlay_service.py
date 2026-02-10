"""
Frame Overlay Service - timestamp and recording indicator on frames.
"""

import cv2  # type: ignore
import numpy as np
from datetime import datetime
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)


class FrameOverlayService:
    """Applies timestamp and recording indicator to frames."""
    
    def __init__(self):
        self._is_recording = False
        self._recording_start: Optional[datetime] = None
        logger.info("FrameOverlayService initialized")
    
    @property
    def is_recording(self) -> bool:
        return self._is_recording
    
    def start_recording(self) -> None:
        self._is_recording = True
        self._recording_start = datetime.now()
        logger.info("Recording started")
    
    def stop_recording(self) -> Optional[float]:
        if not self._is_recording:
            return None
        self._is_recording = False
        duration = (datetime.now() - self._recording_start).total_seconds() if self._recording_start else 0
        self._recording_start = None
        logger.info(f"Recording stopped: {duration:.2f}s")
        return duration
    
    def get_recording_duration(self) -> Optional[float]:
        if not self._is_recording or not self._recording_start:
            return None
        return (datetime.now() - self._recording_start).total_seconds()
    
    def apply_overlay_to_jpeg(self, jpeg_bytes: bytes) -> bytes:
        """Applies overlay to a JPEG frame."""
        try:
            # Decode
            frame = cv2.imdecode(np.frombuffer(jpeg_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return jpeg_bytes
            
            h, w = frame.shape[:2]
            
            # Timestamp - top left corner
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}"
            cv2.putText(frame, timestamp, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.putText(frame, timestamp, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # REC indicator - top right corner (blinking)
            if self._is_recording and int(time.time() * 2) % 2:
                cv2.circle(frame, (w - 20, 20), 8, (0, 0, 255), -1)
                cv2.putText(frame, "REC", (w - 60, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # Recording duration
                duration = self.get_recording_duration()
                if duration:
                    dur_text = f"{int(duration // 60):02d}:{int(duration % 60):02d}"
                    cv2.putText(frame, dur_text, (w - 110, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Encode - high quality for minimal loss
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
            return buffer.tobytes()
            
        except Exception as e:
            logger.error(f"Overlay error: {e}")
            return jpeg_bytes


# Singleton
_overlay_service: Optional[FrameOverlayService] = None

def get_overlay_service() -> FrameOverlayService:
    global _overlay_service
    if _overlay_service is None:
        _overlay_service = FrameOverlayService()
    return _overlay_service
