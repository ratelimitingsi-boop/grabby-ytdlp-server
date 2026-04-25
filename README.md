# Grabby yt-dlp Server

A small FastAPI server that uses **yt-dlp** to extract real download URLs from YouTube and 1000+ other sites. Designed to be deployed on **Render.com's free tier** and called from the Grabby edge function.

## Why this exists

YouTube blocks Supabase/Vercel/Netlify edge functions because they run from datacenter IPs. yt-dlp running on a real server (with Deno installed for the JS challenge) is the standard way real downloader sites work in 2025-2026.

## Deploy to Render (free, ~5 minutes)

### Step 1 — Push this folder to GitHub
1. Create a new GitHub repo (e.g. `grabby-ytdlp-server`)
2. Copy the contents of this `ytdlp-server/` folder into the repo root
3. Commit & push

### Step 2 — Create the Render service
1. Go to https://render.com → **New + → Web Service**
2. Connect your GitHub repo
3. Render will auto-detect `render.yaml` — just click **Apply**
4. Wait ~3 min for first build (it installs yt-dlp + deps)

### Step 3 — Copy your URL + secret
After deploy, Render gives you:
- A URL like `https://grabby-ytdlp.onrender.com`
- A `SHARED_SECRET` env var (auto-generated — view it under **Environment**)

### Step 4 — Add them to Grabby (Lovable)
In your Lovable project, add two backend secrets:
- `YTDLP_SERVER_URL` = the Render URL (no trailing slash)
- `YTDLP_SHARED_SECRET` = the value Render generated

The edge function `cobalt-proxy` will pick them up automatically.

## Test locally (optional)

```bash
pip install -r requirements.txt
uvicorn main:app --reload
curl -X POST http://localhost:8000/grab \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=mfDmYhudsUI","mode":"auto","quality":"720"}'
```

## Notes on Render free tier
- Spins down after 15 min idle → first request after sleep takes ~30 sec
- 750 hours/month free (more than enough for personal use)
- For always-on: upgrade to $7/mo Starter, or set up a cron-job.org ping every 10 min
