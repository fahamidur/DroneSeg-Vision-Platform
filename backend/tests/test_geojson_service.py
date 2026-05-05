from backend.services.geojson_service import detections_to_geojson


def test_detections_to_geojson_polygon():
    record = {
        "image_width": 100,
        "image_height": 100,
        "bounds": [0.0, 0.0, 1.0, 1.0],
        "detections": [
            {"label": "building", "confidence": 0.9, "bbox": [0, 0, 100, 100], "pixel_area": 10000, "color": "#FF6B6B"}
        ],
    }
    geojson = detections_to_geojson(record)
    assert geojson["type"] == "FeatureCollection"
    assert geojson["features"][0]["geometry"]["type"] == "Polygon"
    assert geojson["features"][0]["properties"]["class"] == "building"
