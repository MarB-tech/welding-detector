"""
Video Overlay Service - Nakładanie timestamp na nagrane wideo (post-processing).
"""

import cv2  # type: ignore
import threading
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class VideoOverlayService:
    """Nakłada overlay na nagrane wideo w tle."""
    
    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir
        self._processing: dict[str, dict] = {}  # filename -> status
        self._lock = threading.Lock()
        logger.info("🎬 VideoOverlayService initialized")
    
    def process_video(
        self,
        filename: str,
        start_time: Optional[datetime] = None,
        callback: Optional[Callable[[str, dict], None]] = None
    ) -> bool:
        """
        Rozpocznij nakładanie overlay na wideo w tle.
        
        Args:
            filename: Nazwa pliku wideo
            start_time: Czas rozpoczęcia nagrywania (dla timestampów)
            callback: Funkcja wywoływana po zakończeniu
        
        Returns:
            True jeśli przetwarzanie rozpoczęte
        """
        with self._lock:
            if filename in self._processing:
                return False
            
            input_path = self.recordings_dir / filename
            if not input_path.exists():
                return False
            
            self._processing[filename] = {
                "status": "processing",
                "progress": 0,
                "started_at": datetime.now().isoformat()
            }
        
        # Uruchom w tle
        thread = threading.Thread(
            target=self._process_video_thread,
            args=(filename, start_time, callback),
            daemon=True
        )
        thread.start()
        return True
    
    def _process_video_thread(
        self,
        filename: str,
        start_time: Optional[datetime],
        callback: Optional[Callable[[str, dict], None]]
    ):
        """Główna logika przetwarzania wideo."""
        input_path = self.recordings_dir / filename
        
        # Plik wyjściowy z sufiksem _overlay
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_overlay{ext}"
        output_path = self.recordings_dir / output_filename
        
        cap = None
        writer = None
        
        try:
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise Exception("Nie można otworzyć pliku wideo")
            
            # Parametry wideo
            fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Writer dla wyjścia
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            if not writer.isOpened():
                raise Exception("Nie można utworzyć pliku wyjściowego")
            
            # Czas bazowy dla timestampów
            base_time = start_time or datetime.now()
            frame_duration = timedelta(seconds=1.0 / fps)
            
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Oblicz timestamp dla tej klatki
                frame_time = base_time + (frame_duration * frame_idx)
                
                # Nakładanie overlay
                frame = self._apply_overlay(frame, frame_time, frame_idx, fps)
                
                writer.write(frame)
                frame_idx += 1
                
                # Update progress
                if total_frames > 0:
                    progress = int((frame_idx / total_frames) * 100)
                    with self._lock:
                        if filename in self._processing:
                            self._processing[filename]["progress"] = progress
            
            # Sukces
            result = {
                "status": "completed",
                "output_filename": output_filename,
                "frames_processed": frame_idx,
                "duration_seconds": round(frame_idx / fps, 2)
            }
            
            with self._lock:
                self._processing[filename] = result
            
            logger.info(f"✅ Video overlay completed: {output_filename} ({frame_idx} frames)")
            
            if callback:
                callback(filename, result)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Video overlay failed for {filename}: {error_msg}")
            
            with self._lock:
                self._processing[filename] = {
                    "status": "failed",
                    "error": error_msg
                }
            
            if callback:
                callback(filename, {"status": "failed", "error": error_msg})
                
        finally:
            if cap:
                cap.release()
            if writer:
                writer.release()
    
    def _apply_overlay(
        self,
        frame,
        timestamp: datetime,
        frame_idx: int,
        fps: float
    ):
        """Nakłada timestamp na klatkę."""
        h, w = frame.shape[:2]
        
        # Timestamp - lewy górny róg
        ts_text = timestamp.strftime("%Y-%m-%d %H:%M:%S.") + f"{timestamp.microsecond // 1000:03d}"
        
        # Cień tekstu (lepsze kontrastowanie)
        cv2.putText(frame, ts_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(frame, ts_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Numer klatki - lewy dolny róg
        frame_text = f"Frame: {frame_idx}"
        cv2.putText(frame, frame_text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        cv2.putText(frame, frame_text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Czas nagrania - prawy górny róg
        elapsed_seconds = frame_idx / fps
        elapsed_text = f"{int(elapsed_seconds // 60):02d}:{int(elapsed_seconds % 60):02d}.{int((elapsed_seconds % 1) * 10)}"
        text_size = cv2.getTextSize(elapsed_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        cv2.putText(frame, elapsed_text, (w - text_size[0] - 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(frame, elapsed_text, (w - text_size[0] - 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        return frame
    
    def get_status(self, filename: str) -> Optional[dict]:
        """Pobierz status przetwarzania."""
        with self._lock:
            return self._processing.get(filename)
    
    def get_all_status(self) -> dict:
        """Pobierz status wszystkich przetwarzań."""
        with self._lock:
            return dict(self._processing)
    
    def clear_completed(self) -> int:
        """Usuń zakończone przetwarzania z listy."""
        with self._lock:
            to_remove = [k for k, v in self._processing.items() 
                        if v.get("status") in ("completed", "failed")]
            for k in to_remove:
                del self._processing[k]
            return len(to_remove)


# Singleton
_video_overlay_service: Optional[VideoOverlayService] = None

def get_video_overlay_service() -> VideoOverlayService:
    global _video_overlay_service
    if _video_overlay_service is None:
        from app.services.video_recorder_service import RECORDINGS_DIR
        _video_overlay_service = VideoOverlayService(RECORDINGS_DIR)
    return _video_overlay_service
