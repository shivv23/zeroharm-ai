import logging
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any

logger = logging.getLogger("zeroharm-vision")

try:
    from ultralytics import YOLO
    _HAS_ULTRALYTICS = True
except ImportError:
    YOLO = None
    _HAS_ULTRALYTICS = False
    logger.warning("ultralytics not installed — vision integration disabled")

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    cv2 = None
    _HAS_CV2 = False

import constants as C
from config_loader import get_vision_settings as _get_vision_settings


class VisionIntegration:
    def __init__(self):
        self._model = None
        self._model_path = C.VISION_MODEL_PATH
        self._rtsp_threads: Dict[str, threading.Thread] = {}
        self._rtsp_flags: Dict[str, threading.Event] = {}
        self._rtsp_callbacks: Dict[str, Callable] = {}

    def load_model(self, model_path: Optional[str] = None) -> bool:
        if not _HAS_ULTRALYTICS:
            logger.error("Cannot load model — ultralytics not installed")
            return False
        try:
            path = model_path or self._model_path
            self._model = YOLO(path)
            logger.info(f"YOLO model loaded: {path}")
            return True
        except Exception as e:
            logger.exception(f"Failed to load YOLO model: {e}")
            self._model = None
            return False

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and _HAS_ULTRALYTICS

    def process_frame(self, frame) -> List[Dict[str, Any]]:
        if not self.is_loaded:
            return []
        try:
            results = self._model(frame, verbose=False)
            detections = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    label = self._model.names[cls_id] if self._model.names else str(cls_id)
                    detections.append({
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "confidence": round(conf, 3),
                        "class_id": cls_id,
                        "label": label,
                    })
            return detections
        except Exception as e:
            logger.exception(f"Frame inference error: {e}")
            return []

    def process_rtsp_stream(self, rtsp_url: str, callback: Callable[[List[Dict[str, Any]]], None]) -> bool:
        if not _HAS_CV2:
            logger.error("Cannot process RTSP — opencv-python not installed")
            return False
        if rtsp_url in self._rtsp_threads and self._rtsp_threads[rtsp_url].is_alive():
            logger.warning(f"RTSP stream already active: {rtsp_url}")
            return False
        stop_flag = threading.Event()
        self._rtsp_flags[rtsp_url] = stop_flag
        self._rtsp_callbacks[rtsp_url] = callback
        t = threading.Thread(target=self._rtsp_worker, args=(rtsp_url, stop_flag, callback), daemon=True)
        self._rtsp_threads[rtsp_url] = t
        t.start()
        logger.info(f"RTSP stream started: {rtsp_url}")
        return True

    def stop_rtsp_stream(self, rtsp_url: str) -> bool:
        if rtsp_url not in self._rtsp_flags:
            return False
        self._rtsp_flags[rtsp_url].set()
        self._rtsp_threads.pop(rtsp_url, None)
        self._rtsp_callbacks.pop(rtsp_url, None)
        self._rtsp_flags.pop(rtsp_url, None)
        logger.info(f"RTSP stream stopped: {rtsp_url}")
        return True

    def _rtsp_worker(self, rtsp_url: str, stop_flag: threading.Event, callback: Callable):
        cap = None
        try:
            cap = cv2.VideoCapture(rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            while not stop_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    stop_flag.wait(1.0)
                    continue
                if self.is_loaded:
                    detections = self.process_frame(frame)
                    if detections:
                        try:
                            callback(detections)
                        except Exception as e:
                            logger.error(f"RTSP callback error: {e}")
                else:
                    stop_flag.wait(C.CAMERA_CHECK_INTERVAL)
        except Exception as e:
            logger.exception(f"RTSP worker error for {rtsp_url}: {e}")
        finally:
            if cap is not None:
                cap.release()

    def detect_ppe(self, frame) -> Dict[str, int]:
        if not self.is_loaded:
            return {"helmet": 0, "vest": 0, "gloves": 0, "face_shield": 0, "safety_glasses": 0}
        try:
            detections = self.process_frame(frame)
            counts = {"helmet": 0, "vest": 0, "gloves": 0, "face_shield": 0, "safety_glasses": 0}
            ppe_keywords = {"helmet": ["helmet", "hardhat"], "vest": ["vest", "hi-vis"],
                            "gloves": ["glove"], "face_shield": ["face shield", "faceshield"],
                            "safety_glasses": ["safety glasses", "safety_glasses", "goggles"]}
            for d in detections:
                label = d.get("label", "").lower()
                for ppe_type, keywords in ppe_keywords.items():
                    if any(kw in label for kw in keywords):
                        counts[ppe_type] = counts.get(ppe_type, 0) + 1
            return counts
        except Exception as e:
            logger.exception(f"PPE detection error: {e}")
            return {"helmet": 0, "vest": 0, "gloves": 0, "face_shield": 0, "safety_glasses": 0}

    def detect_zone_violations(self, frame, zone_boundaries: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        if not self.is_loaded:
            return []
        try:
            detections = self.process_frame(frame)
            violations = []
            person_labels = {"person", "worker"}
            persons = [d for d in detections if d.get("label", "").lower() in person_labels]
            for p in persons:
                cx = (p["bbox"][0] + p["bbox"][2]) / 2
                cy = (p["bbox"][1] + p["bbox"][3]) / 2
                for zone in zone_boundaries:
                    x_min = zone.get("x_min", 0)
                    y_min = zone.get("y_min", 0)
                    x_max = zone.get("x_max", 1)
                    y_max = zone.get("y_max", 1)
                    if x_min <= cx <= x_max and y_min <= cy <= y_max:
                        restricted = zone.get("restricted", True)
                        if restricted:
                            violations.append({
                                "zone_id": zone.get("zone_id", "unknown"),
                                "zone_name": zone.get("zone_name", ""),
                                "person_bbox": p["bbox"],
                                "confidence": p["confidence"],
                                "violation_type": "restricted_entry",
                                "timestamp": datetime.now().isoformat(),
                            })
            return violations
        except Exception as e:
            logger.exception(f"Zone violation detection error: {e}")
            return []

    def get_safety_violations_from_detections(
        self, detections: List[Dict[str, Any]], zone_id: str
    ) -> List[Dict[str, Any]]:
        if not detections:
            return []
        try:
            violations = []
            ppe_counts = {"helmet": 0, "vest": 0, "gloves": 0, "face_shield": 0}
            ppe_keywords = {"helmet": ["helmet", "hardhat"], "vest": ["vest", "hi-vis"],
                            "gloves": ["glove"], "face_shield": ["face shield", "faceshield"]}
            person_count = 0
            for d in detections:
                label = d.get("label", "").lower()
                if label == "person":
                    person_count += 1
                for ppe_type, keywords in ppe_keywords.items():
                    if any(kw in label for kw in keywords):
                        ppe_counts[ppe_type] = ppe_counts.get(ppe_type, 0) + 1
            if person_count > 0:
                settings = _get_vision_settings()
                zones = settings.get("zones", {})
                zone_cfg = zones.get(zone_id, {})
                required_ppe = zone_cfg.get("ppe_required", [])
                for item in required_ppe:
                    if ppe_counts.get(item, 0) < person_count:
                        violations.append({
                            "type": "ppe_violation",
                            "severity": settings.get("alert_severity", "high"),
                            "zone_id": zone_id,
                            "detail": f"Missing {item} — detected {ppe_counts.get(item, 0)} but {person_count} worker(s) present",
                            "timestamp": datetime.now().isoformat(),
                            "source": "vision",
                        })
            return violations
        except Exception as e:
            logger.exception(f"Safety violations error: {e}")
            return []

    def get_status(self) -> Dict[str, Any]:
        return {
            "enabled": C.VISION_ENABLED,
            "model_loaded": self.is_loaded,
            "ultralytics_available": _HAS_ULTRALYTICS,
            "opencv_available": _HAS_CV2,
            "active_streams": list(self._rtsp_flags.keys()),
            "model_path": self._model_path,
        }
