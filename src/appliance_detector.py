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
    ON = "ON"
    OFF = "OFF"
    UNKNOWN = "UNKNOWN"


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
        
        # Check brightness distribution for pattern classification
        brightness_distribution = self._analyze_brightness_distribution(gray)
        
        # Handle ceiling fan (circular pattern detected)
        if brightness_distribution == "ceiling_fan_pattern":
            return ApplianceType.CEILING_FAN
        
        # Handle wall fan
        if brightness_distribution == "wall_fan_pattern":
            return ApplianceType.WALL_FAN
        
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
        # Try using OpenCV Canny for better edge detection
        try:
            import cv2
            # Use Canny edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_pixels = np.sum(edges > 0)
            return edge_pixels / (gray.size + 1e-6)
        except ImportError:
            # Fallback: simple gradient-based edge detection
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
        if gray.size == 0:
            return "uniform_bright"
            
        height, width = gray.shape
        
        # Split into center and edge regions
        center_h = height // 3
        center_w = width // 3
        
        center_region = gray[center_h:-center_h, center_w:-center_w]
        
        if center_region.size == 0:
            return "uniform_bright"
        
        # Calculate brightness in different regions
        center_brightness = np.mean(center_region)
        
        # Calculate edge regions (all four sides)
        top_edge = np.mean(gray[:center_h, :])
        bottom_edge = np.mean(gray[-center_h:, :])
        left_edge = np.mean(gray[:, :center_w])
        right_edge = np.mean(gray[:, -center_w:])
        avg_edge = (top_edge + bottom_edge + left_edge + right_edge) / 4
        
        # Overall brightness
        overall_brightness = np.mean(gray)
        
        if overall_brightness == 0:
            return "uniform_bright"
        
        center_ratio = center_brightness / (overall_brightness + 1e-6)
        
        # Edge ratio: center brightness vs edge brightness
        if avg_edge == 0:
            edge_ratio = 2.0  # Strong center if edges are very dark
        else:
            edge_ratio = center_brightness / (avg_edge + 1e-6)
        
        # Calculate variance to detect uniform vs varied brightness
        brightness_variance = np.var(gray)
        
        # Check for circular/radial patterns (projector lens glow or ceiling fan)
        is_circular = self._has_circular_pattern(gray)
        
        # Check for horizontal lines (wall fan blades)
        has_horizontal_lines = self._has_horizontal_lines(gray)
        
        # Classification logic
        # CEILING FAN: circular pattern detected OR high edge density with variance
        if is_circular or (brightness_variance > 200 and center_ratio < 1.5):
            return "ceiling_fan_pattern"
        
        # WALL FAN: horizontal line pattern detected
        if has_horizontal_lines:
            return "wall_fan_pattern"
        
        # Light: uniform brightness (lower variance) and high overall brightness
        if brightness_variance < 500 and overall_brightness > 100:
            return "uniform_bright"
        
        # Projector: very bright center (ratio > 1.8), low variance (uniform glow)
        if center_ratio > 1.8 and brightness_variance < 1000:
            return "center_glow"
        
        # Monitor: bright center, darker edges (ratio > 1.2, edge ratio > 1.3)
        if center_ratio > 1.3 and edge_ratio > 1.4:
            return "center_bright_edges_dark"
        
        # If nothing else, default to light (most common bright appliance)
        if overall_brightness > 80:
            return "uniform_bright"
        
        return "uniform_bright"
    
    def _has_circular_pattern(self, gray: np.ndarray) -> bool:
        """Check for circular/radial pattern (projector lens or ceiling fan)."""
        try:
            import cv2
            # Use Hough circles to detect circular patterns
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=10, maxRadius=100)
            return circles is not None and len(circles[0]) >= 1
        except (ImportError, TypeError):
            return False
    
    def _has_horizontal_lines(self, gray: np.ndarray) -> bool:
        """Check for horizontal line pattern (wall fan blades)."""
        try:
            import cv2
            # Use Hough lines to detect horizontal lines
            lines = cv2.HoughLinesP(gray, 1, np.pi/180, threshold=20, minLineLength=15, maxLineGap=5)
            if lines is None:
                return False
            # Check if more than half the lines are approximately horizontal
            horizontal_count = 0
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.abs(np.arctan2(y2-y1, x2-x1) * 180 / np.pi)
                if angle < 20 or angle > 160:  # Nearly horizontal
                    horizontal_count += 1
            return horizontal_count > len(lines) / 2
        except (ImportError, TypeError):
            return False


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
