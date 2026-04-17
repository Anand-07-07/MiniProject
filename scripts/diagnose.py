#!/usr/bin/env python
"""Diagnostic script to check if the app can open links and detect issues."""
from pathlib import Path
import sys
import webbrowser
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.song_recommender import SongRecommender


def check_browser_available():
    """Check if a web browser is available."""
    print("🔍 Checking web browser availability...")
    if not webbrowser._browsers:
        print("   ⚠ WARNING: No web browser detected!")
        print("   Install Chrome, Firefox, Edge, or Safari.")
        return False
    else:
        print(f"   ✓ Browser available: {list(webbrowser._browsers.keys())}")
        return True


def check_catalogue():
    """Check if song catalogue is valid."""
    print("\n🔍 Checking song catalogue...")
    catalogue_path = PROJECT_ROOT / "data" / "hindi_songs.json"
    
    if not catalogue_path.exists():
        print(f"   ✗ Catalogue not found at {catalogue_path}")
        return False
    
    try:
        with open(catalogue_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("   ✗ Catalogue is not a list!")
            return False
        
        print(f"   ✓ Catalogue loaded: {len(data)} songs")
        
        # Check for URLs
        songs_with_urls = sum(1 for song in data if song.get('urls'))
        print(f"   ✓ Songs with URLs: {songs_with_urls}/{len(data)}")
        
        # Check emotions
        emotions = set(song['emotion'].lower() for song in data)
        print(f"   ✓ Emotions: {', '.join(sorted(emotions))}")
        
        return True
    except Exception as e:
        print(f"   ✗ Error loading catalogue: {e}")
        return False


def check_recommender():
    """Check if song recommender works."""
    print("\n🔍 Checking song recommender...")
    try:
        catalogue_path = PROJECT_ROOT / "data" / "hindi_songs.json"
        recommender = SongRecommender(catalogue_path)
        
        emotions = recommender.emotions()
        print(f"   ✓ Emotions available: {', '.join(emotions)}")
        
        # Test a recommendation
        songs = recommender.recommend("happy", limit=3)
        print(f"   ✓ Sample recommendations for 'happy': {[s.title for s in songs]}")
        
        # Check if songs have URLs
        songs_with_urls = sum(1 for s in songs if s.urls)
        print(f"   ✓ Songs with URLs: {songs_with_urls}/3")
        
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def test_url_opening():
    """Test if we can open a URL."""
    print("\n🔍 Testing URL opening...")
    
    # Get a sample URL from catalogue
    try:
        catalogue_path = PROJECT_ROOT / "data" / "hindi_songs.json"
        recommender = SongRecommender(catalogue_path)
        songs = recommender.recommend("happy", limit=1)
        
        if not songs or not songs[0].urls:
            print("   ✗ No songs with URLs available")
            return False
        
        song = songs[0]
        url = list(song.urls.values())[0]
        provider = list(song.urls.keys())[0]
        
        print(f"   📍 Testing: {song.title} on {provider}")
        print(f"   📍 URL: {url}")
        print(f"   ℹ Try opening this URL manually in your browser to verify it works")
        
        # Don't actually open it, just show what would happen
        print(f"   ℹ App would open: webbrowser.open('{url}')")
        
        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def main():
    """Run all diagnostics."""
    print("=" * 60)
    print("Hindi Music Recommender - Diagnostic Report")
    print("=" * 60)
    
    results = []
    results.append(("Browser Available", check_browser_available()))
    results.append(("Catalogue Valid", check_catalogue()))
    results.append(("Recommender Works", check_recommender()))
    results.append(("URL Available", test_url_opening()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_ok = True
    for check, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check:.<40} {status}")
        if not passed:
            all_ok = False
    
    print("=" * 60)
    
    if all_ok:
        print("\n✓ All checks passed! Your setup looks good.")
        print("\nTo run the app:")
        print("  python -m src.cli webcam --duration 5")
        print("\nIf links don't open automatically, use:")
        print("  python -m src.cli webcam --duration 5 --no-auto-play")
        print("  Then manually open the Spotify/YouTube URLs shown on screen.")
    else:
        print("\n✗ Some checks failed. See TROUBLESHOOTING.md for help.")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
