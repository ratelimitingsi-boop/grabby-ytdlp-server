"""
Self-hosted YouTube downloader API using yt-dlp.
Deploy to Render.com (free tier) — see README.md.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from yt_dlp import YoutubeDL

app = FastAPI(title="Grabby yt-dlp server")

# CORS: allow your Lovable preview + edge function to call this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional shared secret — set SHARED_SECRET in Render env to lock down access
SHARED_SECRET = os.getenv("SHARED_SECRET", "")


class GrabRequest(BaseModel):
    url: str
    mode: str = "auto"          # "auto" | "audio" | "mute"
    quality: str = "1080"       # "144".."4320" or "max"
    audio_format: str = "mp3"   # "mp3" | "ogg" | "wav" | "opus" | "best"
    secret: str = ""


def build_format(mode: str, quality: str) -> str:
    if mode == "audio":
        return "bestaudio/best"
    if mode == "mute":
        if quality == "max":
            return "bestvideo[ext=mp4]/bestvideo"
        return f"bestvideo[height<={quality}][ext=mp4]/bestvideo[height<={quality}]"
    # auto = video + audio
    if quality == "max":
        return "bestvideo+bestaudio/best"
    return (
        f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height<={quality}]/best"
    )


@app.get("/")
def root():
    return {"status": "ok", "service": "grabby-ytdlp"}


@app.post("/grab")
def grab(req: GrabRequest):
    if SHARED_SECRET and req.secret != SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

    ydl_opts = {
        "format": build_format(req.mode, req.quality),
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,        # we just want the URL
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"yt-dlp failed: {e}")

    # Pick the best resolved URL
    download_url = info.get("url")
    title = info.get("title", "video")
    ext = info.get("ext", "mp4")
    thumbnail = info.get("thumbnail")
    duration = info.get("duration")
    height = info.get("height")

    # If format is a merge (video+audio), info["url"] may be missing — fall back
    if not download_url and info.get("requested_formats"):
        # Pick the best video stream URL (user can grab audio separately if needed)
        download_url = info["requested_formats"][0].get("url")

    if not download_url:
        raise HTTPException(status_code=500, detail="No download URL extracted")

    return {
        "status": "redirect",
        "url": download_url,
        "filename": f"{title}.{ext}",
        "title": title,
        "thumbnail": thumbnail,
        "duration": duration,
        "quality": f"{height}p" if height else req.quality,
    }
