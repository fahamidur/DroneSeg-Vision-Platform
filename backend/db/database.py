from contextlib import asynccontextmanager
from typing import AsyncIterator

import aiosqlite

from backend.config import DB_PATH


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    async with get_db() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                image_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                size_bytes INTEGER NOT NULL,
                bounds_json TEXT NOT NULL,
                is_sample INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                detection_id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL REFERENCES images(image_id),
                model_used TEXT NOT NULL,
                detections_json TEXT NOT NULL,
                mask_path TEXT NOT NULL,
                inference_time_ms INTEGER NOT NULL,
                confidence_threshold REAL NOT NULL,
                image_width INTEGER NOT NULL,
                image_height INTEGER NOT NULL,
                bounds_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.commit()
