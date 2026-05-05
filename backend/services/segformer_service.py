import base64
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

from backend.config import MAX_INFERENCE_SIDE, MIN_AREA_RATIO, MODEL_ID, OUTPUT_DIR

ADE20K_FALLBACK_PALETTE = [
    "#FF6B6B", "#4CAF50", "#8BC34A", "#2196F3", "#9E9E9E", "#FF9800", "#795548", "#33691E",
    "#BDBDBD", "#7E57C2", "#26A69A", "#EC407A", "#5C6BC0", "#D4E157", "#8D6E63", "#26C6DA",
]

PREFERRED_LABEL_COLOURS = {
    "building": "#FF6B6B",
    "tree": "#4CAF50",
    "grass": "#8BC34A",
    "water": "#2196F3",
    "road": "#9E9E9E",
    "car": "#FF9800",
    "sidewalk": "#795548",
    "vegetation": "#33691E",
    "fence": "#BDBDBD",
    "earth": "#A1887F",
    "field": "#9CCC65",
    "path": "#BCAAA4",
}


class SegformerService:
    """SegFormer service loaded once and reused across API requests."""

    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.device = "cpu"
        self.processor = None
        self.model = None
        self.id2label: dict[int, str] = {}
        self._load()

    def _load(self) -> None:
        import torch
        from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = SegformerImageProcessor.from_pretrained(self.model_id)
        self.model = SegformerForSemanticSegmentation.from_pretrained(self.model_id)
        self.model.eval()
        self.model.to(self.device)
        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}

    def segment(self, image_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        import torch

        if self.processor is None or self.model is None:
            raise RuntimeError("SegFormer model is not loaded.")

        start = time.perf_counter()
        image = Image.open(image_path).convert("RGB")
        if max(image.size) > MAX_INFERENCE_SIDE:
            image.thumbnail((MAX_INFERENCE_SIDE, MAX_INFERENCE_SIDE), Image.Resampling.LANCZOS)
        width, height = image.size

        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits[0]
            probs_small = torch.softmax(logits, dim=0).detach().cpu().numpy()
            seg_small = np.argmax(probs_small, axis=0).astype(np.uint8)

        seg_map = np.array(
            Image.fromarray(seg_small).resize((width, height), Image.Resampling.NEAREST),
            dtype=np.uint8,
        )

        detections = self._extract_detections(seg_map, seg_small, probs_small, width, height, confidence_threshold)
        mask_image = self._colorize_mask(seg_map)
        mask_filename = f"{uuid.uuid4()}_mask.png"
        mask_path = OUTPUT_DIR / mask_filename
        mask_image.save(mask_path)

        buffer = BytesIO()
        mask_image.save(buffer, format="PNG")
        mask_base64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return {
            "model_used": self.model_id,
            "inference_time_ms": elapsed_ms,
            "image_width": width,
            "image_height": height,
            "detections": detections,
            "mask_filename": mask_filename,
            "mask_path": str(mask_path),
            "mask_base64": mask_base64,
        }

    def _extract_detections(
        self,
        seg_map: np.ndarray,
        seg_small: np.ndarray,
        probs_small: np.ndarray,
        width: int,
        height: int,
        confidence_threshold: float,
    ) -> List[Dict[str, Any]]:
        """Convert the semantic mask into component-level bounding boxes.

        Earlier versions merged every area of the same class into one very large box.
        That made scattered buildings or trees look like one object. This version keeps
        meaningful connected components as separate regions while still allowing the UI
        to toggle them by class label.
        """
        detections: List[Dict[str, Any]] = []
        min_area = max(32, int(width * height * MIN_AREA_RATIO))
        present_classes = np.unique(seg_map)

        for class_id_raw in present_classes:
            class_id = int(class_id_raw)
            label = self.id2label.get(class_id, f"class_{class_id}")
            binary = (seg_map == class_id).astype(np.uint8)
            total_pixel_area = int(binary.sum())
            if total_pixel_area < min_area:
                continue

            small_mask = seg_small == class_id
            if small_mask.any():
                confidence = float(probs_small[class_id][small_mask].mean())
            else:
                confidence = 0.0
            if confidence < confidence_threshold:
                continue

            num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
            colour = self._colour_for_label(label, class_id)
            kept_for_class = 0

            for idx in range(1, num_labels):
                x, y, w, h, area = stats[idx]
                area = int(area)
                if area < min_area:
                    continue
                kept_for_class += 1
                detections.append(
                    {
                        "id": f"{label}-{class_id}-{idx}",
                        "label": label,
                        "confidence": round(confidence, 4),
                        "bbox": [int(x), int(y), int(x + w), int(y + h)],
                        "pixel_area": area,
                        "color": colour,
                    }
                )

            # Fallback for classes that exist but are fragmented into areas below min_area.
            if kept_for_class == 0:
                ys, xs = np.where(binary > 0)
                if len(xs) == 0:
                    continue
                detections.append(
                    {
                        "id": f"{label}-{class_id}-all",
                        "label": label,
                        "confidence": round(confidence, 4),
                        "bbox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
                        "pixel_area": total_pixel_area,
                        "color": colour,
                    }
                )

        detections.sort(key=lambda item: item["pixel_area"], reverse=True)
        return detections[:40]

    def _colour_for_label(self, label: str, class_id: int) -> str:
        normalised = label.lower().replace(" ", "_")
        if normalised in PREFERRED_LABEL_COLOURS:
            return PREFERRED_LABEL_COLOURS[normalised]
        return ADE20K_FALLBACK_PALETTE[class_id % len(ADE20K_FALLBACK_PALETTE)]

    def _colorize_mask(self, seg_map: np.ndarray) -> Image.Image:
        height, width = seg_map.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        for class_id_raw in np.unique(seg_map):
            class_id = int(class_id_raw)
            label = self.id2label.get(class_id, f"class_{class_id}")
            hex_colour = self._colour_for_label(label, class_id).lstrip("#")
            colour = tuple(int(hex_colour[i:i + 2], 16) for i in (0, 2, 4))
            mask = seg_map == class_id
            rgba[mask, 0] = colour[0]
            rgba[mask, 1] = colour[1]
            rgba[mask, 2] = colour[2]
            rgba[mask, 3] = 135
        return Image.fromarray(rgba, mode="RGBA")
