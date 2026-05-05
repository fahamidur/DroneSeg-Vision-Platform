# DroneSeg Vision Platform

DroneSeg Vision Platform is a full-stack technical assessment project for drone imagery semantic segmentation. It lets a user upload or select a drone image, place the image on an OpenStreetMap basemap, run semantic segmentation through a FastAPI backend, display the colour mask and bounding boxes on an interactive MapLibre map, store detection history and export detected regions as GeoJSON.

The default analysis path uses the free SegFormer-B2 ADE20K model through Hugging Face Transformers. Optional GPT vision modes can be enabled through server-side environment variables when an OpenAI API key is available.

## What the project builds

The project builds a browser-based drone image analysis tool with these main capabilities:

1. A Next.js and TypeScript frontend for image upload, map viewing, model selection, confidence filtering, segmentation display and result inspection.
2. A FastAPI backend for file upload, image validation, sample image registration, SegFormer inference, LLM proxy analysis, history storage and GeoJSON export.
3. A MapLibre GL JS map using OpenStreetMap raster tiles, with the uploaded drone image rendered as a georeferenced raster overlay.
4. A pretrained SegFormer-B2 semantic segmentation pipeline that returns a coloured segmentation mask, detected regions, class labels, confidence scores, bounding boxes and pixel areas.
5. SQLite and file-system storage for uploaded images, segmentation masks and detection history.
6. Docker and Hugging Face Spaces support for isolated local development and public deployment.

## Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS | Main user interface and controls |
| Map | MapLibre GL JS | OpenStreetMap basemap, drone raster overlay and mask overlay |
| Backend | FastAPI, Python 3.11 | Upload handling, inference API, history and export endpoints |
| Machine learning | SegFormer-B2 ADE20K, PyTorch, Transformers | Semantic segmentation |
| Image processing | Pillow, OpenCV, NumPy | Image loading, mask generation and connected-component bounding boxes |
| Storage | SQLite and local file system | Uploaded images, masks and detection history |
| Optional AI | OpenAI API through backend only | GPT-based approximate visual analysis |
| Deployment | Docker, Docker Compose, Hugging Face Spaces | Local isolation and public hosting |

## Repository structure

```text
production/
├── Dockerfile
├── docker-compose.yml
├── .gitattributes
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── db/
│   │   ├── database.py
│   │   └── history_repo.py
│   ├── models/
│   │   └── schemas.py
│   ├── routers/
│   │   ├── assets.py
│   │   ├── detect.py
│   │   ├── export.py
│   │   ├── history.py
│   │   ├── llm.py
│   │   └── upload.py
│   ├── services/
│   │   ├── geojson_service.py
│   │   ├── segformer_service.py
│   │   └── upload_service.py
│   ├── sample_images/
│   │   ├── README.md
│   │   └── sample_bounds.json
│   ├── uploads/
│   └── outputs/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   ├── package.json
│   └── .env.local.example
├── model/
│   └── MODEL_NOTES.md
└── scripts/
    ├── deploy_huggingface.sh
    ├── run_local.sh
    └── test_production_docker.sh
```

## Core workflow

1. The user opens the frontend.
2. The frontend checks backend health, loads sample images and loads the latest detection history.
3. The user either selects a sample image from `backend/sample_images` or uploads a new image through the upload panel.
4. The backend validates the file, normalises it to a safe internal image format, renames it using a UUID and stores its metadata in SQLite.
5. The image appears on the MapLibre map using default or user-supplied geographic bounds.
6. The user presses **Run Detection**.
7. The backend loads the image from disk and runs SegFormer-B2 inference.
8. The segmentation map is converted into a colour mask.
9. OpenCV connected-component analysis converts meaningful mask regions into bounding boxes.
10. The backend returns detections, confidence values, pixel areas, mask URL, mask base64 data and inference time.
11. The frontend displays the mask, optional bounding boxes, class list, confidence slider and GeoJSON export button.
12. The detection is saved in SQLite so it can be reloaded from the history panel.

## How the segmentation works

The segmentation pipeline is implemented in `backend/services/segformer_service.py`.

The backend loads `nvidia/segformer-b2-finetuned-ade-512-512` once at startup. Each image is opened with Pillow and resized when needed so that free CPU environments do not run out of memory. The model produces per-pixel class logits. These are converted into a semantic map, then upscaled to the working image size. Each class region is colourised into an RGBA mask. OpenCV connected components are used to find region boxes. Very small regions are filtered using `MIN_AREA_RATIO`, and detections below the selected confidence threshold are removed before returning the result.

The important point is that the coloured mask is the real segmentation output. The rectangular boxes are a simplified visual and export layer derived from mask regions, so they should be treated as approximate boxes rather than exact object outlines.

## Adding sample drone images

The assessment expects bundled sample drone images. To add them:

1. Put the image files inside:

```text
backend/sample_images/
```

2. Supported sample formats are:

```text
.jpg, .jpeg, .JPG, .JPEG, .png, .PNG
```

3. Restart the backend. The startup process automatically registers every image in `backend/sample_images` as a selectable sample.

4. The sample dropdown in the frontend will show the registered images.

The current code supports multiple samples, but the submitted ZIP must include the required sample images before final submission. Without sample images, the dropdown works but has nothing meaningful to show.

## Fixing wrong map placement

Wrong map placement is usually not a segmentation bug. It happens because a normal drone JPG does not automatically tell the web map its four corner coordinates. The app therefore uses default bounds unless better bounds are provided.

Default bounds are configured in `backend/.env`:

```env
DEFAULT_SW_LNG=90.354
DEFAULT_SW_LAT=23.778
DEFAULT_NE_LNG=90.358
DEFAULT_NE_LAT=23.782
```

For accurate placement of a sample image, edit:

```text
backend/sample_images/sample_bounds.json
```

Use this format:

```json
{
  "DJI_20260308132419_0061_V.JPG": [90.354, 23.778, 90.358, 23.782]
}
```

The values mean:

```text
[south_west_longitude, south_west_latitude, north_east_longitude, north_east_latitude]
```

For an uploaded image, adjust the **Map placement bounds** fields in the frontend before running detection. GeoJSON export uses these same bounds, so the map coordinates must be corrected before exporting.

## Running locally with Docker

Docker is the safest option because it keeps Python, Node and model dependencies mostly isolated from the main laptop.

From the project root:

```bash
docker compose build
docker compose up
```

Then open:

```text
http://localhost:3000
```

The backend runs at:

```text
http://localhost:8000
```

To stop the app:

```bash
docker compose down
```

To remove the containers and volumes:

```bash
docker compose down -v
```

## Running without Docker

Backend:

```bash
cd production
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend, in a second terminal:

```bash
cd production/frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000
```

## Optional GPT vision modes

The two GPT options are optional. The SegFormer option works without an API key.

To enable GPT options locally, set these backend environment variables:

```env
ENABLE_LLM=true
OPENAI_API_KEY=your_api_key_here
```

In Docker Compose, edit `docker-compose.yml`:

```yaml
environment:
  ENABLE_LLM: "true"
  OPENAI_API_KEY: "your_api_key_here"
```

On Hugging Face Spaces, add them as Space secrets or variables:

```text
ENABLE_LLM=true
OPENAI_API_KEY=your_api_key_here
```

The OpenAI API key must stay on the backend. It must not be placed in `NEXT_PUBLIC_` variables, frontend code or browser-visible files.

The GPT modes produce approximate bounding boxes and scene descriptions. They do not produce pixel-accurate semantic segmentation masks.

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Backend and model status |
| `/api/samples` | GET | List registered sample images |
| `/api/upload` | POST | Upload and register an image |
| `/api/images/{image_id}` | GET | Serve an uploaded or sample image |
| `/api/detect` | POST | Run SegFormer segmentation on an image |
| `/api/masks/{mask_filename}` | GET | Serve a generated segmentation mask |
| `/api/history` | GET | Return paginated detection history |
| `/api/history/{detection_id}` | GET | Reload one detection result |
| `/api/history/{detection_id}` | DELETE | Delete one detection result |
| `/api/export/geojson/{detection_id}` | GET | Export detections as GeoJSON |
| `/api/llm/analyze` | POST | Run optional GPT vision analysis |

## Hugging Face Spaces deployment

The root `Dockerfile` builds a single production container for Hugging Face Spaces. It builds the frontend as static files and serves them through the FastAPI app on port `7860`.

Basic deployment flow:

```bash
git lfs install
git lfs track "*.JPG" "*.jpg" "*.jpeg" "*.png"
git add .gitattributes
git add .
git commit -m "Deploy DroneSeg Vision Platform"
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push space main
```

If sample drone images are larger than the Hugging Face file limit, Git LFS must track them before commit. After adding LFS tracking, remove old committed large files from Git history if they were committed before tracking.

## Specification alignment

The project is broadly aligned with the specification because it implements the required full-stack structure, upload flow, MapLibre map, SegFormer-B2 inference, detection result panel, history storage, GeoJSON export, optional LLM route, Docker deployment and environment-based configuration.

The strongest implemented areas are:

- FastAPI backend with upload, detection, history, asset serving, LLM and export routers.
- Isolated `SegformerService`, which supports maintainability and future model replacement.
- UUID-renamed uploads, which reduces path traversal risk.
- SQLite history and saved mask output.
- MapLibre overlay with adjustable image opacity and mask opacity.
- Confidence threshold filtering and per-class visibility toggling.
- Server-side OpenAI key handling for optional GPT modes.
- Git LFS configuration for large image files.

The project still needs a few submission-level fixes before being considered fully complete.

## Critical fix before final submission

In `backend/routers/history.py`, the history reload endpoint calculates `mask_filename` but returns `mask_url`, which is not defined. This can break reloading a history item.

Fix this block:

```python
mask_filename = row["mask_path"].split("/")[-1].split("\\")[-1]
```

Then return:

```python
"mask_url": f"/api/masks/{mask_filename}" if mask_filename else "",
```

Without this fix, the history list may load, but clicking a history item can fail.

## Known limitations

1. The project does not include actual sample drone images in the ZIP. It supports samples, but the required images must be added to `backend/sample_images` before final submission.
2. The default map coordinates are only placeholders. Correct placement requires accurate bounds in `sample_bounds.json` or manual bounds entered in the frontend.
3. SegFormer-B2 ADE20K is a general semantic segmentation model, not a drone-specific model. It can misclassify aerial rooftops, roads, open ground and vegetation because aerial imagery has a different viewing angle from many ADE20K training images.
4. Bounding boxes are produced from connected mask regions. They are useful for navigation and GeoJSON export, but they are not exact polygon boundaries.
5. The GPT options are disabled unless `ENABLE_LLM=true` and `OPENAI_API_KEY` are configured on the backend.
6. The frontend currently shows GPT model choices even when the backend has LLM disabled. This is acceptable for an optional feature, but the user experience would be clearer if the options were disabled automatically when `/api/health` reports `llm_enabled=false`.
7. The current georeferencing approach uses rectangular bounds only. It does not read EXIF GPS metadata or perform true orthomosaic georeferencing.

## Suggested improvements

1. Add the three required DJI sample images to `backend/sample_images` and verify that the sample dropdown displays all of them.
2. Add accurate coordinates for every sample in `backend/sample_images/sample_bounds.json`.
3. Fix `backend/routers/history.py` so that reloaded history records return a valid `mask_url`.
4. Disable GPT options in the frontend when `llm_enabled=false` in the health response.
5. Add a frontend button for deleting individual history records.
6. Add EXIF GPS extraction for DJI images and automatically propose map bounds from metadata when possible.
7. Replace rectangular GeoJSON boxes with polygonised mask contours for more realistic GIS output.
8. Add a drone-specific fallback model, such as a UAV-focused segmentation model, to reduce ADE20K domain-shift errors.
9. Add unit tests for upload validation, detection response shape, GeoJSON conversion and LLM-disabled behaviour.
10. Add a small demo dataset and screenshots to the README so the assessment reviewer can understand the expected workflow quickly.

## Troubleshooting

### Upload says the image is not valid

Check that the uploaded file is a real image and not a Git LFS pointer. If it came from a Git repository, run:

```bash
git lfs pull
```

Then upload the real image again.

### The image appears in the wrong place on the map

Edit the bounds in `sample_bounds.json` for sample images or adjust the Map placement bounds in the frontend for uploaded images.

### GPT options do not work

Set these on the backend:

```env
ENABLE_LLM=true
OPENAI_API_KEY=your_api_key_here
```

Then restart the backend or redeploy the Hugging Face Space.

### Segmentation looks weak

The model is pretrained on ADE20K, so some drone scenes will not segment perfectly. Try a clearer image, lower the confidence threshold, increase `MAX_INFERENCE_SIDE` if the server has enough memory, or use a drone-specific segmentation model as a future improvement.

### Hugging Face rejects large image files

Track images with Git LFS before committing them:

```bash
git lfs install
git lfs track "backend/sample_images/*.JPG" "backend/sample_images/*.jpg" "backend/sample_images/*.png"
git add .gitattributes backend/sample_images/
git commit -m "Add sample drone images with LFS"
git push space main
```

## Submission checklist

Before final submission:

- [ ] Add the required DJI sample images inside `backend/sample_images`.
- [ ] Add correct coordinates for each sample image in `sample_bounds.json`.
- [ ] Fix the undefined `mask_url` issue in `backend/routers/history.py`.
- [ ] Run the app locally with Docker.
- [ ] Upload at least one new image and confirm it appears on the map.
- [ ] Run SegFormer detection and confirm the mask appears.
- [ ] Toggle bounding boxes and class visibility.
- [ ] Export GeoJSON and confirm the file downloads.
- [ ] Reload a detection from history.
- [ ] Decide whether GPT options should remain visible or be enabled with an API key.
- [ ] Confirm large sample images are tracked through Git LFS before pushing to Hugging Face.
