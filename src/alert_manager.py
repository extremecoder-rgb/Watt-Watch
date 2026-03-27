"""
Alert Manager for waste detection.
Handles debouncing, event logging, and thumbnails.
Uses SQLite database for concurrent write scalability.
"""

import json
import os
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np
import cv2

try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

from src.database import DatabaseManager, DatabaseConfig, WasteEvent as DBWasteEvent


@dataclass
class WasteEvent:
    event_id: str
    room_id: str
    room_name: str
    timestamp: float
    duration_seconds: float
    light_status: str
    fan_status: str
    monitor_status: str
    thumbnail_path: Optional[str] = None


class AlertManager:
    """Manages waste alerts with debouncing and event logging."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        initial_delay: int = 300,
        repeat_interval: int = 3600
    ):
        self.enabled = config.get("enabled", True)
        self.initial_delay = initial_delay
        self.repeat_interval = repeat_interval
        
        storage_config = config.get("storage", {})
        self.storage_enabled = storage_config.get("enabled", True)
        self.events_file = storage_config.get("events_file", "output/waste_events.json")
        self.thumbnails_dir = storage_config.get("thumbnails_dir", "data/alerts")
        self.thumbnail_width = storage_config.get("thumbnail_width", 320)
        
        # Track waste state per room
        self._room_states: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Twilio SMS config
        self.twilio_config = config.get("twilio", {})
        self.twilio_enabled = self.twilio_config.get("enabled", False) and TwilioClient is not None
        self._twilio_client = None
        
        if self.twilio_enabled:
            try:
                self._twilio_client = TwilioClient(
                    self.twilio_config.get("account_sid"),
                    self.twilio_config.get("auth_token")
                )
                print(f"[AlertManager] Twilio initialized: sender={self.twilio_config.get('from_number')}")
            except Exception as e:
                print(f"[AlertManager] Twilio init error: {e}")
                self.twilio_enabled = False
        
        # WhatsApp config
        self.wa_config = self.twilio_config.get("whatsapp", {})
        self.wa_enabled = self.wa_config.get("enabled", False) and self.twilio_enabled
        
        # Load existing events
        self._events: List[WasteEvent] = []
        
        db_config = config.get("database", {})
        self._use_database = db_config.get("enabled", True)
        self._db_path = db_config.get("db_path", "data/wattwatch.db")
        
        self._db: Optional[DatabaseManager] = None
        if self.storage_enabled and self._use_database:
            self._init_database()
        
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.events_file) if '/' in self.events_file else 'output', exist_ok=True)
    
    def _init_database(self):
        """Initialize database connection."""
        try:
            db_config = DatabaseConfig(db_path=self._db_path)
            self._db = DatabaseManager.get_instance(db_config)
            self._db.start_buffer_flush()
            self._load_events_from_db()
            print(f"[AlertManager] Database initialized: {self._db_path}")
        except Exception as e:
            print(f"[AlertManager] Database init error: {e}, falling back to JSON")
            self._use_database = False
    
    def _load_events_from_db(self):
        """Load existing events from database."""
        if not self._db:
            return
        try:
            rows = self._db.fetchall(
                "SELECT * FROM waste_events ORDER BY timestamp DESC LIMIT 1000"
            )
            for row in rows:
                self._events.append(WasteEvent(
                    event_id=row['event_id'],
                    room_id=row['room_id'],
                    room_name=row.get('room_name', ''),
                    timestamp=row['timestamp'],
                    duration_seconds=row.get('duration_seconds', 0),
                    light_status=row.get('light_status', 'OFF'),
                    fan_status=row.get('fan_status', 'OFF'),
                    monitor_status=row.get('monitor_status', 'OFF'),
                    thumbnail_path=row.get('thumbnail_path')
                ))
        except Exception as e:
            print(f"[AlertManager] Load events error: {e}")
    
    def _save_events_to_db(self, event: WasteEvent):
        """Save event to database."""
        if not self._db:
            return
        try:
            self._db.execute(
                """INSERT OR REPLACE INTO waste_events 
                (event_id, room_id, room_name, timestamp, duration_seconds, 
                 light_status, fan_status, monitor_status, thumbnail_path, anonymized)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (event.event_id, event.room_id, event.room_name, event.timestamp,
                 event.duration_seconds, event.light_status, event.fan_status,
                 event.monitor_status, event.thumbnail_path)
            )
        except Exception as e:
            print(f"[AlertManager] Save event error: {e}")
    
    def _save_events(self):
        """Save events to file (fallback)."""
        if not self.storage_enabled:
            return
        
        if self._use_database and self._db:
            return
        
        try:
            data = {
                'events': [asdict(e) for e in self._events[-1000:]],
                'last_updated': time.time()
            }
            with open(self.events_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def _generate_event_id(self, room_id: str) -> str:
        return f"{room_id}_{int(time.time() * 1000)}"
    
    def _save_thumbnail(self, frame: np.ndarray, event_id: str) -> Optional[str]:
        """Save anonymized thumbnail."""
        if not self.storage_enabled or frame is None:
            return None
        
        try:
            h, w = frame.shape[:2]
            new_w = self.thumbnail_width
            new_h = int(h * new_w / w)
            thumb = cv2.resize(frame, (new_w, new_h))
            
            thumb_path = os.path.join(self.thumbnails_dir, f"{event_id}.jpg")
            cv2.imwrite(thumb_path, thumb, [cv2.IMWRITE_JPEG_QUALITY, 60])
            return thumb_path
        except Exception:
            return None
            
    def _send_sms(self, event: WasteEvent):
        """Send notification via Twilio SMS."""
        if not self.twilio_enabled or not self._twilio_client:
            return
            
        try:
            msg_body = (
                f"⚠️ WATTWATCH ALERT\n"
                f"Energy waste detected in {event.room_name}!\n"
                f"Duration: {event.duration_seconds/60:.1f} mins\n"
                f"Lights: {event.light_status}, Fans: {event.fan_status}, Mon: {event.monitor_status}\n"
                f"Please check the facility."
            )
            
            message = self._twilio_client.messages.create(
                body=msg_body,
                from_=self.twilio_config.get("from_number"),
                to=self.twilio_config.get("to_number")
            )
            print(f"[AlertManager] SMS sent to {self.twilio_config.get('to_number')}: {message.sid}")
        except Exception as e:
            print(f"[AlertManager] SMS error: {e}")
            
    def _send_whatsapp(self, event: WasteEvent):
        """Send notification via Twilio WhatsApp."""
        if not self.wa_enabled or not self._twilio_client:
            return
            
        try:
            # Map event data to template variables
            content_variables = json.dumps({
                "1": event.room_name,
                "2": f"{event.duration_seconds/60:.1f}m"
            })
            
            to_wa = f"whatsapp:{self.twilio_config.get('to_number')}"
            
            message = self._twilio_client.messages.create(
                from_=self.wa_config.get("from_number"),
                content_sid=self.wa_config.get("content_sid"),
                content_variables=content_variables,
                to=to_wa
            )
            print(f"[AlertManager] WhatsApp sent to {to_wa}: {message.sid}")
        except Exception as e:
            print(f"[AlertManager] WhatsApp error: {e}")
    
    def check_room(
        self,
        room_id: str,
        room_name: str,
        person_count: int,
        light_status: str,
        fan_status: str,
        monitor_status: str = "OFF",
        current_frame: Optional[np.ndarray] = None,
        anonymized_frame: Optional[np.ndarray] = None
    ) -> Optional[WasteEvent]:
        """
        Check room and return alert event if conditions met.
        Returns None if no alert should be sent.
        """
        if not self.enabled:
            return None
        
        is_waste = person_count == 0 and (light_status == "ON" or fan_status == "ON" or monitor_status == "ON")
        current_time = time.time()
        
        with self._lock:
            if room_id not in self._room_states:
                self._room_states[room_id] = {
                    'in_waste': False,
                    'waste_start_time': None,
                    'last_alert_time': None,
                    'room_name': room_name,
                    'light_status': light_status,
                    'fan_status': fan_status,
                    'monitor_status': monitor_status
                }
            
            state = self._room_states[room_id]
            state['room_name'] = room_name
            state['light_status'] = light_status
            state['fan_status'] = fan_status
            state['monitor_status'] = monitor_status
            
            if is_waste:
                if not state['in_waste']:
                    # First detection of waste
                    state['in_waste'] = True
                    state['waste_start_time'] = current_time
                
                # Check if we should alert
                waste_duration = current_time - state['waste_start_time']
                should_alert = False
                
                if state['last_alert_time'] is None:
                    # First alert ever for this waste period
                    if waste_duration >= self.initial_delay:
                        should_alert = True
                else:
                    # Subsequent alerts
                    time_since_alert = current_time - state['last_alert_time']
                    if time_since_alert >= self.repeat_interval:
                        should_alert = True
                
                if should_alert:
                    print(f"[ALERT] Waste detected in {room_name}! Duration: {waste_duration:.1f}s")
                    event_id = self._generate_event_id(room_id)
                    thumb_path = self._save_thumbnail(anonymized_frame, event_id)
                    
                    event = WasteEvent(
                        event_id=event_id,
                        room_id=room_id,
                        room_name=room_name,
                        timestamp=current_time,
                        duration_seconds=waste_duration,
                        light_status=light_status,
                        fan_status=fan_status,
                        monitor_status=monitor_status,
                        thumbnail_path=thumb_path
                    )
                    
                    self._events.append(event)
                    self._save_events()
                    self._save_events_to_db(event)
                    
                    # Send multi-channel alerts (SMS, WhatsApp, etc.)
                    self._send_sms(event)
                    self._send_whatsapp(event)
                    
                    state['last_alert_time'] = current_time
                    
                    return event
            else:
                # Not in waste state - reset
                state['in_waste'] = False
                state['waste_start_time'] = None
        
        return None
    
    def get_room_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get current state for a room."""
        with self._lock:
            return self._room_states.get(room_id)
    
    def get_recent_events(self, limit: int = 10) -> List[WasteEvent]:
        """Get recent waste events."""
        return self._events[-limit:] if self._events else []
    
    def get_all_events(self) -> List[WasteEvent]:
        """Get all events."""
        return self._events
    
    def get_waste_duration(self, room_id: str) -> float:
        """Get current waste duration for a room (0 if not in waste)."""
        with self._lock:
            state = self._room_states.get(room_id)
            if state and state['in_waste'] and state['waste_start_time']:
                return time.time() - state['waste_start_time']
        return 0.0
    
    def get_config(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'initial_delay': self.initial_delay,
            'repeat_interval': self.repeat_interval,
            'storage_enabled': self.storage_enabled,
            'events_count': len(self._events)
        }


def create_alert_manager(config: Dict[str, Any]) -> AlertManager:
    """Factory function to create AlertManager."""
    alert_config = config.get('alerts', {})
    initial_delay = alert_config.get('initial_delay_seconds', 3)
    repeat_interval = alert_config.get('repeat_interval_seconds', 15)
    print(f"[AlertManager] Creating with delay={initial_delay}s, repeat={repeat_interval}s")
    return AlertManager(
        config=alert_config,
        initial_delay=initial_delay,
        repeat_interval=repeat_interval
    )
