#!/usr/bin/env python3
"""Export a big list of songs from the catalogue showing Spotify links when present."""
from pathlib import Path
import json

CAT = Path(__file__).resolve().parent.parent / "data" / "hindi_songs.json"

def main():
    payload = json.loads(CAT.read_text(encoding="utf-8"))
    out = []
    for entry in payload:
        title = entry.get("title", "<unknown>")
        artist = entry.get("artist", "<unknown>")
        emotion = entry.get("emotion", "<unknown>")
        urls = entry.get("urls", {}) or {}
        spotify = urls.get("spotify")
        out.append((emotion, title, artist, spotify))

    # Sort by emotion then title
    out.sort(key=lambda x: (x[0], x[1]))

    print("Catalogue songs with Spotify links (or note 'MISSING')")
    print("=" * 80)
    count = 0
    for emotion, title, artist, spotify in out:
        count += 1
        spotify_note = spotify if spotify else "MISSING"
        print(f"{count:03d}. [{emotion.title():8}] {title} — {artist}\n       Spotify: {spotify_note}")
    print("=" * 80)
    print(f"Total songs: {len(out)}; with Spotify: {sum(1 for e in out if e[3])}")

if __name__ == '__main__':
    main()
