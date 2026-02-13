from pydantic_settings import BaseSettings #type: ignore
from typing import Tuple


class Settings(BaseSettings):
    # ============== Application ==============
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_TITLE: str = "Welding Detector API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============== USB Camera ==============
    CAMERA_INDEX: int = 0
    CAMERA_USB_FPS: int = 60
    CAMERA_USB_WIDTH: int = 1280
    CAMERA_USB_HEIGHT: int = 720
    CAMERA_JPEG_QUALITY: int = 95
    
    # Camera FPS settings
    CAMERA_DEFAULT_FPS: float = 30.0
    CAMERA_MIN_FPS: float = 10.0
    CAMERA_MAX_FPS: float = 60.0
    CAMERA_FPS_MEASURE_FRAMES: int = 60
    CAMERA_FPS_SMOOTHING_WINDOW: int = 30
    CAMERA_FPS_MIN_CLAMP: float = 5.0
    CAMERA_FPS_MAX_CLAMP: float = 120.0
    
    # ============== Motion Detection ==============
    MOTION_THRESHOLD_DEFAULT: int = 25
    MOTION_MIN_AREA_PERCENT: float = 0.5
    MOTION_PADDING_FRAMES: int = 30
    MOTION_ANALYZE_STEP: int = 1
    MOTION_MAX_GAP_SECONDS: float = 0.5
    
    # ============== Brightness Detection (Welding) ==============
    BRIGHTNESS_THRESHOLD_WELD: int = 150
    BRIGHTNESS_THRESHOLD_MIN: int = 100
    BRIGHTNESS_THRESHOLD_MAX: int = 255
    MIN_BRIGHT_PERCENT_WELD: float = 2.0
    MIN_BRIGHT_PERCENT_MIN: float = 0.5
    MIN_BRIGHT_PERCENT_MAX: float = 20.0
    RED_HOT_THRESHOLD_PERCENT: float = 3.0
    GAP_TOLERANCE_FRAMES: int = 10
    
    # ============== Image Enhancement ==============
    CLAHE_CLIP_LIMIT_DEFAULT: float = 2.0
    CLAHE_CLIP_LIMIT_MIN: float = 1.0
    CLAHE_CLIP_LIMIT_MAX: float = 4.0
    CLAHE_CLIP_LIMIT_WELD: float = 2.5
    CLAHE_CLIP_LIMIT_HIGH_CONTRAST: float = 4.0
    
    SHARPEN_AMOUNT_DEFAULT: float = 1.0
    SHARPEN_AMOUNT_MIN: float = 0.5
    SHARPEN_AMOUNT_MAX: float = 3.0
    
    GAMMA_DEFAULT: float = 1.0
    
    CONTRAST_ALPHA_DEFAULT: float = 1.0
    CONTRAST_ALPHA_MIN: float = 1.0
    CONTRAST_ALPHA_MAX: float = 3.0
    
    BRIGHTNESS_BETA_DEFAULT: int = 0
    BRIGHTNESS_BETA_MIN: int = -100
    BRIGHTNESS_BETA_MAX: int = 100
    
    DENOISE_STRENGTH_DEFAULT: int = 7
    DENOISE_STRENGTH_MIN: int = 5
    DENOISE_STRENGTH_MAX: int = 15
    
    EDGE_THRESHOLD1: int = 30
    EDGE_THRESHOLD2_DEFAULT: int = 100
    EDGE_THRESHOLD2_WELD: int = 150
    EDGE_OVERLAY_ALPHA: float = 0.7
    
    # ============== ML Training ==============
    ML_EPOCHS_DEFAULT: int = 20
    ML_EPOCHS_MIN: int = 5
    ML_EPOCHS_MAX: int = 100
    
    ML_LEARNING_RATE_DEFAULT: float = 0.001
    ML_LEARNING_RATE_MIN: float = 0.00001
    ML_LEARNING_RATE_MAX: float = 0.1
    
    ML_VALIDATION_SPLIT: float = 0.2
    ML_BATCH_SIZE: int = 32
    
    # Learning rate scheduler
    ML_LR_SCHEDULER_PATIENCE: int = 3
    ML_LR_SCHEDULER_FACTOR: float = 0.5
    
    # Data augmentation
    ML_AUGMENT_BRIGHTNESS: float = 0.2
    ML_AUGMENT_CONTRAST: float = 0.2
    
    # ============== Defect Classification ==============
    DEFECT_EPOCHS_DEFAULT: int = 30
    DEFECT_EPOCHS_MIN: int = 10
    DEFECT_EPOCHS_MAX: int = 100
    
    DEFECT_LEARNING_RATE_DEFAULT: float = 0.001
    DEFECT_VALIDATION_SPLIT: float = 0.2
    
    DEFECT_LR_SCHEDULER_PATIENCE: int = 5
    DEFECT_LR_SCHEDULER_FACTOR: float = 0.5
    
    DEFECT_AUGMENT_BRIGHTNESS: float = 0.3
    DEFECT_AUGMENT_CONTRAST: float = 0.3
    
    # ============== GradCAM ==============
    GRADCAM_ALPHA_DEFAULT: float = 0.4
    GRADCAM_ALPHA_MIN: float = 0.0
    GRADCAM_ALPHA_MAX: float = 1.0
    
    # ============== UI/Overlay Settings ==============
    # Text overlay positions
    OVERLAY_TIMESTAMP_POS: Tuple[int, int] = (10, 20)
    OVERLAY_REC_INDICATOR_RADIUS: int = 8
    OVERLAY_REC_INDICATOR_OFFSET: int = 20
    OVERLAY_REC_TEXT_OFFSET: int = 60
    OVERLAY_DURATION_OFFSET: int = 110
    OVERLAY_FRAME_TEXT_OFFSET: int = 10
    OVERLAY_PREDICTION_POS: Tuple[int, int] = (10, 30)
    
    # Text rendering
    OVERLAY_FONT_SCALE_SMALL: float = 0.5
    OVERLAY_FONT_SCALE_MEDIUM: float = 0.6
    OVERLAY_THICKNESS_THIN: int = 1
    OVERLAY_THICKNESS_THICK: int = 2
    OVERLAY_THICKNESS_SHADOW: int = 3
    
    # Colors (BGR format for OpenCV)
    COLOR_WHITE: Tuple[int, int, int] = (255, 255, 255)
    COLOR_BLACK: Tuple[int, int, int] = (0, 0, 0)
    COLOR_RED: Tuple[int, int, int] = (0, 0, 255)
    COLOR_GREEN: Tuple[int, int, int] = (0, 255, 0)
    COLOR_BLUE: Tuple[int, int, int] = (255, 0, 0)
    COLOR_YELLOW: Tuple[int, int, int] = (0, 255, 255)
    COLOR_CYAN: Tuple[int, int, int] = (255, 255, 0)
    COLOR_MAGENTA: Tuple[int, int, int] = (255, 0, 255)
    COLOR_GRAY: Tuple[int, int, int] = (200, 200, 200)
    
    # ============== API Limits ==============
    API_NOTE_MAX_LENGTH: int = 500
    API_STOP_CAMERA_DELAY: float = 0.2
    
    # ============== Video Analysis ==============
    VIDEO_PROGRESS_MULTIPLIER: int = 100
    MILLISECONDS_PER_SECOND: int = 1000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
