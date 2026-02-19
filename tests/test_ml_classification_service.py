"""Tests for MLClassificationService - basic functionality with mocked PyTorch."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from pathlib import Path
import numpy as np
import torch


@pytest.mark.unit
class TestMLClassificationService:
    """Test MLClassificationService with mocked PyTorch."""

    @pytest.fixture
    def mock_torch(self):
        """Mock torch module."""
        with patch('torch.load') as mock_load, \
             patch('torch.save') as mock_save, \
             patch('torch.no_grad'), \
             patch('torch.cuda.is_available', return_value=False):
            
            # Mock loaded model
            mock_model = Mock()
            mock_model.eval.return_value = None
            mock_model.train.return_value = None
            mock_load.return_value = {
                'model_state_dict': {},
                'class_names': ['OK', 'NOK'],
                'epoch': 10,
                'val_accuracy': 0.95
            }
            
            yield mock_load, mock_save, mock_model

    @pytest.fixture
    def service(self, tmp_path):
        """Create MLClassificationService with mocked dependencies."""
        from app.services.ml_classification_service import MLClassificationService
        import torch
        
        # Mock torch.load to avoid loading actual model
        with patch('torch.load', side_effect=FileNotFoundError()):
            service = MLClassificationService()
            service.device = torch.device("cpu")
            service.model = None  # No model loaded
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

    def test_get_training_data_stats(self, service, tmp_path):
        """Test get_training_data_stats."""
        # Create fake training directories
        ok_dir = tmp_path / "ok"
        nok_dir = tmp_path / "nok"
        ok_dir.mkdir()
        nok_dir.mkdir()
        
        # Add fake images
        for i in range(25):
            (ok_dir / f"img_{i}.jpg").write_bytes(b"fake")
        for i in range(30):
            (nok_dir / f"img_{i}.jpg").write_bytes(b"fake")
        
        service.training_data_dir = tmp_path
        stats = service.get_training_data_stats()
        
        assert stats["ok_samples"] == 25
        assert stats["nok_samples"] == 30
        assert stats["ready_for_training"] is True

    def test_predict_frame_no_model(self, service):
        """Test predict when no model loaded."""
        service.model = None
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with pytest.raises(RuntimeError, match="No model available"):
            service.predict(fake_frame, with_gradcam=False)

    def test_create_model(self, service):
        """Test create_model method."""
        with patch('timm.create_model') as mock_timm:
            mock_model = Mock()
            mock_model.to = Mock(return_value=mock_model)
            mock_timm.return_value = mock_model
            
            model = service.create_model()
            
            assert model is not None
            mock_timm.assert_called_once_with('efficientnet_b0', pretrained=True, num_classes=2)
            mock_model.to.assert_called_once()

    def test_train_with_sufficient_data(self, service, tmp_path):
        """Test train with sufficient data (mocked)."""
        # Create sufficient training data
        ok_dir = tmp_path / "ok"
        nok_dir = tmp_path / "nok"
        ok_dir.mkdir()
        nok_dir.mkdir()
        
        # Create dummy images
        from PIL import Image
        import numpy as np
        for i in range(25):
            img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
            img.save(ok_dir / f"img_{i}.jpg")
            img.save(nok_dir / f"img_{i}.jpg")
        
        service.training_data_dir = tmp_path
        
        with patch.object(service, 'create_model') as mock_create_model, \
             patch('torch.save') as mock_save, \
             patch('torch.optim.AdamW') as mock_optimizer_class, \
             patch('torch.optim.lr_scheduler.ReduceLROnPlateau') as mock_scheduler_class:
            
            import torch
            
            # Create a callable mock that returns tensors with correct batch size
            def mock_forward(images):
                batch_size = images.shape[0]
                return torch.randn(batch_size, 2, requires_grad=True)  # num_classes=2
            
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
            
            # Mock DataLoader to return one batch only
            with patch('torch.utils.data.DataLoader') as mock_loader_class:
                mock_train_loader = Mock()
                mock_val_loader = Mock()
                
                # Single batch for training and validation
                batch_images = torch.zeros(2, 3, 224, 224)
                batch_labels = torch.tensor([0, 1])
                
                mock_train_loader.__iter__ = Mock(return_value=iter([(batch_images, batch_labels)]))
                mock_train_loader.__len__ = Mock(return_value=1)
                mock_val_loader.__iter__ = Mock(return_value=iter([(batch_images, batch_labels)]))
                mock_val_loader.__len__ = Mock(return_value=1)
                
                mock_loader_class.side_effect = [mock_train_loader, mock_val_loader]
                
                result = service.train(epochs=1, batch_size=8, learning_rate=0.001)
                
                # Verify training was attempted
                assert mock_create_model.called
                assert mock_model.train.called
                assert result is not None
                assert 'train_loss' in result
