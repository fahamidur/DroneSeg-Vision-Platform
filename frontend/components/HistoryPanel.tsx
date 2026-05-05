"use client";

import { Clock3 } from "lucide-react";
import type { HistoryItem } from "@/types/detection";

interface HistoryPanelProps {
  items: HistoryItem[];
  onReload: (detectionId: string) => void;
}

export function HistoryPanel({ items, onReload }: HistoryPanelProps) {
  return (
    <section className="rounded-3xl bg-white/90 p-5 shadow-soft ring-1 ring-slate-200 backdrop-blur">
      <div className="mb-4 flex items-center gap-2">
        <Clock3 className="h-5 w-5 text-sky-700" />
        <div>
          <h2 className="text-lg font-bold text-slate-950">History</h2>
          <p className="text-xs text-slate-500">Reload recent segmentation runs.</p>
        </div>
      </div>
      {items.length === 0 ? (
        <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">No detection history yet.</p>
      ) : (
        <div className="max-h-[260px] space-y-2 overflow-auto pr-1">
          {items.map((item) => (
            <button
              key={item.detection_id}
              onClick={() => onReload(item.detection_id)}
              className="w-full rounded-2xl border border-slate-200 bg-white p-3 text-left transition hover:border-sky-300 hover:bg-sky-50"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-semibold text-slate-900">{item.class_count} classes</span>
                <span className="text-[11px] text-slate-500">{new Date(item.timestamp).toLocaleString()}</span>
              </div>
              <p className="mt-1 line-clamp-2 text-xs capitalize text-slate-500">{item.detected_classes.join(", ") || "No classes"}</p>
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
