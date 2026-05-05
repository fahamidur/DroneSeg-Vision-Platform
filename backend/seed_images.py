import json
import shutil
import uuid
from pathlib import Path
from typing import Dict, List

from PIL import Image

from backend.config import DEFAULT_BOUNDS, SAMPLE_IMAGE_DIR, UPLOAD_DIR
from backend.db.history_repo import get_image, insert_image, now_iso
from backend.services.upload_service import normalise_bounds

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
BOUNDS_FILE = SAMPLE_IMAGE_DIR / "sample_bounds.json"


def _load_sample_bounds() -> Dict[str, List[float]]:
    """Load optional per-image georeferencing from backend/sample_images/sample_bounds.json.

    Expected format:
    {
      "DJI_20260308132419_0061_V.JPG": [sw_lng, sw_lat, ne_lng, ne_lat]
    }
    """
    if not BOUNDS_FILE.exists():
        return {}
    try:
        raw = json.loads(BOUNDS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    cleaned: Dict[str, List[float]] = {}
    for filename, bounds in raw.items():
        try:
            cleaned[filename] = normalise_bounds(bounds)
        except Exception:
            continue
    return cleaned


async def seed_sample_images() -> None:
    """Register every JPEG/PNG placed in backend/sample_images as a selectable sample.

    Users only need to add images to backend/sample_images and restart the backend.
    If sample_bounds.json contains a matching filename, that image uses the configured
    coordinates. Otherwise it falls back to DEFAULT_BOUNDS, which can still be adjusted
    from the frontend before detection/export.
    """
    sample_files = sorted(
        source for source in SAMPLE_IMAGE_DIR.iterdir()
        if source.is_file() and source.suffix.lower() in {suffix.lower() for suffix in SUPPORTED_SUFFIXES}
    )
    bounds_by_filename = _load_sample_bounds()

    for source in sample_files:
        image_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"droneseg-sample:{source.name}"))
        existing = await get_image(image_id)

        with Image.open(source) as image:
            width, height = image.size

        stored_ext = ".png" if source.suffix.lower() == ".png" else ".jpg"
        stored_filename = f"{image_id}{stored_ext}"
        destination = UPLOAD_DIR / stored_filename

        if not destination.exists() or destination.stat().st_size != source.stat().st_size:
            shutil.copyfile(source, destination)

        # Re-register samples on every startup so edited bounds take effect without deleting the DB.
        await insert_image(
            {
                "image_id": image_id,
                "filename": source.name,
                "stored_filename": stored_filename,
                "filepath": str(destination),
                "mime_type": "image/png" if stored_ext == ".png" else "image/jpeg",
                "width": width,
                "height": height,
                "size_bytes": destination.stat().st_size,
                "bounds": bounds_by_filename.get(source.name, DEFAULT_BOUNDS),
                "is_sample": True,
                "created_at": existing.get("created_at") if existing else now_iso(),
            }
        )
