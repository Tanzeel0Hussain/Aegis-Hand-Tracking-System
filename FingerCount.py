"""Aegis entry point. No installation, download, or camera access on import."""
import argparse
from pathlib import Path
import sys

from models import DEFAULT_MODEL_DIR, ensure_model


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Must be a positive integer.")
    return number


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Aegis local webcam hand and pose tracking.")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0).")
    parser.add_argument("--width", type=positive_int, default=1280, help="Requested camera width.")
    parser.add_argument("--height", type=positive_int, default=720, help="Requested camera height.")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--download-models", action="store_true", help="Download/repair models, then exit; no camera access.")
    parser.add_argument("--check", action="store_true", help="Load models and infer two blank frames; no camera or window.")
    parser.add_argument("--no-pose", action="store_true", help="Disable body detection to reduce CPU use.")
    parser.add_argument("--no-glow", action="store_true", help="Disable blurred glow rendering.")
    parser.add_argument("--no-mirror", action="store_true", help="Display the original, unmirrored camera image.")
    parser.add_argument("--swap-handedness", action="store_true", help="Swap model Left/Right labels if your camera setup needs it.")
    parser.add_argument("--smooth", type=positive_int, default=7, help="Finger count smoothing window.")
    parser.add_argument("--max-read-failures", type=positive_int, default=10)
    args = parser.parse_args(argv)
    if args.camera < 0:
        parser.error("--camera must be non-negative.")
    if args.smooth > 60:
        parser.error("--smooth must be between 1 and 60.")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        hand_path = ensure_model("hand_landmarker.task", args.model_dir, args.download_models)
        pose_path = None if args.no_pose else ensure_model("pose_landmarker.task", args.model_dir, args.download_models)
        if args.download_models:
            print(f"Models ready in {hand_path.parent}. No camera was opened.")
            return 0
        try:
            from runtime import run_camera, check_models
        except (ImportError, OSError) as error:
            print(f"[ERROR] Runtime dependencies are unavailable: {error}\n"
                  "Use Python 3.11 or 3.12 in a virtual environment, then run:\n"
                  "python -m pip install -r requirements.txt", file=sys.stderr)
            return 1
        if args.check:
            check_models(hand_path, pose_path)
        else:
            run_camera(args, hand_path, pose_path)
        return 0
    except KeyboardInterrupt:
        print("\nStopped.")
        return 0
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
