from typing import Any, Dict, List


def pixel_to_lng_lat(x: float, y: float, width: int, height: int, bounds: List[float]) -> List[float]:
    sw_lng, sw_lat, ne_lng, ne_lat = bounds
    lng = sw_lng + (x / max(width, 1)) * (ne_lng - sw_lng)
    lat = ne_lat - (y / max(height, 1)) * (ne_lat - sw_lat)
    return [round(lng, 8), round(lat, 8)]


def detections_to_geojson(record: Dict[str, Any]) -> Dict[str, Any]:
    width = int(record["image_width"])
    height = int(record["image_height"])
    bounds = record["bounds"]
    features = []

    for detection in record["detections"]:
        x1, y1, x2, y2 = detection["bbox"]
        coordinates = [[
            pixel_to_lng_lat(x1, y1, width, height, bounds),
            pixel_to_lng_lat(x2, y1, width, height, bounds),
            pixel_to_lng_lat(x2, y2, width, height, bounds),
            pixel_to_lng_lat(x1, y2, width, height, bounds),
            pixel_to_lng_lat(x1, y1, width, height, bounds),
        ]]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": coordinates},
                "properties": {
                    "class": detection["label"],
                    "confidence": detection["confidence"],
                    "pixel_area": detection["pixel_area"],
                    "color": detection["color"],
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
