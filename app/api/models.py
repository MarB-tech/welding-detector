"""Pydantic models dla API."""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"


class CameraHealthResponse(BaseModel):
    status: HealthStatus
    camera_index: Optional[int] = None
    fps: Optional[float] = None
    resolution: Optional[str] = None
    is_recording: Optional[bool] = None
    error: Optional[str] = None


class RecordingStatusResponse(BaseModel):
    is_recording: bool
    duration_seconds: Optional[float] = None
    frames: int = 0


class RecordingStartResponse(BaseModel):
    status: str
    filename: str


class RecordingStopResponse(BaseModel):
    status: str
    filename: str
    duration_seconds: float
    frames: int
    size_mb: float


class RecordingFile(BaseModel):
    filename: str
    size_mb: float
    created: str
    note: str = ""


class RecordingListResponse(BaseModel):
    recordings: List[RecordingFile]


class CameraSettingsRequest(BaseModel):
    contrast: Optional[int] = None
    fps: Optional[int] = None
    jpeg_quality: Optional[int] = None
    resolution: Optional[str] = None


# ============== FRAME EXTRACTION ==============

class VideoInfoResponse(BaseModel):
    """Informacje o pliku wideo."""
    filename: str
    frame_count: int
    fps: float
    width: int
    height: int
    duration_seconds: float


class ExtractFramesRequest(BaseModel):
    """Request do ekstrakcji klatek."""
    step: int = 1              # Co która klatka (1 = każda)
    max_frames: Optional[int] = None  # Limit klatek
    output_folder: Optional[str] = None  # Folder docelowy (domyślnie: frames/{filename}/)
    prefix: str = "frame"      # Prefix nazwy pliku
    jpeg_quality: int = 95     # Jakość JPEG


class ExtractFramesResponse(BaseModel):
    """Response z wynikiem ekstrakcji."""
    status: str
    filename: str
    frames_extracted: int
    output_folder: str
    files: List[str]


class FrameResponse(BaseModel):
    """Informacje o pojedynczej klatce."""
    index: int
    timestamp_ms: float
    width: int
    height: int
