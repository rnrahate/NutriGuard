"""
YOLO food-detection integration point.

YOLO_MODEL_PATH is not yet provided in this project. If it's left empty (or
the file doesn't exist), detect() returns a result with configured=False and
the UI shows a plain "not configured yet" notice — it never fabricates boxes,
labels, or confidence values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image


@dataclass
class Detection:
    label: str
    confidence: float
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixel coords


@dataclass
class YoloResult:
    configured: bool
    ran: bool
    detections: list[Detection] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def food_detected(self) -> bool:
        return self.ran and len(self.detections) > 0


def _try_import_ultralytics():
    try:
        from ultralytics import YOLO  # noqa: F401
        return YOLO
    except ImportError:
        return None


def load_yolo(path: Optional[Path]):
    """Returns (model_or_none, error_or_none). Cache this with st.cache_resource at the call site."""
    if path is None or not path.exists():
        return None, None  # simply "not configured" — not an error

    YOLO = _try_import_ultralytics()
    if YOLO is None:
        return None, "ultralytics package is not installed (`pip install ultralytics`)."

    try:
        return YOLO(str(path)), None
    except Exception as exc:  # noqa: BLE001
        return None, f"Failed to load YOLO weights: {exc}"


def detect(image: Image.Image, yolo_model, load_error: Optional[str]) -> YoloResult:
    if yolo_model is None:
        return YoloResult(configured=False, ran=False, error=load_error)

    try:
        results = yolo_model.predict(image.convert("RGB"), verbose=False)
        detections: list[Detection] = []
        for r in results:
            names = r.names
            for box in r.boxes:
                cls_id = int(box.cls.item())
                conf = float(box.conf.item())
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                detections.append(Detection(
                    label=names.get(cls_id, str(cls_id)),
                    confidence=conf,
                    box=(x1, y1, x2, y2),
                ))
        return YoloResult(configured=True, ran=True, detections=detections)
    except Exception as exc:  # noqa: BLE001
        return YoloResult(configured=True, ran=False, error=str(exc))
