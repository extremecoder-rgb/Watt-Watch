"""
Motion smoothing for reducing count jitter.

Provides temporal smoothing to reduce rapid fluctuations in detection counts.
"""

import numpy as np
from typing import List, Optional


class CountSmoother:
    """Smooth detection counts using temporal averaging."""
    
    def __init__(
        self,
        window_size: int = 10,
        method: str = "rolling"
    ):
        """
        Initialize count smoother.
        
        Args:
            window_size: Number of frames to average over
            method: 'rolling' or 'exponential'
        """
        self.window_size = window_size
        self.method = method
        self.history: List[int] = []
        self.alpha = 0.3  # Smoothing factor for exponential
    
    def update(self, raw_count: int) -> float:
        """
        Update with new count and return smoothed value.
        
        Args:
            raw_count: Raw detection count
            
        Returns:
            Smoothed count (float)
        """
        self.history.append(raw_count)
        
        # Keep history within window size
        if len(self.history) > self.window_size:
            self.history.pop(0)
        
        if self.method == "rolling":
            return self._rolling_average()
        elif self.method == "exponential":
            return self._exponential_average()
        else:
            return float(raw_count)
    
    def _rolling_average(self) -> float:
        """Calculate rolling average."""
        if not self.history:
            return 0.0
        return np.mean(self.history)
    
    def _exponential_average(self) -> float:
        """Calculate exponential moving average."""
        if not self.history:
            return 0.0
        
        # Start with first value
        result = float(self.history[0])
        
        # Apply exponential smoothing
        for count in self.history[1:]:
            result = self.alpha * count + (1 - self.alpha) * result
        
        return result
    
    def get_history(self) -> List[int]:
        """Get count history."""
        return self.history.copy()
    
    def get_raw(self) -> int:
        """Get most recent raw count."""
        if self.history:
            return self.history[-1]
        return 0
    
    def reset(self):
        """Reset history."""
        self.history.clear()


class AdaptiveSmoother(CountSmoother):
    """Adaptive smoother that adjusts window based on motion."""
    
    def __init__(
        self,
        min_window: int = 5,
        max_window: int = 20,
        threshold: float = 2.0
    ):
        super().__init__(window_size=max_window)
        self.min_window = min_window
        self.max_window = max_window
        self.threshold = threshold
    
    def update(self, raw_count: int) -> float:
        """Update with adaptive window sizing."""
        # Adjust window based on count variation
        if len(self.history) >= 3:
            variation = np.std(self.history[-3:])
            
            if variation > self.threshold:
                # High variation - use larger window
                self.window_size = min(self.max_window, self.window_size + 1)
            else:
                # Low variation - use smaller window
                self.window_size = max(self.min_window, self.window_size - 1)
        
        return super().update(raw_count)


def create_smoother(
    window_size: int = 10,
    method: str = "rolling",
    adaptive: bool = False
) -> CountSmoother:
    """
    Factory function to create count smoother.
    
    Args:
        window_size: Window size for rolling average
        method: 'rolling' or 'exponential'
        adaptive: Use adaptive smoothing
        
    Returns:
        CountSmoother instance
    """
    if adaptive:
        return AdaptiveSmoother()
    return CountSmoother(window_size=window_size, method=method)