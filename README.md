# Hindi Emotion-Based Music Recommender

This project serves Hindi music suggestions based on the listener's facial emotion. Capture a live mood from your webcam or analyse a saved photo, then browse a curated playlist tailored to that emotion.

## Features
- Real-time facial emotion detection via webcam or static image analysis.
- Voice-based emotion detection from microphone audio.
- Emotion smoothing to reduce jitter across frames.
- Curated Hindi song catalogue grouped by core emotions (happy, sad, angry, surprise, fear, neutral, disgust).
- Optional auto-open behaviour to launch the top recommendation in your browser.

## Requirements
- Python 3.9 or newer (Windows, macOS, or Linux).
- Functional webcam (for live capture mode) or a portrait image file.
- Internet connection if you want to open streaming links.

See [`requirements.txt`](requirements.txt) for the full dependency list.

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

If you're on macOS/Linux, adjust the activation script accordingly (`source .venv/bin/activate`).

## Running the app
Launch the CLI entry point and choose either the webcam or image workflow.

### Webcam mode (default)
```powershell
python -m src.cli webcam --duration 6
```
- `--duration`: capture window in seconds (default 5).
- Webcam feed now displays automatically. Use `--no-show-feed` to suppress the video window.
- The top recommendation does not auto-play by default. Use `--auto-play` to open it automatically.

### Audio mode
```powershell
python -m src.cli audio --duration 5 --language marathi --auto-play-platform youtube
```
- `--duration`: microphone recording duration in seconds (default 5).
- `--sample-rate`: audio sample rate (default 22050).
- `--device`: optional microphone input device index.
- `--language`: choose `hindi` or `marathi` for the default catalogue.
- `--catalogue`: optional custom JSON path if you want a different song list.
- `--auto-play-platform`: choose `spotify`, `youtube`, or `any`.
- The app infers mood from your voice and recommends matching songs.
- `--validate-links`: optional flag to validate YouTube/Spotify IDs when API credentials are configured.
- Set `YOUTUBE_API_KEY` and/or `SPOTIFY_ACCESS_TOKEN` in your environment to enable validation.

### Image mode
```powershell
python -m src.cli image --image path\to\portrait.jpg
```

Additional flags:
- `--catalogue`: path to a custom song catalogue JSON file. If omitted, the app uses `--language` to select the default catalogue.
- `--language`: choose between `hindi` and `marathi` default song catalogues.
- `--limit`: number of recommendations to display (default 5).
- `--min-confidence`: minimum confidence threshold from the emotion detector (default 0.4).
- `--verbose`: enable debug logging.
- `--auto-play-platform`: choose `spotify`, `youtube`, or `any` when auto-playing links.
- `--auto-play` / `--no-auto-play`: toggle auto-launching the top song (default off).

## How Music Playback Works
After emotion detection, the app opens a **Spotify or YouTube link** in your web browser. Music plays through these streaming services, not within the app.

**Flow:**
1. Webcam captures your face ✓
2. Emotion is detected (happy, sad, angry, etc.) ✓
3. Hindi songs matching that emotion are recommended ✓
4. A Spotify/YouTube link **opens in your browser** ✓
5. **Click "Play" on Spotify/YouTube to listen** ✓

## Troubleshooting
If links are not opening or music is not playing, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

## Project structure
```
project/
├── data/
│   └── hindi_songs.json        # curated song catalogue
├── src/
│   ├── __init__.py
│   ├── emotion_detector.py     # FER + OpenCV wrapper
│   ├── song_recommender.py     # recommendation logic
│   ├── app.py                  # orchestration & CLI handler
│   └── cli.py                  # python -m entry point
├── tests/
│   └── test_recommender.py
├── requirements.txt
└── README.md
```

## Testing
```powershell
pytest
```

The included tests verify that the catalogue loads correctly and that recommendation outputs obey expectations.

## Troubleshooting
- **Webcam access issues**: ensure no other application is using the camera. Try `--camera 1` if you have multiple devices.
- **Low confidence detections**: improve lighting, face the camera, and increase `--duration` or lower `--min-confidence` cautiously.
- **Empty recommendations**: extend `data/hindi_songs.json` with more songs or double-check the emotion labels.

## Project website
A clean, modern project website is available in the `website/` folder:
- `website/index.html`
- `website/styles.css`
- `website/script.js`

Open `website/index.html` in your browser to view the project overview, setup steps, usage examples, and feature details.

## Extending
- Augment the song catalogue with additional metadata (tempo, energy) to refine recommendations.
- Integrate with a streaming service API to auto-play full playlists.
- Deploy as a desktop app using PyInstaller or a web app via Flask/Streamlit.

## Web app
A new Flask web frontend is available at the project root:
- `app.py`
- `templates/index.html`
- `static/style.css`
- `static/script.js`

Run the web app from the project root with:
```powershell
pip install -r requirements.txt
python app.py
```
Then open `http://127.0.0.1:5000` in your browser.
