"""Hindi song recommendation engine based on detected emotions."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import json
import logging
import random
import re
from urllib.parse import parse_qs, urlparse

import requests


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class Song:
    """Metadata for a single song in the catalogue."""

    title: str
    artist: str
    emotion: str
    language: str
    tags: List[str]
    urls: Dict[str, str]


class SongRecommender:
    """Loads a curated list of Hindi songs and selects tracks by emotion."""

    def __init__(
        self,
        catalogue_path: Path,
        validate_urls: bool = False,
        youtube_api_key: Optional[str] = None,
        spotify_access_token: Optional[str] = None,
    ) -> None:
        self.catalogue_path = Path(catalogue_path)
        if not self.catalogue_path.exists():
            raise FileNotFoundError(
                f"Song catalogue not found at '{self.catalogue_path}'. Did you run the setup instructions?"
            )
        self.validate_urls = validate_urls
        self.youtube_api_key = youtube_api_key
        self.spotify_access_token = spotify_access_token
        self._songs: List[Song] = self._load_catalogue()
        if not self._songs:
            raise ValueError("Song catalogue is empty. Populate the JSON file with at least one entry.")
        if self.validate_urls:
            self._validate_catalogue_urls()

    def emotions(self) -> List[str]:
        """Return the list of available emotion labels (case-insensitive)."""
        return sorted({song.emotion for song in self._songs})

    def recommend(self, emotion: str, limit: int = 5, include_related: bool = True) -> List[Song]:
        """Return up to ``limit`` songs for the given emotion label.

        Args:
            emotion: Emotion name from the detector (case-insensitive).
            limit: Maximum number of songs to return.
            include_related: If ``True`` and fewer than ``limit`` exact matches
                are available, supplement with songs sharing at least one tag with
                the requested emotion cluster.
        """
        if limit < 1:
            raise ValueError("limit must be >= 1")
        emotion_norm = emotion.strip().lower()
        if not emotion_norm:
            raise ValueError("emotion must be a non-empty string")

        # Find exact matches for the requested emotion.
        exact_matches = [song for song in self._songs if song.emotion == emotion_norm]

        # If include_related is False, or we have enough exact matches, return a random
        # selection (without replacement) from exact matches up to the requested limit.
        if len(exact_matches) >= limit or not include_related:
            LOGGER.debug("Found %d exact songs for emotion '%s'", len(exact_matches), emotion_norm)
            # Use random.sample to vary results between calls; if fewer songs than
            # limit are available, sample will return all of them.
            k = min(limit, len(exact_matches))
            return random.sample(exact_matches, k)

        # Collect related songs by shared tags (e.g., 'upbeat', 'soothing') and
        # pick randomly from those to fill the remainder while preferring exact matches.
        related_tags = _collect_tags(exact_matches)
        related_candidates = [
            song
            for song in self._songs
            if song.emotion != emotion_norm and song.tags and related_tags.intersection(song.tags)
        ]
        LOGGER.debug(
            "Augmenting %d exact matches with %d related candidates for emotion '%s'",
            len(exact_matches),
            len(related_candidates),
            emotion_norm,
        )

        # Start with a randomized ordering of exact matches, then randomly choose
        # enough related candidates (without replacement) to reach the limit.
        results: List[Song] = []
        if exact_matches:
            # Shuffle exact matches for variability
            results = random.sample(exact_matches, k=len(exact_matches))

        remaining = limit - len(results)
        if remaining > 0 and related_candidates:
            take = min(remaining, len(related_candidates))
            results.extend(random.sample(related_candidates, k=take))

        return results

    def choose_random_song_and_platform(self, emotion: str) -> tuple[Song, str, str]:
        """Choose a random song for the given emotion and a random platform URL.

        Returns a tuple of (Song, platform_name, url). Raises ValueError when the
        emotion is invalid or when no songs match.
        """
        emotion_norm = emotion.strip().lower()
        if not emotion_norm:
            raise ValueError("emotion must be a non-empty string")

        matches = [song for song in self._songs if song.emotion == emotion_norm]
        if not matches:
            raise ValueError(f"No songs found for emotion '{emotion_norm}'")

        # Choose a random song and then a random available platform (youtube, spotify, ...)
        song = random.choice(matches)
        if not song.urls:
            raise ValueError(f"Song '{song.title}' has no available URLs")

        platform = random.choice(list(song.urls.keys()))
        url = song.urls[platform]
        return song, platform, url

    def _load_catalogue(self) -> List[Song]:
        with self.catalogue_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        if not isinstance(payload, list):
            raise ValueError("Catalogue JSON must be a list of song objects.")

        songs: List[Song] = []
        for idx, entry in enumerate(payload):
            try:
                song = Song(
                    title=entry["title"].strip(),
                    artist=entry["artist"].strip(),
                    emotion=entry["emotion"].strip().lower(),
                    language=entry.get("language", "Hindi").strip(),
                    tags=[t.strip().lower() for t in entry.get("tags", []) if t.strip()],
                    urls=_normalize_urls({k: v for k, v in entry.get("urls", {}).items() if v}),
                )
            except KeyError as exc:
                raise ValueError(f"Missing key {exc!r} in catalogue entry {idx}") from exc

            if not song.title or not song.artist:
                raise ValueError(f"Catalogue entry {idx} is missing title/artist text")
            if not song.emotion:
                raise ValueError(f"Catalogue entry {idx} has empty emotion")

            songs.append(song)
        LOGGER.info("Loaded %d songs from catalogue.", len(songs))
        return songs

    def _validate_catalogue_urls(self) -> None:
        if not self.validate_urls:
            return

        if not self.youtube_api_key and not self.spotify_access_token:
            LOGGER.warning(
                "Link validation requested, but no YouTube or Spotify credentials were provided."
            )
            return

        for song in self._songs:
            for platform, url_value in song.urls.items():
                if platform == "youtube":
                    if self.youtube_api_key is None:
                        continue
                    video_id = _extract_youtube_video_id(url_value)
                    if video_id is None or not _validate_youtube_video_id(video_id, self.youtube_api_key):
                        LOGGER.warning("Invalid YouTube link for '%s': %s", song.title, url_value)
                elif platform == "spotify":
                    if self.spotify_access_token is None:
                        continue
                    track_id = _extract_spotify_track_id(url_value)
                    if track_id is None or not _validate_spotify_track_id(track_id, self.spotify_access_token):
                        LOGGER.warning("Invalid Spotify link for '%s': %s", song.title, url_value)


def _normalize_urls(urls: Dict[str, str]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for platform, raw_value in urls.items():
        if raw_value is None:
            continue
        value = str(raw_value).strip()
        if not value:
            continue

        if platform == "youtube":
            video_id = _extract_youtube_video_id(value)
            normalized[platform] = (
                f"https://www.youtube.com/watch?v={video_id}"
                if video_id
                else value
            )
        elif platform == "spotify":
            track_id = _extract_spotify_track_id(value)
            normalized[platform] = (
                f"https://open.spotify.com/track/{track_id}"
                if track_id
                else value
            )
        else:
            normalized[platform] = value

    return normalized


def _extract_youtube_video_id(source: str) -> Optional[str]:
    source = source.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", source):
        return source

    parsed = urlparse(source)
    host = parsed.netloc.lower()
    path = parsed.path or ""

    if host in {"youtu.be", "www.youtu.be"}:
        return path.lstrip("/")

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if path.startswith("/embed/"):
            parts = path.split("/")
            return parts[2] if len(parts) > 2 else None
        if path.startswith("/v/"):
            parts = path.split("/")
            return parts[2] if len(parts) > 2 else None

    match = re.search(r"(?:v=|youtu\.be/|embed/|/v/)([A-Za-z0-9_-]{11})", source)
    return match.group(1) if match else None


def _extract_spotify_track_id(source: str) -> Optional[str]:
    source = source.strip()
    if re.fullmatch(r"[A-Za-z0-9]{22}", source):
        return source

    parsed = urlparse(source)
    host = parsed.netloc.lower()
    path = parsed.path or ""
    if host.endswith("spotify.com"):
        segments = [segment for segment in path.split("/") if segment]
        if len(segments) >= 2 and segments[0] == "track":
            candidate = segments[1]
            if re.fullmatch(r"[A-Za-z0-9]{22}", candidate):
                return candidate

    if source.startswith("spotify:track:"):
        candidate = source.split(":")[2] if len(source.split(":")) >= 3 else None
        if candidate and re.fullmatch(r"[A-Za-z0-9]{22}", candidate):
            return candidate

    return None


def _validate_youtube_video_id(video_id: str, api_key: str) -> bool:
    try:
        response = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"id": video_id, "key": api_key, "part": "snippet"},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("items"))
    except requests.RequestException as exc:
        LOGGER.warning("YouTube validation request failed for %s: %s", video_id, exc)
        return False


def _validate_spotify_track_id(track_id: str, access_token: str) -> bool:
    try:
        response = requests.get(
            f"https://api.spotify.com/v1/tracks/{track_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException as exc:
        LOGGER.warning("Spotify validation request failed for %s: %s", track_id, exc)
        return False


def _collect_tags(songs: Iterable[Song]) -> set[str]:
    tags: set[str] = set()
    for song in songs:
        tags.update(song.tags)
    return tags


__all__ = ["Song", "SongRecommender"]
