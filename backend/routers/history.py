from fastapi import APIRouter, HTTPException

from backend.db.history_repo import delete_detection, get_detection, list_history

router = APIRouter(tags=["history"])


@router.get("/history")
async def history(page: int = 1, per_page: int = 20):
    total, rows = await list_history(page, per_page)
    items = []
    for row in rows:
        items.append(
            {
                "detection_id": row["detection_id"],
                "image_id": row["image_id"],
                "timestamp": row["created_at"],
                "model_used": row["model_used"],
                "class_count": len(row["detected_classes"]),
                "image_thumbnail_url": f"/api/images/{row['image_id']}",
                "detected_classes": row["detected_classes"],
            }
        )
    return {"total": total, "page": max(page, 1), "per_page": min(max(per_page, 1), 100), "items": items}


@router.get("/history/{detection_id}")
async def get_history_item(detection_id: str):
    row = await get_detection(detection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Detection history record was not found.")
    mask_filename = row["mask_path"].split("/")[-1].split("\\")[-1]
    return {
        "detection_id": row["detection_id"],
        "image_id": row["image_id"],
        "model_used": row["model_used"],
        "inference_time_ms": row["inference_time_ms"],
        "image_width": row["image_width"],
        "image_height": row["image_height"],
        "bounds": row["bounds"],
        "detections": row["detections"],
        "mask_url": mask_url,
        "mask_base64": None,
    }


@router.delete("/history/{detection_id}")
async def remove_history_item(detection_id: str):
    deleted = await delete_detection(detection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Detection history record was not found.")
    return {"deleted": True, "detection_id": detection_id}
