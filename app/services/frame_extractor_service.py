"""
Frame Extractor Service - extracts frames from MP4 video files into memory (list of numpy arrays)
and optionally saves them to a folder as JPEGs. Uses OpenCV for video processing.
"""

import cv2  # type: ignore
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Generator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FrameData:
    """Frame data with metadata."""
    index: int           # Frame number (0-based)
    frame: np.ndarray    # BGR image as numpy array
    timestamp_ms: float  # Position in milliseconds


class FrameExtractorService:
    """
    Service for extracting frames from video files.
    
    Usage:
        extractor = FrameExtractorService()
        frames = extractor.extract_frames("recordings/rec_20260105_120000.mp4")
        extractor.save_frames_to_folder(frames, "output/frames")
    """
    
    def __init__(self, recordings_dir: Path = Path("recordings")):
        self.recordings_dir = recordings_dir
        logger.info("🎞️ FrameExtractorService initialized")
    
    def extract_frames(
        self, 
        video_path: str | Path, 
        step: int = 1,
        max_frames: Optional[int] = None
    ) -> list[FrameData]:
        """
        Extract frames from a video file into memory.
        
        Args:
            video_path: Path to the video file (absolute or relative to recordings_dir)
            step: Extract every N-th frame (1 = every frame, 2 = every second frame, etc.)
            max_frames: Maximum number of frames to extract (None = all)
            
        Returns:
            List of FrameData with frames and metadata
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file cannot be opened as a video
        """
        path = self._resolve_path(video_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")
        
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {path}")
        
        try:
            frames: list[FrameData] = []
            frame_index = 0
            extracted_count = 0
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Extracting frames from {path.name} ({total_frames} frames, {fps:.1f} fps)")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Extract only every N-th frame
                if frame_index % step == 0:
                    timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    frames.append(FrameData(
                        index=frame_index,
                        frame=frame.copy(),
                        timestamp_ms=timestamp_ms
                    ))
                    extracted_count += 1
                    
                    if max_frames and extracted_count >= max_frames:
                        break
                
                frame_index += 1
            
            logger.info(f"Extracted {len(frames)} frames (step={step})")
            return frames
            
        finally:
            cap.release()
    
    def get_frame(self, filename: str, frame_index: int) -> Optional[np.ndarray]:
        """
        Get a single frame from a video.
        
        Args:
            filename: Name of the video file
            frame_index: Index of the frame
            
        Returns:
            Frame as a numpy array (BGR) or None if not found
        """
        video_path = self.recordings_dir / filename
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return None
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return None
        
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            
            if not ret:
                logger.error(f"Cannot read frame {frame_index} from {filename}")
                return None
            
            return frame
        finally:
            cap.release()
    
    def extract_frames_generator(
        self, 
        video_path: str | Path,
        step: int = 1
    ) -> Generator[FrameData, None, None]:
        """
        Frame generator - for large files (saves RAM).
        
        Yields:
            FrameData with consecutive frames
        """
        path = self._resolve_path(video_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")
        
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {path}")
        
        try:
            frame_index = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_index % step == 0:
                    timestamp_ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    yield FrameData(
                        index=frame_index,
                        frame=frame,
                        timestamp_ms=timestamp_ms
                    )
                
                frame_index += 1
        finally:
            cap.release()
    
    def save_frames_to_folder(
        self,
        frames: list[FrameData],
        output_dir: str | Path,
        prefix: str = "frame",
        jpeg_quality: int = 95
    ) -> list[Path]:
        """
        Save frames as JPEG files.
        
        Args:
            frames: List of FrameData to save
            output_dir: Target folder (will be created if it doesn't exist)
            prefix: File name prefix (e.g., "frame" -> "frame_00001.jpg")
            jpeg_quality: JPEG quality (1-100)
            
        Returns:
            List of paths to the saved files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files: list[Path] = []
        
        for frame_data in frames:
            filename = f"{prefix}_{frame_data.index:05d}.jpg"
            filepath = output_path / filename
            
            cv2.imwrite(
                str(filepath),
                frame_data.frame,
                [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
            )
            saved_files.append(filepath)
        
        logger.info(f"Saved {len(saved_files)} frames to {output_path}")
        return saved_files
    
    def get_video_info(self, video_path: str | Path) -> dict:
        """
        Get video file information.
        
        Returns:
            Dict with: frame_count, fps, width, height, duration_seconds
        """
        path = self._resolve_path(video_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")
        
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {path}")
        
        try:
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            return {
                "frame_count": frame_count,
                "fps": round(fps, 2),
                "width": width,
                "height": height,
                "duration_seconds": round(duration, 2)
            }
        finally:
            cap.release()
    
    def _resolve_path(self, video_path: str | Path) -> Path:
        """Resolve path - absolute or relative to recordings_dir."""
        path = Path(video_path)
        if path.is_absolute():
            return path
        
        # First, check if it exists relative to CWD
        if path.exists():
            return path
        
        # Then, relative to recordings_dir
        return self.recordings_dir / path


# Singleton
_frame_extractor_service: Optional[FrameExtractorService] = None


def get_frame_extractor_service() -> FrameExtractorService:
    """Singleton getter for FrameExtractorService."""
    global _frame_extractor_service
    if _frame_extractor_service is None:
        _frame_extractor_service = FrameExtractorService()
    return _frame_extractor_service
