# Quick Start Guide

## ⚡ Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Check Your Setup (Optional but Recommended)
```bash
python scripts/diagnose.py
```
This will verify that:
- ✓ Your browser is available
- ✓ Song data is loaded correctly
- ✓ Everything is ready to run

### Step 3: Run the App

**With automatic link opening** (default):
```bash
python -m src.cli webcam --duration 5
```

**Or with manual link opening**:
```bash
python -m src.cli webcam --duration 5 --no-auto-play
```

---

## 📸 What Happens

1. **Webcam windows opens** - Shows your face
2. **Emotion detected** - App simulates detecting your emotion (happy, sad, etc.)
3. **Songs recommended** - Shows 5 Indian songs for that emotion
4. **Links appear** - Spotify and YouTube links are displayed
5. **Browser opens** - One song link opens in your browser automatically (or show manually)
6. **Click Play** - Click "Play" in Spotify/YouTube to listen

---

## 🆘 If Links Don't Open

### Option 1: Use Manual Mode
```bash
python -m src.cli webcam --duration 5 --no-auto-play
```
Then copy the Spotify/YouTube URLs from the output and paste them in your browser.

### Option 2: Check Browser
```bash
python scripts/diagnose.py
```
Make sure it shows your browser is available.

### Option 3: More Details
See **TROUBLESHOOTING.md** for detailed solutions.

---

## 📝 Other Options

```bash
# Show the webcam feed while detecting
python -m src.cli webcam --duration 5 --show-feed

# Get more detailed output (debug mode)
python -m src.cli --verbose webcam --duration 5

# Detect emotion from an image instead
python -m src.cli image your_photo.jpg

# Get 10 recommendations instead of 5
python -m src.cli webcam --duration 5 --limit 10

# Lower confidence threshold (more suggestions)
python -m src.cli webcam --duration 5 --min-confidence 0.2
```

---

## 🎵 Important: How Music Plays

**The app opens Spotify/YouTube links in your browser.**

The music DOES NOT play inside the app. You must:
1. Let (or manually open) the Spotify/YouTube link
2. Click "Play" on the Spotify/YouTube page
3. The music streams through Spotify/YouTube

This is the intended design - your browser handles the music playback.

---

## ✅ Expected Output

```
============================================================
✓ Emotion detected: Happy (85% confidence)
============================================================
1. Zinda — Siddharth Mahadevan [Happy]
   Tags: motivational, rock, energetic
   Links:
      • Spotify: https://open.spotify.com/track/7vZ...
      • YouTube: https://www.youtube.com/watch?v...
============================================================

→ Opening first recommendation...
✓ Opened: Zinda on Spotify
```

---

## 🐛 Troubleshooting Quick Links

- **Links not opening?** → Run with `--no-auto-play` and open manually
- **Music not playing?** → Make sure to click "Play" on Spotify/YouTube
- **No emotion detected?** → Try better lighting or use `--image` mode
- **Want debugging info?** → Use `--verbose` flag
- **More help needed?** → See TROUBLESHOOTING.md

---

## 📦 What's Included

```
data/
  └─ hindi_songs.json          # 30+ curated Hindi songs
src/
  ├─ app.py                     # Main application logic (FIXED)
  ├─ cli.py                     # Command-line interface
  ├─ emotion_detector.py        # Face analysis
  └─ song_recommender.py        # Recommendation engine
scripts/
  ├─ run_demo.py               # Demo script
  └─ diagnose.py               # New diagnostic tool
TROUBLESHOOTING.md              # Detailed help (NEW)
FIXES_APPLIED.md                # What was fixed (NEW)
```

---

**Happy listening! 🎵**
