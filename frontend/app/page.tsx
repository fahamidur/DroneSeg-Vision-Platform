"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Map, Play, Radar, RefreshCw } from "lucide-react";
import { DetectionPanel } from "@/components/DetectionPanel";
import { HistoryPanel } from "@/components/HistoryPanel";
import { MapViewer } from "@/components/MapViewer";
import { ModelSelector } from "@/components/ModelSelector";
import { UploadDropzone } from "@/components/UploadDropzone";
import {
  assetUrl,
  getHealth,
  getHistory,
  getHistoryItem,
  getSamples,
  runDetection,
  runLLMDetection,
  uploadImage,
} from "@/lib/api";
import type { Bounds, DetectionResponse, HistoryItem, ImageRecord } from "@/types/detection";

const defaultBounds: Bounds = [90.354, 23.778, 90.358, 23.782];

function isValidBounds(bounds: Bounds): boolean {
  const [swLng, swLat, neLng, neLat] = bounds;

  return (
    Number.isFinite(swLng) &&
    Number.isFinite(swLat) &&
    Number.isFinite(neLng) &&
    Number.isFinite(neLat) &&
    swLng < neLng &&
    swLat < neLat &&
    swLng >= -180 &&
    neLng <= 180 &&
    swLat >= -90 &&
    neLat <= 90
  );
}

export default function HomePage() {
  const [samples, setSamples] = useState<ImageRecord[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [currentImage, setCurrentImage] = useState<ImageRecord | null>(null);
  const [result, setResult] = useState<DetectionResponse | null>(null);
  const [threshold, setThreshold] = useState(0.5);
  const [visibleClasses, setVisibleClasses] = useState<Set<string>>(new Set());
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState("segformer");
  const [imageOpacity, setImageOpacity] = useState(0.78);
  const [maskOpacity, setMaskOpacity] = useState(0.72);
  const [showMask, setShowMask] = useState(true);
  const [showBoxes, setShowBoxes] = useState(false);
  const [manualBounds, setManualBounds] = useState<Bounds>(defaultBounds);
  const [isUploading, setIsUploading] = useState(false);
  const [isDetecting, setIsDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<string>("Checking backend...");

  const loadBaseData = async () => {
    try {
      const [sampleItems, historyItems, healthPayload] = await Promise.all([
        getSamples(),
        getHistory(),
        getHealth(),
      ]);

      setSamples(sampleItems);
      setHistory(historyItems);
      setHealth(healthPayload.message);

      if (!currentImage && sampleItems.length > 0) {
        setCurrentImage(sampleItems[0]);
        setManualBounds(sampleItems[0].bounds ?? defaultBounds);
      }
    } catch {
      setHealth("Backend is not reachable yet.");
    }
  };

  useEffect(() => {
    loadBaseData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const visibleDetections = useMemo(() => result?.detections ?? [], [result]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    if (!isValidBounds(manualBounds)) {
      setIsUploading(false);
      setError("Map bounds are not valid. SW longitude and latitude must be lower than NE longitude and latitude.");
      return;
    }

    try {
      const uploaded = await uploadImage(file, manualBounds);

      setCurrentImage(uploaded);
      setManualBounds(uploaded.bounds ?? manualBounds);
      setResult(null);
      setVisibleClasses(new Set());
      setSelectedLabel(null);
      setHistory(await getHistory());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSampleChange = (imageId: string) => {
    const sample = samples.find((item) => item.image_id === imageId);

    if (sample) {
      setCurrentImage(sample);
      setManualBounds(sample.bounds ?? defaultBounds);
      setResult(null);
      setVisibleClasses(new Set());
      setSelectedLabel(null);
    }
  };

  const handleDetect = async () => {
    if (!currentImage) {
      setError("Select or upload an image first.");
      return;
    }

    const boundsForRun = (currentImage.bounds ?? manualBounds ?? defaultBounds) as Bounds;

    if (!isValidBounds(boundsForRun)) {
      setError("Map bounds are not valid. Fix the placement coordinates before running detection.");
      return;
    }

    setIsDetecting(true);
    setError(null);

    try {
      const detection =
        selectedModel === "segformer"
          ? await runDetection(currentImage.image_id, threshold, boundsForRun)
          : await runLLMDetection(currentImage.image_id, selectedModel, threshold, boundsForRun);

      setResult(detection);
      setVisibleClasses(new Set(detection.detections.map((item) => item.label)));
      setSelectedLabel(null);
      setShowMask(true);
      setShowBoxes(false);
      setHistory(await getHistory());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Detection failed.");
    } finally {
      setIsDetecting(false);
    }
  };

  const handleToggleClass = (label: string) => {
    setVisibleClasses((previous) => {
      const next = new Set(previous);

      if (next.has(label)) {
        next.delete(label);
      } else {
        next.add(label);
      }

      return next;
    });
  };

  const handleBoundChange = (index: number, value: number) => {
    const next = [...manualBounds] as Bounds;
    next[index] = value;

    setManualBounds(next);

    if (currentImage) {
      setCurrentImage({ ...currentImage, bounds: next });
      setResult(null);
      setVisibleClasses(new Set());
      setSelectedLabel(null);
    }
  };

  const handleReloadHistory = async (detectionId: string) => {
    setError(null);

    try {
      const item = await getHistoryItem(detectionId);
      const image = samples.find((sample) => sample.image_id === item.image_id);

      setResult(item);
      setCurrentImage(
        image ?? {
          image_id: item.image_id,
          filename: "History image",
          width: item.image_width,
          height: item.image_height,
          size_bytes: 0,
          url: `/api/images/${item.image_id}`,
          bounds: item.bounds,
        },
      );
      setManualBounds(item.bounds);
      setVisibleClasses(new Set(item.detections.map((detection) => detection.label)));
      setSelectedLabel(null);
      setShowMask(true);
      setShowBoxes(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reload history record.");
    }
  };

  const imageUrl = currentImage?.url ?? null;
  const maskUrl = result?.mask_url ?? null;
  const imageWidth = result?.image_width ?? currentImage?.width ?? 1;
  const imageHeight = result?.image_height ?? currentImage?.height ?? 1;
  const bounds = (result?.bounds ?? currentImage?.bounds ?? defaultBounds) as Bounds;

  return (
    <main className="min-h-screen p-4 md:p-6">
      <div className="mx-auto max-w-[1500px]">
        <header className="mb-5 flex flex-col justify-between gap-4 rounded-3xl bg-white/85 p-5 shadow-soft ring-1 ring-slate-200 backdrop-blur lg:flex-row lg:items-center">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-sky-50 px-3 py-1 text-xs font-bold uppercase tracking-wide text-sky-700">
              <Radar className="h-4 w-4" />
              DroneSeg Vision Platform
            </div>
            <h1 className="text-2xl font-black tracking-tight text-slate-950 md:text-4xl">
              Drone imagery semantic segmentation
            </h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-600">
              Upload a drone image, view it on an OpenStreetMap basemap, run SegFormer-B2 detection,
              inspect class overlays and export GeoJSON.
            </p>
          </div>
          <div className="rounded-2xl bg-slate-950 px-4 py-3 text-sm text-white">
            <p className="font-semibold">Backend status</p>
            <p className="text-xs text-slate-300">{health}</p>
          </div>
        </header>

        {error && (
          <div className="mb-4 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 h-5 w-5" />
            <p>{error}</p>
          </div>
        )}

        <div className="grid gap-5 lg:grid-cols-[360px_minmax(0,1fr)_390px]">
          <aside className="space-y-5">
            <section className="rounded-3xl bg-white/90 p-5 shadow-soft ring-1 ring-slate-200 backdrop-blur">
              <h2 className="mb-1 text-lg font-bold text-slate-950">Image input</h2>
              <p className="mb-4 text-xs text-slate-500">
                Use a bundled sample or upload a drone image.
              </p>

              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Sample image
              </label>
              <select
                value={currentImage?.image_id ?? ""}
                onChange={(event) => handleSampleChange(event.target.value)}
                className="mb-4 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm"
              >
                <option value="">Choose a sample</option>
                {samples.map((sample) => (
                  <option key={sample.image_id} value={sample.image_id}>
                    {sample.filename}
                  </option>
                ))}
              </select>

              <UploadDropzone
                onFile={handleUpload}
                onError={setError}
                disabled={isUploading || isDetecting}
              />

              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-600">
                  Map placement bounds
                </p>
                <p className="mb-3 text-[11px] leading-4 text-slate-500">
                  These coordinates control where the image appears on the map and where GeoJSON polygons are exported.
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    ["SW lng", 0],
                    ["SW lat", 1],
                    ["NE lng", 2],
                    ["NE lat", 3],
                  ].map(([label, index]) => (
                    <label key={label as string} className="text-[11px] font-semibold text-slate-600">
                      {label}
                      <input
                        type="number"
                        step="0.000001"
                        value={manualBounds[index as number]}
                        onChange={(event) => handleBoundChange(index as number, Number(event.target.value))}
                        className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-800"
                      />
                    </label>
                  ))}
                </div>
              </div>

              {currentImage && (
                <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
                  <img
                    src={assetUrl(currentImage.url)}
                    alt={currentImage.filename}
                    className="h-36 w-full object-cover"
                  />
                  <div className="p-3 text-xs text-slate-600">
                    <p className="font-semibold text-slate-900">{currentImage.filename}</p>
                    <p>
                      {currentImage.width} × {currentImage.height}px
                    </p>
                    <p>
                      {currentImage.size_bytes
                        ? `${(currentImage.size_bytes / 1024 / 1024).toFixed(2)} MB`
                        : "Stored image"}
                    </p>
                  </div>
                </div>
              )}
            </section>

            <section className="rounded-3xl bg-white/90 p-5 shadow-soft ring-1 ring-slate-200 backdrop-blur">
              <div className="mb-4 flex items-center gap-2">
                <Map className="h-5 w-5 text-sky-700" />
                <h2 className="text-lg font-bold text-slate-950">Controls</h2>
              </div>
              <div className="space-y-4">
                <ModelSelector value={selectedModel} onChange={setSelectedModel} />

                <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Image opacity {Math.round(imageOpacity * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={imageOpacity}
                    onChange={(event) => setImageOpacity(Number(event.target.value))}
                    className="w-full accent-sky-600"
                  />
                </div>

                {result && (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                    <p className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-600">
                      Segmentation display
                    </p>

                    <label className="mb-2 flex items-center justify-between gap-3 text-sm font-semibold text-slate-700">
                      <span>Show coloured mask</span>
                      <input
                        type="checkbox"
                        checked={showMask}
                        onChange={(event) => setShowMask(event.target.checked)}
                        className="h-4 w-4 accent-sky-600"
                      />
                    </label>

                    <label className="mb-3 flex items-center justify-between gap-3 text-sm font-semibold text-slate-700">
                      <span>Show bounding boxes</span>
                      <input
                        type="checkbox"
                        checked={showBoxes}
                        onChange={(event) => setShowBoxes(event.target.checked)}
                        className="h-4 w-4 accent-sky-600"
                      />
                    </label>

                    <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Mask opacity {Math.round(maskOpacity * 100)}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={maskOpacity}
                      onChange={(event) => setMaskOpacity(Number(event.target.value))}
                      className="w-full accent-sky-600"
                    />

                    <p className="mt-2 text-[11px] leading-4 text-slate-500">
                      The mask is the actual segmentation output. Bounding boxes are approximate rectangles derived from connected mask regions.
                    </p>
                  </div>
                )}

                <button
                  onClick={handleDetect}
                  disabled={!currentImage || isDetecting || isUploading}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-sky-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-sky-200 transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:shadow-none"
                >
                  {isDetecting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  Run Detection
                </button>
              </div>
            </section>

            <HistoryPanel items={history} onReload={handleReloadHistory} />
          </aside>

          <section>
            <MapViewer
              imageUrl={imageUrl}
              maskUrl={maskUrl}
              bounds={bounds}
              imageWidth={imageWidth}
              imageHeight={imageHeight}
              detections={visibleDetections}
              threshold={threshold}
              visibleClasses={visibleClasses}
              selectedLabel={selectedLabel}
              onSelectLabel={setSelectedLabel}
              imageOpacity={imageOpacity}
              showMask={showMask}
              showBoxes={showBoxes}
              maskOpacity={maskOpacity}
            />
          </section>

          <aside>
            <DetectionPanel
              result={result}
              isDetecting={isDetecting}
              threshold={threshold}
              onThresholdChange={setThreshold}
              visibleClasses={visibleClasses}
              onToggleClass={handleToggleClass}
              selectedLabel={selectedLabel}
              onSelectLabel={setSelectedLabel}
              onClear={() => {
                setResult(null);
                setVisibleClasses(new Set());
                setSelectedLabel(null);
              }}
            />
          </aside>
        </div>
      </div>
    </main>
  );
}
