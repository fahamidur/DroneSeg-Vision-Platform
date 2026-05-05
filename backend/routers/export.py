from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.db.history_repo import get_detection
from backend.services.geojson_service import detections_to_geojson

router = APIRouter(tags=["export"])


@router.get("/export/geojson/{detection_id}")
async def export_geojson(detection_id: str):
    row = await get_detection(detection_id)
    if not row:
        raise HTTPException(status_code=404, detail="Detection history record was not found.")
    geojson = detections_to_geojson(row)
    headers = {"Content-Disposition": f"attachment; filename=droneseg_{detection_id}.geojson"}
    return JSONResponse(content=geojson, media_type="application/geo+json", headers=headers)
