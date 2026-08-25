# ParcelPilot — Architecture

CalQuity AI Engineer assessment submission.

## System overview

```text
                    Browser (React)
                           │
                           ▼
              FastAPI (api/main.py)
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    Agent loop         Ops Radar         Static UI
  (src/agent.py)    (src/issues.py)    (frontend/dist)
         │
    ┌────┴────┐
    ▼         ▼
  Tools     LLM API
    │      (Groq/Gemini/Ollama)
    ├─ search_documents ──► FAISS + PDF chunks
    ├─ query_operational_data ──► SQLite
    └─ prepare_escalation ──► pending confirm UI
```

## Components

| Module | Role |
|---|---|
| `frontend/` | React UI — Chat, Ops Radar, Sources, login |
| `api/main.py` | REST API, serves built React app |
| `src/agent.py` | LLM tool-calling loop + JSON fallback |
| `src/tools.py` | Three assessment tools + access filters |
| `src/rag.py` | FAISS vector search over PDFs |
| `src/business_logic.py` | SLA, cancellation, credit calculations |
| `src/access.py` | Role/account-scoped data access |
| `src/reliability.py` | High/medium/low badge from tool results |
| `src/issues.py` | Ops Radar aggregations (no LLM) |
| `scripts/build_index.py` | One-time PDF + Excel ingestion |

## Data flow (chat question)

1. User message → `/api/chat` with session (role + account).
2. Agent calls tools with **access enforced in Python**, not only in the prompt.
3. Tool results returned to LLM; loop until final answer.
4. `compute_reliability(tool_trace)` tags answer high/medium/low.
5. UI shows answer, reliability badge, tool activity, optional escalation modal.

## Source precedence

When documents conflict:

1. Signed customer agreement  
2. Current support policy (v3)  
3. SOP / product operations guide  
4. Deprecated policy v2 (retrievable, never wins)  
5. Historical ticket resolutions (context only — may be wrong)

## Access control

| Role | Scope |
|---|---|
| Customer | Own account orders/tickets + global docs + own agreement |
| Internal Support | All accounts and documents |

## Fixed snapshot clock

All SLA and timing uses **2026-08-16 11:00 Asia/Kolkata** — not the live system clock.

## Deployment

- **Local:** `Start ParcelPilot.bat` → http://localhost:8000  
- **Public:** Render/Railway — single FastAPI process, `GROQ_API_KEY` or `GEMINI_API_KEY` in secrets  
- Pre-built `indexes/` and `db/` committed for fast cold start

## Design decisions

- **SQLite** over live Excel — predictable tool interface, no LLM SQL.
- **Pre-built FAISS** — avoid re-embedding on every page load (important for free hosting).
- **Confirmation gate** on escalations — human-in-the-loop before writes.
- **Ops Radar without LLM** — proactive signals from SQL/rules; LLM only on "Investigate with AI".
