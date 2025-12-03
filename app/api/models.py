"""
Pydantic models dla API.
"""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"


class CameraHealthResponse(BaseModel):
    status: HealthStatus
    camera_index: Optional[int] = None
    fps: Optional[float] = None
    resolution: Optional[str] = None
    error: Optional[str] = None


class AppHealthResponse(BaseModel):
    status: HealthStatus
    app_name: str
    version: str
    camera_status: CameraHealthResponse


# ============== RECORDING ==============

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


class RecordingListResponse(BaseModel):
    recordings: List[RecordingFile]


# ============== CAMERA SETTINGS ==============

class CameraSettingsRequest(BaseModel):
    """Żądanie zmiany ustawień kamery."""
    contrast: Optional[int] = None      # 0-255
    fps: Optional[int] = None           # 15, 30, 60
    jpeg_quality: Optional[int] = None  # 50-100
    resolution: Optional[str] = None    # "HD" lub "FHD"
