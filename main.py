"""
VoxShorts — Backend Server
Perfectly tuned for VoxShorts frontend.

Endpoints:
  GET  /              → serve index.html
  GET  /health        → status check
  POST /upload        → process video + generate hooks + voiceover
  POST /apply-hook    → apply selected hook to existing session
  POST /translate     → translate script to target language
  GET  /sessions/{id} → get session data
  DELETE /sessions/{id} → cleanup session

Requirements:
  pip install fastapi uvicorn python-multipart aiofiles openai moviepy pydub gtts anthropic httpx

Run:
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import uuid
import json
import time
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("voxshorts")

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_KEY    = os.getenv("ELEVENLABS_API_KEY", "")
# External keep-alive URL (set on Render + cron-job.org to prevent sleep):
# 1. Add env var KEEPALIVE_URL = https://<your-app>.onrender.com/ping in Render dashboard
# 2. On cron-job.org: create a cron every 10 min, URL = value of KEEPALIVE_URL
KEEPALIVE_URL     = os.getenv("KEEPALIVE_URL", "")

SESSIONS_DIR = Path("sessions")
STATIC_DIR   = Path("static")
SESSIONS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

SESSION_TTL_HOURS = 4  # Render free tier: conserve disk space

ELEVENLABS_VOICES = {
    "us_clear":  "21m00Tcm4TlvDq8ikWAM",
    "uk_clear":  "AZnzlk1XvdvUeBnXmlld",
    "au_clear":  "EXAVITQu4vr4xnSDxMaL",
    "in_clear":  "ErXwobaYiN019PkySvjV",
    "energetic": "VR6AewLTigWG4xSOukaG",
    "calm":      "pNInz6obpgDQGcFmaJgB",
    "deep":      "yoZ06aMxZJJ28mfd3POQ",
    "warm":      "ThT5KcBeYPX3keUQqHPh",
    "us_fast":  "21m00Tcm4TlvDq8ikWAM",  # alias of us_clear, speed handled by TTS
    "uk_calm":  "AZnzlk1XvdvUeBnXmlld",  # alias of uk_clear, calm variant
}

OPENAI_VOICES = {
    "us_clear": "alloy", "uk_clear": "echo", "au_clear": "fable",
    "in_clear": "onyx",  "energetic": "nova", "calm": "shimmer",
    "deep": "onyx",      "warm": "nova",
    "us_fast": "alloy", "uk_calm": "echo",
}

PREVIEW_TEXTS = {
    'us_clear':  "Hey, ready to go viral? Upload your clip and let's make it happen.",
    'uk_clear':  "Rather good, isn't it? Let me show you what VoxShorts can do.",
    'au_clear':  "G'day! Drop your video in and we'll turn it into a banger.",
    'in_clear':  "Welcome! Let's create something amazing together today.",
    'energetic': "LET'S GO! Your next viral video starts RIGHT NOW!",
    'calm':      "Take a breath. Upload your video, and we'll handle everything else.",
    'deep':      "Welcome to VoxShorts. Your content, elevated.",
    'warm':      "Hi there! So glad you're here. Let's make something great.",
}

VOICE_CONFIG = {
    'us_clear':  {'lang': 'en', 'tld': 'com',    'slow': False},
    'uk_clear':  {'lang': 'en', 'tld': 'co.uk',  'slow': False},
    'au_clear':  {'lang': 'en', 'tld': 'com.au', 'slow': False},
    'in_clear':  {'lang': 'en', 'tld': 'co.in',  'slow': False},
    'energetic': {'lang': 'en', 'tld': 'com',    'slow': False},
    'calm':      {'lang': 'en', 'tld': 'co.uk',  'slow': True},
    'deep':      {'lang': 'en', 'tld': 'com.au', 'slow': True},
    'warm':      {'lang': 'en', 'tld': 'co.in',  'slow': False},
}

NICHE_PROMPTS = {
    "general":    "engaging, broad audience",
    "business":   "professional, ROI-focused, executive audience",
    "education":  "clear, informative, student-friendly",
    "motivation": "inspiring, high energy, emotional",
    "fitness":    "energetic, results-driven, athletic",
    "tech":       "precise, innovation-focused, early adopters",
    "ecommerce":  "conversion-optimized, urgency-driven",
    "finance":    "trustworthy, data-driven, wealth-focused",
    "health":     "empathetic, science-backed, wellness-focused",
    "lifestyle":  "aspirational, relatable, visual",
}

app = FastAPI(title="VoxShorts API", version="2.0.0")
if KEEPALIVE_URL:
    log.info(f"External keep-alive configured: {KEEPALIVE_URL}")
else:
    log.warning("KEEPALIVE_URL not set — server may sleep on Render free tier when no tab is open")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Session Store ───────────────────────────────────────────────────────────

class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def create(self, session_id: str, data: dict):
        data["created_at"] = time.time()
        self._sessions[session_id] = data
        path = SESSIONS_DIR / f"{session_id}.json"
        path.write_text(json.dumps(
            {k: v for k, v in data.items() if k != "file_path"}, default=str
        ))

    def get(self, session_id: str) -> Optional[dict]:
        if session_id in self._sessions:
            return self._sessions[session_id]
        path = SESSIONS_DIR / f"{session_id}.json"
        if path.exists():
            data = json.loads(path.read_text())
            self._sessions[session_id] = data
            return data
        return None

    def update(self, session_id: str, updates: dict):
        if session_id in self._sessions:
            self._sessions[session_id].update(updates)

    def delete(self, session_id: str):
        self._sessions.pop(session_id, None)
        (SESSIONS_DIR / f"{session_id}.json").unlink(missing_ok=True)

    def cleanup_old(self):
        cutoff = time.time() - SESSION_TTL_HOURS * 3600
        for sid, data in list(self._sessions.items()):
            if data.get("created_at", 0) < cutoff:
                self.delete(sid)


sessions = SessionStore()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def normalize_mix(mix_raw) -> float:
    """
    Accept mix as 0-100 (from frontend slider) or 0.0-1.0 (direct float).
    Always returns a 0.0-1.0 float for moviepy.
    """
    try:
        v = float(mix_raw)
    except Exception:
        return 0.5
    if v > 1.0:
        v = v / 100.0
    return max(0.0, min(1.0, v))


async def generate_tts(
    text: str, voice: str, output_path: Path,
    speed: float = 1.0, pitch: float = 0
) -> Path:
    if ELEVENLABS_KEY:
        try:
            voice_id   = ELEVENLABS_VOICES.get(voice, ELEVENLABS_VOICES["us_clear"])
            stability  = 0.5
            similarity = 0.75
            if voice == "energetic": stability = 0.35; similarity = 0.8
            elif voice == "calm":    stability = 0.75; similarity = 0.7
            elif voice == "deep":    stability = 0.8;  similarity = 0.85
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={"xi-api-key": ELEVENLABS_KEY, "Accept": "audio/mpeg"},
                    json={
                        "text": text,
                        "model_id": "eleven_turbo_v2_5",
                        "voice_settings": {
                            "stability": stability, "similarity_boost": similarity,
                            "style": 0.0, "use_speaker_boost": True
                        }
                    },
                )
                r.raise_for_status()
                output_path.write_bytes(r.content)
                return output_path
        except Exception as e:
            log.warning(f"ElevenLabs failed: {e}")

    if OPENAI_API_KEY:
        try:
            import openai
            client   = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            response = await client.audio.speech.create(
                model="tts-1-hd",
                voice=OPENAI_VOICES.get(voice, "alloy"),
                input=text,
                speed=max(0.25, min(4.0, speed)),
            )
            output_path.write_bytes(response.content)
            return output_path
        except Exception as e:
            log.warning(f"OpenAI TTS failed: {e}")

    try:
        from gtts import gTTS
        import io
        cfg = VOICE_CONFIG.get(voice, VOICE_CONFIG['us_clear'])
        tts = gTTS(text=text, lang=cfg['lang'], tld=cfg['tld'], slow=cfg['slow'])
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        output_path.write_bytes(buf.getvalue())
        return output_path
    except Exception as e:
        raise HTTPException(500, f"TTS generation failed: {e}")


async def generate_hooks(
    video_description: str, niche: str, script: Optional[str] = None
) -> list[str]:
    niche_style = NICHE_PROMPTS.get(niche.lower(), NICHE_PROMPTS["general"])
    context     = f"Video context: {video_description}"
    if script:
        context += f"\nExisting script: {script}"

    prompt = f"""You are an expert viral content creator specializing in social media hooks.

{context}
Niche: {niche} ({niche_style})

Generate exactly 7 powerful hook variations for this video's voiceover opening.
Each hook must be 1-3 sentences max, under 25 words, instantly grab attention.

Rules:
- Hook 1: Question hook
- Hook 2: Bold statement / controversial claim
- Hook 3: Story opener ("I was...")
- Hook 4: Number/statistic hook
- Hook 5: Fear/pain point hook
- Hook 6: Promise/transformation hook
- Hook 7: Contrarian/unexpected angle

Return ONLY a JSON array of 7 strings. No explanation."""

    if ANTHROPIC_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                r.raise_for_status()
                content    = r.json()["content"][0]["text"]
                start, end = content.find("["), content.rfind("]") + 1
                if start >= 0 and end > start:
                    hooks = json.loads(content[start:end])
                    if isinstance(hooks, list) and len(hooks) >= 3:
                        return hooks[:7]
        except Exception as e:
            log.warning(f"Anthropic hook generation failed: {e}")

    if OPENAI_API_KEY:
        try:
            import openai
            client  = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            r       = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.85,
            )
            content    = r.choices[0].message.content
            start, end = content.find("["), content.rfind("]") + 1
            if start >= 0 and end > start:
                hooks = json.loads(content[start:end])
                if isinstance(hooks, list) and len(hooks) >= 3:
                    return hooks[:7]
        except Exception as e:
            log.warning(f"OpenAI hook generation failed: {e}")

    return [
        f"Wait — before you scroll past, you need to see this about {niche}.",
        f"I spent 3 years figuring this out so you don't have to.",
        f"Nobody talks about this, but it's the #1 thing holding people back in {niche}.",
        f"What if everything you know about {niche} is wrong?",
        f"The biggest mistake I see in {niche} — and how to fix it in 60 seconds.",
        f"This single {niche} strategy changed everything for me. Completely free.",
        f"Stop doing what you're doing. There's a better way. Let me show you.",
    ]


async def process_video(
    video_path: Path, audio_path: Path, output_path: Path,
    offset: float = 0.0, mix: float = 0.5,
    fade_in: int = 0, fade_out: int = 0,
) -> Path:
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
        video    = VideoFileClip(str(video_path))
        vo_audio = AudioFileClip(str(audio_path))
        if fade_in  > 0: vo_audio = vo_audio.audio_fadein(fade_in / 1000)
        if fade_out > 0: vo_audio = vo_audio.audio_fadeout(fade_out / 1000)
        if video.audio and mix < 1.0:
            final_audio = CompositeAudioClip([
                video.audio.volumex(1.0 - mix),
                vo_audio.set_start(offset).volumex(mix),
            ])
        else:
            final_audio = vo_audio.set_start(offset)
        video.set_audio(final_audio).write_videofile(
            str(output_path), codec="libx264", audio_codec="aac",
            logger=None,
            temp_audiofile=str(output_path.parent / "temp_audio.m4a"),
        )
        video.close()
        vo_audio.close()
        return output_path
    except Exception as e:
        log.warning(f"Video processing failed: {e} — returning audio only")
        shutil.copy(audio_path, output_path.with_suffix(".mp3"))
        return output_path.with_suffix(".mp3")


def generate_srt(text: str, wps: float = 2.5) -> str:
    words    = text.split()
    srt_out  = ""
    t        = 0.0
    for i in range(0, len(words), 8):
        chunk = " ".join(words[i:i + 8])
        dur   = len(chunk.split()) / wps
        s1, s2 = t, t + dur
        fmt = lambda s: (
            f"{int(s//3600):02d}:{int((s%3600)//60):02d}:"
            f"{int(s%60):02d},{int((s%1)*1000):03d}"
        )
        srt_out += f"{i//8+1}\n{fmt(s1)} --> {fmt(s2)}\n{chunk}\n\n"
        t = s2
    return srt_out


async def translate_text(text: str, target_lang: str) -> str:
    lang_names = {
        "en": "English", "nl": "Dutch",    "de": "German",
        "fr": "French",  "es": "Spanish",  "pt": "Portuguese",
        "it": "Italian", "ar": "Arabic",   "ja": "Japanese", "tr": "Turkish",
    }
    prompt = (
        f"Translate to {lang_names.get(target_lang, target_lang)}. "
        f"Return ONLY the translation:\n\n{text}"
    )
    if ANTHROPIC_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                r.raise_for_status()
                return r.json()["content"][0]["text"].strip()
        except Exception as e:
            log.warning(f"Anthropic translation failed: {e}")
    if OPENAI_API_KEY:
        try:
            import openai
            r = await openai.AsyncOpenAI(api_key=OPENAI_API_KEY).chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            log.warning(f"OpenAI translation failed: {e}")
    raise HTTPException(503, "No API key configured for translation.")


async def score_hooks(hooks: list[str], niche: str) -> list[dict]:
    if not hooks:
        return []
    prompt = (
        f'Score these {len(hooks)} hooks for "{niche}" niche (0-100). '
        f'Return ONLY JSON: {{"scores":[{{"index":0,"score":85,"reason":"short reason"}}]}}. '
        f'Hooks:\n' + '\n'.join(f'{i}: "{h}"' for i, h in enumerate(hooks))
    )
    try:
        if ANTHROPIC_API_KEY:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                r.raise_for_status()
                content    = r.json()["content"][0]["text"]
                start, end = content.find("["), content.rfind("]") + 1
                if start >= 0:
                    return json.loads(content[start:end])
    except Exception as e:
        log.warning(f"Hook scoring failed: {e}")
    return [
        {"score": 70 + (i * 3 % 20), "reason": "AI scoring unavailable", "tags": ["hook"]}
        for i, _ in enumerate(hooks)
    ]


async def cleanup_session_files(session_dir: Path, delay: int = 3600):
    await asyncio.sleep(delay)
    if session_dir.exists():
        shutil.rmtree(session_dir, ignore_errors=True)


# ═══════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════

@app.get("/ping")
async def ping():
    """Lightweight liveness probe — no external API calls."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/")
async def root():
    """Serve the frontend index.html."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html; charset=utf-8")
    return JSONResponse(
        {"status": "ok", "message": "Backend running — place index.html in /static"},
        status_code=200,
    )


@app.get("/health")
async def health():
    tts_status = "gtts-fallback"
    if ELEVENLABS_KEY:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(
                    "https://api.elevenlabs.io/v1/user",
                    headers={"xi-api-key": ELEVENLABS_KEY},
                )
                tts_status = "elevenlabs" if r.status_code == 200 else "fallback"
        except:
            tts_status = "fallback"
    elif OPENAI_API_KEY:
        tts_status = "openai"
    return {
        "status":  "ok",
        "version": "2.0.0",
        "tts":     tts_status,
        "engines": [
            k for k, v in {
                "elevenlabs": ELEVENLABS_KEY,
                "openai":     OPENAI_API_KEY,
                "anthropic":  ANTHROPIC_API_KEY,
            }.items() if v
        ],
    }


@app.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file:         UploadFile     = File(...),
    niche:        str            = Form("general"),
    voice:        str            = Form("us_clear"),
    offset:       float          = Form(0.0),
    mix:          str            = Form("80"),   # accepts 0-100 or 0.0-1.0
    speed:        float          = Form(1.0),
    pitch:        float          = Form(0.0),
    script:       Optional[str]  = Form(None),
    emotion:      Optional[str]  = Form(None),
    brand_voice:  Optional[str]  = Form(None),
    fade_in:      int            = Form(0),
    fade_out:     int            = Form(0),
    bgm_duck:     float          = Form(0.2),
    target_lang:  Optional[str]  = Form(None),
    pause_rules:  Optional[str]  = Form(None),
    preset:       Optional[str]  = Form(None),
):
    mix_float   = normalize_mix(mix)
    session_id  = str(uuid.uuid4())
    session_dir = STATIC_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    video_path = session_dir / f"input{Path(file.filename).suffix or '.mp4'}"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    hooks = await generate_hooks(
        f"A {niche} video '{file.filename}'"
        + (f" with script: {script[:200]}" if script else ""),
        niche, script,
    )
    vo_text = script if script else hooks[0]

    if target_lang and target_lang not in ("nl", "en", ""):
        try:
            vo_text = await translate_text(vo_text, target_lang)
        except:
            pass

    audio_path = session_dir / "voiceover.mp3"
    await generate_tts(vo_text, voice, audio_path, speed=speed, pitch=pitch)

    result_path = await process_video(
        video_path, audio_path, session_dir / "output.mp4",
        offset=offset, mix=mix_float, fade_in=fade_in, fade_out=fade_out,
    )
    has_video = result_path.suffix == ".mp4"

    srt_path = session_dir / "subtitles.srt"
    srt_path.write_text(generate_srt(vo_text), encoding="utf-8")

    sessions.create(session_id, {
        "session_id":  session_id,
        "niche":       niche,
        "voice":       voice,
        "hooks":       hooks,
        "hook_text":   hooks[0],
        "all_hooks":   hooks,
        "script":      vo_text,
        "video_path":  str(video_path),
        "audio_path":  str(audio_path),
        "output_path": str(result_path),
        "srt_path":    str(srt_path),
    })
    background_tasks.add_task(
        cleanup_session_files, session_dir, delay=SESSION_TTL_HOURS * 3600
    )

    base = f"/static/{session_id}"
    return {
        "session_id":        session_id,
        "all_hooks":         hooks,
        "hook_text":         hooks[0],
        "download_url":      f"{base}/output.mp4" if has_video else f"{base}/voiceover.mp3",
        "audio_preview_url": f"{base}/voiceover.mp3",
        "srt_url":           f"{base}/subtitles.srt",
        "voice":             voice,
        "word_count":        len(vo_text.split()),
    }


@app.post("/apply-hook")
async def apply_hook(
    session_id:  str   = Form(...),
    hook_index:  int   = Form(0),
    voice:       str   = Form("us_clear"),
    offset:      float = Form(0.0),
    mix:         str   = Form("80"),
    speed:       float = Form(1.0),
    pitch:       float = Form(0.0),
    fade_in:     int   = Form(0),
    fade_out:    int   = Form(0),
):
    mix_float = normalize_mix(mix)
    session   = sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    hooks = session.get("hooks", [])
    if not hooks:
        raise HTTPException(400, "No hooks found in session")

    hook_index  = max(0, min(hook_index, len(hooks) - 1))
    hook_text   = hooks[hook_index]
    session_dir = STATIC_DIR / session_id
    audio_path  = session_dir / f"voiceover_h{hook_index}.mp3"

    await generate_tts(hook_text, voice, audio_path, speed=speed, pitch=pitch)
    result_path = await process_video(
        Path(session["video_path"]), audio_path,
        session_dir / f"output_h{hook_index}.mp4",
        offset=offset, mix=mix_float, fade_in=fade_in, fade_out=fade_out,
    )
    srt_path = session_dir / f"subtitles_h{hook_index}.srt"
    srt_path.write_text(generate_srt(hook_text), encoding="utf-8")
    sessions.update(session_id, {"applied_hook": hook_index, "current_voice": voice})

    base      = f"/static/{session_id}"
    has_video = result_path.suffix == ".mp4"
    return {
        "session_id":        session_id,
        "hook_index":        hook_index,
        "hook_text":         hook_text,
        "download_url":      f"{base}/output_h{hook_index}.mp4" if has_video else f"{base}/voiceover_h{hook_index}.mp3",
        "audio_preview_url": f"{base}/voiceover_h{hook_index}.mp3",
        "srt_url":           f"{base}/subtitles_h{hook_index}.srt",
    }


@app.post("/translate")
async def translate(
    text:   str = Form(...),
    target: str = Form("en"),
    source: str = Form("auto"),
):
    if not text.strip():
        raise HTTPException(400, "Empty text provided")
    return {"translated": await translate_text(text, target), "target": target}


@app.post("/score-hooks")
async def score_hooks_endpoint(request: Request):
    """Score hooks server-side — keeps Anthropic API key secret from browser."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")
    hooks = body.get("hooks", [])
    niche = body.get("niche", "general")
    if not hooks or not isinstance(hooks, list):
        raise HTTPException(400, "hooks must be a non-empty list")
    scores = await score_hooks(hooks[:20], niche)  # cap at 20 for safety
    result = []
    for i, s in enumerate(scores):
        if isinstance(s, dict):
            result.append({"index": i, "score": s.get("score", 70), "reason": s.get("reason", "")})
        else:
            result.append({"index": i, "score": 70, "reason": ""})
    return {"scores": result}


@app.post("/generate-hooks")
async def generate_hooks_endpoint(request: Request):
    """Re-generate hooks for an existing session without re-uploading the video."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")
    session_id = body.get("session_id")
    niche = body.get("niche", "general")
    if not session_id:
        raise HTTPException(400, "session_id is required")
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found or expired")
    video_description = session.get("description", "short-form video")
    script = session.get("script")
    try:
        hooks = await generate_hooks(video_description, niche, script)
    except Exception as e:
        log.error(f"generate-hooks error: {e}")
        raise HTTPException(500, f"Hook generation failed: {e}")
    session["hooks"] = hooks
    session["niche"] = niche
    return {"hooks": hooks, "session_id": session_id}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {k: v for k, v in session.items() if "path" not in k}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    sessions.delete(session_id)
    background_tasks.add_task(cleanup_session_files, STATIC_DIR / session_id, delay=0)
    return {"deleted": session_id}


@app.post("/score-hooks")
async def score_hooks_endpoint(
    hooks: str = Form(...),
    niche: str = Form("general"),
):
    try:
        hook_list = json.loads(hooks)
        if not isinstance(hook_list, list):
            raise ValueError
    except:
        raise HTTPException(400, "hooks must be a valid JSON array")
    return {"scores": await score_hooks(hook_list, niche)}


@app.get("/voices")
async def list_voices():
    return {
        "voices": [
            {"id": "us_clear",  "name": "US Clear",   "flag": "🇺🇸"},
            {"id": "uk_clear",  "name": "UK Clear",   "flag": "🇬🇧"},
            {"id": "au_clear",  "name": "AU Clear",   "flag": "🇦🇺"},
            {"id": "in_clear",  "name": "IN Clear",   "flag": "🇮🇳"},
            {"id": "energetic", "name": "Energetic",  "flag": "⚡"},
            {"id": "calm",      "name": "Calm",       "flag": "🌊"},
            {"id": "deep",      "name": "Deep",       "flag": "🔊"},
            {"id": "warm",      "name": "Warm",       "flag": "☀️"},
        ],
        "tts_engine": (
            "elevenlabs" if ELEVENLABS_KEY
            else "openai" if OPENAI_API_KEY
            else "gtts"
        ),
    }


@app.get("/voices/preview")
async def voice_preview(voice: str = Query("us_clear")):
    """Return a short TTS audio sample for the given voice."""
    # Use cached preview if available
    cached_path = SESSIONS_DIR / f"preview_{voice}.mp3"
    if cached_path.exists():
        return Response(content=cached_path.read_bytes(), media_type="audio/mpeg")

    sample_text = PREVIEW_TEXTS.get(voice, PREVIEW_TEXTS['us_clear'])
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        audio_path = await generate_tts(sample_text, voice, tmp_path)
        audio_bytes = audio_path.read_bytes()
        # Cache for future requests
        cached_path.write_bytes(audio_bytes)
        audio_path.unlink(missing_ok=True)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(500, f"Preview failed: {e}")
