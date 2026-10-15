"""
Sound engine and synthesizer for CodeLan.
Generates retro 8-bit procedural sound effects with zero external dependencies.
"""

import io
import math
import random
import struct
import wave
import threading
from typing import Optional

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

def generate_wav(samples: list[float], sample_rate: int = 22050) -> bytes:
    """Converts a list of floats [-1.0, 1.0] into a mono 16-bit PCM WAV byte stream."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Pack samples to 16-bit signed integers
        raw_data = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            val = int(clamped * 32767.0)
            raw_data.extend(struct.pack('<h', val))
        wav_file.writeframes(raw_data)
    return buffer.getvalue()

def synth_laser(sample_rate: int = 22050) -> bytes:
    duration = 0.15
    num_samples = int(sample_rate * duration)
    samples = []
    freq = 900.0
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = 900.0 * (1.0 - t * 0.75)
        phase += 2 * math.pi * freq / sample_rate
        # Square wave with rapid decay
        val = 0.4 if math.sin(phase) > 0 else -0.4
        env = 1.0 - t
        samples.append(val * env)
    return generate_wav(samples, sample_rate)

def synth_jump(sample_rate: int = 22050) -> bytes:
    duration = 0.18
    num_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = 150.0 + 400.0 * (t ** 0.5)
        phase += 2 * math.pi * freq / sample_rate
        val = 0.4 if math.sin(phase) > 0 else -0.4
        env = 1.0 - (t * 0.6)
        samples.append(val * env)
    return generate_wav(samples, sample_rate)

def synth_coin(sample_rate: int = 22050) -> bytes:
    duration = 0.22
    num_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = 987.77 if t < 0.45 else 1318.51  # B5 then E6
        phase += 2 * math.pi * freq / sample_rate
        val = 0.35 * math.sin(phase)
        env = 1.0 - t
        samples.append(val * env)
    return generate_wav(samples, sample_rate)

def synth_hit(sample_rate: int = 22050) -> bytes:
    duration = 0.12
    num_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = 240.0 * (1.0 - t)
        phase += 2 * math.pi * freq / sample_rate
        noise = (random.random() * 2 - 1) * 0.4
        tone = (0.3 if math.sin(phase) > 0 else -0.3)
        env = 1.0 - t
        samples.append((tone + noise) * env)
    return generate_wav(samples, sample_rate)

def synth_explosion(sample_rate: int = 22050) -> bytes:
    duration = 0.35
    num_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        freq = 120.0 * (1.0 - t * 0.8)
        phase += 2 * math.pi * freq / sample_rate
        noise = (random.random() * 2 - 1) * 0.6
        tone = (0.2 if math.sin(phase) > 0 else -0.2)
        env = (1.0 - t) ** 1.5
        samples.append((tone + noise) * env)
    return generate_wav(samples, sample_rate)

def synth_powerup(sample_rate: int = 22050) -> bytes:
    duration = 0.3
    num_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    notes = [330, 392, 523, 659]  # E, G, C, E
    for i in range(num_samples):
        t = i / num_samples
        note_idx = min(int(t * 4), 3)
        freq = notes[note_idx]
        phase += 2 * math.pi * freq / sample_rate
        val = 0.35 if math.sin(phase) > 0 else -0.35
        env = 1.0 - (t % 0.25)
        samples.append(val * env)
    return generate_wav(samples, sample_rate)

def synth_gameover(sample_rate: int = 22050) -> bytes:
    duration = 0.5
    num_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    notes = [440, 370, 311, 220]
    for i in range(num_samples):
        t = i / num_samples
        note_idx = min(int(t * 4), 3)
        freq = notes[note_idx]
        phase += 2 * math.pi * freq / sample_rate
        val = 0.4 if math.sin(phase) > 0 else -0.4
        env = 1.0 - (t % 0.25)
        samples.append(val * env)
    return generate_wav(samples, sample_rate)

def synth_click(sample_rate: int = 22050) -> bytes:
    duration = 0.03
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / num_samples
        val = (random.random() * 2 - 1) * 0.3 * (1.0 - t)
        samples.append(val)
    return generate_wav(samples, sample_rate)

# Sound cache
SOUND_CACHE: dict[str, bytes] = {}

def get_sound_wav(name: str) -> Optional[bytes]:
    name = name.lower().strip()
    if name not in SOUND_CACHE:
        generators = {
            "laser": synth_laser,
            "shoot": synth_laser,
            "jump": synth_jump,
            "coin": synth_coin,
            "pickup": synth_coin,
            "hit": synth_hit,
            "explosion": synth_explosion,
            "boom": synth_explosion,
            "powerup": synth_powerup,
            "gameover": synth_gameover,
            "click": synth_click,
            "tick": synth_click,
        }
        gen = generators.get(name)
        if gen:
            SOUND_CACHE[name] = gen()
    return SOUND_CACHE.get(name)

def play_sound(name: str):
    """Asynchronously plays a named sound effect."""
    if not HAS_WINSOUND:
        return

    def _play():
        try:
            wav_data = get_sound_wav(name)
            if wav_data:
                winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()

def play_beep(freq: int, duration_ms: int):
    """Asynchronously beeps at frequency for duration."""
    if not HAS_WINSOUND:
        return

    def _beep():
        try:
            winsound.Beep(max(37, min(32767, int(freq))), max(1, min(5000, int(duration_ms))))
        except Exception:
            pass

    threading.Thread(target=_beep, daemon=True).start()
