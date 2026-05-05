# DroneSeg Backend

FastAPI backend for image upload, SegFormer semantic segmentation, detection history, optional LLM analysis and GeoJSON export.

## Local run without Docker

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Run the command from the project root if imports fail:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Sample images

Put JPEG/PNG files in `backend/sample_images`. They are registered automatically on startup.

Optional per-image bounds are stored in `backend/sample_images/sample_bounds.json`.
