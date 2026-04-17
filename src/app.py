"""End-to-end workflow combining emotion detection with song recommendations."""
from __future__ import annotations

from pathlib import Path
from typing import Optional
import argparse
import logging
import os
import random
import sys
import webbrowser

from .emotion_detector import EmotionDetector, EmotionResult
from .song_recommender import SongRecommender
from .voice_emotion_detector import VoiceEmotionDetector


LOGGER = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(asctime)s] %(levelname)s: %(message)s")


def _is_url_available(url: str, timeout: float = 3.0) -> bool:
    """Return True if the given URL appears reachable.

    Performs a lightweight HTTP HEAD request. This is more permissive than
    full GET validation to avoid false negatives from timeouts or strict servers.
    """
    try:
        # Use the standard library to avoid adding new dependencies.
        from urllib.request import Request, urlopen
        from urllib.error import URLError, HTTPError

        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})        
        req.get_method = lambda: 'HEAD'
        
        with urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None)
            # Accept 2xx and 3xx responses as valid (redirects are fine)
            if status is not None and (200 <= status < 400):
                LOGGER.debug("URL %s is reachable (status: %s)", url, status)
                return True
            
            LOGGER.debug("URL %s returned HTTP status %s", url, status)
            return False
    except Exception as exc:
        LOGGER.debug("URL availability check failed for %s: %s (will open anyway)", url, exc)
        # Be permissive - if we can't verify, assume it's OK and let the browser handle it
        return True


def _open_first_url(song, preferred_platform: str = "spotify") -> None:
    if not song.urls:
        LOGGER.info("No streaming links available for %s - %s", song.title, song.artist)
        return

    candidates = []
    if preferred_platform == "any":
        available = [name for name in ("spotify", "youtube") if name in song.urls]
        if available:
            selected = random.choice(available)
            candidates.append((selected, song.urls.get(selected)))
            for name in available:
                if name != selected:
                    candidates.append((name, song.urls.get(name)))
    elif preferred_platform == "youtube":
        if "youtube" in song.urls:
            candidates.append(("youtube", song.urls.get("youtube")))
        if "spotify" in song.urls:
            candidates.append(("spotify", song.urls.get("spotify")))
    else:
        if "spotify" in song.urls:
            candidates.append(("spotify", song.urls.get("spotify")))
        if "youtube" in song.urls:
            candidates.append(("youtube", song.urls.get("youtube")))

    for name, url in song.urls.items():
        if name not in ("spotify", "youtube") and url:
            candidates.append((name, url))

    for name, url in candidates:
        if not url:
            continue

        LOGGER.debug("Attempting to open %s link: %s", name, url)
        if not _is_url_available(url):
            LOGGER.warning("Skipping unavailable %s link for '%s': %s", name, song.title, url)
            continue

        try:
            LOGGER.info("Opening %s link for '%s' by %s", name, song.title, song.artist)
            webbrowser.open(url)
            print(f"✓ Opened: {song.title} on {name.title()}")
            return
        except Exception as exc:
            LOGGER.warning("Failed to open %s link: %s", name, exc)
            continue

    LOGGER.error("Could not open any links for %s - %s", song.title, song.artist)
    print(f"✗ Could not open links. Try opening manually:")


def _open_all_urls(song) -> None:
    if not song.urls:
        LOGGER.info("No streaming links available for %s - %s", song.title, song.artist)
        return

    opened_any = False
    for name, url in song.urls.items():
        if not url:
            continue

        LOGGER.debug("Opening %s link: %s", name, url)
        if not _is_url_available(url):
            LOGGER.warning("Skipping unavailable %s link for '%s': %s", name, song.title, url)
            continue

        try:
            webbrowser.open(url)
            opened_any = True
            print(f"✓ Opened: {song.title} on {name.title()}")
        except Exception as exc:
            LOGGER.warning("Failed to open %s link: %s", name, exc)
            continue

    if not opened_any:
        LOGGER.error("Could not open any links for %s - %s", song.title, song.artist)
        print(f"✗ Could not open links. Try opening manually:")


def run_webcam_flow(args: argparse.Namespace) -> None:
    detector = EmotionDetector(
        camera_index=args.camera,
        smoothing_window=args.smoothing,
        min_confidence=args.min_confidence,
    )
    LOGGER.info("Capturing emotion for %.1f seconds", args.duration)
    print(f"📷 Starting webcam capture for {args.duration} seconds...")
    result = detector.capture_emotion(duration_seconds=args.duration, display_window=args.show_feed)
    if result is None:
        LOGGER.warning("No dominant emotion detected. Try again with better lighting or adjust parameters.")
        print("✗ No emotion detected. Try again with better lighting.")
        return
    _present_recommendations(
        result,
        catalogue_path=Path(args.catalogue),
        limit=args.limit,
        auto_play=args.auto_play,
        auto_play_platform=args.auto_play_platform,
        auto_play_all=args.auto_play_all,
    )


def run_image_flow(args: argparse.Namespace) -> None:
    detector = EmotionDetector(min_confidence=args.min_confidence)
    print(f"📷 Processing image: {args.image}")
    result = detector.detect_from_image(args.image)
    if result is None:
        LOGGER.warning("Unable to detect a confident emotion in the supplied image.")
        print("✗ Could not detect emotion in image. Try a different image.")
        return
    _present_recommendations(
        result,
        catalogue_path=Path(args.catalogue),
        limit=args.limit,
        auto_play=args.auto_play,
        auto_play_platform=args.auto_play_platform,
        auto_play_all=args.auto_play_all,        validate_links=args.validate_links,    )


def run_audio_flow(args: argparse.Namespace) -> None:
    detector = VoiceEmotionDetector(
        sample_rate=args.sample_rate,
        min_confidence=args.min_confidence,
        device=args.device,
    )
    print(f"🎤 Recording audio for {args.duration} seconds...")
    result = detector.capture_emotion(duration_seconds=args.duration)
    if result is None:
        LOGGER.warning("Unable to infer an emotion from microphone audio.")
        print("✗ Could not detect emotion from audio. Try again with a clearer recording.")
        return
    _present_recommendations(
        result,
        catalogue_path=Path(args.catalogue),
        limit=args.limit,
        auto_play=args.auto_play,
        auto_play_platform=args.auto_play_platform,
        auto_play_all=args.auto_play_all,
        validate_links=args.validate_links,
    )


def _present_recommendations(
    emotion: EmotionResult,
    catalogue_path: Path,
    limit: int,
    auto_play: bool,
    auto_play_platform: str = "spotify",
    auto_play_all: bool = False,
    validate_links: bool = False,
) -> None:
    recommender = SongRecommender(
        catalogue_path,
        validate_urls=validate_links,
        youtube_api_key=os.environ.get("YOUTUBE_API_KEY"),
        spotify_access_token=os.environ.get("SPOTIFY_ACCESS_TOKEN"),
    )
    songs = recommender.recommend(emotion.label, limit=limit)
    if not songs:
        LOGGER.warning("No songs available for emotion '%s'", emotion.label)
        return

    ascii_bar = "=" * 60
    print(ascii_bar)
    print(f"✓ Emotion detected: {emotion.label.title()} ({emotion.score:.0%} confidence)")
    print(ascii_bar)
    for idx, song in enumerate(songs, start=1):
        print(f"{idx}. {song.title} — {song.artist} [{song.emotion.title()}]")
        if song.tags:
            print(f"   Tags: {', '.join(song.tags)}")
        if song.urls:
            print("   Links:")
            for name, url in song.urls.items():
                print(f"      • {name.title()}: {url}")
        else:
            print("   ⚠ No streaming links available")
    print(ascii_bar)

    if auto_play:
        if auto_play_all:
            print("\n→ Opening all available links for the first recommendation...")
            _open_all_urls(songs[0])
        else:
            print("\n→ Opening a random matching song for this emotion...")
            try:
                song, platform, url = recommender.choose_random_song_and_platform(emotion.label)
                _open_first_url(song, preferred_platform=auto_play_platform)
            except ValueError:
                _open_first_url(songs[0], preferred_platform=auto_play_platform)
    else:
        print("\nTo play a song, visit one of the links above.")


def _add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--catalogue",
        default=None,
        help="Path to a custom song catalogue JSON file. If omitted, uses the selected language default.",
    )
    parser.add_argument(
        "--language",
        choices=["hindi", "marathi"],
        default="hindi",
        help="Choose between Hindi and Marathi song catalogues.",
    )
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--min-confidence", type=float, default=0.4)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--auto-play",
        dest="auto_play",
        action="store_true",
        help="Open the first recommendation in the browser",
    )
    parser.add_argument(
        "--no-auto-play",
        dest="auto_play",
        action="store_false",
        help="Disable automatic opening of the first recommendation",
    )
    parser.add_argument(
        "--auto-play-platform",
        dest="auto_play_platform",
        choices=["spotify", "youtube", "any"],
        default="spotify",
        help="Prefer Spotify, YouTube, or any available provider when auto-playing.",
    )
    parser.add_argument(
        "--auto-play-all",
        dest="auto_play_all",
        action="store_true",
        help="Open all available song links in the browser.",
    )
    parser.add_argument(
        "--validate-links",
        dest="validate_links",
        action="store_true",
        help="Validate YouTube and Spotify links using API credentials when available.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emotion-aware Hindi and Marathi song recommender")
    _add_shared_arguments(parser)
    parser.set_defaults(auto_play=False, auto_play_all=False)

    subparsers = parser.add_subparsers(dest="mode", required=True)

    webcam = subparsers.add_parser("webcam", help="Use the webcam to capture a live emotion")
    _add_shared_arguments(webcam)
    webcam.add_argument("--camera", type=int, default=0)
    webcam.add_argument("--duration", type=float, default=5.0)
    webcam.add_argument("--smoothing", type=int, default=5)
    webcam.add_argument("--show-feed", dest="show_feed", action="store_true", help="Display the webcam feed")
    webcam.add_argument(
        "--no-show-feed",
        dest="show_feed",
        action="store_false",
        help="Run without displaying the webcam feed",
    )
    webcam.set_defaults(show_feed=True)
    webcam.set_defaults(handler=run_webcam_flow)

    image = subparsers.add_parser("image", help="Infer emotion from a still image")
    _add_shared_arguments(image)
    image.add_argument("image")
    image.set_defaults(handler=run_image_flow)

    audio = subparsers.add_parser("audio", help="Use microphone audio to infer emotion")
    _add_shared_arguments(audio)
    audio.add_argument("--duration", type=float, default=5.0)
    audio.add_argument("--sample-rate", type=int, default=22050)
    audio.add_argument(
        "--device",
        type=int,
        default=None,
        help="Optional microphone device index (use the system default if omitted)",
    )
    audio.set_defaults(handler=run_audio_flow)

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)
    
    # Check if browser is available
    if not webbrowser._browsers:
        LOGGER.warning("No default web browser detected. Links may not open automatically.")
        print("⚠ Warning: No web browser detected. Manual link opening may be needed.")

    if args.catalogue is None:
        default_catalogue = Path(__file__).resolve().parent.parent / "data" / f"{args.language}_songs.json"
        args.catalogue = str(default_catalogue)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return

    try:
        handler(args)
    except Exception as exc:
        LOGGER.error("Error during execution: %s", exc, exc_info=True)
        print(f"\n✗ Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
