"""
Model utilities for WattWatch.

Provides utilities for model management, device detection, and benchmarking.
"""

import sys
from typing import Dict, Any, Optional
import platform


def get_model_info() -> Dict[str, Any]:
    """
    Get information about the YOLOv8 model.
    
    Returns:
        Dictionary with model details
    """
    return {
        "model_name": "yolov8n.pt",
        "model_type": "YOLOv8 Nano",
        "purpose": "People detection (COCO person class)",
        "speed": "Fastest",
        "accuracy": "Good",
        "size_mb": 6.3,
        "note": "Pre-trained on COCO, includes person class (0)"
    }


def check_device() -> str:
    """
    Detect available compute device.
    
    Returns:
        Device string: 'cuda', 'mps', or 'cpu'
    """
    try:
        import torch
        
        if torch.cuda.is_available():
            return "cuda"
        
        # Check for Apple Silicon MPS
        if platform.system() == "Darwin" and platform.processor() == "arm":
            try:
                if torch.backends.mps.is_available():
                    return "mps"
            except AttributeError:
                pass
        
        return "cpu"
    except ImportError:
        return "cpu"


def get_device_info() -> Dict[str, Any]:
    """
    Get detailed device information.
    
    Returns:
        Dictionary with device details
    """
    info = {
        "device": check_device(),
        "platform": platform.system(),
        "python_version": sys.version,
    }
    
    try:
        import torch
        
        info["pytorch_version"] = torch.__version__
        
        if torch.cuda.is_available():
            info["cuda_available"] = True
            info["cuda_version"] = torch.version.cuda
            info["cuda_device_count"] = torch.cuda.device_count()
            info["cuda_device_name"] = torch.cuda.get_device_name(0)
        else:
            info["cuda_available"] = False
            
        # Check MPS (Apple Silicon)
        if platform.system() == "Darwin":
            try:
                info["mps_available"] = torch.backends.mps.is_available()
            except AttributeError:
                info["mps_available"] = False
        else:
            info["mps_available"] = False
            
    except ImportError:
        info["pytorch_available"] = False
    
    return info


def benchmark_model(
    model_name: str = "yolov8n.pt",
    num_runs: int = 100,
    warmup_runs: int = 10
) -> Dict[str, float]:
    """
    Benchmark model inference speed.
    
    Args:
        model_name: Name of YOLOv8 model
        num_runs: Number of inference runs
        warmup_runs: Number of warmup runs before benchmarking
        
    Returns:
        Dictionary with benchmark results
    """
    import time
    import numpy as np
    
    try:
        from ultralytics import YOLO
    except ImportError:
        return {"error": "ultralytics not installed"}
    
    # Create model
    model = YOLO(model_name)
    
    # Create dummy frame (640x480 RGB)
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Warmup
    for _ in range(warmup_runs):
        model(dummy_frame, verbose=False)
    
    # Benchmark
    times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        model(dummy_frame, verbose=False)
        end = time.perf_counter()
        times.append(end - start)
    
    times_ms = [t * 1000 for t in times]
    
    return {
        "model": model_name,
        "runs": num_runs,
        "mean_ms": float(np.mean(times_ms)),
        "std_ms": float(np.std(times_ms)),
        "min_ms": float(np.min(times_ms)),
        "max_ms": float(np.max(times_ms)),
        "mean_fps": float(1000.0 / np.mean(times_ms)),
    }


def estimate_real_time_fps(
    resolution: tuple = (640, 480),
    device: Optional[str] = None
) -> Dict[str, float]:
    """
    Estimate real-time FPS for given resolution and device.
    
    Args:
        resolution: Frame resolution (width, height)
        device: Device to use ('cuda', 'mps', 'cpu') or None for auto
        
    Returns:
        Dictionary with FPS estimates
    """
    if device is None:
        device = check_device()
    
    # Base estimates (yolov8n on reference hardware)
    base_fps = {
        "cpu": 25,      # CPU reference
        "cuda": 80,     # GPU reference  
        "mps": 50,      # Apple Silicon
    }
    
    # Adjust for resolution
    ref_res = (640, 480)
    ref_pixels = ref_res[0] * ref_res[1]
    actual_pixels = resolution[0] * resolution[1]
    ratio = actual_pixels / ref_pixels
    
    # FPS scales roughly with inverse of pixel count
    resolution_factor = 1.0 / (ratio ** 0.5)
    
    base = base_fps.get(device, 25)
    estimated = base * resolution_factor
    
    return {
        "resolution": resolution,
        "device": device,
        "estimated_fps": round(estimated, 1),
        "note": "Based on yolov8n.pt benchmarks"
    }


def print_model_summary() -> None:
    """Print a formatted model summary."""
    info = get_model_info()
    device_info = get_device_info()
    
    print("=" * 50)
    print("WattWatch YOLOv8 Model Summary")
    print("=" * 50)
    print(f"Model: {info['model_name']}")
    print(f"Type: {info['model_type']}")
    print(f"Purpose: {info['purpose']}")
    print(f"Speed: {info['speed']}")
    print(f"Size: {info['size_mb']} MB")
    print("-" * 50)
    print(f"Device: {device_info['device']}")
    print(f"Platform: {device_info['platform']}")
    if device_info.get('cuda_available'):
        print(f"GPU: {device_info.get('cuda_device_name', 'Unknown')}")
    print("=" * 50)


if __name__ == "__main__":
    print_model_summary()
    
    print("\nDevice Info:")
    import json
    print(json.dumps(get_device_info(), indent=2))
    
    print("\nEstimated FPS (640x480):")
    print(json.dumps(estimate_real_time_fps(), indent=2))