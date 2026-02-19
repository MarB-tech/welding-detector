"""Tests for labeling_service.py - label management."""

import pytest
import json
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from app.services.labeling_service import LabelingService, FrameLabel, LabelingStats


class TestLabelingService:
    """Test LabelingService."""
    
    @pytest.mark.unit
    def test_init_creates_directories(self, tmp_path):
        labels_dir = tmp_path / "labels"
        service = LabelingService(labels_dir=labels_dir, recordings_dir=tmp_path)
        
        assert labels_dir.exists()
        assert (labels_dir / "training_data" / "ok").exists()
        assert (labels_dir / "training_data" / "nok").exists()
        assert (labels_dir / "training_data" / "defects" / "porosity").exists()
    
    @pytest.mark.unit
    def test_add_label_ok(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            label = service.add_label("test.mp4", 10, "ok", save_frame=False)
        
        assert label.video_filename == "test.mp4"
        assert label.frame_index == 10
        assert label.label == "ok"
        assert label.defect_type is None
    
    @pytest.mark.unit
    def test_add_label_nok_with_defect(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            label = service.add_label(
                "test.mp4", 20, "nok",
                defect_type="porosity",
                notes="Test defect",
                save_frame=False
            )
        
        assert label.label == "nok"
        assert label.defect_type == "porosity"
        assert label.notes == "Test defect"
    
    @pytest.mark.unit
    def test_get_label(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            service.add_label("test.mp4", 10, "ok", save_frame=False)
        
        label = service.get_label("test.mp4", 10)
        assert label is not None
        assert label.frame_index == 10
        
        # Non-existent label
        assert service.get_label("test.mp4", 999) is None
    
    @pytest.mark.unit
    def test_get_labels_for_video(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            service.add_label("video1.mp4", 10, "ok", save_frame=False)
            service.add_label("video1.mp4", 20, "nok", defect_type="crack", save_frame=False)
            service.add_label("video2.mp4", 15, "ok", save_frame=False)
        
        labels = service.get_labels_for_video("video1.mp4")
        assert len(labels) == 2
        assert all(l.video_filename == "video1.mp4" for l in labels)
    
    @pytest.mark.unit
    def test_remove_label(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            service.add_label("test.mp4", 10, "ok", save_frame=False)
        
        with patch.object(service, '_remove_training_image'):
            result = service.remove_label("test.mp4", 10)
        
        assert result is True
        assert service.get_label("test.mp4", 10) is None
        
        # Remove non-existent
        result = service.remove_label("test.mp4", 999)
        assert result is False
    
    @pytest.mark.unit
    def test_get_stats(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            service.add_label("video1.mp4", 10, "ok", save_frame=False)
            service.add_label("video1.mp4", 20, "ok", save_frame=False)
            service.add_label("video1.mp4", 30, "nok", defect_type="porosity", save_frame=False)
            service.add_label("video2.mp4", 5, "nok", defect_type="crack", save_frame=False)
            service.add_label("video2.mp4", 15, "skip", save_frame=False)
        
        stats = service.get_stats()
        assert stats.total_labeled == 5
        assert stats.ok_count == 2
        assert stats.nok_count == 2
        assert stats.skip_count == 1
        assert stats.videos_labeled == 2
        assert stats.defect_counts["porosity"] == 1
        assert stats.defect_counts["crack"] == 1
    
    @pytest.mark.unit
    def test_persistence(self, tmp_path):
        """Test that labels are saved and loaded correctly."""
        labels_dir = tmp_path / "labels"
        
        # Create and add label
        service1 = LabelingService(labels_dir=labels_dir, recordings_dir=tmp_path)
        with patch.object(service1, '_save_training_image'):
            service1.add_label("test.mp4", 10, "ok", save_frame=False)
        
        # Load in new instance
        service2 = LabelingService(labels_dir=labels_dir, recordings_dir=tmp_path)
        label = service2.get_label("test.mp4", 10)
        
        assert label is not None
        assert label.label == "ok"
    
    @pytest.mark.unit
    def test_update_label_removes_old_image(self, tmp_path):
        """Test that updating a label removes the old training image."""
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            with patch.object(service, '_remove_training_image') as mock_remove:
                # Add original
                service.add_label("test.mp4", 10, "ok", save_frame=False)
                
                # Update to nok
                service.add_label("test.mp4", 10, "nok", defect_type="crack", save_frame=False)
                
                # Should have removed old training image
                mock_remove.assert_called_once()
    
    @pytest.mark.unit
    def test_export_for_training(self, tmp_path):
        """Test that export_for_training returns correct statistics."""
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        
        with patch.object(service, '_save_training_image'):
            service.add_label("test.mp4", 10, "ok", save_frame=False)
            service.add_label("test.mp4", 20, "nok", defect_type="porosity", save_frame=False)
        
        export = service.export_for_training()
        
        assert "ok_count" in export
        assert "nok_count" in export
        assert "total" in export
        assert "ready_for_training" in export
    
    @pytest.mark.unit
    def test_get_label_key(self, tmp_path):
        service = LabelingService(labels_dir=tmp_path, recordings_dir=tmp_path)
        key = service._get_label_key("test.mp4", 10)
        assert key == "test.mp4:10"
