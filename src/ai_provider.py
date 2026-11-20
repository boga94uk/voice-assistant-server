"""
OpenAI / xAI provider selection for the shop server.

If XAI_API_KEY is set, chat goes to api.x.ai (OpenAI-compatible), STT to /v1/stt,
and TTS to /v1/tts. Otherwise the existing OpenAI Whisper / chat / TTS paths are used.
"""
import os
import logging
from typing import Optional

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

XAI_BASE = "https://api.x.ai/v1"
POCKET_TTS_DEFAULT = "http://127.0.0.1:8090"
POCKET_VOICE = {
    "alloy": "alba",
    "echo": "marius",
    "fable": "jane",
    "onyx": "jean",
    "nova": "eve",
    "shimmer": "cosette",
}


def using_xai() -> bool:
    return bool(os.getenv("XAI_API_KEY"))


def api_key() -> str:
    return os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY") or ""


def chat_model(config: Optional[dict] = None) -> str:
    if using_xai():
        return os.getenv("XAI_CHAT_MODEL", "grok-4-fast")
    if config:
        return config.get("openai", {}).get("model", "gpt-4o-mini")
    return "gpt-4o-mini"


def make_chat_client() -> OpenAI:
    key = api_key()
    http_client = httpx.Client(timeout=30.0)
    if using_xai():
        logger.info("AI provider: xAI (%s)", chat_model())
        return OpenAI(api_key=key, base_url=XAI_BASE, http_client=http_client)
    logger.info("AI provider: OpenAI")
    return OpenAI(api_key=key, http_client=http_client)


def _rms(pcm: bytes) -> float:
    if len(pcm) < 2:
        return 0.0
    n = min(len(pcm) // 2, 16000)
    total = 0
    for i in range(n):
        s = int.from_bytes(pcm[i * 2 : i * 2 + 2], "little", signed=True)
        total += s * s
    return (total / n) ** 0.5


def normalize_wav(path: str) -> str:
    """Rewrite a clean 16 kHz mono 16-bit WAV OpenAI will accept. Keep a debug copy."""
    import shutil
    import time
    import wave

    raw = open(path, "rb").read()
    debug_dir = os.path.join(os.path.dirname(path), "debug")
    os.makedirs(debug_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(path, os.path.join(debug_dir, f"in-{stamp}.wav"))
    logger.info(
        "audio bytes=%d magic=%s",
        len(raw),
        raw[:12].hex() if raw else "empty",
    )

    pcm = b""
    rate = 16000
    nch = 1
    sw = 2
    try:
        with wave.open(path, "rb") as w:
            rate = w.getframerate() or 16000
            nch = w.getnchannels() or 1
            sw = w.getsampwidth() or 2
            pcm = w.readframes(w.getnframes())
    except Exception as exc:
        logger.warning("wave parse failed (%s); treating payload as s16le pcm", exc)
        pcm = raw[44:] if len(raw) > 44 and raw[:4] == b"RIFF" else raw
        if len(pcm) % 2:
            pcm = pcm[:-1]
        rate, nch, sw = 16000, 1, 2

    if sw == 2 and nch == 2:
        mono = bytearray()
        for i in range(0, len(pcm) - 3, 4):
            mono.extend(pcm[i : i + 2])
        pcm = bytes(mono)
        nch = 1

    logger.info("pcm bytes=%d rms=%.1f rate=%s nch=%s sw=%s", len(pcm), _rms(pcm), rate, nch, sw)

    out = os.path.join(debug_dir, f"norm-{stamp}.wav")
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000 if rate == 16000 else rate)
        w.writeframes(pcm)
    shutil.copy2(out, path)
    return path


def transcribe_google_web(path: str) -> str:
    """Free unofficial Google web STT (speech_recognition.recognize_google). No API key."""
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language="en-GB")
    except sr.UnknownValueError as exc:
        raise RuntimeError(f"Google heard no speech ({type(exc).__name__})") from exc
    if not text or not str(text).strip():
        raise RuntimeError("Google web STT returned empty text")
    return str(text).strip()


def _transcribe_paid(path: str, key: str) -> str:
    if using_xai():
        with open(path, "rb") as audio:
            resp = httpx.post(
                f"{XAI_BASE}/stt",
                headers={"Authorization": f"Bearer {key}"},
                data={"language": "en", "format": "true"},
                files={"file": ("rec.wav", audio, "audio/wav")},
                timeout=45.0,
            )
        resp.raise_for_status()
        payload = resp.json()
        text = (payload.get("text") or "").strip()
        if not text:
            raise RuntimeError(f"xAI STT empty response: {payload}")
        return text

    client = OpenAI(api_key=key, http_client=httpx.Client(timeout=30.0))
    with open(path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("rec.wav", audio, "audio/wav"),
            response_format="text",
            language="en",
        )
    return transcript.strip()


def transcribe_file(path: str) -> str:
    """Paid STT first (xAI/OpenAI), then free Google web STT."""
    path = normalize_wav(path)
    errors = []
    key = api_key()
    if key:
        try:
            return _transcribe_paid(path, key)
        except Exception as exc:
            logger.warning("Paid STT failed, trying Google web STT: %s", exc)
            errors.append(str(exc))
    try:
        text = transcribe_google_web(path)
        logger.info("Transcription via Google web STT")
        return text
    except Exception as exc:
        errors.append(f"google:{type(exc).__name__}:{exc}")
        raise RuntimeError("All STT backends failed: " + " | ".join(errors))


def pocket_tts_url() -> str:
    return (os.getenv("POCKET_TTS_URL") or POCKET_TTS_DEFAULT).rstrip("/")


def pocket_tts_ready() -> bool:
    try:
        resp = httpx.get(f"{pocket_tts_url()}/health", timeout=1.5)
        if resp.status_code != 200:
            return False
        return bool(resp.json().get("ready"))
    except Exception:
        return False


def _synthesize_pocket(text: str, dest_path: str, voice: str) -> None:
    voice_id = POCKET_VOICE.get(voice, voice or "alba")
    resp = httpx.post(
        f"{pocket_tts_url()}/tts",
        json={"text": text, "voice": voice_id},
        timeout=90.0,
    )
    resp.raise_for_status()
    with open(dest_path, "wb") as out:
        out.write(resp.content)
    logger.info("TTS via Pocket TTS (%s)", voice_id)


def synthesize_wav(text: str, dest_path: str, voice: str = "eve") -> None:
    """Write WAV bytes to dest_path. Pocket TTS first, then xAI/OpenAI."""
    if pocket_tts_ready():
        _synthesize_pocket(text, dest_path, voice)
        return

    key = api_key()
    if not key:
        raise RuntimeError("Pocket TTS is not running and no XAI_API_KEY or OPENAI_API_KEY is configured")

    if using_xai():
        voice_id = voice if voice not in ("alloy", "echo", "fable", "onyx", "nova", "shimmer") else "eve"
        resp = httpx.post(
            f"{XAI_BASE}/tts",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "text": text,
                "voice_id": voice_id,
                "language": "en",
                "output_format": {"codec": "wav", "sample_rate": 16000},
            },
            timeout=45.0,
        )
        resp.raise_for_status()
        with open(dest_path, "wb") as out:
            out.write(resp.content)
        return

    client = OpenAI(api_key=key, http_client=httpx.Client(timeout=30.0))
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice or "alloy",
        input=text,
        response_format="wav",
    )
    response.stream_to_file(dest_path)
