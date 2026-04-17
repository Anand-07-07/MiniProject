# Troubleshooting Guide

## Issue 1: "LINKS ARE NOT OPEN"

The application opens Spotify/YouTube links in your web browser. If links are not opening, try these solutions:

### Solution 1: Check if a browser is installed
Make sure you have a web browser installed:
- **Windows**: Edge, Chrome, or Firefox
- **macOS**: Safari, Chrome, or Firefox  
- **Linux**: Firefox or Chromium

To check your default browser:
```bash
python -c "import webbrowser; print(webbrowser._browsers)"
```

### Solution 2: Set a default browser manually
```python
import webbrowser
webbrowser.register('mychrome', None, webbrowser.BackgroundBrowser(r'C:\Program Files\Google\Chrome\Application\chrome.exe'))
```

### Solution 3: Run with verbose logging
This shows what's happening step-by-step:
```bash
python -m src.cli --verbose webcam --duration 5
```

### Solution 4: Manually check if URLs work
Try opening a Spotify URL directly in your browser:
```
https://open.spotify.com/track/7vZz8oJ5qAqB9MghufRK5k
```

---

## Issue 2: "MUSIC ARE NOT PLAYING"

The application opens links to Spotify or YouTube, where the music plays. Music does NOT play inside the application itself.

### Expected behavior:
1. Face detection ✓
2. Emotion is recognized ✓
3. Songs are recommended ✓
4. A Spotify/YouTube link opens in your browser ✓
5. Click "Play" on Spotify/YouTube to listen ✓

### If music is still not playing in Spotify/YouTube:

1. **Check if Spotify/YouTube URLs are working**
   - Copy the URL from the output
   - Paste it in your browser manually
   - If it works, the app is fine—your browser might be blocking popup links

2. **Enable browser popups**
   - Check your browser settings (Chrome, Firefox, Edge typically block popups)
   - Add an exception for localhost or the app

3. **Check your internet connection**
   - Spotify and YouTube require active internet
   - Make sure you're connected

4. **Verify Spotify/YouTube account**
   - Make sure you have a Spotify or YouTube account logged in
   - Premium Spotify is not required to view the page, but may be required to play

---

## Running the app with debugging

```bash
# Install latest packages
pip install -r requirements.txt

# Run with verbose output to see exactly what's happening
python -m src.cli --verbose webcam --duration 5 --show-feed

# Run without auto-play to manually open links
python -m src.cli webcam --duration 5 --no-auto-play
```

---

## Alternative: Use `--no-auto-play` and open links manually

If automatic link opening doesn't work:

```bash
python -m src.cli webcam --duration 5 --no-auto-play
```

This will show you the Spotify/YouTube links. You can then:
1. Copy and paste them into your browser
2. Or click them if your terminal supports link clicking

---

## Still having issues?

1. Check the logs by running with `--verbose`
2. Verify your internet connection
3. Try a different emotion (webcam might detect 'neutral' instead of 'happy')
4. Use `--show-feed` to see what the webcam is capturing
