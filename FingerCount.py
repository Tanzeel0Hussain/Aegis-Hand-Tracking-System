import sys
import subprocess
import importlib
import os
import urllib.request
from collections import deque
import numpy as np
import math

# --- DEPENDENCY MANAGER ---
def check_and_install(pip_name, import_name):
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"[SYSTEM] Dependency '{import_name}' is missing. Auto-installing '{pip_name}'...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        except subprocess.CalledProcessError:
            print(f"[ERROR] Failed to install {pip_name}.")
            sys.exit(1)

required_packages = {"opencv-python": "cv2", "mediapipe": "mediapipe", "numpy": "numpy"}
print("Initializing System. Checking dependencies...")
for pip_pkg, imp_pkg in required_packages.items():
    check_and_install(pip_pkg, imp_pkg)

# --- AI MODEL DOWNLOADER ---
HAND_MODEL = "hand_landmarker.task"
POSE_MODEL = "pose_landmarker.task"

if not os.path.exists(HAND_MODEL):
    print("\n[SYSTEM] AI Hand Model missing. Downloading...")
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task", HAND_MODEL)

if not os.path.exists(POSE_MODEL):
    print("[SYSTEM] AI Body Pose Model missing. Downloading...")
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task", POSE_MODEL)

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

def draw_corner_brackets(img, x, y, w, h, color, length=20, thickness=2):
    cv2.line(img, (x, y), (x + length, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y), (x, y + length), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w - length, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y), (x + w, y + length), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y + h), (x + length, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y + h), (x, y + h - length), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y + h), (x + w - length, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y + h), (x + w, y + h - length), color, thickness, cv2.LINE_AA)

def get_distance(p1, p2):
    """Calculates the Euclidean distance between two points."""
    return math.hypot(p1[1] - p2[1], p1[2] - p2[2])

def main():
    hand_options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=HAND_MODEL),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.65, 
        min_hand_presence_confidence=0.65,
        min_tracking_confidence=0.65
    )
    hand_detector = vision.HandLandmarker.create_from_options(hand_options)

    pose_options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=POSE_MODEL),
        running_mode=vision.RunningMode.IMAGE,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5
    )
    pose_detector = vision.PoseLandmarker.create_from_options(pose_options)

    THEME_ACCENT = (255, 200, 0)      
    THEME_BONE = (200, 200, 200)      
    POSE_ACCENT = (255, 100, 0)       
    POSE_BONE = (150, 50, 0)          
    DARK_PANEL = (20, 20, 20)
    WHITE = (255, 255, 255)

    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),        
        (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), 
        (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)                                
    ]
    
    # Removed face connections (0 through 10)
    POSE_CONNECTIONS = [
        (11,12), (11,13), (13,15), (15,17), (15,19), (15,21), (17,19),  
        (12,14), (14,16), (16,18), (16,20), (16,22), (18,20),
        (11,23), (12,24), (23,24), (23,25), (24,26), (25,27), (26,28),  
        (27,29), (28,30), (29,31), (30,32), (27,31), (28,32)
    ]
    tipIds = [4, 8, 12, 16, 20]

    count_buffer = deque(maxlen=7)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    cv2.namedWindow("Aegis Hand Scanner", cv2.WINDOW_NORMAL)

    while cap.isOpened():
        success, frame = cap.read()
        if not success: continue

        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape

        dark_overlay = np.zeros((h, w, c), dtype=np.uint8)
        frame = cv2.addWeighted(frame, 0.45, dark_overlay, 0.55, 0)

        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        
        hand_results = hand_detector.detect(mp_image)
        pose_results = pose_detector.detect(mp_image)

        current_frame_fingers = 0
        hands_status_text = []

        glow_canvas = np.zeros_like(frame, dtype=np.uint8)

        # 1. DRAW BODY SKELETON (Without Face)
        if pose_results.pose_landmarks:
            pose_lms = pose_results.pose_landmarks[0]
            pose_points = [(int(lm.x * w), int(lm.y * h)) for lm in pose_lms]

            for connection in POSE_CONNECTIONS:
                idx1, idx2 = connection
                if idx1 < len(pose_points) and idx2 < len(pose_points):
                    if pose_lms[idx1].visibility > 0.3 and pose_lms[idx2].visibility > 0.3:
                        cv2.line(glow_canvas, pose_points[idx1], pose_points[idx2], POSE_BONE, 2, cv2.LINE_AA)
            
            for i, lm in enumerate(pose_lms):
                # Skip rendering nodes 0-10 entirely (Face mapping)
                if i > 10 and lm.visibility > 0.3:
                    cv2.circle(glow_canvas, pose_points[i], 4, POSE_ACCENT, cv2.FILLED, cv2.LINE_AA)

        # 2. DRAW HAND SKELETON & DISTANCE-BASED COUNTING
        if hand_results.hand_landmarks:
            for hand_idx in range(len(hand_results.hand_landmarks)):
                hand_landmarks = hand_results.hand_landmarks[hand_idx]
                
                raw_label = hand_results.handedness[hand_idx][0].category_name
                hand_label = "Right" if raw_label == "Left" else "Left"

                lmList = []
                x_coords, y_coords = [], []
                
                for id, lm in enumerate(hand_landmarks):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])
                    x_coords.append(cx)
                    y_coords.append(cy)

                for connection in HAND_CONNECTIONS:
                    idx1, idx2 = connection
                    cv2.line(glow_canvas, (lmList[idx1][1], lmList[idx1][2]), 
                             (lmList[idx2][1], lmList[idx2][2]), THEME_BONE, 2, cv2.LINE_AA)
                
                for lm in lmList:
                    cv2.circle(glow_canvas, (lm[1], lm[2]), 5, THEME_ACCENT, cv2.FILLED, cv2.LINE_AA)

                box_margin = 30
                min_x, max_x = max(0, min(x_coords) - box_margin), min(w, max(x_coords) + box_margin)
                min_y, max_y = max(0, min(y_coords) - box_margin), min(h, max(y_coords) + box_margin)
                
                draw_corner_brackets(frame, min_x, min_y, max_x - min_x, max_y - min_y, THEME_ACCENT)
                cv2.putText(frame, f"ID:{hand_label.upper()}", (min_x, min_y - 10), 
                            cv2.FONT_HERSHEY_DUPLEX, 0.5, THEME_ACCENT, 1, cv2.LINE_AA)

                # --- NEW ROTATION-INVARIANT FINGER LOGIC ---
                fingers = []
                if len(lmList) == 21:
                    wrist_node = lmList[0]
                    pinky_base = lmList[17]

                    # THUMB: Compare distance from Thumb Tip (4) to Pinky Base (17) 
                    # vs Thumb Middle Joint (3) to Pinky Base (17). Works at any angle.
                    if get_distance(lmList[tipIds[0]], pinky_base) > get_distance(lmList[tipIds[0] - 1], pinky_base):
                        fingers.append(1)
                    else:
                        fingers.append(0)

                    # 4 FINGERS: Compare distance from Finger Tip to Wrist vs Finger PIP Joint to Wrist
                    for id in range(1, 5):
                        if get_distance(lmList[tipIds[id]], wrist_node) > get_distance(lmList[tipIds[id] - 2], wrist_node):
                            fingers.append(1)
                        else:
                            fingers.append(0)

                count = fingers.count(1)
                current_frame_fingers += count
                
                wrist_z = abs(round(hand_landmarks[0].z, 3))
                hands_status_text.append(f"{hand_label.upper()} PORT : {count} FINGERS | DEPTH: {wrist_z}")

        count_buffer.append(current_frame_fingers)
        stable_total_fingers = max(set(count_buffer), key=count_buffer.count) if count_buffer else 0

        # Render Glow Aura
        glow = cv2.GaussianBlur(glow_canvas, (15, 15), 0)
        frame = cv2.addWeighted(frame, 1.0, glow, 0.7, 0)
        frame = cv2.addWeighted(frame, 1.0, glow_canvas, 1.0, 0)

        # 3. MODERN POLYGON HUD
        hud_overlay = frame.copy()
        hud_h = 100 + (len(hands_status_text) * 35)
        
        pts = np.array([
            [20, 20], [500, 20], [470, 20 + hud_h], [20, 20 + hud_h]
        ], np.int32)
        
        cv2.fillPoly(hud_overlay, [pts], DARK_PANEL)
        cv2.polylines(hud_overlay, [pts], True, THEME_ACCENT, 2, cv2.LINE_AA)
        frame = cv2.addWeighted(hud_overlay, 0.9, frame, 0.1, 0)

        cv2.putText(frame, "AEGIS MULTI-TRACKING SYSTEM", (40, 50), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, THEME_BONE, 1, cv2.LINE_AA)
        cv2.putText(frame, f"ACTIVE UNITS: {stable_total_fingers}", (40, 95), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.3, THEME_ACCENT, 2, cv2.LINE_AA)
        
        y_offset = 135
        for status in hands_status_text:
            cv2.putText(frame, status, (40, y_offset), 
                        cv2.FONT_HERSHEY_DUPLEX, 0.55, WHITE, 1, cv2.LINE_AA)
            y_offset += 35

        cv2.imshow("Aegis Hand Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
