# Deploy ParcelPilot — public URL

## Option A — Render (recommended, one-click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/adrija13dg/parcelpilot-ai-support)

1. Click the button above (or open [render.com/deploy?repo=...](https://render.com/deploy?repo=https://github.com/adrija13dg/parcelpilot-ai-support))
2. Sign in to Render → connect GitHub → **Approve** the blueprint
3. Set **`GROQ_API_KEY`** in the form (required for chat)
4. Click **Deploy Blueprint** → URL like `https://parcelpilot-ai-support.onrender.com`

**Note:** First deploy takes ~8–12 min (Docker builds React + installs ML libs). Free tier sleeps after 15 min idle.

Pushes to `main` auto-redeploy after the blueprint is linked.

---

## Option B — GitHub Codespaces (hosted on GitHub)

Best if you want everything on GitHub without a third-party host.

1. Repo → **Settings → Secrets and variables → Codespaces** → add `GROQ_API_KEY`
2. Open [codespaces.new/adrija13dg/parcelpilot-ai-support](https://codespaces.new/adrija13dg/parcelpilot-ai-support)
3. After setup, open forwarded port **8000** → set **Public** → share that URL

**Note:** Codespaces stop when idle (free tier limits). For a 24/7 URL, use Render below.

---

## Option C — Render manual (dashboard)

1. Push to GitHub (already done: `adrija13dg/parcelpilot-ai-support`)
2. Go to [render.com](https://render.com) → **New +** → **Blueprint** → connect repo
3. Render reads `render.yaml` automatically
4. Add secret **`GROQ_API_KEY`** in the dashboard
5. Deploy → URL like `https://parcelpilot-ai-support.onrender.com`

---

## Option D — Quick demo tunnel (today, laptop must stay on)

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
