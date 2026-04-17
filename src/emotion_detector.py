"""Emotion detection utilities (webcam capture with simulated emotion detection).

This module captures frames from a webcam (via OpenCV) but simulates emotion
detection for demonstration purposes. It applies simple smoothing to
reduce jitter in rapid predictions and exposes lightweight data structures for
upstream consumers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import time
import random

import cv2  # type: ignore
# FER import commented out due to compatibility issues
# from fer.fer import FER  # type: ignore  # FER isn't re-exported at top level in newer releases
import numpy as np


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class EmotionResult:
    """Represents a single emotion prediction."""

    label: str
    score: float
    timestamp: float


class EmotionDetector:
    """Webcam capture with simulated emotion detection for demonstration purposes."""

    # Available emotions for mock detection
    EMOTIONS = ["happy", "sad", "angry", "surprise", "fear", "neutral", "disgust"]

    def __init__(
        self,
        camera_index: int = 0,
        smoothing_window: int = 5,
        min_confidence: float = 0.25,
        detector_kwargs: Optional[Dict[str, object]] = None,
    ) -> None:
        """Initialise the emotion detector.

        Args:
            camera_index: Webcam index passed to ``cv2.VideoCapture``.
            smoothing_window: Number of recent predictions considered when
                determining the dominant emotion during streaming capture.
            min_confidence: Minimum probability required for a prediction to be
                considered valid.
            detector_kwargs: Optional keyword arguments (ignored in mock).
        """
        if smoothing_window < 1:
            raise ValueError("smoothing_window must be >= 1")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

        self.camera_index = camera_index
        self.smoothing_window = smoothing_window
        self.min_confidence = min_confidence
        self.face_cascade = self._load_face_cascade()
        self.detector = None
        self._recent: List[EmotionResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detect_from_image(self, image_path: str) -> Optional[EmotionResult]:
        """Process the provided image and return a simulated dominant emotion.

        Args:
            image_path: Path to an image file on disk.

        Returns:
            A simulated ``EmotionResult`` with random emotion and confidence.
        """
        LOGGER.debug("Loading image at %s", image_path)
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Unable to read image at '{image_path}'")

        faces = self._detect_faces(image)
        if not faces:
            LOGGER.warning("No face detected in image at %s", image_path)
            return None

        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the image briefly to show face detection.
        cv2.imshow("Processing Image", image)
        cv2.waitKey(1000)  # Show for 1 second
        cv2.destroyAllWindows()

        return self._predict_single_frame(image)

    def capture_emotion(
        self,
        duration_seconds: float = 5.0,
        display_window: bool = False,
    ) -> Optional[EmotionResult]:
        """Capture webcam frames for the provided duration and return a simulated dominant emotion.

        Args:
            duration_seconds: Number of seconds to capture frames.
            display_window: If ``True``, show the webcam feed with simulated emotion label overlay.

        Returns:
            A simulated ``EmotionResult`` with random emotion detection.
        """
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                "Unable to access webcam. Confirm that a camera is connected and not in use."
            )

        start = time.time()
        frame_count = 0
        try:
            while time.time() - start < duration_seconds:
                ret, frame = cap.read()
                if not ret:
                    LOGGER.warning("Failed to read frame from webcam.")
                    time.sleep(0.1)
                    continue

                frame_count += 1

                faces = self._detect_faces(frame)
                if not faces:
                    LOGGER.debug("No face detected in webcam frame.")
                    if display_window:
                        frame_to_show = frame.copy()
                        cv2.putText(
                            frame_to_show,
                            "No face detected",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            2,
                            cv2.LINE_AA,
                        )
                        cv2.imshow("Emotion Detection", frame_to_show)
                        if cv2.waitKey(1) & 0xFF == 27:
                            break
                    continue

                result = self._predict_single_frame(frame, faces[0])
                if result is not None:
                    self._append_result(result)

                if display_window:
                    frame_to_show = frame.copy()
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame_to_show, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    if result is not None:
                        cv2.putText(
                            frame_to_show,
                            f"Detected: {result.label} ({result.score:.0%})",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),
                            2,
                            cv2.LINE_AA,
                        )
                        cv2.putText(
                            frame_to_show,
                            f"Frame: {frame_count}",
                            (10, 70),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )
                    cv2.imshow("Emotion Detection", frame_to_show)
                    if cv2.waitKey(1) & 0xFF == 27:
                        break
        finally:
            cap.release()
            if display_window:
                cv2.destroyAllWindows()

        LOGGER.info("Captured %d frames from webcam", frame_count)
        return self._aggregate_results()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _predict_mock_emotion(self) -> Optional[EmotionResult]:
        """Return a simulated emotion prediction."""
        # Randomly select an emotion with a random confidence score
        emotion = random.choice(self.EMOTIONS)
        score = random.uniform(self.min_confidence, 0.95)  # Ensure above min_confidence
        
        LOGGER.debug("Simulated emotion detection: %s with confidence %.2f", emotion, score)
        return EmotionResult(label=emotion, score=score, timestamp=time.time())

    def _predict_single_frame(self, frame, face_box=None) -> Optional[EmotionResult]:
        """Mock single frame prediction based on the detected face region."""
        if frame is None:
            return None
        if face_box is not None:
            x, y, w, h = face_box
            face_region = frame[y : y + h, x : x + w]
            if face_region.size == 0:
                return self._predict_mock_emotion()
        return self._predict_mock_emotion()

    def _load_face_cascade(self) -> cv2.CascadeClassifier:
        """Load a Haar cascade classifier for face detection."""
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
            if face_cascade.empty():
                LOGGER.warning(
                    "Unable to load Haar cascade; face detection will be unavailable."
                )
        return face_cascade

    def _detect_faces(self, frame) -> List[tuple[int, int, int, int]]:
        """Detect faces within a frame and return bounding boxes."""
        if self.face_cascade.empty():
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )
        return [tuple(face) for face in faces]

    def _append_result(self, result: EmotionResult) -> None:
        self._recent.append(result)
        if len(self._recent) > self.smoothing_window:
            self._recent.pop(0)

    def _aggregate_results(self) -> Optional[EmotionResult]:
        if not self._recent:
            return None

        # Vote by averaging scores for each label within the smoothing window.
        aggregated: Dict[str, List[EmotionResult]] = {}
        for res in self._recent:
            aggregated.setdefault(res.label, []).append(res)

        # Choose the label with the highest mean confidence; break ties by recency.
        best_label = max(
            aggregated.items(),
            key=lambda kv: (sum(r.score for r in kv[1]) / len(kv[1]), kv[1][-1].timestamp),
        )[0]

        recent_for_label = aggregated[best_label]
        best_result = max(recent_for_label, key=lambda r: r.score)
        LOGGER.info("Dominant emotion detected (simulated): %s (%.1f%%)", best_result.label, best_result.score * 100)

        # Clear the window once aggregated to avoid stale predictions next call.
        self._recent.clear()
        return best_result


__all__ = ["EmotionDetector", "EmotionResult"]
