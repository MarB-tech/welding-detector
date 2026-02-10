"""Pydantic models for API."""

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
    """Information about a video file."""
    filename: str
    frame_count: int
    fps: float
    width: int
    height: int
    duration_seconds: float


class ExtractFramesRequest(BaseModel):
    """Request for frame extraction."""
    step: int = 1              # Every N-th frame (1 = every frame)
    max_frames: Optional[int] = None  # Maximum number of frames
    output_folder: Optional[str] = None  # Output folder (default: frames/{filename}/)
    prefix: str = "frame"      # File name prefix
    jpeg_quality: int = 95     # JPEG quality


class ExtractFramesResponse(BaseModel):
    """Response with extraction results."""
    status: str
    filename: str
    frames_extracted: int
    output_folder: str
    files: List[str]


class FrameResponse(BaseModel):
    """Information about a single frame."""
    index: int
    timestamp_ms: float
    width: int
    height: int


# ============== MOTION DETECTION ==============

class MotionSegmentResponse(BaseModel):
    """Video segment with detected motion."""
    start_frame: int
    end_frame: int
    start_time_ms: float
    end_time_ms: float
    duration_ms: float


class MotionAnalysisResponse(BaseModel):
    """Result of motion analysis in a video."""
    filename: str
    total_frames: int
    fps: float
    duration_seconds: float
    segments: List[MotionSegmentResponse]
    motion_percentage: float


class TrimToMotionRequest(BaseModel):
    """Request for trimming a video based on motion detection."""
    threshold: Optional[int] = None       # Detection threshold (0-255)
    min_area_percent: Optional[float] = None  # Min % of area with changes
    include_all_segments: bool = True     # True = all, False = longest
    output_filename: Optional[str] = None # Output file name


class TrimToMotionResponse(BaseModel):
    """Response with trimming results."""
    status: str
    input_filename: str
    output_filename: Optional[str] = None
    output_path: Optional[str] = None
    segments_count: Optional[int] = None
    frames_written: Optional[int] = None
    duration_seconds: Optional[float] = None
    original_size_mb: Optional[float] = None
    output_size_mb: Optional[float] = None
    reduction_percent: Optional[float] = None
    message: Optional[str] = None


# ============== IMAGE ENHANCEMENT ==============

class EnhancementPresetEnum(str, Enum):
    """Available image enhancement presets."""
    ORIGINAL = "original"           # No changes
    WELD_ENHANCE = "weld_enhance"   # Best for welds
    HIGH_CONTRAST = "high_contrast" # Strong contrast
    EDGE_OVERLAY = "edge_overlay"   # Colored weld edges
    HEATMAP = "heatmap"             # Pseudocolors
    DENOISE = "denoise"             # Noise reduction


class ImageEnhancementParams(BaseModel):
    """Image enhancement parameters - for manual tuning."""
    # CLAHE
    clahe: Optional[float] = None        # clip_limit (1.0-4.0), None = disabled
    clahe_grid: int = 8                  # Grid size
    
    # Sharpening
    sharpen: Optional[float] = None      # amount (0.5-3.0)
    
    # Unsharp mask
    unsharp: Optional[float] = None      # amount
    unsharp_radius: float = 1.0
    
    # Gamma
    gamma: Optional[float] = None        # <1 darker, >1 brighter
    
    # Contrast/Brightness
    contrast: Optional[float] = None     # alpha (1.0-3.0)
    brightness: int = 0                  # beta (-100 to 100)
    
    # Denoise
    denoise: Optional[int] = None        # strength (5-15)
    
    # Edge overlay
    edges: bool = False                  # Enable edge overlay
    edge_color: str = "green"            # green, red, blue, yellow
    
    # Heatmap
    heatmap: Optional[str] = None        # colormap: jet, hot, turbo, etc.


class EnhancementPresetsResponse(BaseModel):
    """List of available presets and options."""
    presets: List[str]
    colormaps: List[str]
    edge_colors: List[str]


# ============== LABELING ==============

class LabelType(str, Enum):
    """Label type."""
    OK = "ok"
    NOK = "nok"
    SKIP = "skip"


class DefectType(str, Enum):
    """Type of weld defect (when label = NOK)."""
    POROSITY = "porosity"           # Porosity - gas bubbles
    CRACK = "crack"                 # Cracks
    LACK_OF_FUSION = "lack_of_fusion"  # Lack of fusion
    UNDERCUT = "undercut"           # Undercut at the edge
    BURN_THROUGH = "burn_through"   # Burn through
    SPATTER = "spatter"             # Spatter
    IRREGULAR_BEAD = "irregular_bead"  # Irregular bead
    CONTAMINATION = "contamination" # Contamination
    OTHER = "other"                 # Other defect


class AddLabelRequest(BaseModel):
    """Request to add a label."""
    label: LabelType
    defect_type: Optional[DefectType] = None  # Required when label=nok
    notes: str = ""
    filters_used: Optional[dict] = None


class FrameLabelResponse(BaseModel):
    """Response with frame label."""
    video_filename: str
    frame_index: int
    label: str
    defect_type: Optional[str] = None
    timestamp: str
    notes: str = ""


class LabelingStatsResponse(BaseModel):
    """Labeling statistics."""
    total_labeled: int
    ok_count: int
    nok_count: int
    skip_count: int
    videos_labeled: int
    defect_counts: Optional[dict] = None  # number of each defect type


class TrainingDataResponse(BaseModel):
    """Training data information."""
    training_data_path: str
    ok_count: int
    nok_count: int
    total: int
    ready_for_training: bool
    defect_counts: Optional[dict] = None
