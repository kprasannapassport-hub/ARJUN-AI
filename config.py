"""
Arjun's settings. Change things here - you don't need to touch the other files.
"""
import os
from pathlib import Path

# Everything Arjun saves (history, tasks, contacts, documents) lives in this folder.
# Keeping it separate means you can update the code without losing your data.
DATA_DIR = Path(os.environ.get("ARJUN_HOME", Path.home() / "Arjun"))
FILES_DIR = DATA_DIR / "files"          # documents Arjun creates go here

# ---- The brain ----
MODEL = os.environ.get("ARJUN_MODEL", "qwen2.5:7b")   # laptop: qwen2.5:7b. Phone: llama3.2:3b (set by start_arjun.sh)
NUM_CTX = 4096              # how much text the model can keep in mind (smaller = less RAM)
MAX_HISTORY = 20            # how many recent messages Arjun keeps in mind

# ---- Hearing (Whisper, runs fully on your laptop) ----
WHISPER_SIZE = "small"      # tiny / base / small / medium
                            # "small" = fast, ok for English+Hindi.
                            # "medium" = noticeably better for Malayalam, but slower.
WHISPER_COMPUTE = "int8"    # keeps memory use low on CPU

# ---- Speaking ----
SPEAK_REPLIES = True        # Arjun speaks his replies (toggle while running with /voice)
TTS_ENGINE = "pyttsx3"      # your choice: Windows built-in voices (offline). Other options: "edge", "piper"

# Voices for each engine. Arjun picks the voice by the language he is replying in.
EDGE_VOICES = {
    "en": "en-IN-PrabhatNeural",
    "hi": "hi-IN-MadhurNeural",
    "ml": "ml-IN-MidhunNeural",
}
PIPER_VOICES = {
    "en": "en_US-ryan-medium",
    "hi": "hi_IN-pratham-medium",
    "ml": "ml_IN-arjun-medium",
}
PIPER_DIR = DATA_DIR / "piper_voices"

# ---- Spotify (see README -> "Spotify setup") ----
SPOTIFY_CLIENT_ID = ""      # paste your Client ID from developer.spotify.com/dashboard between the quotes
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8888/callback"   # must match what you typed in the Spotify dashboard

# ---- Phone app server (server.py) ----
SERVER_PORT = 8765
SERVER_TOKEN = os.environ.get("ARJUN_TOKEN", "Neeraj@21")   # secret password the phone app must send. On the laptop type it between the last two quotes. (On the phone, start_arjun.sh makes one for you.)
