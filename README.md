# Aegis-Hand-Tracking-System
A real-time computer vision system that detects hands and body pose using MediaPipe. Includes rotation-invariant finger counting, depth estimation, and a modern HUD-style interface built with OpenCV.

# 🛡️ Aegis Multi-Tracking System (Hand + Pose Detection)

Aegis Multi-Tracking System is a real-time computer vision project built using Python, OpenCV, and MediaPipe.
It detects **hand landmarks, body pose (without face), and counts fingers accurately** using an angle-independent method.

This project creates a futuristic HUD-style interface with glowing skeleton tracking.

---

## 🚀 Features

* ✋ Real-time **Hand Detection (2 hands supported)**
* 🧍 Full **Body Pose Detection (face removed for privacy & performance)**
* 🔢 **Finger Counting System (Rotation-Invariant)**
* 🌐 Automatic **Model Download System**
* 📦 Auto **Dependency Installation**
* 🎨 Modern UI with:

  * Glow effects
  * HUD panel
  * Bounding brackets
* 📏 Depth estimation using hand Z-axis
* 📊 Stable finger count using buffer smoothing

---

## 🧠 How It Works

### 1. Dependency Manager

The system first checks if required libraries are installed:

* OpenCV
* MediaPipe
* NumPy

If not installed, it automatically installs them using pip.

---

### 2. AI Model Downloader

Two AI models are downloaded automatically if missing:

* Hand Landmarker Model
* Pose Landmarker Model

These models are used for detecting hand and body landmarks.

---

### 3. Video Capture

* Uses webcam (`cv2.VideoCapture(0)`)
* Resolution set to **1920x1080**
* Frame is flipped horizontally for mirror view

---

### 4. Hand Detection System

* Detects up to **2 hands**
* Each hand gives **21 landmark points**
* Draws:

  * Skeleton connections
  * Joint points
  * Bounding box with corner brackets

---

### 5. Finger Counting Logic (Important)

This project uses a **rotation-invariant method**, meaning:

✔ Works at any angle
✔ Works even if hand is tilted

#### Logic:

* **Thumb Detection:**

  * Compare distance between:

    * Thumb tip → Pinky base
    * Thumb joint → Pinky base

* **Other Fingers:**

  * Compare:

    * Finger tip → Wrist
    * Finger middle joint → Wrist

If distance is greater → finger is **open (1)**
Else → **closed (0)**

---

### 6. Pose Detection (Body Tracking)

* Detects full body skeleton
* **Face landmarks removed** (indices 0–10)
* Only body joints are drawn
* Uses visibility threshold for cleaner output

---

### 7. Stability System

To avoid flickering:

* Uses a buffer (`deque`)
* Stores last few frames
* Shows most frequent finger count

This gives **smooth and stable output**

---

### 8. UI & Visual Effects

The system includes a modern HUD interface:

* Dark overlay background
* Glow effect using Gaussian blur
* Polygon information panel
* Live stats:

  * Total active fingers
  * Per-hand data
  * Depth value

---

## 🖥️ Controls

| Key | Action       |
| --- | ------------ |
| Q   | Exit program |

---

## 📦 Installation

### 1. Clone Repository

```bash
https://github.com/Tanzeel0Hussain/Aegis-Hand-Tracking-System.git
```

### 2. Run Project

```bash
python FingerCount.py
```

👉 Dependencies will install automatically.

---

## 📁 Project Structure

```
├── FingerCount.py
└── README.md
```

---

## ⚙️ Requirements

* Python 3.8+
* Webcam

---

## 🧪 Technologies Used

* Python
* OpenCV
* MediaPipe
* NumPy

---

## 📌 Use Cases

* Gesture Control Systems
* Human-Computer Interaction (HCI)
* Gaming Interfaces
* AI Vision Projects
* Robotics Control

---

## ⚠️ Notes

* First run may take time (model download)
* Works best in good lighting conditions
* Webcam quality affects accuracy

---

## 💡 Future Improvements

* Gesture recognition (custom actions)
* AI-based sign language detection
* Multi-person tracking
* GPU acceleration

---

## 👨‍💻 Author

**Tanzeel Hussain**

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!
