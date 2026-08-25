# ParcelPilot AI Support

Production-grade AI support agent with **React** frontend and **FastAPI** backend.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite, blue/white gradient + dark theme |
| Backend | FastAPI |
| Structured data | SQLite |
| Document search | FAISS + sentence-transformers |
| LLM | Groq / Gemini / Ollama (switch in `.env`) |

## Quick start

### 1. Install Python dependencies

```bash
py -m pip install -r requirements.txt
```

### 2. Set API key

Create `.env` from `.env.example`.

### LLM options (pick one in `.env`)

| Provider | Cost | Setup |
|---|---|---|
| **Gemini** (recommended if Groq runs out) | Free tier, generous | Key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → `LLM_PROVIDER=gemini` |
| **Groq** | Free but rate-limited | `GROQ_API_KEY` → `LLM_PROVIDER=groq` |
| **Ollama** | Free, unlimited, local | Install [ollama.com](https://ollama.com), `ollama pull llama3.1:8b` → `LLM_PROVIDER=ollama` |

### 3. Build data index (once, or after adding PDFs)

```bash
py scripts/build_index.py
```

### 4. Development (two terminals)

**Backend:**
```bash
py -m uvicorn api.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 5. Production (single server)

```bash
cd frontend && npm run build && cd ..
py -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

---

## Run automatically (no command every time)

### Option A — Start now, runs in background until reboot

Double-click **`Start ParcelPilot.bat`** in the project folder,  
or run once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

Then open **http://localhost:8000** anytime. One process serves both UI and API.

Stop it:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop.ps1
```

### Option B — Start every time you log in to Windows

Run **once** (as yourself):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-autostart.ps1
```

ParcelPilot starts hidden in the background at login → **http://localhost:8000**

To disable autostart:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/uninstall-autostart.ps1
```

Logs: `logs/server.log`

---

| Role | Account | Tests |
|---|---|---|
| Customer | Northstar Logistics | ORD-1001 free cancel, TKT-501 |
| Customer | LumenWorks | ORD-2002 credit, access control |
| Internal Support | — | All accounts, Issues dashboard |

## Functional test questions

See `TEST_QUESTIONS.md`.

## Documentation for evaluators

- `ARCHITECTURE.md` — system design, data flow, deployment  
- `PRODUCT.md` — features, demo script, requirements mapping  
