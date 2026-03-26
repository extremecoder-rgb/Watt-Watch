"""
Video validation utilities for WattWatch.

Provides functions to validate video files and extract metadata.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import cv2


def validate_video(path: str) -> bool:
    """
    Check if a video file is valid and readable.
    
    Args:
        path: Path to video file
        
    Returns:
        True if video is valid, False otherwise
    """
    if not os.path.exists(path):
        return False
    
    try:
        cap = cv2.VideoCapture(path)
        is_valid = cap.isOpened()
        cap.release()
        return is_valid
    except Exception:
        return False


def get_video_info(path: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a video file.
    
    Args:
        path: Path to video file
        
    Returns:
        Dictionary with video metadata or None if invalid
    """
    if not os.path.exists(path):
        return None
    
    try:
        cap = cv2.VideoCapture(path)
        
        if not cap.isOpened():
            cap.release()
            return None
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        
        # Calculate duration
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return {
            "path": path,
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": duration,
            "fourcc": fourcc,
            "valid": True
        }
    except Exception as e:
        return {
            "path": path,
            "valid": False,
            "error": str(e)
        }


def validate_directory(dir_path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate all video files in a directory.
    
    Args:
        dir_path: Path to directory
        extensions: List of video extensions to check (default: common video formats)
        
    Returns:
        Dictionary with validation results
    """
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    if not os.path.isdir(dir_path):
        return {
            "valid": False,
            "error": f"Directory not found: {dir_path}"
        }
    
    results = {
        "directory": dir_path,
        "valid_videos": [],
        "invalid_videos": [],
        "total": 0
    }
    
    for filename in os.listdir(dir_path):
        filepath = os.path.join(dir_path, filename)
        
        # Check if it's a video file
        if any(filename.lower().endswith(ext) for ext in extensions):
            results["total"] += 1
            
            if validate_video(filepath):
                results["valid_videos"].append(filename)
            else:
                results["invalid_videos"].append(filename)
    
    return results


def check_video_quality(path: str, min_fps: float = 15, min_width: int = 640) -> Dict[str, Any]:
    """
    Check if video meets minimum quality requirements.
    
    Args:
        path: Path to video file
        min_fps: Minimum frames per second
        min_width: Minimum frame width
        
    Returns:
        Dictionary with quality check results
    """
    info = get_video_info(path)
    
    if not info or not info.get("valid"):
        return {
            "passed": False,
            "reason": "Invalid video file"
        }
    
    issues = []
    
    if info["fps"] < min_fps:
        issues.append(f"FPS too low: {info['fps']:.1f} < {min_fps}")
    
    if info["width"] < min_width:
        issues.append(f"Resolution too low: {info['width']} < {min_width}")
    
    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "video_info": info
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_validator.py <video_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    
    if validate_video(path):
        info = get_video_info(path)
        if info and info.get("valid"):
            print(f"Valid video: {path}")
            print(f"  Resolution: {info['width']}x{info['height']}")
            print(f"  FPS: {info['fps']:.2f}")
            print(f"  Frames: {info['frame_count']}")
            print(f"  Duration: {info['duration']:.2f}s")
        else:
            print(f"Could not get video info: {path}")
    else:
        print(f"Invalid video: {path}")