import base64
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from PIL import Image

from backend.config import ENABLE_LLM, OPENAI_API_KEY
from backend.db.history_repo import get_image, insert_detection, now_iso
from backend.services.upload_service import normalise_bounds

router = APIRouter(tags=["optional-llm"])

ALLOWED_LLM_MODELS = {"gpt-4o-mini", "gpt-4.1-mini"}
LLM_COLOURS = {
    "building": "#FF6B6B",
    "rooftop": "#FF6B6B",
    "water": "#2196F3",
    "tree": "#4CAF50",
    "vegetation": "#33691E",
    "road": "#9E9E9E",
    "open ground": "#A1887F",
    "vehicle": "#FF9800",
    "car": "#FF9800",
}
FALLBACK_COLOURS = ["#FF6B6B", "#4CAF50", "#2196F3", "#9E9E9E", "#FF9800", "#7E57C2", "#26A69A", "#EC407A"]


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(cleaned[start:end + 1])
    if isinstance(parsed, list):
        return {"detections": parsed}
    return parsed


def _colour_for_label(label: str, index: int) -> str:
    normalised = label.lower().strip().replace("_", " ")
    for key, colour in LLM_COLOURS.items():
        if key in normalised:
            return colour
    return FALLBACK_COLOURS[index % len(FALLBACK_COLOURS)]


def _normalise_bbox(raw_bbox: Any, width: int, height: int) -> List[int] | None:
    if not isinstance(raw_bbox, list) or len(raw_bbox) != 4:
        return None
    try:
        values = [float(v) for v in raw_bbox]
    except (TypeError, ValueError):
        return None

    x1, y1, x2, y2 = values

    # Some LLM prompts return 0-1000 coordinates. Scale them when all values fit that range.
    if max(values) <= 1000 and (width > 1000 or height > 1000):
        x1 = x1 / 1000 * width
        x2 = x2 / 1000 * width
        y1 = y1 / 1000 * height
        y2 = y2 / 1000 * height

    x1, x2 = sorted((max(0, min(width, x1)), max(0, min(width, x2))))
    y1, y2 = sorted((max(0, min(height, y1)), max(0, min(height, y2))))
    if x2 - x1 < 2 or y2 - y1 < 2:
        return None
    return [int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))]


def _normalise_detections(parsed: Dict[str, Any], width: int, height: int, threshold: float) -> List[Dict[str, Any]]:
    raw_items = parsed.get("detections", [])
    if not isinstance(raw_items, list):
        return []

    detections: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("class") or "region").strip().lower()
        try:
            confidence = float(item.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))
        if confidence < threshold:
            continue

        bbox = _normalise_bbox(item.get("bbox") or item.get("approximate_bbox"), width, height)
        if bbox is None:
            continue
        x1, y1, x2, y2 = bbox
        detections.append(
            {
                "id": f"llm-{index}",
                "label": label,
                "confidence": round(confidence, 4),
                "bbox": bbox,
                "pixel_area": int((x2 - x1) * (y2 - y1)),
                "color": _colour_for_label(label, index),
            }
        )
    detections.sort(key=lambda item: item["pixel_area"], reverse=True)
    return detections[:40]


@router.post("/llm/analyze")
async def llm_analyze(request: Request):
    if not ENABLE_LLM:
        raise HTTPException(status_code=503, detail="LLM mode is disabled. Set ENABLE_LLM=true on the server and provide OPENAI_API_KEY.")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured on the server.")

    payload = await request.json()
    image_id = payload.get("image_id")
    model = payload.get("model", "gpt-4o-mini")
    if model not in ALLOWED_LLM_MODELS:
        raise HTTPException(status_code=422, detail="Unsupported LLM model selected.")

    try:
        threshold = float(payload.get("confidence_threshold", 0.5))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="confidence_threshold must be numeric.") from exc
    threshold = max(0.0, min(1.0, threshold))

    image_record = await get_image(image_id)
    if not image_record:
        raise HTTPException(status_code=404, detail="Image ID was not found.")

    image_path = Path(image_record["filepath"])
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file was not found on disk.")

    bounds = normalise_bounds(payload.get("bounds") or image_record.get("bounds"))
    image_bytes = image_path.read_bytes()
    mime_type = image_record.get("mime_type", "image/jpeg")
    image_data_url = f"data:{mime_type};base64," + base64.b64encode(image_bytes).decode("utf-8")

    with Image.open(image_path) as image:
        width, height = image.size

    started = time.perf_counter()
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Return only valid JSON. You are an expert aerial imagery analyst. Do not use markdown.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Analyse this drone aerial image. The original image size is {width}x{height} pixels. "
                                "Identify buildings, rooftops, trees, vegetation, roads, water, open ground and vehicles. "
                                "Return exactly this JSON shape: "
                                "{\"detections\":[{\"label\":\"building\",\"description\":\"brief note\",\"confidence\":0.82,\"bbox\":[x1,y1,x2,y2]}],\"scene_summary\":\"brief summary\"}. "
                                "Use pixel coordinates on the original image size."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                },
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content or "{}"
        parsed = _extract_json(content)
        detections = _normalise_detections(parsed, width, height, threshold)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail=f"LLM returned invalid JSON: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM request failed: {exc}") from exc

    detection_id = str(uuid.uuid4())
    inference_time_ms = int((time.perf_counter() - started) * 1000)
    record = {
        "detection_id": detection_id,
        "image_id": image_record["image_id"],
        "model_used": model,
        "detections": detections,
        "mask_path": "",
        "inference_time_ms": inference_time_ms,
        "confidence_threshold": threshold,
        "image_width": width,
        "image_height": height,
        "bounds": bounds,
        "created_at": now_iso(),
    }
    await insert_detection(record)

    return {
        "detection_id": detection_id,
        "image_id": image_record["image_id"],
        "model_used": model,
        "inference_time_ms": inference_time_ms,
        "image_width": width,
        "image_height": height,
        "bounds": bounds,
        "detections": detections,
        "mask_url": "",
        "mask_base64": None,
    }
