# Deploy ParcelPilot — public URL

## Option A — Render (recommended, permanent free URL)

1. **Push to GitHub** (create repo at github.com → upload or `git push`)
2. Go to [render.com](https://render.com) → **New +** → **Blueprint** → connect repo
3. Render reads `render.yaml` automatically
4. Add secret **`GROQ_API_KEY`** (or `GEMINI_API_KEY` + `LLM_PROVIDER=gemini`) in the dashboard
5. Deploy → URL like `https://parcelpilot-ai-support.onrender.com`

**Note:** First deploy takes ~5–10 min (Docker + ML models). Free tier sleeps after 15 min idle.

---

## Option B — Quick demo tunnel (today, laptop must stay on)

```powershell
# Terminal 1 — start app
Start ParcelPilot.bat

# Terminal 2 — install cloudflare tunnel once:
winget install Cloudflare.cloudflared

# Then:
cloudflared tunnel --url http://localhost:8000
```

Copy the `https://*.trycloudflare.com` URL into your submission.

---

## What's included for deploy

| File | Purpose |
|---|---|
| `Dockerfile` | Production container (pre-built UI + FAISS + SQLite) |
| `render.yaml` | One-click Render blueprint |
| `.env` | **NOT deployed** — set secrets in hosting dashboard |

## Required secrets (hosting dashboard)

```
GROQ_API_KEY=your_key
LLM_PROVIDER=groq
```

Or for more free quota:

```
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key
```
