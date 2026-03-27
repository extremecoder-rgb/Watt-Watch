"""
Microzone Intelligence Module

Divides the camera frame into a grid of micro-zones and tracks
per-zone occupancy for row-wise energy optimization and heatmap generation.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import time


@dataclass
class ZoneInfo:
    """Information about a single micro-zone."""
    zone_id: str
    row: int
    col: int
    current_count: int = 0
    cumulative_count: float = 0.0  # Decayed accumulation for heatmap
    last_occupied: float = 0.0
    is_occupied: bool = False


class MicrozoneTracker:
    """
    Tracks occupancy across a grid of micro-zones.
    
    The frame is divided into (rows x cols) zones.
    Each person detection is mapped to whichever zone(s) their
    bounding box center falls into.
    """

    def __init__(self, rows: int = 4, cols: int = 4, decay: float = 0.97):
        """
        Args:
            rows: Number of horizontal rows to divide the frame into.
            cols: Number of vertical columns.
            decay: Exponential decay factor applied to the cumulative
                   heatmap every update (0.95-0.99 recommended).
        """
        self.rows = rows
        self.cols = cols
        self.decay = decay
        self._zones: Dict[str, ZoneInfo] = {}
        self._heatmap = np.zeros((rows, cols), dtype=np.float64)
        self._current_grid = np.zeros((rows, cols), dtype=np.int32)
        self._frame_w = 0
        self._frame_h = 0

        # Pre-create zone objects
        for r in range(rows):
            for c in range(cols):
                zid = f"Z{r}{c}"
                self._zones[zid] = ZoneInfo(zone_id=zid, row=r, col=c)

    # ------------------------------------------------------------------
    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_width: int,
        frame_height: int,
        total_wattage: float = 0.0
    ) -> Dict[str, Any]:
        """
        Update zone occupancy from a list of person detections.

        Args:
            detections: list of dicts with key ``bbox`` = [x1, y1, x2, y2].
            frame_width: width of the source frame in pixels.
            frame_height: height of the source frame in pixels.
            total_wattage: Total environment wattage (lights/fans) to calculate savings.

        Returns:
            A summary dict ready for JSON serialisation.
        """
        self._frame_w = frame_width
        self._frame_h = frame_height

        cell_w = frame_width / self.cols
        cell_h = frame_height / self.rows

        # Decay the cumulative heatmap
        self._heatmap *= self.decay

        # Reset current snapshot
        self._current_grid[:] = 0
        for z in self._zones.values():
            z.current_count = 0
            z.is_occupied = False

        now = time.time()

        for det in detections:
            bbox = det.get("bbox", [])
            if len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            col = int(min(cx / cell_w, self.cols - 1))
            row = int(min(cy / cell_h, self.rows - 1))
            col = max(0, col)
            row = max(0, row)

            zid = f"Z{row}{col}"
            zone = self._zones[zid]
            zone.current_count += 1
            zone.is_occupied = True
            zone.last_occupied = now

            self._current_grid[row, col] += 1
            self._heatmap[row, col] += 1.0

        return self._build_summary(total_wattage=total_wattage)

    # ------------------------------------------------------------------
    def _build_summary(self, total_wattage: float = 0.0) -> Dict[str, Any]:
        """Build a JSON-serialisable summary of current microzone state."""
        # Normalise heatmap to 0-1 for the frontend colour scale
        hmax = self._heatmap.max()
        if hmax > 0:
            norm = (self._heatmap / hmax).tolist()
        else:
            norm = self._heatmap.tolist()

        # Row-wise aggregation
        row_data = []
        occupied_rows = 0
        total_rows = self.rows
        
        for r in range(self.rows):
            # Ensure we use standard Python bool, not numpy.bool_
            is_occupied = bool((self._current_grid[r] > 0).any())
            row_count = int(self._current_grid[r].sum())
            row_heat = float(self._heatmap[r].sum())
            
            if is_occupied:
                occupied_rows += 1
                
            row_data.append({
                "row": r,
                "label": f"Row {r+1}",
                "person_count": row_count,
                "occupied": is_occupied,
                "heat": round(row_heat, 2),
                # If row is idle, we have 100% potential for that row's LEDs/Fans
                "optimization_potential_percent": 100 if not is_occupied else 0
            })

        # Calculate workspace optimization index (WOI) - Higher is better
        # WOI = (Total Rows - Occupied Rows) / Total Rows
        efficiency_score = (occupied_rows / total_rows) * 100 if total_rows > 0 else 100
        potential_savings_watts = (1.0 - (occupied_rows / total_rows)) * total_wattage if total_rows > 0 else 0
        
        # Zone-level detail
        zones = []
        for r in range(self.rows):
            for c in range(self.cols):
                zid = f"Z{r}{c}"
                z = self._zones[zid]
                zones.append({
                    "zone_id": zid,
                    "row": r,
                    "col": c,
                    "count": int(z.current_count),
                    "occupied": bool(z.is_occupied),
                })

        return {
            "rows": self.rows,
            "cols": self.cols,
            "heatmap": norm,
            "current_grid": self._current_grid.tolist(),
            "row_summary": row_data,
            "zones": zones,
            "total_occupied_zones": int((self._current_grid > 0).sum()),
            "total_zones": self.rows * self.cols,
            "efficiency_score": round(float(efficiency_score), 1),
            "potential_savings_watts": round(float(potential_savings_watts), 2),
            "occupied_rows": int(occupied_rows),
            "total_rows": int(total_rows)
        }

    # ------------------------------------------------------------------
    def get_heatmap_overlay(
        self,
        frame_width: int,
        frame_height: int,
    ) -> np.ndarray:
        """
        Return a colour-mapped heatmap image (BGRA) of shape
        (frame_height, frame_width, 4) suitable for alpha-blending on
        the display frame.
        """
        import cv2

        hmax = self._heatmap.max()
        if hmax > 0:
            norm = (self._heatmap / hmax * 255).astype(np.uint8)
        else:
            norm = np.zeros((self.rows, self.cols), dtype=np.uint8)

        # Up-scale to frame size with interpolation
        big = cv2.resize(norm, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)
        coloured = cv2.applyColorMap(big, cv2.COLORMAP_JET)

        # Build BGRA with transparency proportional to heat
        alpha = cv2.resize(norm, (frame_width, frame_height), interpolation=cv2.INTER_LINEAR)
        alpha = (alpha.astype(np.float32) / 255 * 120).astype(np.uint8)  # max 120/255 opacity

        bgra = np.zeros((frame_height, frame_width, 4), dtype=np.uint8)
        bgra[:, :, :3] = coloured
        bgra[:, :, 3] = alpha
        return bgra

    def blend_heatmap(self, frame: np.ndarray) -> np.ndarray:
        """
        Blend the heatmap overlay onto a BGR frame and return the result.
        """
        import cv2

        h, w = frame.shape[:2]
        overlay = self.get_heatmap_overlay(w, h)

        alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0
        colour = overlay[:, :, :3].astype(np.float32)

        out = frame.astype(np.float32)
        out = out * (1 - alpha) + colour * alpha
        return out.astype(np.uint8)
