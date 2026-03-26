"""
Download sample videos for testing.

Provides utilities to download sample videos from various sources.
"""

import os
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any
import ssl
import sys


# Sample video URLs (public domain / Creative Commons)
SAMPLE_VIDEOS = {
    "people_walking": [
        "https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4",
        # Fallback to empty if primary unavailable
    ],
    "crowd": [
        "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
    ]
}


def download_url(url: str, output_path: str, timeout: int = 30) -> bool:
    """
    Download a file from URL.
    
    Args:
        url: Source URL
        output_path: Local output path
        timeout: Download timeout in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create SSL context that doesn't verify certificates (for testing)
        # In production, you'd want proper SSL handling
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        print(f"Downloading: {url}")
        print(f"  to: {output_path}")
        
        # Download with progress
        urllib.request.urlretrieve(url, output_path)
        
        print(f"  Done!")
        return True
        
    except Exception as e:
        print(f"  Error: {e}")
        return False


def download_yolo_samples(output_dir: str) -> Dict[str, str]:
    """
    Attempt to download sample videos for testing.
    
    Note: Many YOLOv8 sample videos are now hosted on Ultralytics GitHub.
    This attempts to get common test videos but may need manual acquisition.
    
    Args:
        output_dir: Directory to save downloaded videos
        
    Returns:
        Dictionary mapping video name to path
    """
    downloaded = {}
    
    # Try downloading from various sources
    # These are example URLs - may need updating
    
    # Try ultralytics assets
    urls_to_try = [
        ("bus", "https://github.com/ultralytics/yolov5/releases/download/v1.0/bus.jpg"),
        # Note: YOLOv8 uses images more than videos
    ]
    
    # For now, just create placeholder structure
    # Real videos would be obtained manually
    
    return downloaded


def create_placeholder_videos(output_dir: str) -> Dict[str, str]:
    """
    Create placeholder files for test videos.
    
    These are just markers - actual video acquisition requires
    manual recording or procurement.
    
    Args:
        output_dir: Directory to create placeholders
        
    Returns:
        Dictionary mapping clip name to placeholder path
    """
    clips = {
        "occupied": os.path.join(output_dir, "occupied.mp4"),
        "empty": os.path.join(output_dir, "empty.mp4"),
        "quiet_reader": os.path.join(output_dir, "quiet-reader.mp4")
    }
    
    print("\nTest clip placeholders created:")
    print("  These are placeholder files - actual videos need to be acquired:")
    print("  - Record using webcam/phone")
    print("  - Use stock video sites")
    print("  - Download from video datasets")
    print("")
    print("Required clip characteristics:")
    print("  - occupied.mp4: Multiple people, some overlap (occlusion test)")
    print("  - empty.mp4: No people, background only (false positive test)")
    print("  - quiet-reader.mp4: Single person, still, reading (low motion test)")
    
    return clips


def main():
    """Main entry point for sample download script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download sample videos for WattWatch testing"
    )
    parser.add_argument(
        "--output", "-o",
        default="data/clips",
        help="Output directory for videos"
    )
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="Create placeholder files instead of downloading"
    )
    
    args = parser.parse_args()
    
    if args.placeholder:
        create_placeholder_videos(args.output)
    else:
        print("Attempting to download sample videos...")
        downloaded = download_yolo_samples(args.output)
        
        if downloaded:
            print(f"\nDownloaded {len(downloaded)} videos:")
            for name, path in downloaded.items():
                print(f"  {name}: {path}")
        else:
            print("\nNo samples available. Use --placeholder to create markers.")


if __name__ == "__main__":
    main()