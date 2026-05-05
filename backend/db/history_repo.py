import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.db.database import get_db


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def insert_image(record: Dict[str, Any]) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO images
            (image_id, filename, stored_filename, filepath, mime_type, width, height, size_bytes, bounds_json, is_sample, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["image_id"],
                record["filename"],
                record["stored_filename"],
                record["filepath"],
                record["mime_type"],
                record["width"],
                record["height"],
                record["size_bytes"],
                json.dumps(record["bounds"]),
                1 if record.get("is_sample") else 0,
                record.get("created_at", now_iso()),
            ),
        )
        await db.commit()


async def get_image(image_id: str) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM images WHERE image_id = ?", (image_id,))
        row = await cur.fetchone()

    if not row:
        return None

    item = dict(row)
    item["bounds"] = json.loads(item["bounds_json"])
    return item


async def list_sample_images() -> List[Dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute("SELECT * FROM images WHERE is_sample = 1 ORDER BY filename")
        rows = await cur.fetchall()

    items: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["bounds"] = json.loads(item["bounds_json"])
        item["url"] = f"/api/images/{item['image_id']}"
        items.append(item)

    return items


async def insert_detection(record: Dict[str, Any]) -> None:
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO detections
            (detection_id, image_id, model_used, detections_json, mask_path, inference_time_ms,
             confidence_threshold, image_width, image_height, bounds_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["detection_id"],
                record["image_id"],
                record["model_used"],
                json.dumps(record["detections"]),
                record["mask_path"],
                record["inference_time_ms"],
                record["confidence_threshold"],
                record["image_width"],
                record["image_height"],
                json.dumps(record["bounds"]),
                record.get("created_at", now_iso()),
            ),
        )
        await db.commit()


async def list_history(page: int = 1, per_page: int = 20) -> Tuple[int, List[Dict[str, Any]]]:
    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)
    offset = (page - 1) * per_page

    async with get_db() as db:
        count_cur = await db.execute("SELECT COUNT(*) AS total FROM detections")
        total_row = await count_cur.fetchone()

        cur = await db.execute(
            """
            SELECT d.*, i.filename
            FROM detections d
            LEFT JOIN images i ON i.image_id = d.image_id
            ORDER BY d.created_at DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        )
        rows = await cur.fetchall()

    total = int(total_row["total"] if total_row else 0)

    items: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        detections = json.loads(item["detections_json"])
        item["detections"] = detections
        item["detected_classes"] = sorted({d["label"] for d in detections})
        items.append(item)

    return total, items


async def get_detection(detection_id: str) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        cur = await db.execute(
            """
            SELECT d.*, i.filepath, i.mime_type, i.filename
            FROM detections d
            LEFT JOIN images i ON i.image_id = d.image_id
            WHERE d.detection_id = ?
            """,
            (detection_id,),
        )
        row = await cur.fetchone()

    if not row:
        return None

    item = dict(row)
    item["detections"] = json.loads(item["detections_json"])
    item["bounds"] = json.loads(item["bounds_json"])
    return item


async def delete_detection(detection_id: str) -> bool:
    record = await get_detection(detection_id)

    async with get_db() as db:
        cur = await db.execute("DELETE FROM detections WHERE detection_id = ?", (detection_id,))
        await db.commit()
        deleted = cur.rowcount > 0

    if record and record.get("mask_path"):
        try:
            Path(record["mask_path"]).unlink(missing_ok=True)
        except OSError:
            pass

    return deleted
