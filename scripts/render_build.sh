#!/usr/bin/env bash
set -euo pipefail

pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Pre-download ONNX embedding model (lightweight vs PyTorch)
python -c "from fastembed import TextEmbedding; list(TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2').embed(['warmup']))"
