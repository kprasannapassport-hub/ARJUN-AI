"""
Arjun's ears and mouth.
  listen() -> records from your microphone, Whisper turns speech into text (offline).
  speak()  -> turns Arjun's reply into sound, using the engine chosen in config.py.
Heavy libraries are imported only when needed, so text mode starts fast.
"""
import os
import re
import sys
import asyncio
import tempfile
import subprocess
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import config

_whisper = None
_TEMP = Path(tempfile.gettempdir())


# ----------------------------------------------------------------------
# HEARING
# ----------------------------------------------------------------------
def _get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        print("   (loading Whisper - the first time it downloads the model, please wait...)")
        _whisper = WhisperModel(config.WHISPER_SIZE, device="cpu", compute_type=config.WHISPER_COMPUTE)
    return _whisper


def record_until_silence(max_seconds=25, silence_seconds=1.3, wait_seconds=8):
    """Record from the mic. Starts when you speak, stops after you go quiet."""
    import numpy as np
    import sounddevice as sd

    rate, block_len = 16000, 1600            # 0.1 second blocks
    pre_roll, frames = [], []
    started, quiet_blocks, idle_blocks = False, 0, 0

    with sd.InputStream(samplerate=rate, channels=1, dtype="float32", blocksize=block_len) as stream:
        noise = [float(np.sqrt(np.mean(stream.read(block_len)[0] ** 2))) for _ in range(5)]
        threshold = max(0.012, 3 * sum(noise) / len(noise))
        for _ in range(int(max_seconds * 10)):
            data, _ = stream.read(block_len)
            level = float(np.sqrt(np.mean(data ** 2)))
            if level > threshold:
                if not started:
                    frames.extend(pre_roll)
                started, quiet_blocks = True, 0
            elif started:
                quiet_blocks += 1
            else:
                idle_blocks += 1
                pre_roll = (pre_roll + [data])[-3:]
            if started:
                frames.append(data)
                if quiet_blocks >= int(silence_seconds * 10):
                    break
            elif idle_blocks >= wait_seconds * 10:
                return None
    if not frames:
        return None
    return np.concatenate(frames).flatten()


def listen() -> str:
    """Listen once and return what you said as text ('' if nothing was heard)."""
    audio = record_until_silence()
    if audio is None:
        return ""
    model = _get_whisper()
    language = None
    try:  # choose the most likely of English / Hindi / Malayalam
        _, _, probs = model.detect_language(audio)
        allowed = {code: p for code, p in probs if code in ("en", "hi", "ml")}
        if allowed:
            language = max(allowed, key=allowed.get)
    except Exception:
        language = None
    segments, _ = model.transcribe(audio, language=language, beam_size=5, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


# ----------------------------------------------------------------------
# SPEAKING
# ----------------------------------------------------------------------
def detect_script(text: str) -> str:
    """Which voice to use: 'ml' for Malayalam letters, 'hi' for Devanagari, else 'en'."""
    hi = len(re.findall(r"[\u0900-\u097F]", text))
    ml = len(re.findall(r"[\u0D00-\u0D7F]", text))
    if hi == 0 and ml == 0:
        return "en"
    return "ml" if ml >= hi else "hi"


def clean_for_speech(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_`#>|]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:600]            # don't read out essays


def _play(path):
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    pygame.mixer.music.load(str(path))
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()


def _speak_edge(text, lang):
    import edge_tts
    out = _TEMP / "arjun_tts.mp3"

    async def go():
        await edge_tts.Communicate(text, config.EDGE_VOICES[lang]).save(str(out))

    asyncio.run(go())
    _play(out)


def _speak_piper(text, lang):
    voice = config.PIPER_VOICES[lang]
    config.PIPER_DIR.mkdir(parents=True, exist_ok=True)
    if not (config.PIPER_DIR / f"{voice}.onnx").exists():
        print(f"   (downloading voice {voice} - one time only)")
        subprocess.run([sys.executable, "-m", "piper.download_voices", voice,
                        "--data-dir", str(config.PIPER_DIR)], check=True)
    out = _TEMP / "arjun_tts.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", voice, "--data-dir", str(config.PIPER_DIR),
                    "-f", str(out), "--", text], check=True)
    _play(out)


def _speak_pyttsx3(text, lang):
    import pyttsx3
    engine = pyttsx3.init()
    wanted = {"en": "english", "hi": "hindi", "ml": "malayalam"}[lang]
    for v in engine.getProperty("voices"):
        if wanted in v.name.lower():
            engine.setProperty("voice", v.id)
            break
    engine.say(text)
    engine.runAndWait()


def speak(text: str) -> None:
    text = clean_for_speech(text)
    if not text:
        return
    lang = detect_script(text)
    try:
        {"edge": _speak_edge, "piper": _speak_piper, "pyttsx3": _speak_pyttsx3}[config.TTS_ENGINE](text, lang)
    except Exception as e:
        print(f"   [voice output problem: {e}]")
