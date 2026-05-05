````markdown
# DroneSeg Vision Platform

DroneSeg Vision Platform is a full-stack drone imagery semantic segmentation application. It allows users to upload or select drone images, view them as georeferenced raster overlays on an OpenStreetMap basemap, run semantic segmentation using SegFormer-B2, inspect detected land-cover classes, view segmentation masks and export detection results as GeoJSON.

The project is designed as a technical proof-of-concept for full-stack machine learning deployment. It combines a Next.js frontend, a FastAPI backend, a pretrained semantic segmentation model, SQLite-based history storage and map-based visualisation.

## Project Purpose

The purpose of DroneSeg is to demonstrate how drone imagery can be processed through a web-based machine learning system. The application focuses on identifying visible land-cover and scene categories such as buildings, trees, vegetation, roads, water bodies, open ground and other relevant image regions.

The workflow follows a simple user journey:

1. Select a sample drone image or upload a new image.
2. View the image on an OpenStreetMap basemap.
3. Adjust map placement bounds where needed.
4. Run semantic segmentation.
5. Inspect the colour mask, detected classes and confidence scores.
6. Toggle overlays and bounding boxes.
7. Export detection results as GeoJSON.

## Main Features

- Interactive OpenStreetMap map viewer using MapLibre GL JS
- Drone image raster overlay with adjustable opacity
- Drag-and-drop image upload
- Sample image dropdown support
- Configurable geographic image bounds
- SegFormer-B2 semantic segmentation backend
- Colourised segmentation mask overlay
- Detection result panel with labels, confidence values, pixel areas and colours
- Optional bounding box visualisation
- Confidence threshold filtering
- Detection history storage using SQLite
- GeoJSON export for GIS-compatible outputs
- Optional GPT-4o-mini and gpt-4.1-mini vision analysis mode
- Docker-based deployment support
- Hugging Face Spaces deployment support

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js 14 and TypeScript | Web interface, state handling and user interaction |
| UI Styling | Tailwind CSS | Responsive and clean interface design |
| Map Engine | MapLibre GL JS | OpenStreetMap basemap and raster overlays |
| Backend | FastAPI | REST API, upload handling and inference routing |
| ML Model | SegFormer-B2 ADE20K | Semantic segmentation |
| ML Runtime | PyTorch and Hugging Face Transformers | Model loading and inference |
| Image Processing | Pillow, NumPy and OpenCV | Image validation, masks and bounding boxes |
| Storage | SQLite and local file system | Detection history, uploaded images and output masks |
| Optional AI | OpenAI GPT-4o-mini and gpt-4.1-mini | Approximate vision-language analysis |
| Deployment | Docker | Isolated build and runtime environment |

## Model Used

The main semantic segmentation model used in this project is:

```text
nvidia/segformer-b2-finetuned-ade-512-512
````

This is a SegFormer-B2 model fine-tuned on the ADE20K dataset. It provides pixel-level semantic segmentation across 150 scene categories. The model is loaded once when the FastAPI backend starts and is reused for detection requests.

The model receives an uploaded or selected image, processes it through the Hugging Face image processor, generates a segmentation map and returns structured detection results to the frontend.

## Project Structure

```text
DroneSeg/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── seed_images.py
│   ├── requirements.txt
│   ├── routers/
│   │   ├── detect.py
│   │   ├── upload.py
│   │   ├── history.py
│   │   ├── export.py
│   │   ├── images.py
│   │   └── llm.py
│   ├── services/
│   │   ├── segformer_service.py
│   │   ├── upload_service.py
│   │   ├── geojson_service.py
│   │   └── llm_service.py
│   ├── models/
│   │   └── schemas.py
│   ├── db/
│   │   ├── database.py
│   │   └── history_repo.py
│   ├── sample_images/
│   │   └── sample_bounds.json
│   ├── uploads/
│   └── outputs/
│
├── frontend/
│   ├── app/
│   │   └── page.tsx
│   ├── components/
│   │   ├── MapViewer.tsx
│   │   ├── DetectionPanel.tsx
│   │   ├── HistoryPanel.tsx
│   │   ├── ModelSelector.tsx
│   │   └── UploadDropzone.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── types/
│   │   └── detection.ts
│   ├── package.json
│   └── next.config.js
│
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

## How the System Works

### 1. Image Input

The user can either select a bundled sample image or upload a new drone image. The upload component accepts common image formats and the backend validates the file using Pillow before storing it.

Uploaded images are renamed using a UUID before being saved. This prevents unsafe file names and keeps the storage structure clean.

### 2. Map Display

The frontend displays an OpenStreetMap basemap through MapLibre GL JS. The drone image is rendered as a raster image layer using geographic bounds in this format:

```text
[south_west_longitude, south_west_latitude, north_east_longitude, north_east_latitude]
```

These bounds control where the image appears on the map. They also control the geographic position of exported GeoJSON polygons.

### 3. Segmentation Request

When the user clicks **Run Detection**, the frontend sends the selected image ID, confidence threshold and geographic bounds to the backend.

The backend receives the request through the detection API and sends the stored image to the SegFormer service.

### 4. SegFormer Inference

The backend loads the image, normalises it and processes it through SegFormer-B2. The output is a semantic segmentation map where each pixel is assigned a predicted class.

The backend then creates:

* A colourised segmentation mask
* Detected class labels
* Confidence scores
* Pixel areas
* Bounding boxes derived from connected mask regions
* A detection history record
* A mask image stored in the outputs directory

### 5. Result Visualisation

The frontend receives the detection response and displays:

* The segmentation mask on top of the drone image
* Detected classes in the results panel
* Confidence values
* Pixel area values
* Colour swatches
* Optional bounding boxes
* Model name and inference time

The mask is treated as the main segmentation output. Bounding boxes are shown as secondary visual aids and are useful for inspection and GeoJSON export.

### 6. History Storage

Detection results are saved into SQLite. The history panel allows previous detections to be reloaded into the interface.

### 7. GeoJSON Export

The GeoJSON export converts detected bounding boxes from pixel coordinates into map coordinates using the saved image bounds. This produces GIS-compatible polygon features with class labels, confidence values and pixel areas.

## Setup with Docker

Docker is the recommended setup method because it keeps the project isolated from the main machine.

### Step 1

Unzip the project.

```bash
unzip DroneSeg.zip
cd DroneSeg
```

### Step 2

Place the provided DJI sample images inside:

```text
backend/sample_images/
```

Example:

```text
backend/sample_images/DJI_20260308132416_0059_V.JPG
backend/sample_images/DJI_20260308132418_0060_V.JPG
backend/sample_images/DJI_20260308132419_0061_V.JPG
```

### Step 3

Set image bounds in:

```text
backend/sample_images/sample_bounds.json
```

Example:

```json
{
  "DJI_20260308132416_0059_V.JPG": [90.354, 23.778, 90.358, 23.782],
  "DJI_20260308132418_0060_V.JPG": [90.354, 23.778, 90.358, 23.782],
  "DJI_20260308132419_0061_V.JPG": [90.354, 23.778, 90.358, 23.782]
}
```

### Step 4

Build and run the project.

```bash
docker compose up --build
```

### Step 5

Open the application.

```text
http://localhost:3000
```

The backend API will run on:

```text
http://localhost:8000
```

## Local Development Setup

Docker is preferred, but the project can also be run manually.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

On Windows:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

## Environment Variables

The project can run with the default SegFormer model without an OpenAI key.

Optional environment variables can be placed in a `.env` file.

```env
MODEL_ID=nvidia/segformer-b2-finetuned-ade-512-512
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
DB_PATH=droneseg.db
CORS_ORIGINS=http://localhost:3000
ENABLE_LLM=false
OPENAI_API_KEY=
```

For optional GPT vision mode:

```env
ENABLE_LLM=true
OPENAI_API_KEY=your_openai_api_key_here
```

The OpenAI API key is used only on the backend. It is not exposed to the browser.

## Sample Image Bounds

The file below controls the default map placement of sample images:

```text
backend/sample_images/sample_bounds.json
```

Each image should have four values:

```text
[south_west_longitude, south_west_latitude, north_east_longitude, north_east_latitude]
```

Example:

```json
{
  "sample.jpg": [90.354, 23.778, 90.358, 23.782]
}
```

If exact drone image coordinates are not available, approximate bounds can be used for demonstration. The frontend also allows manual adjustment of the map bounds before detection.

## API Endpoints

| Method | Endpoint                             | Purpose                          |
| ------ | ------------------------------------ | -------------------------------- |
| GET    | `/api/health`                        | Check backend status             |
| GET    | `/api/samples`                       | Load available sample images     |
| POST   | `/api/upload`                        | Upload a new image               |
| POST   | `/api/detect`                        | Run SegFormer segmentation       |
| POST   | `/api/llm/analyze`                   | Run optional GPT vision analysis |
| GET    | `/api/history`                       | Retrieve detection history       |
| GET    | `/api/history/{detection_id}`        | Reload a saved detection         |
| GET    | `/api/export/geojson/{detection_id}` | Export detection as GeoJSON      |
| GET    | `/api/images/{image_id}`             | Serve stored images              |
| GET    | `/api/masks/{mask_filename}`         | Serve segmentation masks         |

## Detection Response Format

A successful detection response follows this structure:

```json
{
  "detection_id": "uuid",
  "image_id": "uuid",
  "model_used": "nvidia/segformer-b2-finetuned-ade-512-512",
  "inference_time_ms": 2430,
  "image_width": 3840,
  "image_height": 2160,
  "bounds": [90.354, 23.778, 90.358, 23.782],
  "detections": [
    {
      "label": "building",
      "confidence": 0.91,
      "bbox": [120, 80, 1260, 920],
      "pixel_area": 48230,
      "color": "#FF6B6B"
    }
  ],
  "mask_url": "/api/masks/example_mask.png"
}
```

## GeoJSON Export

The exported GeoJSON uses the saved geographic bounds of the image. Each bounding box is converted into a geographic polygon.

Example feature:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [90.3541, 23.7782],
        [90.3545, 23.7782],
        [90.3545, 23.7786],
        [90.3541, 23.7786],
        [90.3541, 23.7782]
      ]
    ]
  },
  "properties": {
    "class": "building",
    "confidence": 0.91,
    "pixel_area": 48230,
    "color": "#FF6B6B"
  }
}
```

## LLM Vision Mode

The project includes optional LLM vision support using:

```text
gpt-4o-mini
gpt-4.1-mini
```

This mode analyses the image and returns approximate visual regions. It does not replace SegFormer because it is not pixel-level semantic segmentation. It is included as an additional analysis option for image interpretation.

To enable it:

```env
ENABLE_LLM=true
OPENAI_API_KEY=your_openai_api_key_here
```

The model selector in the frontend allows the user to choose between:

```text
SegFormer-B2
GPT-4o-mini
gpt-4.1-mini
```

## Upload Support

The project supports image upload through the frontend dropzone. Uploaded files are validated on the backend before being saved.

Supported upload formats include:

```text
JPG
JPEG
PNG
WebP
BMP
TIFF
```

WebP, BMP and TIFF files are normalised internally for reliable processing. HEIC and AVIF images should be converted to JPG before upload.

## Running on Hugging Face Spaces

The project can be deployed as a Docker-based Hugging Face Space.

Recommended steps:

```bash
git init
git add .
git commit -m "Initial DroneSeg deployment"
git remote add origin https://huggingface.co/spaces/your-username/DroneSeg
git push origin main
```

For large DJI images, use Git LFS:

```bash
git lfs install
git lfs track "backend/sample_images/*.JPG"
git lfs track "backend/sample_images/*.jpg"
git lfs track "backend/sample_images/*.jpeg"
git lfs track "backend/sample_images/*.png"
git add .gitattributes backend/sample_images/
git commit -m "Add sample drone images with Git LFS"
git push
```

Alternatively, upload large image files using the Hugging Face CLI:

```bash
pip install -U huggingface_hub
hf auth login
hf upload your-username/DroneSeg backend/sample_images backend/sample_images --repo-type space
```

## Git Ignore Recommendation

The repository should not include runtime outputs, local databases or temporary files.

Recommended `.gitignore` content:

```gitignore
.env
.env.local
__pycache__/
*.pyc

backend/uploads/*
backend/outputs/*
backend/*.db

frontend/.next/
frontend/node_modules/
node_modules/

.DS_Store
```

Sample images may be tracked if required for submission:

```gitignore
!backend/sample_images/
!backend/sample_images/*.JPG
!backend/sample_images/*.jpg
!backend/sample_images/*.jpeg
!backend/sample_images/*.png
!backend/sample_images/sample_bounds.json
```

## Testing the Application

A normal test run should follow this sequence:

1. Start the application with Docker.
2. Open the frontend at `http://localhost:3000`.
3. Select one bundled sample image.
4. Confirm that the image appears on the OpenStreetMap basemap.
5. Adjust bounds if needed.
6. Click **Run Detection**.
7. Confirm that the segmentation mask appears.
8. Confirm that the results panel lists detected classes.
9. Toggle bounding boxes.
10. Adjust the confidence threshold.
11. Export the GeoJSON file.
12. Reload a previous detection from history.

## Key Design Decisions

### SegFormer-B2 as the main model

SegFormer-B2 was selected because it provides semantic segmentation without requiring project-specific model training. Its ADE20K class coverage includes several classes relevant to drone and urban imagery.

### FastAPI backend

FastAPI was used because it supports clean REST endpoints, image upload handling, asynchronous routes and easy integration with Python-based machine learning libraries.

### MapLibre GL JS frontend map

MapLibre GL JS was used because it is open-source, works well with OpenStreetMap tiles and supports georeferenced raster image overlays.

### SQLite storage

SQLite was selected because the project is a proof-of-concept and does not require a separate database server. It stores image records and detection history locally.

### UUID file naming

Uploaded files are renamed using UUIDs. This improves safety, avoids filename collisions and prevents direct reliance on user-provided file names.

### Mask-first visualisation

The segmentation mask is the primary result because semantic segmentation is a pixel-level task. Bounding boxes are included as secondary visual aids and for GeoJSON export.

## Future Development

Future development could extend the prototype through more advanced geospatial and machine learning features:

* Use drone EXIF and XMP metadata to estimate image placement automatically.
* Add support for orthomosaic GeoTIFF files.
* Fine-tune a UAV-specific segmentation model for stronger aerial accuracy.
* Add polygon-level segmentation export rather than rectangular bounding boxes.
* Add user authentication for multi-user deployments.
* Add cloud storage for uploaded images and masks.
* Add batch processing for multiple drone images.
* Add comparison between SegFormer and other segmentation models.
* Add a dedicated GIS export panel for QGIS and ArcGIS workflows.
* Add model performance metrics using labelled validation images.

## Summary

DroneSeg Vision Platform demonstrates a complete full-stack semantic segmentation workflow for drone imagery. It combines image upload, OpenStreetMap visualisation, pretrained SegFormer inference, segmentation mask rendering, detection history and GeoJSON export in one deployable web application.

The project shows how computer vision, geospatial mapping and web deployment can be integrated into a practical drone image analysis platform.

```
```
