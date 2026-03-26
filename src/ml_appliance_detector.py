"""
ML-based Appliance Detector using trained CNN model.

This provides an alternative to the rule-based detector using deep learning.
"""

import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import torch
from PIL import Image

from src.appliance_detector import ApplianceDetector as BaseDetector


class MLApplianceDetector:
    """
    Machine Learning based appliance detector using MobileNetV2.
    
    Uses a trained CNN model to classify appliance type and ON/OFF status.
    """
    
    def __init__(
        self,
        model_path: str = 'models/appliance_classifier.pt',
        device: Optional[str] = None
    ):
        """
        Initialize ML detector.
        
        Args:
            model_path: Path to trained model
            device: Device to use ('cpu', 'cuda')
        """
        self.model_path = model_path
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.type_classes = []
        self.image_size = 224
        
        # Try to load model
        self._try_load_model()
    
    def _try_load_model(self):
        """Try to load the trained model."""
        if not Path(self.model_path).exists():
            print(f"Warning: Model not found at {self.model_path}")
            print("Using rule-based detection as fallback")
            self.model = None
            return
        
        try:
            checkpoint = torch.load(
                self.model_path,
                map_location=self.device,
                weights_only=False
            )
            
            # Recreate model architecture
            from scripts.train_appliance import ApplianceClassifier
            
            self.model = ApplianceClassifier(
                checkpoint['num_types'],
                checkpoint['num_status'],
                pretrained=False
            )
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            self.type_classes = checkpoint.get('type_classes', [])
            self.image_size = checkpoint.get('image_size', 224)
            
            print(f"Loaded ML model from {self.model_path}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Using rule-based detection as fallback")
            self.model = None
    
    def _get_transform(self):
        """Get image preprocessing transform."""
        from torchvision import transforms
        return transforms.Compose([
            transforms.Resize((self.image_size, self.image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def detect(
        self,
        frame: np.ndarray,
        roi: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """
        Detect appliance type and status.
        
        Args:
            frame: Video frame (BGR format)
            roi: Optional region of interest
            
        Returns:
            Dictionary with 'appliance_type', 'status', and confidence scores
        """
        # Use ML model if available
        if self.model is not None:
            return self._detect_ml(frame, roi)
        else:
            # Fallback to rule-based
            return self._detect_rule_based(frame, roi)
    
    def _detect_ml(
        self,
        frame: np.ndarray,
        roi: Optional[Tuple[int, int, int, int]]
    ) -> Dict[str, Any]:
        """Detect using ML model."""
        # Extract ROI
        if roi is not None:
            x1, y1, x2, y2 = roi
            region = frame[y1:y2, x1:x2]
        else:
            region = frame
        
        # Convert to RGB and then to PIL Image
        import cv2
        region_rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(region_rgb)
        
        # Preprocess
        transform = self._get_transform()
        image_tensor = transform(pil_image).unsqueeze(0).to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(image_tensor)
            
            type_probs = torch.softmax(outputs['type_logits'], dim=1)
            status_probs = torch.softmax(outputs['status_logits'], dim=1)
            
            type_idx = type_probs.argmax().item()
            status_idx = status_probs.argmax().item()
            
            type_conf = type_probs[0, type_idx].item()
            status_conf = status_probs[0, status_idx].item()
        
        return {
            'appliance_type': self.type_classes[type_idx] if type_idx < len(self.type_classes) else 'unknown',
            'type_confidence': type_conf,
            'status': 'ON' if status_idx == 1 else 'OFF',
            'status_confidence': status_conf,
            'method': 'ml'
        }
    
    def _detect_rule_based(
        self,
        frame: np.ndarray,
        roi: Optional[Tuple[int, int, int, int]]
    ) -> Dict[str, Any]:
        """Detect using rule-based fallback."""
        base_detector = BaseDetector()
        
        # Use the base detector
        appliance_type = base_detector.detect_appliance(frame, roi)
        status = base_detector.classify_status(frame, appliance_type, roi)
        
        return {
            'appliance_type': appliance_type.value,
            'type_confidence': 0.5,
            'status': status.value,
            'status_confidence': 0.5,
            'method': 'rule_based'
        }
    
    def detect_from_image_path(
        self,
        image_path: str,
        roi: Optional[Tuple[int, int, int, int]] = None
    ) -> Dict[str, Any]:
        """Detect from image file path."""
        import cv2
        frame = cv2.imread(image_path)
        if frame is None:
            raise ValueError(f"Could not read image: {image_path}")
        return self.detect(frame, roi)


def create_ml_detector(
    model_path: str = 'models/appliance_classifier.pt',
    device: Optional[str] = None
) -> MLApplianceDetector:
    """Factory function to create ML detector."""
    return MLApplianceDetector(model_path, device)
