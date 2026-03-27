"""
Appliance Status Recognition Module using Roboflow Inference API.

Detects Light ON/OFF and Ceiling Fan ON/OFF states using pre-trained models.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import numpy as np
import cv2
import concurrent.futures
import time
import os

LOG_FILE = "logs/appliance_debug.log"

def _log(msg: str):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")


class ApplianceType(Enum):
    """Supported appliance types."""
    LIGHT = "light"
    CEILING_FAN = "ceiling_fan"
    MONITOR = "monitor"
    UNKNOWN = "unknown"


class Status(Enum):
    """Appliance power status."""
    ON = "ON"
    OFF = "OFF"
    UNKNOWN = "UNKNOWN"


@dataclass
class ApplianceStatusResult:
    """Result of appliance status detection."""
    appliance_type: ApplianceType
    status: Status
    confidence: float
    bounding_box: Optional[List[float]] = None
    model_predictions: Optional[Dict[str, Any]] = None


class RoboflowClient:
    """Wrapper for Roboflow inference API client."""
    
    def __init__(self):
        self._client = None
        self._initialized = False
    
    def _ensure_client(self):
        """Initialize the Roboflow client if not already initialized."""
        if not self._initialized:
            try:
                from inference_sdk import InferenceHTTPClient
                self._client = InferenceHTTPClient(
                    api_url="https://serverless.roboflow.com",
                    api_key="p3oHA7T2HAO4pgy61Vae"
                )
                self._initialized = True
            except ImportError:
                raise ImportError("inference-sdk package not installed. Run: pip install inference-sdk")
    
    def infer(self, image_path: str, model_id: str) -> Dict[str, Any]:
        """
        Run inference on an image using Roboflow API.
        
        Args:
            image_path: Path to the image file
            model_id: Roboflow model ID
            
        Returns:
            Prediction results from the model
        """
        self._ensure_client()
        return self._client.infer(image_path, model_id=model_id)
    
    def infer_frame(self, frame: np.ndarray, model_id: str, temp_dir: str = "temp") -> Dict[str, Any]:
        """
        Run inference on a numpy array frame by saving to temp file first.
        
        Args:
            frame: Image as numpy array (BGR format)
            model_id: Roboflow model ID
            temp_dir: Directory to save temporary image
            
        Returns:
            Prediction results from the model
        """
        import os
        from pathlib import Path
        
        self._ensure_client()
        
        temp_dir_path = Path(temp_dir)
        temp_dir_path.mkdir(parents=True, exist_ok=True)
        
        temp_image_path = temp_dir_path / f"temp_frame_{int(time.time()*1000)}.jpg"
        
        cv2.imwrite(str(temp_image_path), frame)
        
        result = None
        try:
            result = self.infer(str(temp_image_path), model_id)
        except Exception as e:
            _log(f"API ERROR: {e}")
            result = {}
        finally:
            if temp_image_path.exists():
                temp_image_path.unlink()
        
        return result if result is not None else {}
        
    def test_connection(self, model_id: str) -> bool:
        """Test the connection to Roboflow API."""
        try:
            self._ensure_client()
            # Try a very small dummy inference or just check client
            print(f"Testing Roboflow connection for model: {model_id}...")
            return self._client is not None
        except Exception as e:
            print(f"Roboflow connection test failed: {e}")
            return False


class ApplianceStatusRecognizer:
    """
    Recognizes appliance status (ON/OFF) using Roboflow inference API.
    
    Uses two models:
    - Light detection: coms-room-light-63vyv/1
    - Ceiling fan detection: ceiling-fan-detection-epfsk/1
    """
    
    LIGHT_MODEL_ID = "coms-room-light-63vyv/1"
    CEILING_FAN_MODEL_ID = "ceiling-fan-detection-epfsk/1"
    MONITOR_MODEL_ID = "monitor_detection-uj19t-zqnlq/1"
    
    def __init__(self, use_temp_files: bool = True):
        """
        Initialize the appliance status recognizer.
        
        Args:
            use_temp_files: If True, saves frames to temp files for inference.
                          If False, assumes images are saved separately.
        """
        self._client = RoboflowClient()
        self._use_temp_files = use_temp_files
    
    def detect_light_status(self, frame: np.ndarray) -> ApplianceStatusResult:
        """
        Detect light ON/OFF status.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            ApplianceStatusResult with light status
        """
        try:
            if self._use_temp_files:
                predictions = self._client.infer_frame(frame, self.LIGHT_MODEL_ID)
            else:
                raise ValueError("Direct frame inference requires temp files")
            
            return self._parse_light_predictions(predictions)
            
        except Exception as e:
            return ApplianceStatusResult(
                appliance_type=ApplianceType.LIGHT,
                status=Status.UNKNOWN,
                confidence=0.0,
                model_predictions={"error": str(e)}
            )
    
    def detect_ceiling_fan_status(self, frame: np.ndarray) -> ApplianceStatusResult:
        """
        Detect ceiling fan ON/OFF status.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            ApplianceStatusResult with ceiling fan status
        """
        try:
            if self._use_temp_files:
                predictions = self._client.infer_frame(frame, self.CEILING_FAN_MODEL_ID)
            else:
                raise ValueError("Direct frame inference requires temp files")
            
            _log(f"FAN RAW PREDICTIONS: {predictions}")
            return self._parse_ceiling_fan_predictions(predictions)
            
        except Exception as e:
            return ApplianceStatusResult(
                appliance_type=ApplianceType.CEILING_FAN,
                status=Status.UNKNOWN,
                confidence=0.0,
                model_predictions={"error": str(e)}
            )
            
    def detect_monitor_status(self, frame: np.ndarray) -> ApplianceStatusResult:
        """
        Detect monitor ON/OFF status.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            ApplianceStatusResult with monitor status
        """
        try:
            if self._use_temp_files:
                predictions = self._client.infer_frame(frame, self.MONITOR_MODEL_ID)
            else:
                raise ValueError("Direct frame inference requires temp files")
            
            _log(f"MONITOR RAW PREDICTIONS: {predictions}")
            return self._parse_monitor_predictions(predictions)
            
        except Exception as e:
            _log(f"MONITOR ERROR: {e}")
            return ApplianceStatusResult(
                appliance_type=ApplianceType.MONITOR,
                status=Status.UNKNOWN,
                confidence=0.0,
                model_predictions={"error": str(e)}
            )
    
    def detect_all_appliances(self, frame: np.ndarray) -> List[ApplianceStatusResult]:
        """
        Detect both light and ceiling fan status in parallel to reduce latency.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            List of ApplianceStatusResult for each appliance type
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_light = executor.submit(self.detect_light_status, frame)
            future_fan = executor.submit(self.detect_ceiling_fan_status, frame)
            future_monitor = executor.submit(self.detect_monitor_status, frame)
            
            # Wait for all results
            light_result = future_light.result()
            fan_result = future_fan.result()
            monitor_result = future_monitor.result()
            
        return [light_result, fan_result, monitor_result]
    
    def _parse_light_predictions(self, predictions: Dict[str, Any]) -> ApplianceStatusResult:
        """
        Parse Roboflow predictions for light detection.
        
        The model likely returns predictions with class labels like:
        - "light on" or "light"
        - "light off"
        
        Args:
            predictions: Raw predictions from Roboflow API
            
        Returns:
            Parsed ApplianceStatusResult
        """
        predictions_dict = predictions if isinstance(predictions, dict) else {}
        
        predictions_list = predictions_dict.get("predictions", [])
        
        print(f"\n>>> LIGHT API RESPONSE: {predictions_dict}")
        print(f">>> PREDICTIONS LIST: {predictions_list}")
        
        if not predictions_list:
            return ApplianceStatusResult(
                appliance_type=ApplianceType.LIGHT,
                status=Status.UNKNOWN,
                confidence=0.0,
                model_predictions=predictions_dict
            )
        
        highest_conf = 0.0
        detected_class = "unknown"
        bbox = None
        
        # Log status for debugging
        print("\n" + "="*40)
        if not predictions_list:
            print("DIAGNOSTIC - Light check: No lights detected in frame")
        else:
            print(f"DIAGNOSTIC - Light objects found: {len(predictions_list)}")
            print(f"DIAGNOSTIC - Labels: {[p.get('class') for p in predictions_list]}")
        print("="*40 + "\n")
            
        for pred in predictions_list:
            conf = pred.get("confidence", 0.0)
            class_name = pred.get("class", pred.get("class_name", "")).lower()
            
            if conf > highest_conf:
                highest_conf = conf
                detected_class = class_name
                # Roboflow returns x, y, width, height (center coords)
                if "x" in pred and "width" in pred:
                    bbox = [pred["x"], pred["y"], pred["width"], pred["height"]]
                else:
                    bbox = pred.get("bbox", [])
        
        # Improved parsing for light status
        status = Status.OFF
        if any(token in detected_class for token in ["on", "light", "glow", "lamp", "bright", "tube"]):
            if "off" not in detected_class:
                status = Status.ON
            else:
                status = Status.OFF
        
        if status == Status.ON:
            print(f"DIAGNOSTIC - SUCCESS: Light status determined as ON (Conf: {highest_conf:.2f})")
        
        return ApplianceStatusResult(
            appliance_type=ApplianceType.LIGHT,
            status=status,
            confidence=highest_conf,
            bounding_box=bbox,
            model_predictions=predictions_dict
        )
    
    def _parse_ceiling_fan_predictions(self, predictions: Dict[str, Any]) -> ApplianceStatusResult:
        """
        Parse Roboflow predictions for ceiling fan detection.
        
        The model likely returns predictions with class labels like:
        - "fan on" or "ceiling fan"
        - "fan off"
        
        Args:
            predictions: Raw predictions from Roboflow API
            
        Returns:
            Parsed ApplianceStatusResult
        """
        predictions_dict = predictions if isinstance(predictions, dict) else {}
        
        predictions_list = predictions_dict.get("predictions", [])
        
        print(f"\n>>> FAN API RESPONSE: {predictions_dict}")
        print(f">>> PREDICTIONS LIST: {predictions_list}")
        
        if not predictions_list:
            return ApplianceStatusResult(
                appliance_type=ApplianceType.CEILING_FAN,
                status=Status.UNKNOWN,
                confidence=0.0,
                model_predictions=predictions_dict
            )
        
        highest_conf = 0.0
        detected_class = "unknown"
        bbox = None
        
        if predictions_list:
            print(f"DEBUG - Fan predictions: {[p.get('class') for p in predictions_list]}")
            
        for pred in predictions_list:
            conf = pred.get("confidence", 0.0)
            class_name = pred.get("class", pred.get("class_name", "")).lower()
            
            if conf > highest_conf:
                highest_conf = conf
                detected_class = class_name
                # Roboflow returns x, y, width, height (center coords)
                if "x" in pred and "width" in pred:
                    bbox = [pred["x"], pred["y"], pred["width"], pred["height"]]
                else:
                    bbox = pred.get("bbox", [])
        
        # Improved parsing for fan status
        status = Status.OFF
        if any(token in detected_class for token in ["on", "fan", "spinning", "ceiling", "rotor"]):
            if "off" not in detected_class:
                status = Status.ON
            else:
                status = Status.OFF
        
        return ApplianceStatusResult(
            appliance_type=ApplianceType.CEILING_FAN,
            status=status,
            confidence=highest_conf,
            bounding_box=bbox,
            model_predictions=predictions_dict
        )
        
    def _parse_monitor_predictions(self, predictions: Dict[str, Any]) -> ApplianceStatusResult:
        """Parse Roboflow predictions for monitor detection."""
        predictions_dict = predictions if isinstance(predictions, dict) else {}
        predictions_list = predictions_dict.get("predictions", [])
        
        _log(f"MONITOR API RESPONSE: {predictions_dict}")
        
        if not predictions_list:
            return ApplianceStatusResult(
                appliance_type=ApplianceType.MONITOR,
                status=Status.OFF,
                confidence=0.0,
                model_predictions=predictions_dict
            )
        
        highest_conf = 0.0
        detected_class = "unknown"
        bbox = None
        
        for pred in predictions_list:
            conf = pred.get("confidence", 0.0)
            class_name = pred.get("class", pred.get("class_name", "")).lower()
            
            if conf > highest_conf:
                highest_conf = conf
                detected_class = class_name
                # Roboflow returns x, y, width, height (center coords)
                if "x" in pred and "width" in pred:
                    bbox = [pred["x"], pred["y"], pred["width"], pred["height"]]
                else:
                    bbox = pred.get("bbox", [])
        
        # Determine status
        status = Status.OFF
        if any(token in detected_class for token in ["on", "active", "display", "monitor", "screen", "power"]):
            if "off" not in detected_class:
                status = Status.ON
            else:
                status = Status.OFF
        
        return ApplianceStatusResult(
            appliance_type=ApplianceType.MONITOR,
            status=status,
            confidence=highest_conf,
            bounding_box=bbox,
            model_predictions=predictions_dict
        )


def create_appliance_recognizer() -> ApplianceStatusRecognizer:
    """Factory function to create an ApplianceStatusRecognizer instance."""
    return ApplianceStatusRecognizer()


def detect_light(frame: np.ndarray) -> ApplianceStatusResult:
    """Convenience function to detect light status."""
    recognizer = ApplianceStatusRecognizer()
    return recognizer.detect_light_status(frame)


def detect_ceiling_fan(frame: np.ndarray) -> ApplianceStatusResult:
    """Convenience function to detect ceiling fan status."""
    recognizer = ApplianceStatusRecognizer()
    return recognizer.detect_ceiling_fan_status(frame)