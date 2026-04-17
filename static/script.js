const startButton = document.getElementById('startButton');
const videoPreview = document.getElementById('videoPreview');
const videoOverlay = document.getElementById('videoOverlay');
const cameraPlaceholder = document.getElementById('cameraPlaceholder');
const inputStatus = document.getElementById('inputStatus');
const fallbackCard = document.getElementById('fallbackCard');
const loadingLayer = document.getElementById('loadingLayer');
const resultSummary = document.getElementById('resultSummary');
const songResults = document.getElementById('songResults');

let currentStream = null;

function setStatus(message, type = 'secondary') {
  inputStatus.textContent = message;
  inputStatus.className = `mt-3 text-${type}`;
}

function showFallback(message) {
  fallbackCard.classList.remove('d-none');
  setStatus(message, 'warning');
}

function showVideoOverlay(enabled) {
  videoOverlay.classList.toggle('d-none', !enabled);
  cameraPlaceholder.classList.toggle('d-none', enabled);
}

function showLoading(enabled) {
  loadingLayer.classList.toggle('d-none', !enabled);
  startButton.disabled = enabled;
}

function clearResults() {
  resultSummary.textContent = '';
  songResults.innerHTML = '';
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, string) {
    for (let i = 0; i < string.length; i += 1) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  function floatTo16BitPCM(output, offset, input) {
    for (let i = 0; i < input.length; i += 1, offset += 2) {
      const s = Math.max(-1, Math.min(1, input[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
  }

  writeString(0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, samples.length * 2, true);
  floatTo16BitPCM(view, 44, samples);

  return new Blob([view], { type: 'audio/wav' });
}

function flattenBuffers(buffers) {
  const length = buffers.reduce((acc, buffer) => acc + buffer.length, 0);
  const result = new Float32Array(length);
  let offset = 0;
  buffers.forEach((buffer) => {
    result.set(buffer, offset);
    offset += buffer.length;
  });
  return result;
}

function captureSnapshot() {
  const canvas = document.createElement('canvas');
  canvas.width = videoPreview.videoWidth || 640;
  canvas.height = videoPreview.videoHeight || 480;
  const context = canvas.getContext('2d');
  if (!context) {
    return null;
  }
  context.drawImage(videoPreview, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/png');
}

async function recordAudio(stream, durationSeconds = 4) {
  if (!window.AudioContext && !window.webkitAudioContext) {
    return null;
  }

  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(stream);
  const recorder = audioContext.createScriptProcessor(4096, 1, 1);
  const buffers = [];

  recorder.onaudioprocess = (event) => {
    const channelData = event.inputBuffer.getChannelData(0);
    buffers.push(new Float32Array(channelData));
  };

  source.connect(recorder);
  recorder.connect(audioContext.destination);

  await new Promise((resolve) => setTimeout(resolve, durationSeconds * 1000));

  source.disconnect();
  recorder.disconnect();
  await audioContext.close();

  const samples = flattenBuffers(buffers);
  const wavBlob = encodeWav(samples, audioContext.sampleRate || 22050);
  return wavBlob;
}

async function captureMedia() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error('Camera and microphone are not supported in this browser.');
  }

  const constraints = { video: { width: { ideal: 640 }, height: { ideal: 480 } }, audio: true };
  return navigator.mediaDevices.getUserMedia(constraints);
}

function toDataURL(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function analyzeMood(photoData, audioData) {
  const response = await fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ photo: photoData, audio: audioData }),
  });
  if (!response.ok) {
    throw new Error('Server analysis failed');
  }
  return response.json();
}

function buildSongHtml(song) {
  const embedded = song.youtubeEmbedId
    ? `<iframe src="https://www.youtube.com/embed/${song.youtubeEmbedId}?rel=0" allowfullscreen title="YouTube player"></iframe>`
    : '<div class="text-muted">No YouTube preview available.</div>';

  const spotifyButton = song.spotify
    ? `<a href="${song.spotify}" target="_blank" rel="noreferrer" class="btn btn-sm btn-outline-success">Open on Spotify</a>`
    : '';

  const youtubeButton = song.youtubeUrl
    ? `<a href="${song.youtubeUrl}" target="_blank" rel="noreferrer" class="btn btn-sm btn-outline-danger">Watch on YouTube</a>`
    : '';

  return `
    <div class="card song-card">
      <div class="card-body">
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
          <div>
            <h5>${song.title}</h5>
            <p class="mb-1 text-muted">${song.artist}</p>
            <span class="badge bg-primary">Emotion: ${song.emotion}</span>
          </div>
          <div class="d-flex gap-2 flex-wrap">${spotifyButton}${youtubeButton}</div>
        </div>
        ${embedded}
      </div>
    </div>
  `;
}

async function stopStream(stream) {
  if (!stream) {
    return;
  }
  stream.getTracks().forEach((track) => track.stop());
  videoPreview.srcObject = null;
  cameraPlaceholder.classList.remove('d-none');
}

async function runDetection() {
  clearResults();
  showLoading(true);
  showVideoOverlay(false);
  resultSummary.textContent = 'Preparing camera and microphone...';
  fallbackCard.classList.add('d-none');

  try {
    currentStream = await captureMedia();
    videoPreview.srcObject = currentStream;
    videoPreview.classList.remove('d-none');
    cameraPlaceholder.classList.add('d-none');
    await new Promise((resolve) => {
      const timeout = setTimeout(resolve, 3000);
      videoPreview.onloadeddata = () => {
        clearTimeout(timeout);
        resolve();
      };
    });
    await videoPreview.play();
    showVideoOverlay(true);
    setStatus('Live feed active. Capturing audio and snapshot...', 'success');

    const audioBlob = await recordAudio(currentStream, 4);
    const photoData = captureSnapshot();
    if (!photoData && !audioBlob) {
      throw new Error('Unable to capture any inputs from your device.');
    }

    setStatus('Sending data to the server for emotion detection...', 'info');
    const audioData = audioBlob ? await toDataURL(audioBlob) : null;
    const result = await analyzeMood(photoData, audioData);

    const details = [];
    if (result.facePrediction) {
      details.push(`Face: ${result.facePrediction.label}`);
    }
    if (result.voicePrediction) {
      details.push(`Voice: ${result.voicePrediction.label}`);
    }
    const summary = `Final emotion: <strong>${result.emotion}</strong> <small class="text-muted">(source: ${result.source})</small>`;
    resultSummary.innerHTML = `${summary}${details.length ? `<div class="text-muted small mt-2">${details.join(' · ')}</div>` : ''}`;
    songResults.innerHTML = result.songs.map(buildSongHtml).join('');

    if (!result.songs.length) {
      songResults.innerHTML = '<div class="alert alert-warning">No songs were found for the detected emotion.</div>';
    }

    setStatus('Detection complete. Enjoy your curated playlist!', 'success');
  } catch (error) {
    console.error(error);
    showFallback('Unable to access camera or microphone. Please allow permissions or use a compatible device.');
    resultSummary.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
  } finally {
    showLoading(false);
    showVideoOverlay(false);
    await stopStream(currentStream);
    cameraPlaceholder.classList.remove('d-none');
    currentStream = null;
  }
}

startButton.addEventListener('click', runDetection);
