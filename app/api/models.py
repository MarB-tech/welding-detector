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
