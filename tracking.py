"""Camera-independent geometry, smoothing, and timestamp helpers."""
import math
from collections import Counter, deque


def count_fingers(landmarks, width=1, height=1):
    """Heuristic count in image space; not invariant to 3D hand rotation."""
    if len(landmarks) != 21 or width <= 0 or height <= 0:
        return 0
    points = [(lm.x * width, lm.y * height) for lm in landmarks]
    if not all(math.isfinite(v) for point in points for v in point):
        return 0

    def distance(a, b):
        return math.dist(points[a], points[b])

    palm = distance(0, 9)
    if palm < 1e-8:
        return 0
    margin = palm * 0.08
    fingers = [distance(4, 17) > distance(3, 17) + margin]
    fingers.extend(distance(tip, 0) > distance(tip - 2, 0) + margin
                   for tip in (8, 12, 16, 20))
    return sum(fingers)


class StableCount:
    """Short majority filter; ties favor the most recent observation."""
    def __init__(self, window=7):
        if window < 1:
            raise ValueError("Smoothing window must be positive.")
        self.values = deque(maxlen=window)
        self.hand_count = None

    def update(self, count, hands):
        if hands != self.hand_count or hands == 0:
            self.values.clear()
        self.hand_count = hands
        if hands == 0:
            return 0
        self.values.append(count)
        frequencies = Counter(self.values)
        highest = max(frequencies.values())
        return next(value for value in reversed(self.values)
                    if frequencies[value] == highest)


class VideoClock:
    """MediaPipe VIDEO mode requires strictly increasing milliseconds."""
    def __init__(self):
        self.last = -1

    def next(self, monotonic_seconds):
        self.last = max(self.last + 1, int(monotonic_seconds * 1000))
        return self.last


def hand_label(raw_label, swap=False):
    if raw_label not in ("Left", "Right"):
        return "Unknown"
    return ("Right" if raw_label == "Left" else "Left") if swap else raw_label
