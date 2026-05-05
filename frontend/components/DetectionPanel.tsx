"use client";

import { Download, Eye, EyeOff, Loader2, Trash2 } from "lucide-react";
import type { DetectionResponse } from "@/types/detection";
import { geojsonUrl } from "@/lib/api";

interface DetectionPanelProps {
  result: DetectionResponse | null;
  isDetecting: boolean;
  threshold: number;
  onThresholdChange: (value: number) => void;
  visibleClasses: Set<string>;
  onToggleClass: (label: string) => void;
  selectedLabel: string | null;
  onSelectLabel: (label: string | null) => void;
  onClear: () => void;
}

export function DetectionPanel({
  result,
  isDetecting,
  threshold,
  onThresholdChange,
  visibleClasses,
  onToggleClass,
  selectedLabel,
  onSelectLabel,
  onClear
}: DetectionPanelProps) {
  const filtered = result?.detections.filter((item) => item.confidence >= threshold) ?? [];
  const isLlmResult = Boolean(result?.model_used?.startsWith("gpt-"));
  const uniqueClassCount = result ? new Set(result.detections.map((item) => item.label)).size : 0;

  return (
    <section className="rounded-3xl bg-white/90 p-5 shadow-soft ring-1 ring-slate-200 backdrop-blur">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-950">Detection results</h2>
          <p className="text-xs text-slate-500">Segmentation mask or optional LLM regions, class confidence and export.</p>
        </div>
        {result && (
          <button onClick={onClear} className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:bg-slate-50" title="Clear results">
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>

      {isDetecting && (
        <div className="mb-4 flex items-center gap-3 rounded-2xl bg-sky-50 p-4 text-sm text-sky-800">
          <Loader2 className="h-5 w-5 animate-spin" />
          {isLlmResult ? "Running optional LLM vision analysis. Results are approximate." : "Running SegFormer inference. Large drone images may take longer on free CPU hardware."}
        </div>
      )}

      {!result && !isDetecting && (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
          Upload or choose a sample image, then run detection to view classes, bounding boxes and the mask overlay.
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-3 gap-2 rounded-2xl bg-slate-50 p-3 text-center text-xs">
            <div>
              <p className="font-bold text-slate-900">{result.detections.length}</p>
              <p className="text-slate-500">Regions</p>
            </div>
            <div>
              <p className="font-bold text-slate-900">{result.inference_time_ms} ms</p>
              <p className="text-slate-500">Inference</p>
            </div>
            <div>
              <p className="font-bold text-slate-900">{Math.round(threshold * 100)}%</p>
              <p className="text-slate-500">Threshold</p>
            </div>
          </div>

          <div className="mt-3 rounded-2xl bg-white p-3 text-xs text-slate-600 ring-1 ring-slate-200">
            <p><span className="font-semibold text-slate-900">Model:</span> {result.model_used}</p>
            <p><span className="font-semibold text-slate-900">Unique classes:</span> {uniqueClassCount}</p>
            <p className="mt-2 rounded-xl bg-sky-50 p-2 text-sky-800">The coloured raster mask is the actual semantic segmentation. The rectangles are only approximate region boxes for export and navigation.</p>
            {isLlmResult && <p className="mt-2 rounded-xl bg-amber-50 p-2 text-amber-800">LLM Vision Mode uses approximate visual reasoning, not pixel-accurate semantic segmentation.</p>}
          </div>

          <div className="mt-4">
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">Confidence threshold</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={threshold}
              onChange={(event) => onThresholdChange(Number(event.target.value))}
              className="w-full accent-sky-600"
            />
          </div>

          <div className="mt-4 max-h-[330px] space-y-2 overflow-auto pr-1">
            {filtered.map((item) => {
              const visible = visibleClasses.has(item.label);
              const selected = selectedLabel === item.label;
              return (
                <button
                  key={item.id ?? item.label}
                  onClick={() => onSelectLabel(selected ? null : item.label)}
                  className={`w-full rounded-2xl border p-3 text-left transition ${
                    selected ? "border-sky-500 bg-sky-50" : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-sm font-semibold capitalize text-slate-900">{item.label}</span>
                    </div>
                    <span className="text-xs font-semibold text-slate-600">{Math.round(item.confidence * 100)}%</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full" style={{ width: `${Math.round(item.confidence * 100)}%`, backgroundColor: item.color }} />
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                    <span>{item.pixel_area.toLocaleString()} pixels</span>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(event) => {
                        event.stopPropagation();
                        onToggleClass(item.label);
                      }}
                      className="inline-flex items-center gap-1 rounded-full border border-slate-200 px-2 py-1 hover:bg-slate-50"
                    >
                      {visible ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
                      {visible ? "Visible" : "Hidden"}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          <a
            href={geojsonUrl(result.detection_id)}
            target="_blank"
            rel="noreferrer"
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            <Download className="h-4 w-4" />
            Export GeoJSON
          </a>
        </>
      )}
    </section>
  );
}
