import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from backend.db.history_repo import get_image, insert_detection, now_iso
from backend.models.schemas import DetectionRequest
from backend.services.upload_service import normalise_bounds, save_upload

router = APIRouter(tags=["detect"])


@router.post("/detect")
async def detect(request: Request) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    bounds = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        file = form.get("file")
        if file is None:
            raise HTTPException(status_code=422, detail="Multipart detection requires a file field.")
        threshold_raw = form.get("confidence_threshold", "0.5")
        try:
            confidence_threshold = float(threshold_raw)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="confidence_threshold must be numeric.") from exc
        bounds_values = [form.get("sw_lng"), form.get("sw_lat"), form.get("ne_lng"), form.get("ne_lat")]
        if all(value is not None for value in bounds_values):
            bounds = [float(value) for value in bounds_values]
        image_record = await save_upload(file, normalise_bounds(bounds))
    else:
        try:
            payload = DetectionRequest.model_validate(await request.json())
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Detection request requires image_id and optional confidence_threshold.") from exc
        confidence_threshold = payload.confidence_threshold
        image_record = await get_image(payload.image_id)
        if not image_record:
            raise HTTPException(status_code=404, detail="Image ID was not found.")
        bounds = normalise_bounds(payload.bounds or image_record.get("bounds"))

    if not 0 <= confidence_threshold <= 1:
        raise HTTPException(status_code=422, detail="confidence_threshold must be between 0 and 1.")

    seg_service = getattr(request.app.state, "seg_service", None)
    model_error = getattr(request.app.state, "model_error", None)
    if seg_service is None:
        detail = "SegFormer model is not loaded."
        if model_error:
            detail += f" Startup error: {model_error}"
        raise HTTPException(status_code=503, detail=detail)

    try:
        result = seg_service.segment(image_record["filepath"], confidence_threshold)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Inference failed: {exc}") from exc

    detection_id = str(uuid.uuid4())
    record = {
        "detection_id": detection_id,
        "image_id": image_record["image_id"],
        "model_used": result["model_used"],
        "detections": result["detections"],
        "mask_path": result["mask_path"],
        "inference_time_ms": result["inference_time_ms"],
        "confidence_threshold": confidence_threshold,
        "image_width": result["image_width"],
        "image_height": result["image_height"],
        "bounds": bounds,
        "created_at": now_iso(),
    }
    await insert_detection(record)

    return {
        "detection_id": detection_id,
        "image_id": image_record["image_id"],
        "model_used": result["model_used"],
        "inference_time_ms": result["inference_time_ms"],
        "image_width": result["image_width"],
        "image_height": result["image_height"],
        "bounds": bounds,
        "detections": result["detections"],
        "mask_url": f"/api/masks/{result['mask_filename']}",
        "mask_base64": result["mask_base64"],
    }
