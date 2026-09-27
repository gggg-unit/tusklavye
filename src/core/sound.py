"""Sound feedback using Qt's QSoundEffect with auto-generated WAV files.

Generates short beep tones at startup if sound files are missing, so the
app works out of the box without any external audio assets.
"""
from __future__ import annotations

import logging
import math
import struct
import wave
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import QUrl, QObject

logger = logging.getLogger(__name__)

try:
    from PySide6.QtMultimedia import QSoundEffect
    _HAS_QTMULTIMEDIA = True
except ImportError:
    QSoundEffect = None
    _HAS_QTMULTIMEDIA = False
    logger.warning("QtMultimedia not available; sound will be disabled")

from ..config import SOUNDS_DIR

_SAMPLE_RATE = 16000
_MAX_SAMPLE = 32767


def _generate_tone(
    path: Path,
    freqs: List[float],
    durations_ms: List[int],
    volume: float = 0.3,
) -> None:
    """Generate a multi-segment sine-wave WAV with smooth fade in/out.

    ``freqs`` and ``durations_ms`` must be the same length; each segment is
    played back-to-back. Used for both the single-tone key/error sounds and
    the two-tone success sound.
    """
    if len(freqs) != len(durations_ms):
        raise ValueError("freqs and durations_ms must have equal length")

    segment_samples = [int(_SAMPLE_RATE * d / 1000) for d in durations_ms]
    n_samples = sum(segment_samples)
    fade_samples = min(n_samples // 4, int(_SAMPLE_RATE * 0.015))

    frames: list = []
    seg_start = 0
    for seg_idx, (freq, seg_n) in enumerate(zip(freqs, segment_samples)):
        for i in range(seg_n):
            global_i = seg_start + i
            t = global_i / _SAMPLE_RATE
            env = 1.0
            if global_i < fade_samples:
                env = global_i / fade_samples
            elif global_i > n_samples - fade_samples:
                env = (n_samples - global_i) / fade_samples
            sample = int(volume * _MAX_SAMPLE * env * math.sin(2 * math.pi * freq * t))
            frames.append(struct.pack("<h", sample))
        seg_start += seg_n

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(b"".join(frames))


def _ensure_sound_files() -> None:
    """Generate WAV files if they don't exist."""
    files = {
        "key.wav": lambda p: _generate_tone(p, [880.0], [35], 0.25),
        "error.wav": lambda p: _generate_tone(p, [200.0], [120], 0.35),
        "success.wav": lambda p: _generate_tone(p, [660.0, 880.0], [80, 120], 0.3),
    }
    for filename, gen in files.items():
        path = SOUNDS_DIR / filename
        if not path.exists():
            try:
                gen(path)
            except Exception as e:
                logger.warning(f"Failed to generate sound {filename}: {e}")


class SoundManager(QObject):
    """Plays key/error/success sounds via Qt's QSoundEffect."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._key_sound: Optional[QSoundEffect] = None
        self._error_sound: Optional[QSoundEffect] = None
        self._success_sound: Optional[QSoundEffect] = None
        self.enabled = True
        self.key_enabled = True
        self.error_enabled = True
        self._volume = 0.5
        self._init_sounds()

    def _init_sounds(self):
        if not _HAS_QTMULTIMEDIA:
            return
        try:
            _ensure_sound_files()
            self._key_sound = self._make_sound("key.wav")
            self._error_sound = self._make_sound("error.wav")
            self._success_sound = self._make_sound("success.wav")
        except Exception as e:
            logger.warning(f"Sound initialization failed: {e}")
            self._key_sound = None
            self._error_sound = None
            self._success_sound = None

    def _make_sound(self, filename: str) -> Optional[QSoundEffect]:
        if not _HAS_QTMULTIMEDIA:
            return None
        path = SOUNDS_DIR / filename
        if not path.exists():
            return None
        try:
            snd = QSoundEffect(self)
            snd.setSource(QUrl.fromLocalFile(str(path)))
            snd.setVolume(self._volume)
            return snd
        except Exception as e:
            logger.warning(f"Failed to create sound {filename}: {e}")
            return None

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        for snd in (self._key_sound, self._error_sound, self._success_sound):
            if snd is not None:
                snd.setVolume(self._volume)

    def play_key(self) -> None:
        if not self.enabled or not self.key_enabled:
            return
        self._play(self._key_sound)

    def play_error(self) -> None:
        if not self.enabled or not self.error_enabled:
            return
        self._play(self._error_sound)

    def play_success(self) -> None:
        if not self.enabled:
            return
        self._play(self._success_sound)

    @staticmethod
    def _play(sound: Optional[QSoundEffect]):
        if sound is None:
            return
        try:
            if sound.isPlaying():
                sound.stop()
            sound.play()
        except Exception as e:
            logger.warning(f"Sound playback failed: {e}")
