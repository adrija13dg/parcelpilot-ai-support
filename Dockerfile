# ParcelPilot — production container (optimized for Render free tier)
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ONNX embedding model at build time
RUN python -c "from fastembed import TextEmbedding; list(TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2').embed(['warmup']))"

COPY api/ api/
COPY src/ src/
COPY scripts/ scripts/
COPY data/ data/
COPY db/ db/
COPY indexes/ indexes/
COPY frontend/dist/ frontend/dist/

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
