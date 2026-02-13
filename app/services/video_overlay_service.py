"""
Video Overlay Service - add timestamp to recorded video (post-processing).
"""

import cv2  # type: ignore
import threading
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable
from app.config.settings import settings

logger = logging.getLogger(__name__)


class VideoOverlayService:
    """Applies overlay to recorded video in the background."""
    
    def __init__(self, recordings_dir: Path):
        self.recordings_dir = recordings_dir
        self._processing: dict[str, dict] = {}  # filename -> status
        self._lock = threading.Lock()
        logger.info("VideoOverlayService initialized")
    
    def process_video(
        self,
        filename: str,
        start_time: Optional[datetime] = None,
        callback: Optional[Callable[[str, dict], None]] = None
    ) -> bool:
        """
        Start applying overlay to video in the background.
        
        Args:
            filename: Name of the video file
            start_time: Recording start time (for timestamps)
            callback: Function called upon completion
        
        Returns:
            True if processing started, False if file is already being processed or doesn't exist
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
        
        # run processing in a separate thread
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
        """Main video processing logic."""
        input_path = self.recordings_dir / filename
        
        # Output file with _overlay suffix
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_overlay{ext}"
        output_path = self.recordings_dir / output_filename
        
        cap = None
        writer = None
        
        try:
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise Exception("Cannot open video file")
            
            # Video parameters
            fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Output writer
            fourcc = cv2.VideoWriter.fourcc(*'mp4v')
            writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            if not writer.isOpened():
                raise Exception("Cannot create output file")
            
            # Base time for timestamps
            base_time = start_time or datetime.now()
            frame_duration = timedelta(seconds=1.0 / fps)
            
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate timestamp for this frame
                frame_time = base_time + (frame_duration * frame_idx)
                
                # Apply overlay
                frame = self._apply_overlay(frame, frame_time, frame_idx, fps)
                
                writer.write(frame)
                frame_idx += 1
                
                # Update progress
                if total_frames > 0:
                    progress = int((frame_idx / total_frames) * 100)
                    with self._lock:
                        if filename in self._processing:
                            self._processing[filename]["progress"] = progress
            
            # Success
            result = {
                "status": "completed",
                "output_filename": output_filename,
                "frames_processed": frame_idx,
                "duration_seconds": round(frame_idx / fps, 2)
            }
            
            with self._lock:
                self._processing[filename] = result
            
            logger.info(f"Video overlay completed: {output_filename} ({frame_idx} frames)")
            
            if callback:
                callback(filename, result)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Video overlay failed for {filename}: {error_msg}")
            
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
        """Apply timestamp overlay to a frame."""
        h, w = frame.shape[:2]
        
        # Timestamp - top left corner
        ts_text = timestamp.strftime("%Y-%m-%d %H:%M:%S.") + f"{timestamp.microsecond // 1000:03d}"
        
        # Text shadow (better contrast)
        cv2.putText(frame, ts_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                   settings.OVERLAY_FONT_SCALE_MEDIUM, settings.COLOR_BLACK, settings.OVERLAY_THICKNESS_SHADOW)
        cv2.putText(frame, ts_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                   settings.OVERLAY_FONT_SCALE_MEDIUM, settings.COLOR_WHITE, settings.OVERLAY_THICKNESS_THIN)
        
        # Frame number - bottom left corner
        frame_text = f"Frame: {frame_idx}"
        cv2.putText(frame, frame_text, (settings.OVERLAY_FRAME_TEXT_OFFSET, h - settings.OVERLAY_FRAME_TEXT_OFFSET), 
                   cv2.FONT_HERSHEY_SIMPLEX, settings.OVERLAY_FONT_SCALE_SMALL, 
                   settings.COLOR_BLACK, settings.OVERLAY_THICKNESS_THICK)
        cv2.putText(frame, frame_text, (settings.OVERLAY_FRAME_TEXT_OFFSET, h - settings.OVERLAY_FRAME_TEXT_OFFSET), 
                   cv2.FONT_HERSHEY_SIMPLEX, settings.OVERLAY_FONT_SCALE_SMALL, 
                   settings.COLOR_GRAY, settings.OVERLAY_THICKNESS_THIN)
        
        # Elapsed time - top right corner
        elapsed_seconds = frame_idx / fps
        elapsed_text = f"{int(elapsed_seconds // 60):02d}:{int(elapsed_seconds % 60):02d}.{int((elapsed_seconds % 1) * 10)}"
        text_size = cv2.getTextSize(elapsed_text, cv2.FONT_HERSHEY_SIMPLEX, settings.OVERLAY_FONT_SCALE_MEDIUM, 1)[0]
        cv2.putText(frame, elapsed_text, (w - text_size[0] - 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                   settings.OVERLAY_FONT_SCALE_MEDIUM, settings.COLOR_BLACK, settings.OVERLAY_THICKNESS_SHADOW)
        cv2.putText(frame, elapsed_text, (w - text_size[0] - 10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                   settings.OVERLAY_FONT_SCALE_MEDIUM, settings.COLOR_GREEN, settings.OVERLAY_THICKNESS_THIN)
        
        return frame
    
    def get_status(self, filename: str) -> Optional[dict]:
        """Get processing status."""
        with self._lock:
            return self._processing.get(filename)
    
    def get_all_status(self) -> dict:
        """Get status of all processing tasks."""
        with self._lock:
            return dict(self._processing)
    
    def clear_completed(self) -> int:
        """Remove completed processing tasks from the list."""
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
        _video_overlay_service = VideoOverlayService(Path("recordings"))
    return _video_overlay_service
