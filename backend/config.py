import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def _path_from_env(name: str, default: str) -> Path:
    raw = os.getenv(name, default)
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


UPLOAD_DIR = _path_from_env("UPLOAD_DIR", "uploads")
OUTPUT_DIR = _path_from_env("OUTPUT_DIR", "outputs")
DB_PATH = _path_from_env("DB_PATH", "droneseg.db")
SAMPLE_IMAGE_DIR = _path_from_env("SAMPLE_IMAGE_DIR", "sample_images")

MODEL_ID = os.getenv("MODEL_ID", "nvidia/segformer-b2-finetuned-ade-512-512")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_INFERENCE_SIDE = int(os.getenv("MAX_INFERENCE_SIDE", "1280"))
MIN_AREA_RATIO = float(os.getenv("MIN_AREA_RATIO", "0.001"))
LOAD_MODEL_ON_STARTUP = os.getenv("LOAD_MODEL_ON_STARTUP", "true").lower() == "true"
ENABLE_LLM = os.getenv("ENABLE_LLM", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_BOUNDS = [
    float(os.getenv("DEFAULT_SW_LNG", "90.354")),
    float(os.getenv("DEFAULT_SW_LAT", "23.778")),
    float(os.getenv("DEFAULT_NE_LNG", "90.358")),
    float(os.getenv("DEFAULT_NE_LAT", "23.782")),
]

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = [item.strip() for item in _raw_origins.split(",") if item.strip()]

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
