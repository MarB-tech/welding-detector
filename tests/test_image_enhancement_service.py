"""Tests for image_enhancement_service.py - image filters."""

import pytest
import numpy as np
import cv2
from app.services.image_enhancement_service import (
    ImageEnhancementService,
    EnhancementPreset,
    EnhancementParams
)


class TestImageEnhancementService:
    """Test ImageEnhancementService."""
    
    @pytest.fixture
    def test_frame(self):
        """Generates test frame 100x100."""
        return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    @pytest.fixture
    def service(self):
        return ImageEnhancementService()
    
    @pytest.mark.unit
    def test_init(self, service):
        assert service is not None
        assert len(service.PRESETS) > 0
    
    @pytest.mark.unit
    def test_presets_exist(self, service):
        """Test that all presets are defined."""
        assert EnhancementPreset.ORIGINAL in service.PRESETS
        assert EnhancementPreset.WELD_ENHANCE in service.PRESETS
        assert EnhancementPreset.HIGH_CONTRAST in service.PRESETS
        assert EnhancementPreset.EDGE_OVERLAY in service.PRESETS
        assert EnhancementPreset.HEATMAP in service.PRESETS
        assert EnhancementPreset.DENOISE in service.PRESETS
    
    @pytest.mark.unit
    def test_apply_preset_original(self, service, test_frame):
        """ORIGINAL preset should return the unchanged image."""
        result = service.apply_preset(test_frame, EnhancementPreset.ORIGINAL)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_apply_preset_weld_enhance(self, service, test_frame):
        """WELD_ENHANCE preset should return the enhanced image."""
        result = service.apply_preset(test_frame, EnhancementPreset.WELD_ENHANCE)
        assert result.shape == test_frame.shape
        assert result.dtype == test_frame.dtype
    
    @pytest.mark.unit
    def test_apply_preset_high_contrast(self, service, test_frame):
        """HIGH_CONTRAST preset should return the high contrast image."""
        result = service.apply_preset(test_frame, EnhancementPreset.HIGH_CONTRAST)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_apply_preset_edge_overlay(self, service, test_frame):
        """EDGE_OVERLAY preset should return the image with edge overlay."""
        result = service.apply_preset(test_frame, EnhancementPreset.EDGE_OVERLAY)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_apply_preset_heatmap(self, service, test_frame):
        """HEATMAP preset should return the image with heatmap applied."""
        result = service.apply_preset(test_frame, EnhancementPreset.HEATMAP)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_apply_preset_denoise(self, service, test_frame):
        """DENOISE preset should return the denoised image."""
        result = service.apply_preset(test_frame, EnhancementPreset.DENOISE)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_no_params(self, service, test_frame):
        """Test enhance with no parameters."""
        params = EnhancementParams()
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_clahe(self, service, test_frame):
        """Test enhance with CLAHE parameters."""
        params = EnhancementParams(clahe_enabled=True, clahe_clip_limit=2.0)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_sharpen(self, service, test_frame):
        """Test enhance with sharpen parameters."""
        params = EnhancementParams(sharpen_enabled=True, sharpen_amount=1.5)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_unsharp(self, service, test_frame):
        """Test enhance with unsharp parameters."""
        params = EnhancementParams(unsharp_enabled=True, unsharp_amount=1.5)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_gamma(self, service, test_frame):
        """Test enhance with gamma parameters."""
        params = EnhancementParams(gamma_enabled=True, gamma_value=1.2)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_contrast(self, service, test_frame):
        """Test enhance with contrast parameters."""
        params = EnhancementParams(contrast_enabled=True, contrast_alpha=1.5, contrast_beta=10)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_denoise(self, service, test_frame):
        """Test enhance with denoise parameters."""
        params = EnhancementParams(denoise_enabled=True, denoise_strength=9)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_edge_overlay(self, service, test_frame):
        """Test enhance with edge overlay parameters."""
        params = EnhancementParams(
            edge_overlay_enabled=True,
            edge_threshold1=50,
            edge_threshold2=150
        )
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_heatmap(self, service, test_frame):
        """Test enhance with heatmap parameters."""
        params = EnhancementParams(heatmap_enabled=True, heatmap_colormap=cv2.COLORMAP_JET)
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
    
    @pytest.mark.unit
    def test_enhance_combined_filters(self, service, test_frame):
        """Test enhance with combined filters."""
        params = EnhancementParams(
            clahe_enabled=True,
            sharpen_enabled=True,
            denoise_enabled=True,
            contrast_enabled=True
        )
        result = service.enhance(test_frame, params)
        assert result.shape == test_frame.shape
