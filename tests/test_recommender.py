from pathlib import Path

import pytest

from src.song_recommender import SongRecommender


CATALOGUE = Path(__file__).resolve().parent.parent / "data" / "hindi_songs.json"


@pytest.fixture(scope="module")
def recommender() -> SongRecommender:
    return SongRecommender(CATALOGUE)


def test_catalogue_contains_entries(recommender: SongRecommender) -> None:
    songs = recommender.recommend("happy", limit=10)
    assert songs, "Expected at least one song for 'happy' emotion"


def test_recommend_respects_limit(recommender: SongRecommender) -> None:
    limit = 3
    songs = recommender.recommend("sad", limit=limit)
    assert len(songs) <= limit


def test_recommend_rejects_invalid_input(recommender: SongRecommender) -> None:
    with pytest.raises(ValueError):
        recommender.recommend("   ", limit=1)
    with pytest.raises(ValueError):
        recommender.recommend("happy", limit=0)


def test_choose_random_song_and_platform(recommender: SongRecommender) -> None:
    song, platform, url = recommender.choose_random_song_and_platform("happy")
    # platform must be a key present in the song's urls mapping and url must match
    assert platform in song.urls
    assert url == song.urls[platform]
    assert isinstance(platform, str)
    assert isinstance(url, str)
