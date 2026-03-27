"""
Privacy-first face anonymization module.
Uses Haar cascade for face detection with maximum blur.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import cv2
import os

_CASCADE_CACHE: List[cv2.CascadeClassifier] = []
_CASCADE_LOADED = False

def _load_cascades_once() -> bool:
    global _CASCADE_CACHE, _CASCADE_LOADED
    if _CASCADE_LOADED:
        return len(_CASCADE_CACHE) > 0
    
    cv2_data_path = os.path.join(os.path.dirname(cv2.__file__), "data")
    cascade_files = ["haarcascade_frontalface_alt.xml", "haarcascade_frontalface_default.xml"]
    
    for cf in cascade_files:
        cp = os.path.join(cv2_data_path, cf)
        if os.path.exists(cp):
            c = cv2.CascadeClassifier(cp)
            if not c.empty():
                _CASCADE_CACHE.append(c)
    
    _CASCADE_LOADED = True
    return len(_CASCADE_CACHE) > 0

class PrivacyFilter:
    def __init__(
        self,
        blur_method: str = "solid",
        blur_level: int = 99,
        pixelate_blocks: int = 4,
        face_height_ratio: float = 0.25,
        face_width_ratio: float = 0.35,
        skip_frames: int = 2
    ):
        self.blur_method = blur_method
        self.blur_level = max(3, blur_level if blur_level % 2 == 1 else blur_level + 1)
        self.pixelate_blocks = max(2, pixelate_blocks)
        self.face_height_ratio = face_height_ratio
        self.face_width_ratio = face_width_ratio
        self.skip_frames = skip_frames
        self._frame_count = 0
        self._cached_faces: List[Dict[str, Any]] = []
        self._face_cascades = _CASCADE_CACHE
        self._haar_loaded = _load_cascades_once()
    
    @property
    def is_loaded(self) -> bool:
        return self._haar_loaded
    
    def detect_faces_with_haar(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        if not self._haar_loaded or not self._face_cascades:
            return []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        
        cascade = self._face_cascades[0]
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40), flags=cv2.CASCADE_SCALE_IMAGE)
        
        return [{"bbox": [int(x), int(y), int(x + w), int(y + h)], "confidence": 1.0} for (x, y, w, h) in faces]
    
    def estimate_faces_from_persons(self, person_bboxes: List[List[float]]) -> List[List[float]]:
        face_bboxes = []
        for bbox in person_bboxes:
            x1, y1, x2, y2 = map(int, bbox)
            person_h = y2 - y1
            person_w = x2 - x1
            face_h = int(person_h * self.face_height_ratio)
            face_w = int(person_w * self.face_width_ratio)
            face_x1 = x1 + (person_w - face_w) // 2
            face_y1 = y1 + int(person_h * 0.05)
            face_x2 = face_x1 + face_w
            face_y2 = face_y1 + face_h
            if face_w > 20 and face_h > 20:
                face_bboxes.append([face_x1, face_y1, face_x2, face_y2])
        return face_bboxes
    
    def detect_faces(self, frame: np.ndarray, person_bboxes: Optional[List[List[float]]] = None) -> List[Dict[str, Any]]:
        self._frame_count += 1
        
        if self._frame_count % self.skip_frames == 0:
            haar_detections = self.detect_faces_with_haar(frame)
            if haar_detections:
                self._cached_faces = haar_detections
            elif person_bboxes:
                face_bboxes = self.estimate_faces_from_persons(person_bboxes)
                self._cached_faces = [{"bbox": bbox, "confidence": 0.7, "method": "estimation"} for bbox in face_bboxes]
            else:
                self._cached_faces = []
        
        return self._cached_faces
    
    def _apply_solid_blur(self, face_roi: np.ndarray) -> np.ndarray:
        h, w = face_roi.shape[:2]
        avg_color = np.mean(face_roi, axis=(0, 1))
        solid = np.full((h, w, 3), avg_color, dtype=np.uint8)
        solid = cv2.GaussianBlur(solid, (31, 31), 0)
        return solid
    
    def anonymize_frame(
        self,
        frame: np.ndarray,
        person_bboxes: Optional[List[List[float]]] = None,
        face_bboxes: Optional[List[List[float]]] = None
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        if face_bboxes:
            detections = [{"bbox": bbox, "confidence": 1.0, "method": "provided"} for bbox in face_bboxes]
        else:
            detections = self.detect_faces(frame, person_bboxes)
        
        anonymized = frame.copy()
        
        for face in detections:
            bbox = face["bbox"]
            x1, y1, x2, y2 = map(int, bbox)
            
            # Maximum padding - cover entire head
            pad_x = int((x2 - x1) * 0.6)
            pad_y = int((y2 - y1) * 0.5)
            
            x1 = max(0, x1 - pad_x)
            y1 = max(0, y1 - pad_y)
            x2 = min(frame.shape[1], x2 + pad_x)
            y2 = min(frame.shape[0], y2 + pad_y)
            
            if x2 <= x1 or y2 <= y1:
                continue
            
            face_roi = anonymized[y1:y2, x1:x2]
            
            # Solid blur - completely replaces with average color
            blurred = self._apply_solid_blur(face_roi)
            
            anonymized[y1:y2, x1:x2] = blurred
        
        return anonymized, detections
    
    def verify_anonymization(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not detections:
            return {"verified": True, "message": "No faces to anonymize", "faces_before": 0, "faces_after": 0}
        
        anonymized, _ = self.anonymize_frame(frame, face_bboxes=[d["bbox"] for d in detections])
        remaining = self.detect_faces_with_haar(anonymized)
        
        return {
            "verified": len(remaining) == 0,
            "message": "Identity leak prevented" if len(remaining) == 0 else "WARNING: faces still detectable",
            "faces_before": len(detections),
            "faces_after": len(remaining)
        }
    
    def get_config(self) -> Dict[str, Any]:
        return {
            "blur_method": self.blur_method,
            "blur_level": self.blur_level,
            "pixelate_blocks": self.pixelate_blocks,
            "face_height_ratio": self.face_height_ratio,
            "face_width_ratio": self.face_width_ratio,
            "haar_available": self._haar_loaded
        }

def create_privacy_filter(blur_method: str = "solid", blur_level: int = 99, pixelate_blocks: int = 4) -> PrivacyFilter:
    return PrivacyFilter(blur_method=blur_method, blur_level=blur_level, pixelate_blocks=pixelate_blocks)
