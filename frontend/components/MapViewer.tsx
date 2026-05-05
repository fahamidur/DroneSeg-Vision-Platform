"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import maplibregl, { Map, type StyleSpecification } from "maplibre-gl";
import type { Bounds, DetectionItem } from "@/types/detection";
import { assetUrl } from "@/lib/api";

interface MapViewerProps {
  imageUrl: string | null;
  maskUrl: string | null;
  bounds: Bounds;
  imageWidth: number;
  imageHeight: number;
  detections: DetectionItem[];
  threshold: number;
  visibleClasses: Set<string>;
  selectedLabel: string | null;
  onSelectLabel: (label: string | null) => void;
  imageOpacity: number;
  showMask: boolean;
  showBoxes: boolean;
  maskOpacity: number;
}

interface ScreenBox {
  key: string;
  label: string;
  confidence: number;
  color: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

const emptyStyle: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors"
    }
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }]
};

function imageCoordinates(bounds: Bounds): [[number, number], [number, number], [number, number], [number, number]] {
  const [swLng, swLat, neLng, neLat] = bounds;
  return [
    [swLng, neLat],
    [neLng, neLat],
    [neLng, swLat],
    [swLng, swLat]
  ];
}

function pixelToLngLat(x: number, y: number, width: number, height: number, bounds: Bounds): [number, number] {
  const [swLng, swLat, neLng, neLat] = bounds;
  const lng = swLng + (x / Math.max(width, 1)) * (neLng - swLng);
  const lat = neLat - (y / Math.max(height, 1)) * (neLat - swLat);
  return [lng, lat];
}

export function MapViewer({
  imageUrl,
  maskUrl,
  bounds,
  imageWidth,
  imageHeight,
  detections,
  threshold,
  visibleClasses,
  selectedLabel,
  onSelectLabel,
  imageOpacity,
  showMask,
  showBoxes,
  maskOpacity
}: MapViewerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);
  const [screenBoxes, setScreenBoxes] = useState<ScreenBox[]>([]);
  const resolvedImageUrl = imageUrl ? assetUrl(imageUrl) : null;
  const resolvedMaskUrl = maskUrl ? assetUrl(maskUrl) : null;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: emptyStyle,
      center: [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
      zoom: 16,
      attributionControl: { compact: true }
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !resolvedImageUrl) return;

    const updateImage = () => {
      const coords = imageCoordinates(bounds);
      if (map.getLayer("drone-image-layer")) map.removeLayer("drone-image-layer");
      if (map.getSource("drone-image")) map.removeSource("drone-image");
      map.addSource("drone-image", { type: "image", url: resolvedImageUrl, coordinates: coords });
      map.addLayer({ id: "drone-image-layer", type: "raster", source: "drone-image", paint: { "raster-opacity": imageOpacity } });
      map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]], { padding: 40, duration: 700 });
    };

    if (map.loaded()) updateImage();
    else map.once("load", updateImage);
  }, [resolvedImageUrl, bounds, imageOpacity]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (map.getLayer("mask-layer")) map.removeLayer("mask-layer");
    if (map.getSource("mask-image")) map.removeSource("mask-image");
    if (!resolvedMaskUrl || !showMask) return;

    const addMask = () => {
      map.addSource("mask-image", { type: "image", url: resolvedMaskUrl, coordinates: imageCoordinates(bounds) });
      map.addLayer({ id: "mask-layer", type: "raster", source: "mask-image", paint: { "raster-opacity": maskOpacity, "raster-resampling": "nearest" } });
    };

    if (map.loaded()) addMask();
    else map.once("load", addMask);
  }, [resolvedMaskUrl, bounds, showMask, maskOpacity]);

  const activeDetections = useMemo(
    () => showBoxes ? detections.filter((item) => item.confidence >= threshold && visibleClasses.has(item.label)) : [],
    [detections, threshold, visibleClasses, showBoxes]
  );

  const updateBoxes = useCallback(() => {
    const map = mapRef.current;
    if (!map || imageWidth <= 0 || imageHeight <= 0) {
      setScreenBoxes([]);
      return;
    }
    const boxes = activeDetections.map((item, index) => {
      const [x1, y1, x2, y2] = item.bbox;
      const topLeft = map.project(pixelToLngLat(x1, y1, imageWidth, imageHeight, bounds));
      const bottomRight = map.project(pixelToLngLat(x2, y2, imageWidth, imageHeight, bounds));
      return {
        key: item.id ?? `${item.label}-${index}`,
        label: item.label,
        confidence: item.confidence,
        color: item.color,
        x: Math.min(topLeft.x, bottomRight.x),
        y: Math.min(topLeft.y, bottomRight.y),
        width: Math.abs(bottomRight.x - topLeft.x),
        height: Math.abs(bottomRight.y - topLeft.y)
      };
    });
    setScreenBoxes(boxes);
  }, [activeDetections, bounds, imageWidth, imageHeight]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    updateBoxes();
    map.on("move", updateBoxes);
    map.on("zoom", updateBoxes);
    map.on("resize", updateBoxes);
    return () => {
      map.off("move", updateBoxes);
      map.off("zoom", updateBoxes);
      map.off("resize", updateBoxes);
    };
  }, [updateBoxes]);

  return (
    <div className="relative h-full min-h-[620px] overflow-hidden rounded-[2rem] bg-slate-900 shadow-soft ring-1 ring-slate-200">
      <div ref={containerRef} className="h-full min-h-[620px] w-full" />
      {resolvedMaskUrl && showMask && (
        <div className="pointer-events-none absolute left-4 top-4 rounded-full bg-white/95 px-3 py-1 text-xs font-bold text-slate-800 shadow">
          Segmentation mask active
        </div>
      )}
      {showBoxes && (
        <div className="pointer-events-none absolute left-4 top-12 rounded-full bg-white/90 px-3 py-1 text-[11px] font-semibold text-slate-600 shadow">
          Boxes are derived from mask regions
        </div>
      )}
      <svg className="pointer-events-none absolute inset-0 h-full w-full">
        {screenBoxes.map((box) => {
          const selected = selectedLabel === box.label;
          return (
            <g key={box.key} className="pointer-events-auto cursor-pointer" onClick={() => onSelectLabel(selected ? null : box.label)}>
              <rect
                x={box.x}
                y={box.y}
                width={box.width}
                height={box.height}
                fill="transparent"
                stroke={box.color}
                strokeWidth={selected ? 4 : 2.5}
                strokeDasharray={selected ? "0" : "8 5"}
                rx={8}
              />
              <foreignObject x={box.x} y={Math.max(0, box.y - 30)} width={190} height={30}>
                <div className="inline-flex max-w-[180px] items-center gap-2 rounded-full bg-white/95 px-3 py-1 text-xs font-bold capitalize text-slate-900 shadow">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: box.color }} />
                  {box.label} {Math.round(box.confidence * 100)}%
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>
      {!resolvedImageUrl && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-slate-950/40 p-8 text-center text-white">
          <div>
            <p className="text-xl font-bold">No image selected</p>
            <p className="mt-2 max-w-md text-sm text-slate-200">Upload a drone image or select a bundled sample to begin.</p>
          </div>
        </div>
      )}
    </div>
  );
}
