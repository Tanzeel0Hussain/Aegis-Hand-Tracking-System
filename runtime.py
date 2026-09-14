"""OpenCV display and MediaPipe VIDEO-mode inference."""
from contextlib import ExitStack
import time

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from tracking import StableCount, VideoClock, count_fingers, hand_label

WINDOW = "Aegis Hand Scanner"
ACCENT = (255, 200, 0)
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),(0,17),
]
POSE_CONNECTIONS = [
    (11,12),(11,13),(13,15),(15,17),(15,19),(15,21),(17,19),
    (12,14),(14,16),(16,18),(16,20),(16,22),(18,20),
    (11,23),(12,24),(23,24),(23,25),(24,26),(25,27),(26,28),
    (27,29),(28,30),(29,31),(30,32),(27,31),(28,32),
]


def create_detectors(stack, hand_path, pose_path):
    hand = stack.enter_context(vision.HandLandmarker.create_from_options(
        vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(hand_path)),
            running_mode=vision.RunningMode.VIDEO, num_hands=2,
            min_hand_detection_confidence=0.65,
            min_hand_presence_confidence=0.65,
            min_tracking_confidence=0.65)))
    pose = None
    if pose_path is not None:
        pose = stack.enter_context(vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(pose_path)),
                running_mode=vision.RunningMode.VIDEO,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5)))
    return hand, pose


def infer(frame, hand, pose, timestamp):
    # Inference sees the original brightness, before any decorative overlay.
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    return hand.detect_for_video(image, timestamp), (
        pose.detect_for_video(image, timestamp) if pose is not None else None)


def safe_destroy_windows():
    try:
        cv2.destroyAllWindows()
    except cv2.error:
        pass


def should_exit():
    key = cv2.waitKey(1) & 0xFF
    return key in (ord("q"), ord("Q"), 27) or cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1


def draw_brackets(image, left, top, right, bottom):
    length = max(4, min(20, (right-left)//3, (bottom-top)//3))
    for x, dx in ((left, length), (right, -length)):
        for y, dy in ((top, length), (bottom, -length)):
            cv2.line(image, (x,y), (x+dx,y), ACCENT, 2, cv2.LINE_AA)
            cv2.line(image, (x,y), (x,y+dy), ACCENT, 2, cv2.LINE_AA)


def render(frame, hands, pose, smoother, fps, glow=True, swap=False):
    height, width = frame.shape[:2]
    canvas = np.zeros_like(frame)
    display = cv2.convertScaleAbs(frame, alpha=0.55)
    statuses = []
    total = 0
    if pose is not None and pose.pose_landmarks:
        landmarks = pose.pose_landmarks[0]
        pts = [(int(lm.x*width), int(lm.y*height)) for lm in landmarks]
        for a, b in POSE_CONNECTIONS:
            if (landmarks[a].visibility or 0) > 0.5 and (landmarks[b].visibility or 0) > 0.5:
                cv2.line(canvas, pts[a], pts[b], (150,70,0), 2, cv2.LINE_AA)
        for index in range(11, len(landmarks)):
            if (landmarks[index].visibility or 0) > 0.5:
                cv2.circle(canvas, pts[index], 3, (255,120,0), -1, cv2.LINE_AA)
    for index, landmarks in enumerate(hands.hand_landmarks):
        if len(landmarks) != 21:
            continue
        points = [(int(lm.x*width), int(lm.y*height)) for lm in landmarks]
        for a, b in HAND_CONNECTIONS:
            cv2.line(canvas, points[a], points[b], (200,200,200), 2, cv2.LINE_AA)
        for point in points:
            cv2.circle(canvas, point, 4, ACCENT, -1, cv2.LINE_AA)
        left = max(0, min(p[0] for p in points)-20)
        top = max(0, min(p[1] for p in points)-20)
        right = min(width-1, max(p[0] for p in points)+20)
        bottom = min(height-1, max(p[1] for p in points)+20)
        draw_brackets(display, left, top, right, bottom)
        count = count_fingers(landmarks, width, height)
        total += count
        categories = hands.handedness[index] if index < len(hands.handedness) else []
        label = hand_label(categories[0].category_name if categories else "", swap)
        confidence = categories[0].score if categories else 0
        cv2.putText(display, label.upper(), (left, max(15,top-8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, ACCENT, 1, cv2.LINE_AA)
        statuses.append(f"{label.upper()}: {count} fingers | label {confidence:.0%}")
    stable = smoother.update(total, len(hands.hand_landmarks))
    if glow:
        display = cv2.addWeighted(display, 1, cv2.GaussianBlur(canvas, (15,15), 0), 0.7, 0)
    display = cv2.addWeighted(display, 1, canvas, 1, 0)
    # Draw HUD at a fixed logical size, then scale for the actual capture resolution.
    panel = np.full((175, 510, 3), 20, dtype=np.uint8)
    cv2.rectangle(panel, (0,0), (509,174), ACCENT, 1)
    cv2.putText(panel, "AEGIS | HAND + POSE TRACKING", (14,25), cv2.FONT_HERSHEY_DUPLEX, 0.6, (220,220,220), 1, cv2.LINE_AA)
    cv2.putText(panel, f"FINGERS: {stable}", (14,66), cv2.FONT_HERSHEY_DUPLEX, 1, ACCENT, 2, cv2.LINE_AA)
    cv2.putText(panel, f"FPS {fps:.1f} | HANDS {len(hands.hand_landmarks)} | POSE {'ON' if pose is not None else 'OFF'}",
                (14,90), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (190,190,190), 1, cv2.LINE_AA)
    for row, status in enumerate(statuses[:2]):
        cv2.putText(panel, status, (14,113+row*20), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (240,240,240), 1, cv2.LINE_AA)
    cv2.putText(panel, "Q / ESC: quit | heuristic count, not a measurement", (14,160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (155,155,155), 1, cv2.LINE_AA)
    margin = max(0, min(15, width//20, height//20))
    scale = min(1.0, (width-2*margin)/510, (height-2*margin)/175)
    panel = cv2.resize(panel, (max(1,int(510*scale)), max(1,int(175*scale))))
    ph, pw = panel.shape[:2]
    display[margin:margin+ph, margin:margin+pw] = panel
    return display


def run_camera(args, hand_path, pose_path):
    with ExitStack() as stack:
        capture = cv2.VideoCapture(args.camera)
        stack.callback(capture.release)
        stack.callback(safe_destroy_windows)
        if not capture.isOpened():
            raise RuntimeError(f"Cannot open camera {args.camera}. Check camera permission, close other camera apps, or try --camera 1.")
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        hand, pose = create_detectors(stack, hand_path, pose_path)
        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        smoother = StableCount(args.smooth)
        clock = VideoClock()
        failures = 0
        previous = time.monotonic()
        fps = 0
        while True:
            success, frame = capture.read()
            if not success or frame is None or frame.size == 0:
                failures += 1
                if failures >= args.max_read_failures:
                    raise RuntimeError("Camera stopped returning frames. Reconnect it or try a different --camera index.")
                if should_exit():
                    break
                time.sleep(0.03)
                continue
            failures = 0
            if not args.no_mirror:
                frame = cv2.flip(frame, 1)
            now = time.monotonic()
            instant = 1 / max(now-previous, 1e-6)
            fps = instant if fps == 0 else 0.9*fps + 0.1*instant
            previous = now
            hands, body = infer(frame, hand, pose, clock.next(now))
            image = render(frame, hands, body, smoother, fps, not args.no_glow, args.swap_handedness)
            cv2.imshow(WINDOW, image)
            if should_exit():
                break


def check_models(hand_path, pose_path):
    with ExitStack() as stack:
        hand, pose = create_detectors(stack, hand_path, pose_path)
        blank = np.zeros((480,640,3), dtype=np.uint8)
        smoother = StableCount()
        for timestamp in (0,33):
            hands, body = infer(blank, hand, pose, timestamp)
            image = render(blank, hands, body, smoother, 0)
            if image.shape != blank.shape:
                raise RuntimeError("Unexpected rendered frame dimensions.")
    print("PASS: model initialization, VIDEO inference, and HUD rendering on two synthetic blank frames. Webcam accuracy was not tested.")
