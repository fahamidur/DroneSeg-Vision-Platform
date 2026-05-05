# ---------- Backend development image ----------
FROM python:3.11-slim AS backend-dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user
ENV PATH=$HOME/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --chown=user backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

COPY --chown=user backend /app/backend

# ---------- Frontend build ----------
FROM node:20-bookworm AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend ./
ENV NEXT_PUBLIC_API_URL=
ENV NEXT_PUBLIC_ENABLE_LLM=false
RUN npm run build

# ---------- Production image for Hugging Face Spaces ----------
FROM python:3.11-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user

ENV HOME=/home/user
ENV PATH=$HOME/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV UPLOAD_DIR=/app/backend/uploads
ENV OUTPUT_DIR=/app/backend/outputs
ENV DB_PATH=/app/backend/droneseg.db
ENV MODEL_ID=nvidia/segformer-b2-finetuned-ade-512-512
ENV MAX_UPLOAD_SIZE_MB=50
ENV MAX_INFERENCE_SIDE=1280
ENV CORS_ORIGINS=*
ENV LOAD_MODEL_ON_STARTUP=true
ENV ENABLE_LLM=false
ENV OPENAI_API_KEY=

WORKDIR /app

COPY --chown=user backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /app/backend/requirements.txt

COPY --chown=user backend /app/backend
COPY --from=frontend-build --chown=user /app/frontend/out /app/frontend_out

RUN mkdir -p /app/backend/uploads /app/backend/outputs

EXPOSE 7860

CMD sh -c "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"
