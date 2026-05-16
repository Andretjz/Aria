# Aria backend — production image (CPU-only, slim)
# Build context: aria/ directory  (fly deploy runs from aria/)
# See aria/fly.toml for Fly.io machine spec (2 shared CPU, 4 GB RAM, Frankfurt).
# GPU dependencies are excluded — cloud AI APIs (Gladia, Claude, OpenAI) replace local models.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system aria \
    && useradd --system --gid aria --no-create-home aria

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy package root and backend — preserves the aria.backend.* import path
COPY __init__.py ./aria/__init__.py
COPY backend/ ./aria/backend/

RUN chown -R aria:aria /app
USER aria

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "aria.backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
