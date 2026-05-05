from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config import OUTPUT_DIR
from backend.db.history_repo import get_image, list_sample_images

router = APIRouter(tags=["assets"])


@router.get("/images/{image_id}")
async def serve_image(image_id: str):
    image = await get_image(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image ID was not found.")
    path = Path(image["filepath"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file was not found on disk.")
    return FileResponse(path, media_type=image["mime_type"], filename=image["filename"])


@router.get("/masks/{mask_filename}")
async def serve_mask(mask_filename: str):
    safe_name = Path(mask_filename).name
    path = OUTPUT_DIR / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Mask file was not found.")
    return FileResponse(path, media_type="image/png", filename=safe_name)


@router.get("/samples")
async def samples():
    items = await list_sample_images()
    return {
        "items": [
            {
                "image_id": item["image_id"],
                "filename": item["filename"],
                "width": item["width"],
                "height": item["height"],
                "size_bytes": item["size_bytes"],
                "url": item["url"],
                "bounds": item["bounds"],
                "created_at": item["created_at"],
            }
            for item in items
        ]
    }
