from fastapi import APIRouter, File, Form, UploadFile

from backend.services.upload_service import normalise_bounds, save_upload

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    sw_lng: float | None = Form(default=None),
    sw_lat: float | None = Form(default=None),
    ne_lng: float | None = Form(default=None),
    ne_lat: float | None = Form(default=None),
):
    bounds = None
    if None not in (sw_lng, sw_lat, ne_lng, ne_lat):
        bounds = [sw_lng, sw_lat, ne_lng, ne_lat]
    record = await save_upload(file, normalise_bounds(bounds))
    return {
        "image_id": record["image_id"],
        "filename": record["filename"],
        "width": record["width"],
        "height": record["height"],
        "size_bytes": record["size_bytes"],
        "url": f"/api/images/{record['image_id']}",
        "bounds": record["bounds"],
    }
