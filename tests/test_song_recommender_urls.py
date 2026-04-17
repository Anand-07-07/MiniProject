from __future__ import annotations

from src.song_recommender import _extract_spotify_track_id, _extract_youtube_video_id, _normalize_urls


def test_extract_youtube_video_id_from_full_url() -> None:
    assert _extract_youtube_video_id("https://www.youtube.com/watch?v=EVmdS0pT1Zs") == "EVmdS0pT1Zs"


def test_extract_spotify_track_id_from_full_url() -> None:
    assert _extract_spotify_track_id("https://open.spotify.com/track/1oS0J3j4s1eUwcomfNUnqW") == "1oS0J3j4s1eUwcomfNUnqW"


def test_normalize_urls_converts_ids_to_full_links() -> None:
    original = {"youtube": "EVmdS0pT1Zs", "spotify": "1oS0J3j4s1eUwcomfNUnqW"}
    normalized = _normalize_urls(original)

    assert normalized["youtube"] == "https://www.youtube.com/watch?v=EVmdS0pT1Zs"
    assert normalized["spotify"] == "https://open.spotify.com/track/1oS0J3j4s1eUwcomfNUnqW"
