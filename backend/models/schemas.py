from typing import List, Optional

from pydantic import BaseModel, Field


Bounds = List[float]


class ImageRecord(BaseModel):
    image_id: str
    filename: str
    width: int
    height: int
    size_bytes: int
    url: str
    bounds: Bounds
    created_at: str


class DetectionRequest(BaseModel):
    image_id: str
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    bounds: Optional[Bounds] = None


class DetectionItem(BaseModel):
    id: Optional[str] = None
    label: str
    confidence: float
    bbox: List[int]
    pixel_area: int
    color: str


class DetectionResponse(BaseModel):
    detection_id: str
    image_id: str
    model_used: str
    inference_time_ms: int
    image_width: int
    image_height: int
    bounds: Bounds
    detections: List[DetectionItem]
    mask_url: str
    mask_base64: Optional[str] = None


class HistoryItem(BaseModel):
    detection_id: str
    image_id: str
    timestamp: str
    model_used: str
    class_count: int
    image_thumbnail_url: str
    detected_classes: List[str]


class HistoryResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: List[HistoryItem]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_id: str
    llm_enabled: bool
    message: str
