"""
Utility functions for WattWatch occupancy detection system.
"""

import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import cv2


class FPSCounter:
    """Counter for tracking frames per second."""
    
    def __init__(self, window_size: int = 30):
        """
        Initialize FPS counter.
        
        Args:
            window_size: Number of frames to average over
        """
        self.window_size = window_size
        self.frame_times: List[float] = []
        self.start_time = time.time()
        self.frame_count = 0
    
    def update(self) -> None:
        """Update counter with a new frame."""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        # Keep only recent frame times within window
        if len(self.frame_times) > self.window_size:
            self.frame_times.pop(0)
        
        self.frame_count += 1
    
    def get_fps(self) -> float:
        """
        Get current FPS.
        
        Returns:
            Frames per second
        """
        if len(self.frame_times) < 2:
            return 0.0
        
        # Calculate FPS from frame time differences
        time_diffs = np.diff(self.frame_times)
        if len(time_diffs) == 0 or np.mean(time_diffs) == 0:
            return 0.0
        
        return 1.0 / np.mean(time_diffs)
    
    def get_average_fps(self) -> float:
        """
        Get average FPS since counter started.
        
        Returns:
            Average frames per second
        """
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0.0
        return self.frame_count / elapsed
    
    def reset(self) -> None:
        """Reset the FPS counter."""
        self.frame_times.clear()
        self.start_time = time.time()
        self.frame_count = 0
    
    def get_stats(self) -> Dict[str, float]:
        """Get FPS statistics."""
        return {
            "current_fps": self.get_fps(),
            "average_fps": self.get_average_fps(),
            "total_frames": self.frame_count,
            "elapsed_time": time.time() - self.start_time
        }


class VideoFrameExtractor:
    """Extractor for reading video frames."""
    
    def __init__(self, video_path: str):
        """
        Initialize video frame extractor.
        
        Args:
            video_path: Path to video file or camera index
        """
        self.video_path = video_path
        self.cap = None
        self.frame_index = 0
        self.total_frames = 0
        self.fps = 0
        self.width = 0
        self.height = 0
    
    def open(self) -> bool:
        """
        Open the video file or camera.
        
        Returns:
            True if opened successfully
        """
        try:
            import cv2
            
            # Handle camera index (numeric string)
            if self.video_path.isdigit():
                self.cap = cv2.VideoCapture(int(self.video_path))
            else:
                self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                return False
            
            # Get video properties
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            return True
        except Exception as e:
            print(f"Error opening video: {e}")
            return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read next frame from video.
        
        Returns:
            Frame as numpy array or None if no more frames
        """
        if self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            self.frame_index += 1
            return frame
        return None
    
    def read_frames(self, count: int = 1) -> List[np.ndarray]:
        """
        Read multiple frames.
        
        Args:
            count: Number of frames to read
            
        Returns:
            List of frames
        """
        frames = []
        for _ in range(count):
            frame = self.read_frame()
            if frame is None:
                break
            frames.append(frame)
        return frames
    
    def seek(self, frame_index: int) -> bool:
        """
        Seek to specific frame.
        
        Args:
            frame_index: Target frame index
            
        Returns:
            True if seek successful
        """
        if self.cap is None:
            return False
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        self.frame_index = frame_index
        return True
    
    def release(self) -> None:
        """Release video capture resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def get_properties(self) -> Dict[str, Any]:
        """Get video properties."""
        return {
            "path": self.video_path,
            "total_frames": self.total_frames,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "current_frame": self.frame_index
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


class JSONLogger:
    """Logger for outputting detection results to JSON."""
    
    def __init__(self, output_path: str):
        """
        Initialize JSON logger.
        
        Args:
            output_path: Path to output JSON file
        """
        self.output_path = Path(output_path)
        self.results: List[Dict[str, Any]] = []
    
    def log_frame(
        self,
        frame_index: int,
        detection_count: int,
        detections: List[Dict[str, Any]],
        fps: float
    ) -> None:
        """
        Log detection results for a frame.
        
        Args:
            frame_index: Frame number
            detection_count: Number of people detected
            detections: List of detection dictionaries
            fps: Current FPS
        """
        self.results.append({
            "frame": frame_index,
            "count": detection_count,
            "detections": detections,
            "fps": fps,
            "timestamp": time.time()
        })
    
    def save(self) -> None:
        """Save results to JSON file."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w') as f:
            json.dump({
                "results": self.results,
                "summary": {
                    "total_frames": len(self.results),
                    "total_detections": sum(r["count"] for r in self.results),
                    "avg_count": sum(r["count"] for r in self.results) / len(self.results) if self.results else 0
                }
            }, f, indent=2)
    
    def clear(self) -> None:
        """Clear stored results."""
        self.results.clear()
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get all logged results."""
        return self.results


def draw_detections(
    frame: np.ndarray,
    detections: List[Dict[str, Any]]
) -> np.ndarray:
    """
    Draw bounding boxes on frame.
    
    Args:
        frame: Video frame
        detections: List of detection dictionaries
        
    Returns:
        Frame with drawn boxes
    """
    try:
        import cv2
        
        output = frame.copy()
        
        for det in detections:
            bbox = det["bbox"]
            conf = det["confidence"]
            
            x1, y1, x2, y2 = map(int, bbox)
            
            # Draw rectangle
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"Person: {conf:.2f}"
            cv2.putText(output, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return output
    except ImportError:
        return frame