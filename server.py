import os
import uuid
import shutil
import random
import subprocess
import datetime as dt
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import srt
from gtts import gTTS

# -------------------------------------------------------------------
# Paths & folders
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = STATIC_DIR / "outputs"

for d in [STATIC_DIR, UPLOAD_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------
# FastAPI app
# -------------------------------------------------------------------
app = FastAPI(title="AutoSubtitle Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # eventueel later beperken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve /static
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def sanitize_offset(raw: str) -> float:
    """Zorgt dat '0,3' of '0.3' allebei werken."""
    if raw is None:
        return 0.0
    raw = raw.replace(",", ".")
    try:
        v = float(raw)
        return max(0.0, v)
    except ValueError:
        return 0.0


def sanitize_mix(raw: str) -> int:
    """Clamp mix tussen 0–100."""
    try:
        v = int(float(raw))
    except ValueError:
        v = 80
    return max(0, min(100, v))


def generate_hooks(niche: str, voice: str, num: int = 5) -> List[str]:
    """Genereer meerdere hooks op basis van niche + voice-style."""
    niche = (niche or "content").strip()
    voice = (voice or "neutral").strip().lower()

    style_words = {
        "male": ["bold", "no-fluff", "direct"],
        "female": ["warm", "confident", "sharp"],
        "energetic": ["high-energy", "punchy", "fast-paced"],
        "calm": ["low-key", "soothing", "steady"],
    }.get(voice, ["clean", "simple", "high-converting"])

    templates = [
        "Stop scrolling. This {niche} trick changes everything.",
        "You’re doing {niche} wrong — here’s the 10-second fix.",
        "If you care about {niche}, watch the next 3 seconds.",
        "Nobody talks about this {niche} shortcut — but you should.",
        "You’ll wish you knew this {niche} hack sooner.",
        "Before you do your next {niche} post, see this.",
        "This is why your {niche} content isn’t performing.",
        "I used this {niche} move and everything changed.",
        "The most underrated {niche} secret nobody shares.",
        "Here’s the brutal truth about {niche} in 2025.",
    ]

    hooks: List[str] = []
    attempts = 0
    target = max(num, 1)

    while len(hooks) < target and attempts < target * 10:
        attempts += 1
        t = random.choice(templates)
        sw = random.choice(style_words)
        h = t.format(niche=niche)
        h = h.replace("this ", f"{sw} ", 1) if "this " in h else h
        h = h.strip()
        if h not in hooks:
            hooks.append(h)

    return hooks[:target]


def build_srt(text: str) -> str:
    """Maak een simpel SRT-bestand met 1–3 regels uit de hook."""
    text = text.strip()
    if not text:
        text = "Your AI voice-over is ready."

    words = text.split()
    # splits ongeveer in 2-3 stukken
    chunks = []
    chunk_size = max(4, len(words) // 3 or 1)
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))

    subtitles = []
    start = 0.0
    for idx, chunk in enumerate(chunks, start=1):
        end = start + max(1.8, len(chunk.split()) * 0.4)
        subtitles.append(
            srt.Subtitle(
                index=idx,
                start=dt.timedelta(seconds=start),
                end=dt.timedelta(seconds=end),
                content=chunk,
            )
        )
        start = end + 0.2

    return srt.compose(subtitles)


def merge_video_and_audio(
    video_path: Path,
    audio_path: Path,
    out_path: Path,
    offset_sec: float,
    mix_pct: int,
) -> None:
    """
    Merge origineel video + AI audio met ffmpeg.
    - offset_sec: start vertraging AI voice
    - mix_pct: hoeveel % AI voice vs origineel
    """

    offset_ms = max(0, int(offset_sec * 1000))
    mix_pct = max(0, min(100, mix_pct))

    # volume verhouding
    ai_vol = mix_pct / 100.0
    orig_vol = (100 - mix_pct) / 100.0

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-filter_complex",
        (
            f"[0:a]volume={orig_vol}[a0];"
            f"[1:a]adelay={offset_ms}|{offset_ms},volume={ai_vol}[a1];"
            f"[a0][a1]amix=inputs=2:duration=first[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(out_path),
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        # Fallback: gewoon kopiëren als ffmpeg faalt
        shutil.copyfile(video_path, out_path)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@app.get("/")
async def index():
    """
    Serve index.html uit /static als die bestaat,
    anders gewoon een simpele JSON (handig om te testen).
    """
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"status": "ok", "message": "Backend running, index.html not found in /static"}, status_code=200)


@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    niche: str = Form("content"),
    voice: str = Form("male"),
    offset: str = Form("0"),
    mix: str = Form("80"),
):
    """
    Hoofd endpoint dat door jouw frontend wordt aangeroepen.
    Verwacht:
    - file: video
    - niche: bv. 'fitness', 'business'
    - voice: 'male'|'female'|'energetic'|'calm'
    - offset: string, bv. '0.3' of '0,3'
    - mix: string, percentage ('80' etc.)
    """

    # 1) Save upload
    if not file.filename:
        return JSONResponse({"detail": "No file uploaded"}, status_code=400)

    uid = uuid.uuid4().hex
    ext = Path(file.filename).suffix or ".mp4"
    in_video_path = UPLOAD_DIR / f"{uid}{ext}"

    with open(in_video_path, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    # 2) Hooks genereren
    all_hooks = generate_hooks(niche=niche, voice=voice, num=5)
    hook_text = all_hooks[0] if all_hooks else "Your AI voice-over is ready."

    # 3) AI voice-over als MP3 maken (gTTS)
    audio_path = OUTPUT_DIR / f"{uid}.mp3"
    try:
        tts = gTTS(text=hook_text, lang="en")
        tts.save(audio_path.as_posix())
    except Exception as e:
        # Fallback: als gTTS faalt, maak een leeg / dummy bestand
        with open(audio_path, "wb") as f_dummy:
            f_dummy.write(b"")  # leeg, maar bestand bestaat tenminste

    # 4) SRT-bestand genereren
    srt_text = build_srt(hook_text)
    srt_path = OUTPUT_DIR / f"{uid}.srt"
    with open(srt_path, "w", encoding="utf-8") as f_srt:
        f_srt.write(srt_text)

    # 5) Video + audio mergen
    out_video_path = OUTPUT_DIR / f"{uid}.mp4"
    off = sanitize_offset(offset)
    mix_val = sanitize_mix(mix)
    try:
        merge_video_and_audio(in_video_path, audio_path, out_video_path, off, mix_val)
    except Exception:
        # laatste fallback
        shutil.copyfile(in_video_path, out_video_path)

return {
    "session_id": uid,
    "download_url": f"/static/outputs/{out_video_path.name}",
    "srt_url": f"/static/outputs/{srt_path.name}",
    "audio_preview_url": f"/static/outputs/{audio_path.name}",
    "hook_text": hook_text,
    "all_hooks": all_hooks,
}

