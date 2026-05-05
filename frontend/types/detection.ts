export type Bounds = [number, number, number, number];

export interface ImageRecord {
  image_id: string;
  filename: string;
  width: number;
  height: number;
  size_bytes: number;
  url: string;
  bounds: Bounds;
  created_at?: string;
}

export interface DetectionItem {
  id?: string;
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
  pixel_area: number;
  color: string;
}

export interface DetectionResponse {
  detection_id: string;
  image_id: string;
  model_used: string;
  inference_time_ms: number;
  image_width: number;
  image_height: number;
  bounds: Bounds;
  detections: DetectionItem[];
  mask_url: string;
  mask_base64?: string | null;
}

export interface HistoryItem {
  detection_id: string;
  image_id: string;
  timestamp: string;
  model_used: string;
  class_count: number;
  image_thumbnail_url: string;
  detected_classes: string[];
}
