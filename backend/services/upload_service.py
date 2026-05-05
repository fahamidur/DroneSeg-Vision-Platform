import mimetypes
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from backend.config import DEFAULT_BOUNDS, MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR
from backend.db.history_repo import insert_image, now_iso

# The SRS requires JPEG and PNG. The backend also accepts common browser image
# formats and converts them safely into JPEG or PNG for internal storage.
ALLOWED_SUFFIXES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/x-ms-bmp",
}


def normalise_bounds(bounds: Optional[list[float]]) -> list[float]:
    if not bounds or len(bounds) != 4:
        return DEFAULT_BOUNDS

    try:
        sw_lng, sw_lat, ne_lng, ne_lat = [float(v) for v in bounds]
    except (TypeError, ValueError):
        return DEFAULT_BOUNDS

    if sw_lng >= ne_lng or sw_lat >= ne_lat:
        return DEFAULT_BOUNDS

    if not (
        -180 <= sw_lng <= 180
        and -180 <= ne_lng <= 180
        and -90 <= sw_lat <= 90
        and -90 <= ne_lat <= 90
    ):
        return DEFAULT_BOUNDS

    return [sw_lng, sw_lat, ne_lng, ne_lat]


def _is_git_lfs_pointer(content: bytes) -> bool:
    head = content[:150].decode("utf-8", errors="ignore")
    return "version https://git-lfs.github.com/spec/v1" in head


def _validate_extension_and_mime(original_name: str, content_type: Optional[str]) -> None:
    suffix = Path(original_name).suffix.lower()
    guessed_mime = mimetypes.guess_type(original_name)[0] or ""
    received_mime = content_type or ""

    # Some browsers send empty or generic MIME types, so suffix is also checked.
    if (
        suffix not in ALLOWED_SUFFIXES
        and received_mime not in ALLOWED_MIME_TYPES
        and guessed_mime not in ALLOWED_MIME_TYPES
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Unsupported image type. Upload JPEG or PNG. WebP, BMP and TIFF "
                "can also be accepted and converted automatically. HEIC and AVIF "
                "must be converted to JPG first."
            ),
        )


def _open_and_normalise_image(content: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(content))
        image.load()
    except UnidentifiedImageError as exc:
        if _is_git_lfs_pointer(content):
            raise HTTPException(
                status_code=422,
                detail=(
                    "This file is a Git LFS pointer, not the real image. "
                    "Run 'git lfs pull' and try again."
                ),
            ) from exc

        raise HTTPException(
            status_code=422,
            detail=(
                "The uploaded file is not a valid image. Use a real JPG or PNG file. "
                "If the image is HEIC or AVIF, convert it to JPG first."
            ),
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                "The image could not be opened. It may be corrupted, incomplete, "
                "or saved in a format that is not supported by this server."
            ),
        ) from exc

    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    return image


def _encode_for_storage(image: Image.Image, original_suffix: str) -> tuple[bytes, str, str]:
    buffer = BytesIO()

    # Keep transparent PNGs as PNG. Everything else is normalised to JPEG.
    if original_suffix == ".png" or image.mode == "RGBA":
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), ".png", "image/png"

    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(buffer, format="JPEG", quality=92, optimize=True, progressive=True)
    return buffer.getvalue(), ".jpg", "image/jpeg"


async def save_upload(file: UploadFile, bounds: Optional[list[float]] = None) -> Dict[str, Any]:
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=422, detail="Uploaded image is empty.")

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail="Uploaded image exceeds the configured size limit of 50 MB.",
        )

    original_name = Path(file.filename or "uploaded_image").name
    original_suffix = Path(original_name).suffix.lower()

    _validate_extension_and_mime(original_name, file.content_type)

    image = _open_and_normalise_image(content)
    width, height = image.size

    stored_bytes, ext, mime_type = _encode_for_storage(image, original_suffix)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_id = str(uuid.uuid4())
    stored_filename = f"{stored_id}{ext}"
    stored_path = UPLOAD_DIR / stored_filename
    stored_path.write_bytes(stored_bytes)

    record = {
        "image_id": stored_id,
        "filename": original_name,
        "stored_filename": stored_filename,
        "filepath": str(stored_path),
        "mime_type": mime_type,
        "width": width,
        "height": height,
        "size_bytes": len(stored_bytes),
        "bounds": normalise_bounds(bounds),
        "is_sample": False,
        "created_at": now_iso(),
    }

    await insert_image(record)
    return record
