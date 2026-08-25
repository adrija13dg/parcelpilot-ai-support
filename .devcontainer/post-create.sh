#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip
pip install -r requirements.txt

cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
npm run build
cd ..

{
  echo "LLM_PROVIDER=${LLM_PROVIDER:-groq}"
  if [ -n "${GROQ_API_KEY:-}" ]; then
    echo "GROQ_API_KEY=${GROQ_API_KEY}"
  fi
  if [ -n "${GEMINI_API_KEY:-}" ]; then
    echo "GEMINI_API_KEY=${GEMINI_API_KEY}"
  fi
} > .env

if ! grep -qE 'GROQ_API_KEY=.+' .env && ! grep -qE 'GEMINI_API_KEY=.+' .env; then
  echo ""
  echo "⚠️  No LLM API key found."
  echo "   Add GROQ_API_KEY or GEMINI_API_KEY under:"
  echo "   GitHub repo → Settings → Secrets and variables → Codespaces"
  echo ""
  cp .env.example .env
fi

echo "✓ ParcelPilot setup complete"
