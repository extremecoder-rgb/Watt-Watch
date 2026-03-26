"""
WattWatch - Intelligent Occupancy Detection System

YOLOv8-based real-time people detection and counting.
"""

__version__ = "0.1.0"
__author__ = "WattWatch Team"

from src.detector import YOLODetector
from src.utils import FPSCounter, VideoFrameExtractor, JSONLogger

__all__ = [
    "YOLODetector",
    "FPSCounter",
    "VideoFrameExtractor",
    "JSONLogger",
]