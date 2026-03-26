"""
People tracker for handling occlusions.

Uses centroid-based tracking to maintain identity across frames.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional


class PeopleTracker:
    """Track people across video frames using centroid matching."""
    
    def __init__(
        self,
        max_distance: float = 50.0,
        max_frames_to_skip: int = 5
    ):
        """
        Initialize tracker.
        
        Args:
            max_distance: Maximum centroid distance to match (pixels)
            max_frames_to_skip: Frames to wait before removing lost track
        """
        self.max_distance = max_distance
        self.max_frames_to_skip = max_frames_to_skip
        self.next_id = 0
        self.tracks: Dict[int, Dict[str, Any]] = {}
    
    def _get_centroid(self, bbox: List[float]) -> Tuple[float, float]:
        """Calculate centroid of bounding box."""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def _distance(self, c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between centroids."""
        return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
    
    def track(self, detections: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Track detections across frames.
        
        Args:
            detections: List of detection dicts with 'bbox' key
            
        Returns:
            Tuple of (tracked_detections, total_count)
        """
        if not detections:
            # No detections - update existing tracks
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id]['frames_skipped'] += 1
            self._remove_lost_tracks()
            return [], 0
        
        # Get centroids of current detections
        current_centroids = [
            (i, self._get_centroid(det['bbox'])) 
            for i, det in enumerate(detections)
        ]
        
        matched_tracks = set()
        tracked_detections = []
        
        # Match detections to existing tracks
        for track_id, track in self.tracks.items():
            if track_id in matched_tracks:
                continue
            
            track_centroid = track['centroid']
            best_match_idx = None
            best_distance = float('inf')
            
            for det_idx, det_centroid in current_centroids:
                if det_idx in matched_tracks:
                    continue
                    
                dist = self._distance(track_centroid, det_centroid)
                if dist < best_distance and dist <= self.max_distance:
                    best_distance = dist
                    best_match_idx = det_idx
            
            if best_match_idx is not None:
                # Update track with new detection
                matched_tracks.add(best_match_idx)
                track['centroid'] = current_centroids[best_match_idx][1]
                track['bbox'] = detections[best_match_idx]['bbox']
                track['frames_skipped'] = 0
                
                tracked_detections.append({
                    'id': track_id,
                    'bbox': detections[best_match_idx]['bbox'],
                    'confidence': detections[best_match_idx].get('confidence', 1.0)
                })
        
        # Create new tracks for unmatched detections
        for det_idx, det_centroid in current_centroids:
            if det_idx not in matched_tracks:
                new_id = self._get_next_id()
                self.tracks[new_id] = {
                    'id': new_id,
                    'centroid': det_centroid,
                    'bbox': detections[det_idx]['bbox'],
                    'frames_skipped': 0
                }
                tracked_detections.append({
                    'id': new_id,
                    'bbox': detections[det_idx]['bbox'],
                    'confidence': detections[det_idx].get('confidence', 1.0)
                })
        
        # Clean up lost tracks
        self._remove_lost_tracks()
        
        return tracked_detections, len(self.tracks)
    
    def _get_next_id(self) -> int:
        """Get next available track ID."""
        new_id = self.next_id
        self.next_id += 1
        return new_id
    
    def _remove_lost_tracks(self):
        """Remove tracks that have been missing for too long."""
        lost_tracks = [
            track_id for track_id, track in self.tracks.items()
            if track['frames_skipped'] > self.max_frames_to_skip
        ]
        for track_id in lost_tracks:
            del self.tracks[track_id]
    
    def get_count(self) -> int:
        """Get current track count."""
        return len(self.tracks)
    
    def reset(self):
        """Reset tracker state."""
        self.next_id = 0
        self.tracks.clear()


def create_tracker(
    max_distance: float = 50.0,
    max_frames_to_skip: int = 5
) -> PeopleTracker:
    """Factory function to create PeopleTracker."""
    return PeopleTracker(
        max_distance=max_distance,
        max_frames_to_skip=max_frames_to_skip
    )