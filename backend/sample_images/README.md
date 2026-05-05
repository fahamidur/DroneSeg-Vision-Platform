# Sample drone images

Place the three DJI sample images here before running the app.

Supported formats: `.jpg`, `.jpeg`, `.JPG`, `.JPEG`, `.png`, `.PNG`.

The backend automatically registers every image in this folder as a selectable sample on startup.

To fix map placement, edit `sample_bounds.json` and add one entry per filename:

```json
{
  "DJI_20260308132419_0061_V.JPG": [90.354, 23.778, 90.358, 23.782]
}
```

The four values are:

`[south_west_longitude, south_west_latitude, north_east_longitude, north_east_latitude]`

If no entry is provided for an image, the app still works using the default bounds. The bounds can also be adjusted from the frontend before detection and GeoJSON export.
