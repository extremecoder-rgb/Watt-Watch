"""
YOLOv8-based people detector for occupancy detection.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path


class YOLODetector:
    """YOLOv8 detector for people detection."""
    
    # COCO class ID for person
    PERSON_CLASS_ID = 0
    
    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence_threshold: float = 0.3,
        device: Optional[str] = None
    ):
        """
        Initialize the YOLOv8 detector.
        
        Args:
            model_name: YOLOv8 model variant (yolov8n.pt, yolov8s.pt, etc.)
            confidence_threshold: Minimum confidence for detections
            device: Device to run inference on ('cpu', 'cuda', or None for auto)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model = None
        self._model_loaded = False
    
    def load_model(self) -> None:
        """Load the YOLOv8 model."""
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_name)
            if self.device:
                self.model.to(self.device)
            self._model_loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLOv8 model: {e}")
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model_loaded
    
    def detect_people(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect people in a video frame.
        
        Args:
            frame: Video frame as numpy array (BGR format from OpenCV)
            
        Returns:
            List of detections, each containing bbox, confidence, class_id
        """
        if not self._model_loaded:
            self.load_model()
        
        # Run inference
        results = self.model(frame, verbose=False)
        
        detections = []
        if results and len(results) > 0:
            result = results[0]
            
            # Get boxes, confidence, and class IDs
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()  # xyxy format
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy()
                
                # Filter for person class
                for box, conf, cls_id in zip(boxes, confidences, class_ids):
                    if int(cls_id) == self.PERSON_CLASS_ID and conf >= self.confidence_threshold:
                        detections.append({
                            "bbox": box.tolist(),  # [x1, y1, x2, y2]
                            "confidence": float(conf),
                            "class_id": int(cls_id),
                            "class_name": "person"
                        })
        
        return detections
    
    def detect_and_count(self, frame: np.ndarray) -> int:
        """
        Detect people and return count.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Number of people detected
        """
        detections = self.detect_people(frame)
        return len(detections)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "loaded": self._model_loaded,
            "confidence_threshold": self.confidence_threshold,
            "person_class_id": self.PERSON_CLASS_ID,
            "device": self.device or "auto"
        }


def create_detector(
    model_name: str = "yolov8n.pt",
    confidence: float = 0.3,
    device: Optional[str] = None
) -> YOLODetector:
    """
    Factory function to create a YOLODetector instance.
    
    Args:
        model_name: YOLOv8 model variant
        confidence: Confidence threshold
        device: Device for inference
        
    Returns:
        Configured YOLODetector instance
    """
    detector = YOLODetector(
        model_name=model_name,
        confidence_threshold=confidence,
        device=device
    )
    return detector