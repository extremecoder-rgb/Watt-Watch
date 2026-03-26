"""
Appliance Detector Module

Detects and classifies appliance types (projector, monitor, light, fans) and their
ON/OFF status using brightness analysis and edge detection.
"""

import numpy as np
from enum import Enum
from typing import Tuple, Optional, List
from dataclasses import dataclass


class ApplianceType(Enum):
    """Supported appliance types."""
    PROJECTOR = "projector"
    MONITOR = "monitor"
    LIGHT = "light"
    CEILING_FAN = "ceiling_fan"
    WALL_FAN = "wall_fan"
    UNKNOWN = "unknown"


class Status(Enum):
    """Appliance power status."""
    ON = "on"
    OFF = "off"
    UNKNOWN = "unknown"


@dataclass
class DetectionResult:
    """Result of appliance detection."""
    appliance_type: ApplianceType
    status: Status
    confidence: float
    roi: Tuple[int, int, int, int]


class ApplianceDetector:
    """
    Appliance detector using brightness pattern analysis and edge detection.
    
    Distinguishes between projectors, monitors, lights, and fans (which have
    distinguishing oscillating patterns and blade-like edges).
    """
    
    # Thresholds for classification
    ON_THRESHOLD = 100  # Mean brightness threshold for ON
    OFF_THRESHOLD = 50   # Mean brightness threshold for OFF
    
    # Brightness variance thresholds
    HIGH_VARIANCE_THRESHOLD = 500  # Indicates screen flicker
    
    def __init__(self):
        """Initialize the appliance detector."""
        pass
    
    def detect_appliance(self, frame: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> ApplianceType:
        """
        Detect the type of appliance in the given frame.
        
        Args:
            frame: Input frame as numpy array (H, W, C)
            roi: Optional region of interest (x1, y1, x2, y2)
            
        Returns:
            Detected appliance type
        """
        if roi is None:
            roi = self.get_roi(frame, ApplianceType.UNKNOWN)
        
        # Extract ROI from frame
        x1, y1, x2, y2 = roi
        roi_frame = frame[y1:y2, x1:x2]
        
        if roi_frame.size == 0:
            return ApplianceType.UNKNOWN
        
        # Convert to grayscale if needed
        if len(roi_frame.shape) == 3:
            gray = np.mean(roi_frame, axis=2).astype(np.uint8)
        else:
            gray = roi_frame
        
        # Analyze brightness patterns
        mean_brightness = np.mean(gray)
        
        # Calculate edge density (Canny-like edge detection using simple gradient)
        edge_density = self._calculate_edge_density(gray)
        
        # Check for fan characteristics
        is_fan = self._is_fan(gray, edge_density)
        if is_fan == "ceiling":
            return ApplianceType.CEILING_FAN
        elif is_fan == "wall":
            return ApplianceType.WALL_FAN
        
        # Analyze brightness distribution to distinguish projector/monitor/light
        brightness_distribution = self._analyze_brightness_distribution(gray)
        
        # Projector: bright white/blue light in center, lens glow pattern
        if brightness_distribution == "center_glow":
            return ApplianceType.PROJECTOR
        
        # Monitor: rectangular screen with bright center, darker edges
        if brightness_distribution == "center_bright_edges_dark":
            return ApplianceType.MONITOR
        
        # Light: bright circular/rectangular area, strong glow
        if brightness_distribution == "uniform_bright":
            return ApplianceType.LIGHT
        
        return ApplianceType.UNKNOWN
    
    def classify_status(self, frame: np.ndarray, appliance_type: ApplianceType, 
                        roi: Optional[Tuple[int, int, int, int]] = None) -> Status:
        """
        Classify the ON/OFF status of the appliance.
        
        Args:
            frame: Input frame as numpy array
            appliance_type: The detected appliance type
            roi: Optional region of interest (x1, y1, x2, y2)
            
        Returns:
            ON, OFF, or UNKNOWN status
        """
        if roi is None:
            roi = self.get_roi(frame, appliance_type)
        
        x1, y1, x2, y2 = roi
        roi_frame = frame[y1:y2, x1:x2]
        
        if roi_frame.size == 0:
            return Status.UNKNOWN
        
        # Convert to grayscale if needed
        if len(roi_frame.shape) == 3:
            gray = np.mean(roi_frame, axis=2).astype(np.uint8)
        else:
            gray = roi_frame
        
        # Calculate mean brightness
        mean_brightness = np.mean(gray)
        
        # Calculate brightness variance (for detecting screen flicker)
        variance = np.var(gray)
        
        # Status classification logic
        # ON: mean > 100 OR high variance (screen flicker)
        # OFF: brightness < 50
        if mean_brightness > self.ON_THRESHOLD or variance > self.HIGH_VARIANCE_THRESHOLD:
            return Status.ON
        elif mean_brightness < self.OFF_THRESHOLD:
            return Status.OFF
        
        return Status.UNKNOWN
    
    def detect(self, frame: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> DetectionResult:
        """
        Detect appliance type and status in a single call.
        
        Args:
            frame: Input frame
            roi: Optional region of interest
            
        Returns:
            DetectionResult with type, status, confidence, and ROI
        """
        if roi is None:
            # Try to detect type first, then get appropriate ROI
            detected_type = self.detect_appliance(frame, None)
            roi = self.get_roi(frame, detected_type)
        else:
            detected_type = self.detect_appliance(frame, roi)
        
        status = self.classify_status(frame, detected_type, roi)
        
        # Calculate confidence based on brightness metrics
        x1, y1, x2, y2 = roi
        roi_frame = frame[y1:y2, x1:x2]
        
        if roi_frame.size > 0:
            if len(roi_frame.shape) == 3:
                gray = np.mean(roi_frame, axis=2).astype(np.uint8)
            else:
                gray = roi_frame
            
            mean_brightness = np.mean(gray)
            variance = np.var(gray)
            
            # Confidence based on how clear the classification is
            if status == Status.ON:
                confidence = min(1.0, (mean_brightness / 200.0) + (variance / 2000.0))
            elif status == Status.OFF:
                confidence = min(1.0, (self.OFF_THRESHOLD - mean_brightness) / 50.0 + 0.5)
            else:
                confidence = 0.5
        else:
            confidence = 0.0
        
        return DetectionResult(
            appliance_type=detected_type,
            status=status,
            confidence=confidence,
            roi=roi
        )
    
    def get_roi(self, frame: np.ndarray, appliance_type: ApplianceType) -> Tuple[int, int, int, int]:
        """
        Get typical region of interest for the given appliance type.
        
        Args:
            frame: Input frame to get dimensions from
            appliance_type: Type of appliance
            
        Returns:
            Bounding box (x1, y1, x2, y2)
        """
        height, width = frame.shape[:2]
        
        # Default to center region
        center_x, center_y = width // 2, height // 2
        roi_width = width // 4
        roi_height = height // 4
        
        # Adjust ROI based on appliance type
        if appliance_type == ApplianceType.PROJECTOR:
            # Projector typically in center-upper area
            center_x = width // 2
            center_y = height // 3
            roi_width = width // 3
            roi_height = height // 3
        elif appliance_type == ApplianceType.MONITOR:
            # Monitor typically in center
            center_x = width // 2
            center_y = height // 2
            roi_width = width // 2
            roi_height = height // 2
        elif appliance_type == ApplianceType.LIGHT:
            # Light typically in center-upper area
            center_x = width // 2
            center_y = height // 4
            roi_width = width // 4
            roi_height = height // 3
        elif appliance_type == ApplianceType.CEILING_FAN:
            # Ceiling fan typically in center-upper area
            center_x = width // 2
            center_y = height // 4
            roi_width = width // 3
            roi_height = height // 3
        elif appliance_type == ApplianceType.WALL_FAN:
            # Wall fan typically on the side
            center_x = width // 4
            center_y = height // 2
            roi_width = width // 3
            roi_height = height // 2
        
        # Calculate bounding box
        x1 = max(0, center_x - roi_width // 2)
        y1 = max(0, center_y - roi_height // 2)
        x2 = min(width, center_x + roi_width // 2)
        y2 = min(height, center_y + roi_height // 2)
        
        return (x1, y1, x2, y2)
    
    def _calculate_edge_density(self, gray: np.ndarray) -> float:
        """
        Calculate edge density using simple gradient computation.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Edge density (proportion of edge pixels)
        """
        # Simple Sobel-like edge detection
        if gray.size == 0:
            return 0.0
        
        # Calculate gradients
        gx = np.abs(np.diff(gray, axis=1))
        gy = np.abs(np.diff(gray, axis=0))
        
        # Combine gradients
        edges = np.zeros_like(gray)
        edges[:, :-1] += gx
        edges[:-1, :] += gy
        
        # Normalize
        edges = edges / (edges.max() + 1e-6)
        
        # Count edge pixels above threshold
        edge_threshold = 0.1
        edge_pixels = np.sum(edges > edge_threshold)
        total_pixels = edges.size
        
        return edge_pixels / total_pixels
    
    def _is_fan(self, gray: np.ndarray, edge_density: float) -> Optional[str]:
        """
        Check if the image contains a fan (ceiling or wall).
        
        Args:
            gray: Grayscale ROI
            edge_density: Calculated edge density
            
        Returns:
            "ceiling", "wall", or None
        """
        # Fans have high edge density due to blade patterns
        if edge_density < 0.15:
            return None
        
        # Check for oscillating pattern (blades)
        # Analyze horizontal and vertical brightness profiles
        h_profile = np.mean(gray, axis=0)  # Horizontal profile
        v_profile = np.mean(gray, axis=1)  # Vertical profile
        
        # Check for periodic patterns (indicative of fan blades)
        h_variance = np.var(h_profile)
        v_variance = np.var(v_profile)
        
        # Ceiling fans have more circular blade patterns
        # Wall fans have more rectangular frame patterns
        if v_variance > h_variance * 1.5:
            return "ceiling"
        elif h_variance > v_variance * 1.5:
            return "wall"
        
        return None
    
    def _analyze_brightness_distribution(self, gray: np.ndarray) -> str:
        """
        Analyze brightness distribution pattern.
        
        Args:
            gray: Grayscale ROI
            
        Returns:
            Distribution type: "center_glow", "center_bright_edges_dark", "uniform_bright"
        """
        height, width = gray.shape
        
        # Split into center and edge regions
        center_x, center_y = width // 2, height // 2
        center_region = gray[
            center_y//2:3*center_y//2,
            center_x//2:3*center_x//2
        ]
        
        # Calculate brightness in different regions
        center_brightness = np.mean(center_region)
        
        # Compare to overall brightness
        overall_brightness = np.mean(gray)
        
        if center_brightness == 0:
            return "uniform_bright"
        
        ratio = center_brightness / (overall_brightness + 1e-6)
        
        # Analyze edge brightness
        edge_left = np.mean(gray[:, :width//4])
        edge_right = np.mean(gray[:, 3*width//4:])
        edge_top = np.mean(gray[:height//4, :])
        edge_bottom = np.mean(gray[3*height//4:, :])
        avg_edge = (edge_left + edge_right + edge_top + edge_bottom) / 4
        
        edge_ratio = center_brightness / (avg_edge + 1e-6)
        
        if ratio > 1.5 and edge_ratio > 1.8:
            return "center_glow"  # Projector - strong center glow
        elif ratio > 1.2 and edge_ratio > 1.3:
            return "center_bright_edges_dark"  # Monitor - bright center, darker edges
        else:
            return "uniform_bright"  # Light - uniform brightness


# Standalone functions for convenience
def detect_appliance(frame: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None) -> ApplianceType:
    """
    Detect appliance type in the given frame.
    
    Args:
        frame: Input frame
        roi: Optional region of interest
        
    Returns:
        Detected appliance type
    """
    detector = ApplianceDetector()
    return detector.detect_appliance(frame, roi)


def classify_status(frame: np.ndarray, appliance_type: ApplianceType, 
                    roi: Optional[Tuple[int, int, int, int]] = None) -> Status:
    """
    Classify the ON/OFF status of the appliance.
    
    Args:
        frame: Input frame
        appliance_type: Detected appliance type
        roi: Optional region of interest
        
    Returns:
        ON, OFF, or UNKNOWN status
    """
    detector = ApplianceDetector()
    return detector.classify_status(frame, appliance_type, roi)
