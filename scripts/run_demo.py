from pathlib import Path
import sys

# Ensure the project root is on sys.path so `src` can be imported when the
# script is executed directly (without setting PYTHONPATH).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.song_recommender import SongRecommender

CATALOG = PROJECT_ROOT / "data" / "hindi_songs.json"


def show(recommender: SongRecommender, emotion: str, limit: int = 3) -> None:
    songs = recommender.recommend(emotion, limit=limit)
    print(f"Emotion: {emotion} -> {[s.title for s in songs]}")


if __name__ == "__main__":
    rec = SongRecommender(CATALOG)
    print("Demo: three consecutive recommendations for 'happy' (limit=3) to show randomness")
    for i in range(3):
        show(rec, "happy", limit=3)
    print("\nDemo: one recommendation for 'sad' (limit=2)")
    show(rec, "sad", limit=2)
