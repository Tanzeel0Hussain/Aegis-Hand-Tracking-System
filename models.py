"""Explicit model setup; importing this module never downloads anything."""
from pathlib import Path
import os
import tempfile
import time
import urllib.request
import zipfile

DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "models"
MODEL_URLS = {
    "hand_landmarker.task": "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
    "pose_landmarker.task": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
}
MAX_DOWNLOAD_BYTES = 40 * 1024 * 1024


def valid_model(path):
    """Check bundle structure and CRC, not publisher authenticity."""
    try:
        with zipfile.ZipFile(path) as bundle:
            return any(name.endswith(".tflite") for name in bundle.namelist()) and bundle.testzip() is None
    except (OSError, zipfile.BadZipFile, RuntimeError, EOFError):
        return False


def ensure_model(name, directory=DEFAULT_MODEL_DIR, download=False):
    if name not in MODEL_URLS:
        raise ValueError("Unknown model.")
    path = Path(directory).expanduser().resolve() / name
    if valid_model(path):
        return path
    if not download:
        raise RuntimeError(
            f"Model missing or damaged: {path}\n"
            "Run: python FingerCount.py --download-models "
            f'--model-dir "{path.parent}"'
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(3):
        temporary = None
        try:
            request = urllib.request.Request(MODEL_URLS[name], headers={"User-Agent": "Aegis-Tracking/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                expected = response.headers.get("Content-Length")
                expected = int(expected) if expected is not None else None
                if expected is not None and expected > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Model download exceeds size limit.")
                with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".part", delete=False) as output:
                    temporary = Path(output.name)
                    size = 0
                    deadline = time.monotonic() + 120
                    while True:
                        if time.monotonic() > deadline:
                            raise TimeoutError("Model download exceeded two minutes.")
                        block = response.read(64 * 1024)
                        if not block:
                            break
                        size += len(block)
                        if size > MAX_DOWNLOAD_BYTES:
                            raise ValueError("Model download exceeds size limit.")
                        output.write(block)
                if expected is not None and size != expected:
                    raise ValueError("Model download was incomplete.")
            if not valid_model(temporary):
                raise ValueError("Downloaded file is not a valid model bundle.")
            os.replace(temporary, path)
            return path
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            last_error = error
            if attempt < 2:
                time.sleep(attempt + 1)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    raise RuntimeError(f"Could not download {name}. Check your internet connection and retry: {last_error}") from last_error
