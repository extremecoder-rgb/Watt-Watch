"""
Database models for WattWatch.
Data classes for waste events, detection counts, and energy savings.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import time


@dataclass
class WasteEvent:
    """Waste event alert data."""
    event_id: str
    room_id: str
    room_name: str
    timestamp: float
    duration_seconds: float
    light_status: str
    fan_status: str
    monitor_status: str
    thumbnail_path: Optional[str] = None
    anonymized: bool = True
    created_at: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at
        if self.id:
            data['id'] = self.id
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WasteEvent':
        return cls(
            id=data.get('id'),
            event_id=data['event_id'],
            room_id=data['room_id'],
            room_name=data.get('room_name', ''),
            timestamp=data['timestamp'],
            duration_seconds=data.get('duration_seconds', 0),
            light_status=data.get('light_status', 'OFF'),
            fan_status=data.get('fan_status', 'OFF'),
            monitor_status=data.get('monitor_status', 'OFF'),
            thumbnail_path=data.get('thumbnail_path'),
            anonymized=data.get('anonymized', True),
            created_at=data.get('created_at')
        )


@dataclass
class DetectionCount:
    """Detection count for a room at a point in time."""
    room_id: str
    timestamp: float
    person_count: int
    light_status: str
    fan_status: str
    monitor_status: str
    id: Optional[int] = None
    created_at: Optional[str] = None
    
    def to_tuple(self) -> tuple:
        return (
            self.room_id,
            self.timestamp,
            self.person_count,
            self.light_status,
            self.fan_status,
            self.monitor_status
        )


@dataclass
class EnergySaving:
    """Daily energy savings for a room."""
    room_id: str
    date: str
    waste_duration_seconds: float
    estimated_kwh: float
    cost_saved: float
    alert_count: int
    max_concurrent_people: int
    total_detections: int
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PrivacyConfig:
    """Privacy configuration and verification."""
    raw_images_stored: bool = False
    face_detection_enabled: bool = True
    thumbnails_anonymized: bool = True
    credentials_encrypted: bool = True
    data_retention_days: int = 30
    blur_method: str = "pixelate"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExportRow:
    """CSV export row format."""
    timestamp: str
    room_id: str
    room_name: str
    duration_minutes: float
    light_status: str
    fan_status: str
    monitor_status: str
    estimated_kwh: float
    cost_saved: float
    thumbnail_available: bool
    
    def to_csv_row(self) -> List[str]:
        return [
            self.timestamp,
            self.room_id,
            self.room_name,
            f"{self.duration_minutes:.2f}",
            self.light_status,
            self.fan_status,
            self.monitor_status,
            f"{self.estimated_kwh:.4f}",
            f"{self.cost_saved:.4f}",
            "Yes" if self.thumbnail_available else "No"
        ]
    
    @staticmethod
    def csv_headers() -> List[str]:
        return [
            "Timestamp",
            "Room ID",
            "Room Name",
            "Duration (minutes)",
            "Light Status",
            "Fan Status",
            "Monitor Status",
            "Est. Energy Saved (kWh)",
            "Cost Saved ($)",
            "Anonymized Thumbnail"
        ]
