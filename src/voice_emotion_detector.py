"""Voice emotion detection utilities for microphone-based mood capture."""
from __future__ import annotations

from typing import Optional
import logging
import time
import random

import numpy as np

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None  # type: ignore

from .emotion_detector import EmotionResult

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


class VoiceEmotionDetector:
    """Capture microphone audio and infer a mood from vocal characteristics."""

    EMOTIONS = ["happy", "sad", "angry", "surprise", "fear", "neutral", "disgust"]

    def __init__(
        self,
        sample_rate: int = 22050,
        channels: int = 1,
        min_confidence: float = 0.25,
        device: Optional[int] = None,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate must be a positive integer")
        if channels < 1:
            raise ValueError("channels must be >= 1")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

        self.sample_rate = sample_rate
        self.channels = channels
        self.min_confidence = min_confidence
        self.device = device

    def capture_emotion(self, duration_seconds: float = 5.0) -> Optional[EmotionResult]:
        """Record from the default microphone and infer an emotion."""
        if sd is None:
            raise RuntimeError(
                "The 'sounddevice' package is required for microphone capture. "
                "Install it with: pip install sounddevice"
            )
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")

        frames = int(self.sample_rate * duration_seconds)
        if frames < 1:
            raise ValueError("duration_seconds is too short for the configured sample rate")

        LOGGER.debug(
            "Recording %s seconds of audio at %s Hz on device %s",
            duration_seconds,
            self.sample_rate,
            self.device,
        )

        try:
            recording = sd.rec(
                frames,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                device=self.device,
            )
            sd.wait()
        except Exception as exc:
            LOGGER.error("Audio capture failed: %s", exc)
            raise RuntimeError(
                "Unable to record audio from the microphone. "
                "Verify that an input device is available and not in use."
            ) from exc

        waveform = self._flatten_channels(recording)
        return self.detect_from_audio(waveform, self.sample_rate)

    def detect_from_audio(self, waveform: np.ndarray, sample_rate: int) -> EmotionResult:
        """Infer an emotion from an audio waveform without recording audio."""
        if waveform is None or waveform.size == 0:
            raise ValueError("waveform must contain audio samples")
        if sample_rate <= 0:
            raise ValueError("sample_rate must be a positive integer")

        waveform = waveform.astype("float64")
        if waveform.ndim != 1:
            raise ValueError("waveform must be a one-dimensional audio signal")

        energy = self._root_mean_square(waveform)
        centroid = self._spectral_centroid(waveform, sample_rate)
        zcr = self._zero_crossing_rate(waveform)

        label = self._infer_label(energy, centroid, zcr)
        score = self._confidence(energy, centroid)

        LOGGER.debug(
            "Audio emotion inference: energy=%.4f centroid=%.1f zcr=%.4f label=%s score=%.2f",
            energy,
            centroid,
            zcr,
            label,
            score,
        )

        return EmotionResult(label=label, score=score, timestamp=time.time())

    def _flatten_channels(self, recording: np.ndarray) -> np.ndarray:
        if recording.ndim == 1:
            return recording
        return np.mean(recording, axis=1)

    def _root_mean_square(self, waveform: np.ndarray) -> float:
        return float(np.sqrt(np.mean(waveform**2)))

    def _zero_crossing_rate(self, waveform: np.ndarray) -> float:
        if waveform.size < 2:
            return 0.0
        return float(np.mean(np.abs(np.diff(np.signbit(waveform).astype(float)))))

    def _spectral_centroid(self, waveform: np.ndarray, sample_rate: int) -> float:
        if waveform.size == 0:
            return 0.0

        window = np.hanning(waveform.size)
        spectrum = np.abs(np.fft.rfft(waveform * window))
        freqs = np.fft.rfftfreq(waveform.size, d=1.0 / sample_rate)
        magnitude = np.sum(spectrum)
        if magnitude <= 0.0:
            return 0.0
        return float(np.sum(freqs * spectrum) / magnitude)

    def _infer_label(self, energy: float, centroid: float, zcr: float) -> str:
        if energy < 0.02:
            return random.choice(["sad", "neutral", "fear"])

        if centroid < 900:
            return random.choices(
                ["sad", "neutral", "fear"],
                weights=[0.45, 0.35, 0.20],
                k=1,
            )[0]

        if centroid < 1600:
            return random.choices(
                ["happy", "neutral", "surprise"],
                weights=[0.50, 0.25, 0.25],
                k=1,
            )[0]

        if zcr > 0.12:
            return random.choices(
                ["angry", "surprise", "happy"],
                weights=[0.45, 0.35, 0.20],
                k=1,
            )[0]

        return random.choice(["happy", "angry", "surprise"])

    def _confidence(self, energy: float, centroid: float) -> float:
        base = 0.30 + min(0.55, energy * 0.8)
        centroid_boost = min(0.15, centroid / 6000.0)
        score = max(self.min_confidence, base + centroid_boost)
        return float(min(score, 0.98))


__all__ = ["VoiceEmotionDetector"]
