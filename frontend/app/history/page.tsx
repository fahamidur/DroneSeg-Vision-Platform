"use client";

import { useEffect, useState } from "react";
import { getHistory } from "@/lib/api";
import type { HistoryItem } from "@/types/detection";

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);

  useEffect(() => {
    getHistory().then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="mx-auto max-w-4xl rounded-3xl bg-white p-6 shadow-soft ring-1 ring-slate-200">
        <h1 className="text-2xl font-black text-slate-950">Detection history</h1>
        <p className="mt-1 text-sm text-slate-500">Recent DroneSeg inference records.</p>
        <div className="mt-6 space-y-3">
          {items.map((item) => (
            <div key={item.detection_id} className="rounded-2xl border border-slate-200 p-4">
              <div className="flex items-center justify-between">
                <p className="font-bold text-slate-900">{item.class_count} detected classes</p>
                <p className="text-xs text-slate-500">{new Date(item.timestamp).toLocaleString()}</p>
              </div>
              <p className="mt-2 text-sm capitalize text-slate-600">{item.detected_classes.join(", ")}</p>
            </div>
          ))}
          {items.length === 0 && <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">No history records yet.</p>}
        </div>
      </div>
    </main>
  );
}
