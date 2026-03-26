"""
Data Collection and Frame Extraction for Appliance Detection

Extracts frames from videos and prepares them for training.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import cv2


def extract_frames_from_video(
    video_path: str,
    output_dir: str,
    frame_interval: int = 30,
    max_frames: int = 100,
    roi: Optional[tuple] = None
) -> List[str]:
    """
    Extract frames from video at regular intervals.
    
    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        frame_interval: Extract every N frames
        max_frames: Maximum frames to extract
        roi: Optional (x1, y1, x2, y2) region of interest to crop
        
    Returns:
        List of saved frame paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video {video_path}")
        return []
    
    frame_paths = []
    frame_idx = 0
    saved = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Extract at intervals
        if frame_idx % frame_interval == 0:
            # Crop to ROI if provided
            if roi is not None:
                x1, y1, x2, y2 = roi
                frame = frame[y1:y2, x1:x2]
            
            # Resize to standard size
            frame = cv2.resize(frame, (224, 224))
            
            # Save frame
            output_file = output_path / f"frame_{saved:05d}.jpg"
            cv2.imwrite(str(output_file), frame)
            frame_paths.append(str(output_file))
            saved += 1
            
            if saved >= max_frames:
                break
        
        frame_idx += 1
    
    cap.release()
    print(f"Extracted {saved} frames to {output_dir}")
    return frame_paths


def extract_frames_from_directory(
    image_dir: str,
    output_dir: str,
    resize_to: tuple = (224, 224)
) -> List[str]:
    """
    Process existing images and resize for training.
    
    Args:
        image_dir: Directory containing source images
        output_dir: Directory to save processed images
        resize_to: Target size (width, height)
        
    Returns:
        List of saved file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    frame_paths = []
    
    for img_path in Path(image_dir).iterdir():
        if img_path.suffix.lower() not in image_extensions:
            continue
            
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        
        # Resize
        img = cv2.resize(img, resize_to)
        
        # Save
        output_file = output_path / img_path.name
        cv2.imwrite(str(output_file), img)
        frame_paths.append(str(output_file))
    
    print(f"Processed {len(frame_paths)} images to {output_dir}")
    return frame_paths


def create_synthetic_appliance_dataset(
    output_dir: str,
    num_samples: int = 100,
    image_size: tuple = (224, 224)
) -> List[Dict[str, Any]]:
    """
    Create synthetic appliance images for initial training.
    
    This is useful for testing the pipeline when real data is not available.
    The model trained on synthetic data will need fine-tuning with real images.
    
    Args:
        output_dir: Directory to save synthetic images
        num_samples: Number of samples per class
        image_size: Size of generated images
        
    Returns:
        List of labels with file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    labels = []
    height, width = image_size
    
    np.random.seed(42)  # For reproducibility
    
    # Classes and their properties
    classes = {
        'monitor_on': {'brightness': 180, 'variance': 200, 'pattern': 'screen'},
        'monitor_off': {'brightness': 40, 'variance': 50, 'pattern': 'screen'},
        'projector_on': {'brightness': 220, 'variance': 100, 'pattern': 'glow'},
        'projector_off': {'brightness': 25, 'variance': 20, 'pattern': 'glow'},
        'light_on': {'brightness': 200, 'variance': 150, 'pattern': 'circular'},
        'light_off': {'brightness': 35, 'variance': 30, 'pattern': 'circular'},
        'ceiling_fan_on': {'brightness': 100, 'variance': 500, 'pattern': 'blades'},
        'ceiling_fan_off': {'brightness': 50, 'variance': 100, 'pattern': 'blades'},
        'wall_fan_on': {'brightness': 90, 'variance': 400, 'pattern': 'horizontal'},
        'wall_fan_off': {'brightness': 45, 'variance': 80, 'pattern': 'horizontal'},
    }
    
    for class_name, props in classes.items():
        class_dir = output_path / class_name
        class_dir.mkdir(exist_ok=True)
        
        for i in range(num_samples):
            # Create base image (use float to avoid overflow)
            base_brightness = props['brightness']
            img = np.random.randint(
                max(0, base_brightness - 30),
                min(255, base_brightness + 30),
                (height, width, 3),
                dtype=np.uint8
            )
            
            # Add pattern-specific features
            if props['pattern'] == 'screen':
                # Monitor: bright center, darker edges
                center_h, center_w = height // 2, width // 2
                center_region = img[center_h-50:center_h+50, center_w-70:center_w+70]
                center_region[:] = np.clip(center_region + 80, 0, 255)
                # Add some content variation
                for _ in range(5):
                    x = np.random.randint(50, width-50)
                    y = np.random.randint(50, height-50)
                    w = np.random.randint(20, 50)
                    h = np.random.randint(15, 30)
                    img[y:y+h, x:x+w] = np.random.randint(100, 220, (h, w, 3))
                    
            elif props['pattern'] == 'glow':
                # Projector: radial glow from center
                center_x, center_y = width // 2, height // 2
                y, x = np.ogrid[:height, :width]
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                max_dist = np.sqrt(center_x**2 + center_y**2)
                glow = (1 - dist / max_dist) * 150
                img = np.clip(img + glow[:, :, np.newaxis].astype(np.uint8), 0, 255)
                
            elif props['pattern'] == 'circular':
                # Light: circular bright area
                center_x, center_y = width // 2, height // 4
                radius = min(width, height) // 4
                y, x = np.ogrid[:height, :width]
                mask = (x - center_x)**2 + (y - center_y)**2 <= radius**2
                img[mask] = np.clip(img[mask] + 100, 0, 255)
                
            elif props['pattern'] == 'blades':
                # Ceiling fan: circular with blade lines
                center_x, center_y = width // 2, height // 2
                outer_radius = min(width, height) // 3
                # Draw blades
                for angle in np.linspace(0, 2*np.pi, 4, endpoint=False):
                    end_x = int(center_x + outer_radius * 0.8 * np.cos(angle))
                    end_y = int(center_y + outer_radius * 0.8 * np.sin(angle))
                    cv2.line(img, (center_x, center_y), (end_x, end_y), (120, 120, 120), 3)
                    
            elif props['pattern'] == 'horizontal':
                # Wall fan: horizontal lines
                for y_pos in range(height // 3, 2 * height // 3, 20):
                    cv2.line(img, (width // 4, y_pos), (3 * width // 4, y_pos), (110, 110, 110), 4)
            
            # Add noise
            noise = np.random.randint(-10, 10, (height, width, 3))
            img = np.clip(img + noise, 0, 255).astype(np.uint8)
            
            # Save
            filename = f"{class_name}_{i:04d}.jpg"
            filepath = class_dir / filename
            cv2.imwrite(str(filepath), img)
            
            # Extract labels
            parts = class_name.split('_')
            appliance_type = parts[0]
            status = parts[1]
            
            labels.append({
                'filename': filename,
                'filepath': str(filepath),
                'appliance_type': appliance_type,
                'status': status,
                'class_name': class_name
            })
    
    print(f"Created {len(labels)} synthetic images in {output_dir}")
    return labels


def create_dataset_manifest(
    labels: List[Dict[str, Any]],
    output_file: str
) -> None:
    """Create a JSON manifest of the dataset."""
    with open(output_file, 'w') as f:
        json.dump(labels, f, indent=2)
    print(f"Created manifest: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Data collection for appliance detection'
    )
    parser.add_argument(
        '--video',
        help='Input video file to extract frames from'
    )
    parser.add_argument(
        '--output-dir',
        default='data/appliances/raw',
        help='Output directory for frames'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Frame extraction interval'
    )
    parser.add_argument(
        '--max-frames',
        type=int,
        default=100,
        help='Maximum frames to extract'
    )
    parser.add_argument(
        '--roi',
        nargs=4,
        type=int,
        metavar=('X1', 'Y1', 'X2', 'Y2'),
        help='Region of interest to crop'
    )
    parser.add_argument(
        '--synthetic',
        action='store_true',
        help='Generate synthetic dataset for testing'
    )
    parser.add_argument(
        '--num-samples',
        type=int,
        default=100,
        help='Samples per class for synthetic data'
    )
    parser.add_argument(
        '--image-dir',
        help='Process existing images from directory'
    )
    
    args = parser.parse_args()
    
    if args.synthetic:
        # Generate synthetic data
        labels = create_synthetic_appliance_dataset(
            args.output_dir,
            args.num_samples
        )
        manifest_path = Path(args.output_dir) / 'manifest.json'
        create_dataset_manifest(labels, str(manifest_path))
        
    elif args.video:
        # Extract from video
        frames = extract_frames_from_video(
            args.video,
            args.output_dir,
            args.interval,
            args.max_frames,
            tuple(args.roi) if args.roi else None
        )
        print(f"Extracted {len(frames)} frames")
        
    elif args.image_dir:
        # Process existing images
        frames = extract_frames_from_directory(
            args.image_dir,
            args.output_dir
        )
        print(f"Processed {len(frames)} images")
        
    else:
        parser.print_help()


if __name__ == '__main__':
    sys.exit(main())
