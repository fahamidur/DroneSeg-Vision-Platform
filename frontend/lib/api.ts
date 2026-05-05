import type { DetectionResponse, HistoryItem, ImageRecord } from "@/types/detection";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function absoluteApiUrl(path: string): string {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

export function assetUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("data:")) return path;
  if (path.startsWith("http")) return path;
  return absoluteApiUrl(path);
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // keep default message
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function getHealth() {
  const response = await fetch(absoluteApiUrl("/api/health"));
  return parseResponse<{ status: string; model_loaded: boolean; model_id: string; llm_enabled: boolean; message: string }>(response);
}

export async function getSamples(): Promise<ImageRecord[]> {
  const response = await fetch(absoluteApiUrl("/api/samples"), { cache: "no-store" });
  const payload = await parseResponse<{ items: ImageRecord[] }>(response);
  return payload.items;
}

export async function uploadImage(file: File, bounds?: number[]): Promise<ImageRecord> {
  const form = new FormData();
  form.append("file", file);
  if (bounds && bounds.length === 4) {
    form.append("sw_lng", String(bounds[0]));
    form.append("sw_lat", String(bounds[1]));
    form.append("ne_lng", String(bounds[2]));
    form.append("ne_lat", String(bounds[3]));
  }
  const response = await fetch(absoluteApiUrl("/api/upload"), {
    method: "POST",
    body: form
  });
  return parseResponse<ImageRecord>(response);
}

export async function runDetection(imageId: string, confidenceThreshold: number, bounds: number[]): Promise<DetectionResponse> {
  const response = await fetch(absoluteApiUrl("/api/detect"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id: imageId, confidence_threshold: confidenceThreshold, bounds })
  });
  return parseResponse<DetectionResponse>(response);
}

export async function runLLMDetection(imageId: string, model: string, confidenceThreshold: number, bounds: number[]): Promise<DetectionResponse> {
  const response = await fetch(absoluteApiUrl("/api/llm/analyze"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id: imageId, model, confidence_threshold: confidenceThreshold, bounds })
  });
  return parseResponse<DetectionResponse>(response);
}

export async function getHistory(): Promise<HistoryItem[]> {
  const response = await fetch(absoluteApiUrl("/api/history?page=1&per_page=20"), { cache: "no-store" });
  const payload = await parseResponse<{ items: HistoryItem[] }>(response);
  return payload.items;
}

export async function getHistoryItem(detectionId: string): Promise<DetectionResponse> {
  const response = await fetch(absoluteApiUrl(`/api/history/${detectionId}`), { cache: "no-store" });
  return parseResponse<DetectionResponse>(response);
}

export function geojsonUrl(detectionId: string): string {
  return absoluteApiUrl(`/api/export/geojson/${detectionId}`);
}
