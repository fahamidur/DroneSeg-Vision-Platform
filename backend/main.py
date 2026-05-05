from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import CORS_ORIGINS, ENABLE_LLM, LOAD_MODEL_ON_STARTUP, MODEL_ID
from backend.db.database import init_db
from backend.routers import assets, detect, export, history, llm, upload
from backend.seed_images import seed_sample_images
from backend.models.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_sample_images()
    app.state.seg_service = None
    app.state.model_error = None
    if LOAD_MODEL_ON_STARTUP:
        try:
            from backend.services.segformer_service import SegformerService

            app.state.seg_service = SegformerService(MODEL_ID)
        except Exception as exc:
            app.state.model_error = str(exc)
    yield


app = FastAPI(title="DroneSeg API", version="1.0.0", lifespan=lifespan)

allow_origins = CORS_ORIGINS
allow_credentials = "*" not in allow_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(detect.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(llm.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    model_loaded = app.state.seg_service is not None
    error = app.state.model_error
    message = "Ready" if model_loaded else "Model is not loaded"
    if error:
        message = f"Model load error: {error}"
    return {
        "status": "ok" if model_loaded or not error else "degraded",
        "model_loaded": model_loaded,
        "model_id": MODEL_ID,
        "llm_enabled": ENABLE_LLM,
        "message": message,
    }


frontend_out = Path("/app/frontend_out")
if frontend_out.exists():
    app.mount("/", StaticFiles(directory=str(frontend_out), html=True), name="frontend")
