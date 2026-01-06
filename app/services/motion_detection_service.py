"""
Motion Detection Service - wykrywanie ruchu w nagraniach wideo.

Serwis do detekcji segmentów z ruchem w nagraniach spawalniczych.
Używa cv2.absdiff do porównywania kolejnych klatek.
"""

import cv2  # type: ignore
import numpy as np
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MotionSegment:
    """Segment wideo z ruchem."""
    start_frame: int
    end_frame: int
    start_time_ms: float
    end_time_ms: float
    duration_ms: float


@dataclass
class MotionAnalysisResult:
    """Wynik analizy ruchu w wideo."""
    filename: str
    total_frames: int
    fps: float
    duration_seconds: float
    segments: list[MotionSegment]
    motion_percentage: float  # Procent klatek z ruchem


class MotionDetectionService:
    """
    Serwis do detekcji ruchu w nagraniach wideo.
    
    Użycie:
        service = MotionDetectionService()
        result = service.detect_motion("recordings/rec_20260105_120000.mp4")
        
        # Przytnij wideo do segmentów z ruchem
        service.trim_to_motion("input.mp4", "output.mp4")
    """
    
    def __init__(
        self,
        recordings_dir: Path = Path("recordings"),
        threshold: int = 25,           # Próg różnicy pikseli
        min_area_percent: float = 0.5, # Min % powierzchni ze zmianą
        min_segment_frames: int = 5,   # Min klatek na segment
        padding_frames: int = 30       # Padding przed/po segmencie (0.5s @60fps)
    ):
        self.recordings_dir = recordings_dir
        self.threshold = threshold
        self.min_area_percent = min_area_percent
        self.min_segment_frames = min_segment_frames
        self.padding_frames = padding_frames
        logger.info("🔍 MotionDetectionService initialized")
    
    def detect_motion(
        self,
        video_path: str | Path,
        threshold: Optional[int] = None,
        min_area_percent: Optional[float] = None,
        analyze_step: int = 1
    ) -> MotionAnalysisResult:
        """
        Analizuje wideo i wykrywa segmenty z ruchem.
        
        Args:
            video_path: Ścieżka do pliku wideo
            threshold: Próg różnicy pikseli (0-255)
            min_area_percent: Minimalny % powierzchni ze zmianą
            analyze_step: Co która klatka analizować (1 = każda)
            
        Returns:
            MotionAnalysisResult z listą segmentów
        """
        path = self._resolve_path(video_path)
        threshold = threshold or self.threshold
        min_area = min_area_percent or self.min_area_percent
        
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {path}")
        
        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"🎬 Analyzing motion in {path.name} ({total_frames} frames)")
            
            # Wczytaj pierwszą klatkę
            ret, prev_frame = cap.read()
            if not ret:
                raise ValueError("Cannot read first frame")
            
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)
            
            frame_height, frame_width = prev_frame.shape[:2]
            total_pixels = frame_width * frame_height
            min_changed_pixels = int(total_pixels * min_area / 100)
            
            motion_frames: list[int] = []
            frame_idx = 1
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_idx % analyze_step == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)
                    
                    # Różnica między klatkami
                    diff = cv2.absdiff(prev_gray, gray)
                    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
                    
                    # Policz piksele ze zmianą
                    changed_pixels = cv2.countNonZero(thresh)
                    
                    if changed_pixels >= min_changed_pixels:
                        motion_frames.append(frame_idx)
                    
                    prev_gray = gray
                
                frame_idx += 1
            
            # Grupuj klatki w segmenty
            segments = self._group_into_segments(motion_frames, total_frames, fps)
            
            motion_pct = (len(motion_frames) / (total_frames / analyze_step) * 100) if total_frames > 0 else 0
            
            logger.info(f"✅ Found {len(segments)} motion segments ({motion_pct:.1f}% motion)")
            
            return MotionAnalysisResult(
                filename=path.name,
                total_frames=total_frames,
                fps=fps,
                duration_seconds=duration,
                segments=segments,
                motion_percentage=round(motion_pct, 2)
            )
        finally:
            cap.release()
    
    def _group_into_segments(
        self, 
        motion_frames: list[int], 
        total_frames: int,
        fps: float
    ) -> list[MotionSegment]:
        """Grupuje klatki z ruchem w ciągłe segmenty."""
        if not motion_frames:
            return []
        
        segments = []
        start = motion_frames[0]
        end = motion_frames[0]
        
        # Max przerwa między klatkami w jednym segmencie (0.5s)
        max_gap = int(fps * 0.5)
        
        for frame in motion_frames[1:]:
            if frame - end <= max_gap:
                end = frame
            else:
                # Dodaj padding i zapisz segment
                seg_start = max(0, start - self.padding_frames)
                seg_end = min(total_frames - 1, end + self.padding_frames)
                
                if seg_end - seg_start >= self.min_segment_frames:
                    segments.append(MotionSegment(
                        start_frame=seg_start,
                        end_frame=seg_end,
                        start_time_ms=seg_start / fps * 1000,
                        end_time_ms=seg_end / fps * 1000,
                        duration_ms=(seg_end - seg_start) / fps * 1000
                    ))
                
                start = frame
                end = frame
        
        # Ostatni segment
        seg_start = max(0, start - self.padding_frames)
        seg_end = min(total_frames - 1, end + self.padding_frames)
        
        if seg_end - seg_start >= self.min_segment_frames:
            segments.append(MotionSegment(
                start_frame=seg_start,
                end_frame=seg_end,
                start_time_ms=seg_start / fps * 1000,
                end_time_ms=seg_end / fps * 1000,
                duration_ms=(seg_end - seg_start) / fps * 1000
            ))
        
        # Scal nakładające się segmenty
        return self._merge_overlapping(segments, fps)
    
    def _merge_overlapping(self, segments: list[MotionSegment], fps: float) -> list[MotionSegment]:
        """Scala nakładające się lub bliskie segmenty."""
        if len(segments) <= 1:
            return segments
        
        merged = [segments[0]]
        
        for seg in segments[1:]:
            last = merged[-1]
            # Jeśli segmenty nakładają się lub są blisko
            if seg.start_frame <= last.end_frame + self.padding_frames:
                # Rozszerz ostatni segment
                merged[-1] = MotionSegment(
                    start_frame=last.start_frame,
                    end_frame=max(last.end_frame, seg.end_frame),
                    start_time_ms=last.start_time_ms,
                    end_time_ms=max(last.end_frame, seg.end_frame) / fps * 1000,
                    duration_ms=(max(last.end_frame, seg.end_frame) - last.start_frame) / fps * 1000
                )
            else:
                merged.append(seg)
        
        return merged
    
    def trim_to_motion(
        self,
        video_path: str | Path,
        output_path: Optional[str | Path] = None,
        threshold: Optional[int] = None,
        min_area_percent: Optional[float] = None,
        include_all_segments: bool = True
    ) -> dict:
        """
        Przycina wideo do segmentów z ruchem.
        
        Args:
            video_path: Ścieżka do wideo źródłowego
            output_path: Ścieżka wyjściowa (domyślnie: {input}_trimmed.mp4)
            threshold: Próg detekcji ruchu
            min_area_percent: Min % powierzchni ze zmianą
            include_all_segments: True = wszystkie segmenty, False = tylko najdłuższy
            
        Returns:
            Słownik z informacjami o przyciętym wideo
        """
        path = self._resolve_path(video_path)
        
        # Wykryj segmenty
        analysis = self.detect_motion(path, threshold, min_area_percent)
        
        if not analysis.segments:
            logger.warning(f"⚠️ No motion detected in {path.name}")
            return {
                "status": "no_motion",
                "filename": path.name,
                "message": "No motion segments detected"
            }
        
        # Wybierz segmenty
        if include_all_segments:
            segments = analysis.segments
        else:
            # Tylko najdłuższy segment
            segments = [max(analysis.segments, key=lambda s: s.duration_ms)]
        
        # Ustal ścieżkę wyjściową
        if output_path:
            out_path = Path(output_path)
        else:
            out_path = path.parent / f"{path.stem}_trimmed.mp4"
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Otwórz źródło
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # type: ignore
            writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
            
            if not writer.isOpened():
                raise ValueError("Cannot create output video")
            
            frames_written = 0
            
            for seg in segments:
                cap.set(cv2.CAP_PROP_POS_FRAMES, seg.start_frame)
                
                for _ in range(seg.end_frame - seg.start_frame + 1):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    writer.write(frame)
                    frames_written += 1
            
            writer.release()
            
            # Informacje o wyniku
            output_size = out_path.stat().st_size / (1024 * 1024)
            original_size = path.stat().st_size / (1024 * 1024)
            
            logger.info(f"✂️ Trimmed {path.name} -> {out_path.name} ({frames_written} frames)")
            
            return {
                "status": "completed",
                "input_filename": path.name,
                "output_filename": out_path.name,
                "output_path": str(out_path),
                "segments_count": len(segments),
                "frames_written": frames_written,
                "duration_seconds": round(frames_written / fps, 2),
                "original_size_mb": round(original_size, 2),
                "output_size_mb": round(output_size, 2),
                "reduction_percent": round((1 - output_size / original_size) * 100, 1) if original_size > 0 else 0
            }
        finally:
            cap.release()
    
    def _resolve_path(self, video_path: str | Path) -> Path:
        """Rozwiązuje ścieżkę do pliku wideo."""
        path = Path(video_path)
        # Jeśli ścieżka absolutna lub już istnieje - użyj jej
        if path.is_absolute() or path.exists():
            return path
        # W przeciwnym razie szukaj w recordings_dir
        return self.recordings_dir / path


# Singleton dla FastAPI dependency injection
_motion_detection_service: Optional[MotionDetectionService] = None


def get_motion_detection_service() -> MotionDetectionService:
    """FastAPI dependency - zwraca singleton MotionDetectionService."""
    global _motion_detection_service
    if _motion_detection_service is None:
        _motion_detection_service = MotionDetectionService()
    return _motion_detection_service
