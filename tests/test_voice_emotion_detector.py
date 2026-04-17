from __future__ import annotations

import numpy as np

from src.voice_emotion_detector import VoiceEmotionDetector


def test_detect_from_audio_returns_supported_emotion() -> None:
    detector = VoiceEmotionDetector(min_confidence=0.25)
    waveform = np.zeros(22050, dtype="float32")
    result = detector.detect_from_audio(waveform, sample_rate=22050)

    assert result.label in detector.EMOTIONS
    assert 0.25 <= result.score <= 1.0


def test_detect_from_audio_high_energy_signal() -> None:
    detector = VoiceEmotionDetector(min_confidence=0.25)
    time = np.linspace(0, 1, 22050, endpoint=False, dtype="float32")
    waveform = 0.8 * np.sin(2 * np.pi * 300 * time)
    result = detector.detect_from_audio(waveform.astype("float32"), sample_rate=22050)

    assert result.label in detector.EMOTIONS
    assert result.score >= 0.25
