# Aegis Hand Tracking System

Local webcam hand and body-pose tracking with a glowing OpenCV HUD. Built with Python and MediaPipe Tasks.

Detect up to two hands, estimate extended fingers, and display a body skeleton. Includes a Python desktop application and a browser demo. Neither is a biometric identity system.

## Browser demo

**[Open Aegis Live](https://tanzeel0hussain.github.io/Cybersecurity-Projects/aegis/)**

The demo is hosted under the existing Cybersecurity portfolio. Its canonical source is this repository's web directory; only static browser files are copied to the hosting repository after verification.

The browser version is in **web/**. Start Camera downloads the pinned MediaPipe JavaScript/WASM and model assets, then requests webcam permission. Select Hands, Full Body, Air Drawing, Color Portal, or Touchless Music. Mode changes restart the camera session cleanly.

- Stop Camera, tab hiding, or leaving the page releases the camera and closes models.
- A late camera-permission response is immediately closed if the session was cancelled.
- Camera frames remain on the device; jsDelivr and Google receive asset requests, not camera uploads.
- Requires HTTPS (or localhost), camera permission, WebAssembly, and a recent browser.
- CPU inference is capped at approximately 15 processing cycles per second to limit workload. Hand/pose inference runs synchronously; actual performance depends on the device.
- Mirror changes the preview only. Handedness labels are model estimates for the original input.
- The same finger-count heuristic and its limitations apply to both versions.

### Download and run the same five modes

1. [Download the project ZIP](https://github.com/Tanzeel0Hussain/Aegis-Hand-Tracking-System/archive/refs/heads/main.zip) and extract it completely.
2. Install Python 3 if it is not already installed. **No pip packages or Node.js are needed for the browser studio.**
3. Windows: double-click **Start-Aegis.bat**. macOS/Linux: open a terminal in the extracted folder and run **python3 launcher.py**.
4. Keep the launcher window open and allow camera permission in the browser. Stop Camera releases the webcam; Ctrl+C closes the local server.

The launcher serves only `web/` on your own computer (127.0.0.1) and opens the browser automatically. Internet is required to load third-party model/JS/WASM assets; this download is **not a fully offline bundle**. If automatic opening fails, copy the printed URL into your browser. macOS users can also run `sh Start-Aegis.command`.

| Mode | Controls |
|---|---|
| Hands | Show one or two palms for landmarks and estimated finger counts |
| Full Body | Step back to keep head, torso, arms, and feet visible; tracks one person |
| Air Drawing | Pinch thumb and index to draw; release to lift the pen. Ink, brush, Undo, Clear, and Save PNG controls are provided |
| Color Portal | Show both hands; separation controls portal size, vertical position changes colors |
| Touchless Music | Start Camera → Enable Sound. Raise the screen-right hand to raise pitch; spread both hands for volume. Choose pentatonic notes or theremin glide, sine/triangle tone, and master volume |

Air drawings stay in the current page while switching modes, but disappear on reload. Save PNG exports only the drawing, matching the mirror setting, with a transparent background. It does not recognize handwriting as text. Drawing is limited to 12,000 points to bound memory. Color Portal is a stylized 2D effect; it does not measure physical depth. Reduced-motion preferences remove automatic rotation.

Touchless Music uses the browser Web Audio API, with no microphone or audio uploads. It starts muted and uses a single oscillator. Missing/crossed hands mute the note; Stop Camera, mode changes and tab hiding close the audio context. A 250 ms audio-clock fade prevents a held tone if tracking stalls. It needs both hands visible and is an experimental instrument, not a calibrated MIDI controller.

### Browser code map

| File | Responsibility |
|---|---|
| `web/index.html` | Accessible studio layout, mode selection, download link |
| `web/style.css` | Responsive appearance |
| `web/app.mjs` | Session lifecycle, UI events, mode wiring |
| `web/detectors.mjs` | Pinned MediaPipe model loading and cleanup |
| `web/tracking.mjs` | Finger geometry, smoothing, skeleton connections |
| `web/render.mjs` | Confidence-gated skeleton rendering |
| `web/modes/air-draw.mjs` | Pinch detection, strokes, undo and drawing rendering |
| `web/modes/gesture-effects.mjs` | Two-hand color portal rendering |
| `web/modes/music.mjs` | Pure gesture-to-note mapping, audio lifecycle and music overlay |
| `launcher.py` | Standard-library local server and browser launcher |
| `web-tests/` | Geometry, drawing, effects and browser lifecycle checks |

Run geometry/mode tests with `node --test web-tests/*.test.mjs`. Browser CI also downloads actual MediaPipe models and uses a synthetic camera. The Python desktop app below is a separate hand/body HUD; the new drawing, portal and music modes belong to the browser studio, available both online and through the download launcher.

The web workflow tests lifecycle behavior, geometry, responsive layouts and real MediaPipe inference using Chromium's synthetic camera. This does not verify real-hand accuracy or every physical camera/browser combination.

## Features

- MediaPipe VIDEO-mode tracking with strictly increasing frame timestamps.
- Hand and optional single-person body-pose inference.
- Finger-count heuristic with short-window smoothing and immediate reset when no hands are detected.
- Hand skeletons, corner brackets, total finger count, model handedness confidence, and measured loop FPS.
- Configurable camera and capture resolution; optional mirror and glow effects.
- Explicit model setup with timeouts, bounded retries, temporary-file cleanup, and atomic replacement.
- Camera and detector cleanup on normal exit, camera failure, inference failure, and Ctrl+C.
- No package installation or camera access during import.

## Installation

Use **Python 3.11 or 3.12** and a fresh virtual environment. The direct dependency versions in requirements.txt are selected for this MediaPipe Tasks API; newer Python versions are not validated here.

### Linux / macOS

~~~bash
git clone https://github.com/Tanzeel0Hussain/Aegis-Hand-Tracking-System.git
cd Aegis-Hand-Tracking-System
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python FingerCount.py --download-models
python FingerCount.py --check
python FingerCount.py
~~~

If Python 3.12 is installed instead, use python3.12 for the virtual-environment command. On Ubuntu, the venv package matching that Python interpreter may need to be installed.

### Windows PowerShell

~~~powershell
git clone https://github.com/Tanzeel0Hussain/Aegis-Hand-Tracking-System.git
cd Aegis-Hand-Tracking-System
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe FingerCount.py --download-models
.\.venv\Scripts\python.exe FingerCount.py --check
.\.venv\Scripts\python.exe FingerCount.py
~~~

The Windows/macOS webcam and GUI paths still require manual hardware validation. CI runs on Linux.

**Install only one OpenCV distribution.** MediaPipe uses opencv-contrib-python, already included in requirements.txt. Installing opencv-python or a headless variant alongside it can cause cv2 conflicts.

## Controls and options

Q, Escape, or the window close button exits. Ctrl+C also releases resources.

| Option | Purpose |
|---|---|
| --camera 1 | Select a different camera |
| --width 640 --height 480 | Request a smaller capture size |
| --no-pose | Disable body inference and skip the pose model |
| --no-glow | Disable the blurred glow effect |
| --no-mirror | Display the original camera orientation |
| --swap-handedness | Explicitly swap model Left/Right labels for your camera setup |
| --smooth 5 | Set smoothing to 5 frames; allowed range 1–60 |
| --model-dir /path/to/models | Use a custom model directory |
| --download-models | Download/repair models and exit without opening the camera |
| --check | Initialize models, run two synthetic blank frames, and exit without a camera/window |

For a lower CPU workload:

~~~bash
python FingerCount.py --no-pose --no-glow --width 640 --height 480
~~~

Requested resolution is a camera preference, not a guarantee; drawing uses the actual returned dimensions. Files in the models directory are located relative to the project by default, not the terminal's current working directory.

## Counting and interpretation

The count compares finger-tip distances to joint distances in image space, with a small palm-relative margin. It tolerates in-plane rotation better than vertical-coordinate checks but can be wrong under occlusion, foreshortening, curled thumbs, or unusual poses. It has not been validated as accurate at every angle.

The total is smoothed; individual hand counts are immediate and can briefly differ from the displayed total. The smoother resets when the number of detected hands changes. Labels are MediaPipe handedness estimates, not persistent hand IDs; verify them with your own camera.

**No physical depth measurement is reported.** MediaPipe's normalized hand z is relative to the wrist; the wrist z value is not a camera-to-hand distance.

In the Python desktop HUD, face landmarks are omitted from drawing only. The browser Full Body mode includes coarse pose face points. The pose model still processes the entire image and may predict face landmarks. This does not anonymize the camera feed.

## Privacy and models

The application performs inference locally and contains no frame upload or recording path. The explicit model-download command contacts Google's official model hosting. Once dependencies and models are present, camera operation requires no application network requests.

Model bundles are checked for ZIP structure and CRC integrity, not cryptographic publisher authenticity. Corrupt or incomplete downloads do not replace the existing file. Third-party MediaPipe models and dependencies retain their upstream terms.

Official references:
- [Hand Landmarker Python guide](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)
- [Hand Landmarker models and output](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
- [Pose Landmarker guide](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)

## Verification

~~~bash
python -m unittest discover -s tests -v
python FingerCount.py --check
~~~

CI checks Python 3.11 and 3.12 dependency installation, dependency consistency, compilation, geometry/smoothing behavior, model-download failure handling, and mocked camera cleanup. It also downloads the real models and runs VIDEO-mode inference and HUD rendering on synthetic blank frames.

**These checks do not establish real webcam tracking accuracy, real-world FPS, or GUI behavior on your laptop.** Validate an open palm, closed fist, both hands, hand disappearance, window close, and camera disconnect in a local session.

## Troubleshooting

- **Missing/damaged model:** rerun --download-models with the same --model-dir.
- **Camera will not open:** allow camera access, close other camera applications, or try --camera 1.
- **Frames stop arriving:** the app exits after a bounded number of failures instead of spinning indefinitely.
- **Missing shared libraries on Linux:** OpenCV needs a desktop GUI environment and system GL/GLib libraries; on Ubuntu these are commonly libgl1 and libglib2.0-0.
- **GUI unavailable over SSH/headless environments:** use --check for camera-free validation; live display requires a graphical desktop.
- **No compatible MediaPipe wheel:** use the documented Python version and a supported platform; do not install packages into the system Python.

## Project files

| File | Responsibility |
|---|---|
| FingerCount.py | CLI, explicit setup, friendly startup errors |
| runtime.py | Camera lifecycle, VIDEO inference, OpenCV HUD |
| tracking.py | Finger heuristic, count smoothing, timestamps |
| models.py | Model paths, validation, atomic downloads |
| requirements.txt | Pinned direct dependencies |
| tests/ | Regression tests |
| .github/workflows/tests.yml | Linux CI and real-model smoke checks |

Maintained by [Tanzeel Hussain](https://github.com/Tanzeel0Hussain).

