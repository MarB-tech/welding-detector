"""Tests for DefectClassifierService - basic functionality with mocked PyTorch."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import numpy as np
import torch


@pytest.mark.unit
class TestDefectClassifierService:
    """Test DefectClassifierService with mocked PyTorch."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create DefectClassifierService with mocked dependencies."""
        from app.services.defect_classifier_service import DefectClassifierService
        
        # Mock torch.load to avoid loading actual model
        with patch('torch.load', side_effect=FileNotFoundError()):
            service = DefectClassifierService()
            service.device = torch.device("cpu")
            service.model = None  # No model loaded
            service.class_names = ['porosity', 'crack', 'spatter']
            service.training_data_dir = tmp_path
            yield service

    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.device == torch.device("cpu")

    def test_get_model_info_no_model(self, service):
        """Test get_model_info when no model loaded."""
        service.model = None
        info = service.get_model_info()
        
        assert "model_loaded" in info
        assert info["model_loaded"] is False

    def test_get_model_info_with_model(self, service):
        """Test get_model_info when model is loaded."""
        service.model = Mock()
        service.defect_types = ['porosity', 'crack', 'spatter']
        
        info = service.get_model_info()
        
        assert info["model_loaded"] is True
        assert info["device"] == "cpu"

    def test_get_training_data_stats(self, service, tmp_path):
        """Test get_training_data_stats."""
        # The service expects: training_data_dir / "defects" / {class_name} / *.jpg
        # So if training_data_dir = tmp_path, files should be in tmp_path/defects/{class}/
        training_dir = tmp_path
        defects_base = training_dir / "defects"
        porosity_dir = defects_base / "porosity"
        crack_dir = defects_base / "crack"
        porosity_dir.mkdir(parents=True)
        crack_dir.mkdir(parents=True)
        
        # Add fake images
        for i in range(15):
            (porosity_dir / f"img_{i}.jpg").write_bytes(b"fake")
        for i in range(20):
            (crack_dir / f"img_{i}.jpg").write_bytes(b"fake")
        
        service.training_data_dir = training_dir
        stats = service.get_training_data_stats()
        
        # Check that stats contain sample counts
        assert "total_samples" in stats
        assert stats["total_samples"] == 35
        assert stats["class_counts"]["porosity"] == 15
        assert stats["class_counts"]["crack"] == 20

    def test_classify_frame_no_model(self, service):
        """Test predict when no model loaded."""
        service.model = None
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with pytest.raises(RuntimeError, match="No defect classifier available"):
            service.predict(fake_frame, with_gradcam=False)

    def test_train_insufficient_data(self, service, tmp_path):
        """Test train with insufficient data."""
        # Create directory with too few samples in labels/training_data/defects
        training_dir = tmp_path / "labels" / "training_data" / "defects"
        porosity_dir = training_dir / "porosity"
        porosity_dir.mkdir(parents=True)
        
        for i in range(3):
            (porosity_dir / f"img_{i}.jpg").write_bytes(b"fake")
        
        service.training_data_dir = training_dir
        
        with pytest.raises(ValueError, match="Insufficient training data"):
            service.train(epochs=10)

    def test_list_defect_types(self, service):
        """Test defect_types attribute."""
        service.defect_types = ['porosity', 'crack', 'spatter', 'undercut']
        
        types = service.defect_types
        
        assert len(types) >= 4
        assert 'porosity' in types

    def test_create_model(self, service):
        """Test create_model method."""
        service.num_classes = 3
        service.class_names = ['porosity', 'crack', 'spatter']
        
        with patch('timm.create_model') as mock_timm:
            mock_model = Mock()
            mock_model.to = Mock(return_value=mock_model)
            mock_timm.return_value = mock_model
            
            model = service.create_model()
            
            assert model is not None
            mock_timm.assert_called_once_with('efficientnet_b0', pretrained=True, num_classes=3)
            mock_model.to.assert_called_once()

    def test_train_with_sufficient_data(self, service, tmp_path):
        """Test train with sufficient data (mocked)."""
        # Create sufficient training data in defects subdirectory
        defects_dir = tmp_path / "defects"
        porosity_dir = defects_dir / "porosity"
        crack_dir = defects_dir / "crack"
        spatter_dir = defects_dir / "spatter"
        porosity_dir.mkdir(parents=True)
        crack_dir.mkdir()
        spatter_dir.mkdir()
        
        # Create dummy images
        from PIL import Image
        import numpy as np
        for i in range(20):
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(porosity_dir / f"img_{i}.jpg")
            img.save(crack_dir / f"img_{i}.jpg")
            img.save(spatter_dir / f"img_{i}.jpg")
        
        service.training_data_dir = tmp_path
        
        with patch.object(service, 'create_model') as mock_create_model, \
             patch('torch.save') as mock_save, \
             patch('torch.optim.AdamW') as mock_optimizer_class, \
             patch('torch.optim.lr_scheduler.ReduceLROnPlateau') as mock_scheduler_class:
            
            import torch
            
            # Create a callable mock that returns tensors with correct batch size
            def mock_forward(images):
                batch_size = images.shape[0]
                # num_classes will be 3 (porosity, crack, spatter)
                return torch.randn(batch_size, 3, requires_grad=True)
            
            mock_model = Mock()
            mock_model.parameters.return_value = [Mock()]
            mock_model.train = Mock()
            mock_model.eval = Mock()
            mock_model.to = Mock(return_value=mock_model)
            mock_model.side_effect = mock_forward
            mock_create_model.return_value = mock_model
            
            # Mock optimizer and scheduler
            mock_optimizer = Mock()
            mock_optimizer.zero_grad = Mock()
            mock_optimizer.step = Mock()
            mock_optimizer_class.return_value = mock_optimizer
            
            mock_scheduler = Mock()
            mock_scheduler.step = Mock()
            mock_scheduler_class.return_value = mock_scheduler
            
            # Mock DataLoader to return one batch
            with patch('torch.utils.data.DataLoader') as mock_loader_class:
                mock_train_loader = Mock()
                mock_val_loader = Mock()
                
                batch_images = torch.zeros(3, 3, 224, 224)
                batch_labels = torch.tensor([0, 1, 2])
                
                mock_train_loader.__iter__ = Mock(return_value=iter([(batch_images, batch_labels)]))
                mock_train_loader.__len__ = Mock(return_value=1)
                mock_val_loader.__iter__ = Mock(return_value=iter([(batch_images, batch_labels)]))
                mock_val_loader.__len__ = Mock(return_value=1)
                
                mock_loader_class.side_effect = [mock_train_loader, mock_val_loader]
                
                result = service.train(epochs=1, batch_size=8)
                
                # Verify training was attempted
                assert mock_create_model.called
                assert mock_model.train.called
                assert result is not None
                assert 'train_loss' in result

    def test_predict_with_model(self, service):
        """Test predict with loaded model."""
        import torch
        
        service.model = Mock()
        service.class_names = ['porosity', 'crack', 'spatter']
        service.num_classes = 3
        
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with patch('torch.no_grad'), \
             patch('cv2.cvtColor', return_value=fake_frame), \
             patch('cv2.resize', return_value=fake_frame), \
             patch.object(service, 'transform') as mock_transform:
            
            mock_tensor = torch.randn(3, 224, 224)
            mock_transform.return_value = mock_tensor
            
            # Mock model output
            mock_output = torch.tensor([[0.7, 0.2, 0.1]])
            service.model.return_value = mock_output
            
            result = service.predict(fake_frame, with_gradcam=False)
            
            assert "prediction" in result
            assert "confidence" in result
            assert result["prediction"] in service.class_names
