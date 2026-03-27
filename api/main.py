"""
WattWatch Real-time API Server
Connects to IP webcam and provides real-time detection results via WebSocket.
Supports privacy-first ghost mode for face anonymization.
"""

import asyncio
import cv2
import numpy as np
import base64
import sys
import os
from pathlib import Path
import time
import json

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import threading

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import uuid

# Import enums from src so comparisons work correctly
from src.appliance_status import ApplianceType, Status


@dataclass
class DetectionResult:
    """Single detection result."""
    label: str
    confidence: float
    bbox: List[float]


@dataclass
class FrameResult:
    """Result for a single frame."""
    frame_id: int
    timestamp: float
    person_count: int
    detections: List[Dict[str, Any]]
    light_status: str
    fan_status: str
    image_width: int
    image_height: int
    processing_time_ms: float


class IPWebcamCapture:
    """Captures frames from IP webcam."""
    
    def __init__(self, url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.url = url
        self.username = username
        self.password = password
        self.cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._lock = threading.Lock()
        
    def connect(self) -> bool:
        """Connect to the IP webcam."""
        url = self.url.strip()
        
        # Handle webcam index (e.g., "0")
        try:
            if url.isdigit():
                url = int(url)
            elif url == "0":
                url = 0
        except:
            pass
        
        # If it's a string URL, ensure it has proper protocol
        if isinstance(url, str) and not url.startswith('http'):
            # Maybe it's just an IP address
            if ':' in url:
                url = 'http://' + url
            elif url.isdigit():
                url = int(url)
        
        print(f"Attempting to open video source: {url}")
        
        try:
            # Try different backends
            self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(url, cv2.CAP_ANY)
            
            if not self.cap.isOpened():
                print(f"Failed to open video source: {url}")
                return False
            
            # Test if we can read a frame
            ret, frame = self.cap.read()
            if not ret:
                print(f"Could not read first frame from {url}. Retrying with '/video'...")
                if isinstance(url, str) and not url.endswith('/video'):
                    self.cap.release()
                    new_url = url.rstrip('/') + '/video'
                    self.cap = cv2.VideoCapture(new_url, cv2.CAP_FFMPEG)
                    ret, frame = self.cap.read()
                    if ret:
                        print(f"Connected to {new_url}")
                        url = new_url
                    else:
                        print(f"Failed to read from {new_url} as well.")
                        return False
                else:
                    return False
                
            # Set buffer to minimal to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._running = True
            print(f"Successfully connected to camera")
            return True
        except Exception as e:
            import traceback
            print(f"Error opening camera: {traceback.format_exc()}")
            return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Read a frame from the webcam."""
        if not self.cap or not self._running:
            return None
        
        with self._lock:
            ret, frame = self.cap.read()
            if not ret:
                return None
            return frame
    
    def release(self):
        """Release the capture."""
        self._running = False
        with self._lock:
            if self.cap:
                self.cap.release()
                self.cap = None


@dataclass
class RoomData:
    """Data for a single room."""
    room_id: str
    room_name: str
    person_count: int
    light_status: str
    fan_status: str
    status: str
    last_update: float
    energy_saved: float = 0.0


class MultiRoomDetector:
    """Detector that manages multiple room data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.person_detector = None
        self.appliance_recognizer = None
        self.privacy_filter = None
        self.privacy_enabled = False
        self._frame_count = 0
        self._rooms: Dict[str, RoomData] = {}
        self._load_models()
        self._init_rooms()
        # Appliance status cache (updated by background thread)
        self._last_light_status = Status.OFF
        self._last_fan_status = Status.OFF
        # Background appliance detection
        self._latest_appliance_frame = None
        self._latest_result = None
        self._stop_event = threading.Event()
        self._appliance_frame_event = threading.Event()
        self._lock = threading.Lock()
        self._appliance_thread = None
        
        # Privacy storage settings
        privacy_config = config.get("privacy", {})
        storage_config = privacy_config.get("storage", {})
        self._save_raw = storage_config.get("save_raw", True)
        self._save_anon = storage_config.get("save_anonymized", True)
        self._save_every_n = storage_config.get("save_every_n_frames", 10)
        self._raw_dir = os.path.join(root_dir, storage_config.get("raw_dir", "data/raw"))
        self._anon_dir = os.path.join(root_dir, storage_config.get("anonymized_dir", "data/anonymized"))
        
        # Create directories
        if self._save_raw:
            os.makedirs(self._raw_dir, exist_ok=True)
        if self._save_anon:
            os.makedirs(self._anon_dir, exist_ok=True)

    def start_background_processing(self):
        """Start the background appliance detection thread."""
        if self._appliance_thread is None or not self._appliance_thread.is_alive():
            self._stop_event.clear()
            self._appliance_thread = threading.Thread(
                target=self._appliance_detection_loop, daemon=True
            )
            self._appliance_thread.start()
            print("Background appliance detection thread started")

    def stop_background_processing(self):
        """Stop the background appliance detection thread."""
        self._stop_event.set()
        self._appliance_frame_event.set()
        if self._appliance_thread:
            self._appliance_thread.join(timeout=2.0)
            print("Background appliance detection thread stopped")

    def submit_appliance_frame(self, frame: np.ndarray):
        """Push a frame to the appliance detection queue (non-blocking)."""
        with self._lock:
            self._latest_appliance_frame = frame.copy()
        self._appliance_frame_event.set()

    def _appliance_detection_loop(self):
        """Dedicated loop that runs appliance detection independently of the WS stream."""
        while not self._stop_event.is_set():
            triggered = self._appliance_frame_event.wait(timeout=1.0)
            if self._stop_event.is_set():
                break
            if not triggered:
                continue

            frame_to_process = None
            with self._lock:
                if self._latest_appliance_frame is not None:
                    frame_to_process = self._latest_appliance_frame.copy()
                    self._latest_appliance_frame = None
            self._appliance_frame_event.clear()

            if frame_to_process is None or self.appliance_recognizer is None:
                continue

            try:
                results = self.appliance_recognizer.detect_all_appliances(frame_to_process)
                with self._lock:
                    for r in results:
                        print(f"[BG Appliance] {r.appliance_type.value}: {r.status.value} (conf={r.confidence:.2f})")
                        if r.appliance_type == ApplianceType.LIGHT:
                            self._last_light_status = r.status
                        elif r.appliance_type == ApplianceType.CEILING_FAN:
                            self._last_fan_status = r.status
            except Exception as e:
                print(f"[BG Appliance] Error: {e}")
    
    def _init_rooms(self):
        """Initialize room data."""
        rooms_config = [
            {"id": "room-101", "name": "Lecture Hall 101"},
            {"id": "room-102", "name": "Lab 102"},
            {"id": "room-103", "name": "Meeting Room 103"},
            {"id": "room-104", "name": "Library 104"},
            {"id": "room-105", "name": "Seminar Hall 105"},
            {"id": "room-106", "name": "Computer Lab 106"},
        ]
        
        for room in rooms_config:
            self._rooms[room["id"]] = RoomData(
                room_id=room["id"],
                room_name=room["name"],
                person_count=0,
                light_status="OFF",
                fan_status="OFF",
                status="secure",
                last_update=time.time()
            )
    
    def _load_models(self):
        """Load the YOLO, appliance detection, and privacy filter models."""
        from src.detector import YOLODetector
        
        # Load YOLO for person detection
        model_config = self.config.get("model", {})
        model_name = model_config.get("name", "yolov8n.pt")
        
        # Ensure model path is absolute to the root
        if not os.path.isabs(model_name):
            model_path = os.path.join(root_dir, model_name)
            if os.path.exists(model_path):
                model_name = model_path
        
        self.person_detector = YOLODetector(
            model_name=model_name,
            confidence_threshold=model_config.get("confidence_threshold", 0.55),
            device=self.config.get("device", {}).get("type")
        )
        print("Loading YOLO model...")
        self.person_detector.load_model()
        print("YOLO model loaded")
        
        # Load privacy filter
        privacy_config = self.config.get("privacy", {})
        if privacy_config.get("enabled", True):
            try:
                from src.privacy_filter import PrivacyFilter
                self.privacy_filter = PrivacyFilter(
                    blur_method=privacy_config.get("blur_method", "solid"),
                    blur_level=privacy_config.get("blur_level", 99),
                    pixelate_blocks=privacy_config.get("pixelate_blocks", 4),
                    skip_frames=privacy_config.get("skip_frames", 3)
                )
                self.privacy_enabled = True
                print(f"Privacy filter loaded: {self.privacy_filter.get_config()}")
            except Exception as e:
                print(f"Warning: Could not load privacy filter: {e}")
                self.privacy_filter = None
                self.privacy_enabled = False
        else:
            self.privacy_filter = None
            self.privacy_enabled = False
        
        # Load appliance recognizer
        if self.config.get("appliance", {}).get("enabled", False):
            try:
                from src.appliance_status import ApplianceStatusRecognizer
                self.appliance_recognizer = ApplianceStatusRecognizer()
                print("Appliance recognizer loaded")
            except Exception as e:
                print(f"Warning: Could not load appliance recognizer: {e}")
    
    def process_frame(self, frame: np.ndarray, room_id: str = "room-101") -> FrameResult:
        """Process a single frame and return detection results."""
        start_time = time.time()
        
        # Resize frame for faster processing (standard YOLO/Roboflow size)
        h, w = frame.shape[:2]
        proc_w = 640
        proc_h = int(h * proc_w / w)
        proc_frame = cv2.resize(frame, (proc_w, proc_h))
        
        # Person detection
        person_detections = self.person_detector.detect_people(proc_frame)
        person_count = len(person_detections)
        
        # Adjust bounding boxes back to original size
        scale_x = w / proc_w
        scale_y = h / proc_h
        
        # Format detections for output
        detections = []
        for det in person_detections:
            bbox = det.get("bbox", [])
            if bbox:
                bbox = [bbox[0] * scale_x, bbox[1] * scale_y, bbox[2] * scale_x, bbox[3] * scale_y]
                
            detections.append({
                "label": det.get("class_name", "person"),
                "confidence": float(det.get("confidence", 0)),
                "bbox": bbox
            })
        
        # Appliance detection — use the cached result from the background thread
        self._frame_count += 1

        # Get last known status from background thread cache
        room = self._rooms.get(room_id)
        with self._lock:
            light_status = self._last_light_status.value
            fan_status = self._last_fan_status.value

        # Feed frame to background appliance detector
        if self.appliance_recognizer and self._latest_appliance_frame is not None:
            pass  # background thread picks it up

        # Update room data
        room_status = "waste" if (person_count == 0 and (light_status == "ON" or fan_status == "ON")) else "secure"

        if room:
            room.person_count = person_count
            room.light_status = light_status
            room.fan_status = fan_status
            room.status = room_status
            room.last_update = time.time()

        processing_time = (time.time() - start_time) * 1000

        height, width = frame.shape[:2]

        return FrameResult(
            frame_id=self._frame_count,
            timestamp=time.time(),
            person_count=person_count,
            detections=detections,
            light_status=light_status,
            fan_status=fan_status,
            image_width=width,
            image_height=height,
            processing_time_ms=processing_time
        )
    
    def get_all_rooms(self) -> Dict[str, RoomData]:
        """Get data for all rooms."""
        return self._rooms
    



# Global state
app_state = {
    "capture": None,
    "detector": None,
    "running": False,
    "config": {}
}


app = FastAPI(title="WattWatch Realtime API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CameraConfig(BaseModel):
    url: str
    username: Optional[str] = None
    password: Optional[str] = None


@app.post("/api/camera/connect")
async def connect_camera(config: CameraConfig):
    """Connect to IP webcam."""
    try:
        # Stop existing capture
        if app_state["capture"]:
            app_state["capture"].release()
        
        # Load config
        import yaml
        # Try local first, then parent
        config_path = Path("config.yaml")
        if not config_path.exists():
            config_path = Path(__file__).resolve().parent.parent / "config.yaml"
            
        if config_path.exists():
            print(f"Loading config from {config_path}")
            with open(config_path) as f:
                app_state["config"] = yaml.safe_load(f)
        else:
            print("No config.yaml found, using defaults")
            app_state["config"] = {}
        
        # Create new capture
        capture = IPWebcamCapture(
            url=config.url,
            username=config.username,
            password=config.password
        )
        
        print(f"Received URL: {config.url}")
        
        print("Connecting to camera capture...")
        connect_result = capture.connect()
        
        if not connect_result:
            print("Camera connection failed")
            raise HTTPException(
                status_code=400, 
                detail=f"Could not connect to '{config.url}'. "
                       f"Make sure:\n"
                       f"1. IP Webcam app is running on your phone\n"
                       f"2. Phone and PC are on the same WiFi\n"
                       f"3. Use the exact URL from the app"
            )
        
        print("Camera connected successfully. Initializing detector...")

        try:
            app_state["capture"] = capture
            app_state["detector"] = MultiRoomDetector(app_state["config"])
            # Start the background appliance detection thread
            app_state["detector"].start_background_processing()
        except Exception as det_e:
            import traceback
            print(f"Detector initialization failed: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Detector error: {str(det_e)}")

        print("Detector initialized. System ready.")
        app_state["running"] = True

        return {"status": "connected", "message": "Camera connected successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"Fatal error in connect_camera: {tb}")
        raise HTTPException(
            status_code=500, 
            detail={"message": str(e), "traceback": tb}
        )


@app.post("/api/camera/disconnect")
async def disconnect_camera():
    """Disconnect from IP webcam."""
    if app_state["capture"]:
        app_state["capture"].release()
        app_state["capture"] = None
    app_state["running"] = False
    return {"status": "disconnected"}


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    rooms_data = {}
    if app_state["detector"]:
        rooms = app_state["detector"].get_all_rooms()
        for room_id, room in rooms.items():
            rooms_data[room_id] = {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "person_count": room.person_count,
                "light_status": room.light_status,
                "fan_status": room.fan_status,
                "status": room.status,
                "last_update": room.last_update
            }
    
    return {
        "running": app_state["running"],
        "camera_connected": app_state["capture"] is not None,
        "frame_count": app_state["detector"]._frame_count if app_state["detector"] else 0,
        "privacy_enabled": app_state["detector"].privacy_enabled if app_state["detector"] else False,
        "rooms": rooms_data
    }


@app.get("/api/rooms")
async def get_rooms():
    """Get data for all rooms."""
    if not app_state["detector"]:
        return {"rooms": {}}
    
    rooms = app_state["detector"].get_all_rooms()
    rooms_data = {}
    for room_id, room in rooms.items():
        rooms_data[room_id] = {
            "room_id": room.room_id,
            "room_name": room.room_name,
            "person_count": room.person_count,
            "light_status": room.light_status,
            "fan_status": room.fan_status,
            "status": room.status,
            "last_update": room.last_update
        }
    
    return {"rooms": rooms_data}


@app.post("/api/privacy/toggle")
async def toggle_privacy(enabled: bool):
    """Toggle privacy mode on/off."""
    if not app_state["detector"]:
        raise HTTPException(status_code=400, detail="Detector not initialized")
    
    app_state["detector"].privacy_enabled = enabled
    return {"privacy_enabled": enabled}


@app.get("/api/privacy/status")
async def get_privacy_status():
    """Get current privacy mode status."""
    if not app_state["detector"]:
        return {"privacy_enabled": False, "available": False}
    
    return {
        "privacy_enabled": app_state["detector"].privacy_enabled,
        "privacy_available": app_state["detector"].privacy_filter is not None
    }


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time video streaming."""
    await websocket.accept()

    # Performance: process every frame but skip heavy ops periodically
    frame_counter = 0
    APPLIANCE_SUBMIT_EVERY = 5
    DETECTION_SKIP = 3  # Skip YOLO every N frames
    JPEG_QUALITY = 50   # Lower for faster encoding
    
    # Cached state for skipping heavy processing
    cached_person_count = 0
    cached_detections = []
    cached_light = "OFF"
    cached_fan = "OFF"

    try:
        while True:
            if not app_state["running"] or not app_state["capture"]:
                await asyncio.sleep(0.1)
                continue

            # Read frame (this is where most of the latency comes from - network)
            frame = app_state["capture"].read_frame()
            if frame is None:
                await asyncio.sleep(0.01)
                continue

            detector = app_state["detector"]
            person_count = 0
            light_status = "OFF"
            fan_status = "OFF"
            processing_time = 0
            detections = []

            # Get cached values when skipping detection
            use_cache = frame_counter % DETECTION_SKIP != 0
            
            if detector and not use_cache:
                start = time.time()

                # --- Person detection (YOLO) ---
                h, w = frame.shape[:2]
                proc_w = 640
                proc_h = int(h * proc_w / w)
                proc_frame = cv2.resize(frame, (proc_w, proc_h))

                person_dets = detector.person_detector.detect_people(proc_frame)
                person_count = len(person_dets)
                scale_x, scale_y = w / proc_w, h / proc_h
                detections = [
                    {
                        "label": d.get("class_name", "person"),
                        "confidence": float(d.get("confidence", 0)),
                        "bbox": [
                            d["bbox"][0] * scale_x, d["bbox"][1] * scale_y,
                            d["bbox"][2] * scale_x, d["bbox"][3] * scale_y
                        ] if d.get("bbox") else []
                    }
                    for d in person_dets
                ]

                # Update cache
                cached_person_count = person_count
                cached_detections = detections
                
                # --- Submit frame to background appliance detector ---
                frame_counter += 1
                if frame_counter % APPLIANCE_SUBMIT_EVERY == 0:
                    detector.submit_appliance_frame(proc_frame)

                # --- Read cached appliance status ---
                with detector._lock:
                    light_status = detector._last_light_status.value
                    fan_status = detector._last_fan_status.value
                    cached_light = light_status
                    cached_fan = fan_status

                # Update room data
                room = detector._rooms.get("room-101")
                room_status = "waste" if (person_count == 0 and (light_status == "ON" or fan_status == "ON")) else "secure"
                if room:
                    room.person_count = person_count
                    room.light_status = light_status
                    room.fan_status = fan_status
                    room.status = room_status
                    room.last_update = time.time()

                processing_time = (time.time() - start) * 1000
                detector._frame_count += 1
            else:
                # Use cached values
                person_count = cached_person_count
                detections = cached_detections
                light_status = cached_light
                fan_status = cached_fan
                
                room = detector._rooms.get("room-101") if detector else None
                if room:
                    room.person_count = person_count
                    room.light_status = light_status
                    room.fan_status = fan_status

            # Extract person bboxes for privacy filter
            person_bboxes = [d["bbox"] for d in detections if d.get("bbox")]

            # Apply privacy filter ONLY if people detected (skip if empty frame)
            raw_frame = frame.copy()
            anonymized_frame = frame.copy()
            face_detections = []
            
            if detector and getattr(detector, "privacy_enabled", False) and detector.privacy_filter and person_count > 0:
                try:
                    anonymized_frame, face_detections = detector.privacy_filter.anonymize_frame(
                        frame,
                        person_bboxes=person_bboxes
                    )
                except Exception as e:
                    pass

            # Resize for display - smaller for faster transmission
            h, w = frame.shape[:2]
            display_frame = anonymized_frame if detector and getattr(detector, "privacy_enabled", False) else frame
            if w > 640:
                display_frame = cv2.resize(display_frame, (640, int(h * 640 / w)))
                raw_frame = cv2.resize(raw_frame, (640, int(h * 640 / w)))

            # Encode with lower quality for speed
            _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')

            # Only send raw frame occasionally (not every frame)
            raw_frame_base64 = None
            if frame_counter % 30 == 0:
                _, raw_buffer = cv2.imencode('.jpg', raw_frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                raw_frame_base64 = base64.b64encode(raw_buffer).decode('utf-8')

            response = {
                "frame_id": int(time.time() * 1000),
                "timestamp": time.time(),
                "person_count": person_count,
                "detections": detections,
                "light_status": light_status,
                "fan_status": fan_status,
                "processing_time_ms": processing_time,
                "privacy_enabled": detector.privacy_enabled if detector else False,
                "frame": f"data:image/jpeg;base64,{frame_base64}",
                "raw_frame": f"data:image/jpeg;base64,{raw_frame_base64}" if raw_frame_base64 else None
            }

            await websocket.send_json(response)

            # Minimal sleep - just yield to event loop
            await asyncio.sleep(0.001)
            frame_counter += 1

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/ws/detections")
async def websocket_detections(websocket: WebSocket):
    """WebSocket endpoint for detection data only (no video)."""
    await websocket.accept()
    
    try:
        while True:
            if not app_state["running"] or not app_state["capture"]:
                await asyncio.sleep(0.1)
                continue
            
            frame = app_state["capture"].read_frame()
            if frame is None:
                await asyncio.sleep(0.05)
                continue
            
            if app_state["detector"]:
                result = app_state["detector"].process_frame(frame)
                
                response = {
                    "frame_id": result.frame_id,
                    "timestamp": result.timestamp,
                    "person_count": result.person_count,
                    "detections": result.detections,
                    "light_status": result.light_status,
                    "fan_status": result.fan_status,
                    "processing_time_ms": result.processing_time_ms
                }
                
                await websocket.send_json(response)
            
            await asyncio.sleep(0.05)
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)