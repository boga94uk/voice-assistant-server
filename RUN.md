# Voice Assistant Server — how to run

Shop backend for the ESP32-S3 voice watch. Pairing, placeholders, and the full run steps are in [SETUP.md](SETUP.md).

This server transcribes speech, talks to the Businessflow phoneshop API, and speaks replies through Pocket TTS.

## What you need

- Windows 10/11 (Linux works too; printer open-PDF is Windows-only)
- Python 3.10
- ffmpeg on PATH (WAV conversion for the watch)
- An OpenAI API key (`sk-...`)
- A Businessflow shop login (the same account the watch uses)
- Optional: [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) if the watch should reach the shop over the internet
- Optional: Pocket TTS sidecar on `127.0.0.1:8090` (see the firmware repo `tts/`)

## First-time setup

```powershell
cd VoiceAssistantServer
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
copy config\env.example config\.env
copy config\devices.example.yaml config\devices.yaml
notepad config\.env
notepad config\devices.yaml
```

In `config/.env` set `OPENAI_API_KEY`.

In `config/devices.yaml` set:

- `device_id` — watch MAC, e.g. `AA:BB:CC:DD:EE:FF`
- `secret` — 64 hex chars, must match the HMAC secret flashed / provisioned on the watch
- `phoneshop_username` / `phoneshop_password` — the Businessflow login (`YOUR_PHONESHOP_USERNAME` / `YOUR_PHONESHOP_PASSWORD`)

Edit `config/config.yaml` if the Businessflow host or TTS voice should change. See [SETUP.md](SETUP.md) for every placeholder.

## Start locally

```powershell
.\venv\Scripts\python.exe src\server.py
```

Health check: http://127.0.0.1:8080/health  
Admin: http://127.0.0.1:8080/admin

On this shop PC the desktop shortcut **Shop stack** runs a watchdog that keeps:

1. this server on `:8080`
2. Pocket TTS on `:8090`
3. Cloudflare tunnel `YOUR_TUNNEL_NAME` → `https://your-server.example.com`

Script: `YOUR_FIRMWARE_DIR\watch-shop-stack.bat` (in the firmware/tools tree).

## Public URL (watch off the LAN)

```powershell
cloudflared tunnel run YOUR_TUNNEL_NAME
```

Point the tunnel at `http://127.0.0.1:8080`. Provision the watch with that HTTPS origin.

## HMAC

The watch signs each request with `X-Device-ID`, `X-Device-Time`, `X-Device-Signature`. Time window is 180 seconds. The `secret` in `devices.yaml` must match the watch.

## Do not commit

- `config/.env`
- `config/devices.yaml`
- `logs/`, `audio_temp/`, `invoices/`, `venv/`
