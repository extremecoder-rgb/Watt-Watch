"""
Frame extraction utilities for WattWatch.

Provides functions to extract frames from videos at various intervals.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import cv2


def extract_frames(
    video_path: str,
    output_dir: str,
    count: int = 10
) -> List[str]:
    """
    Extract evenly distributed frames from a video.
    
    Args:
        video_path: Path to input video
        output_dir: Output directory for extracted frames
        count: Number of frames to extract
        
    Returns:
        List of paths to extracted frame images
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if total_frames == 0:
        cap.release()
        raise ValueError("Video has no frames")
    
    # Calculate frame indices to extract
    indices = []
    if count > 1:
        step = (total_frames - 1) / (count - 1)
        for i in range(count):
            indices.append(int(i * step))
    else:
        indices = [0]
    
    extracted_paths = []
    base_name = Path(video_path).stem
    
    for idx, frame_idx in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        
        ret, frame = cap.read()
        
        if ret:
            output_path = os.path.join(output_dir, f"{base_name}_frame_{idx:04d}.jpg")
            cv2.imwrite(output_path, frame)
            extracted_paths.append(output_path)
    
    cap.release()
    
    return extracted_paths


def extract_at_interval(
    video_path: str,
    output_dir: str,
    interval: int = 30
) -> List[str]:
    """
    Extract frames at regular intervals from a video.
    
    Args:
        video_path: Path to input video
        output_dir: Output directory for extracted frames
        interval: Extract every N frames
        
    Returns:
        List of paths to extracted frame images
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    extracted_paths = []
    frame_idx = 0
    extract_idx = 0
    base_name = Path(video_path).stem
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
        
        if frame_idx % interval == 0:
            output_path = os.path.join(
                output_dir, 
                f"{base_name}_frame_{extract_idx:04d}.jpg"
            )
            cv2.imwrite(output_path, frame)
            extracted_paths.append(output_path)
            extract_idx += 1
        
        frame_idx += 1
    
    cap.release()
    
    return extracted_paths


def batch_extract(
    video_dir: str,
    output_dir: str,
    count_per_video: int = 10,
    extensions: Optional[List[str]] = None
) -> Dict[str, List[str]]:
    """
    Extract frames from multiple videos in a directory.
    
    Args:
        video_dir: Directory containing video files
        output_dir: Output directory for extracted frames
        count_per_video: Number of frames to extract per video
        extensions: List of video extensions to process
        
    Returns:
        Dictionary mapping video name to list of extracted frame paths
    """
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    results = {}
    
    for filename in os.listdir(video_dir):
        if any(filename.lower().endswith(ext) for ext in extensions):
            video_path = os.path.join(video_dir, filename)
            video_name = Path(filename).stem
            video_output = os.path.join(output_dir, video_name)
            
            try:
                paths = extract_frames(video_path, video_output, count_per_video)
                results[filename] = paths
                print(f"Extracted {len(paths)} frames from {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                results[filename] = []
    
    return results


def extract_with_timestamps(
    video_path: str,
    output_dir: str,
    timestamps: List[float]
) -> List[Tuple[str, float]]:
    """
    Extract frames at specific timestamps.
    
    Args:
        video_path: Path to input video
        output_dir: Output directory for extracted frames
        timestamps: List of timestamps in seconds
        
    Returns:
        List of tuples (frame_path, timestamp)
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    base_name = Path(video_path).stem
    
    results = []
    
    for idx, timestamp in enumerate(sorted(timestamps)):
        frame_idx = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        
        ret, frame = cap.read()
        
        if ret:
            output_path = os.path.join(
                output_dir, 
                f"{base_name}_ts_{timestamp:.2f}.jpg"
            )
            cv2.imwrite(output_path, frame)
            results.append((output_path, timestamp))
    
    cap.release()
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python extract_frames.py <video_path> <output_dir> [count]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    try:
        paths = extract_frames(video_path, output_dir, count)
        print(f"Extracted {len(paths)} frames to {output_dir}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)