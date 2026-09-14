import math
from types import SimpleNamespace
import unittest

from tracking import StableCount, VideoClock, count_fingers, hand_label


def hand(opened=True):
    points = [(0.0, 0.0)] * 21
    for base, x in ((5,-0.2),(9,0),(13,0.2),(17,0.4)):
        points[base] = (x,0.3)
        points[base+1] = (x,0.6)
        points[base+2] = (x,0.8)
        points[base+3] = (x,1.0 if opened else 0.2)
    points[3] = (-0.3,0.3)
    points[4] = (-0.6,0.5) if opened else (0.1,0.2)
    return [SimpleNamespace(x=x,y=y) for x,y in points]


class TrackingTests(unittest.TestCase):
    def test_open_and_closed_synthetic_hands(self):
        self.assertEqual(count_fingers(hand()),5)
        self.assertEqual(count_fingers(hand(False)),0)

    def test_in_plane_rotation_translation_scale_and_reflection(self):
        for opened, expected in ((True,5),(False,0)):
            for angle in (0,0.4,1.6,3.1):
                points = hand(opened)
                for lm in points:
                    x,y=lm.x,lm.y
                    lm.x=4+2*(x*math.cos(angle)-y*math.sin(angle))
                    lm.y=-2+2*(x*math.sin(angle)+y*math.cos(angle))
                self.assertEqual(count_fingers(points),expected)
                for lm in points:
                    lm.x=-lm.x
                self.assertEqual(count_fingers(points),expected)

    def test_invalid_and_collapsed_landmarks(self):
        self.assertEqual(count_fingers([]),0)
        self.assertEqual(count_fingers([SimpleNamespace(x=0,y=0)]*21),0)
        points=hand()
        points[8].x=float("nan")
        self.assertEqual(count_fingers(points),0)

    def test_ties_favor_newest_count(self):
        stable=StableCount()
        self.assertEqual(stable.update(2,1),2)
        self.assertEqual(stable.update(3,1),3)

    def test_no_hands_and_hand_count_change_clear_history(self):
        stable=StableCount()
        for _ in range(7):
            stable.update(5,1)
        self.assertEqual(stable.update(0,0),0)
        self.assertEqual(stable.update(1,1),1)
        self.assertEqual(stable.update(8,2),8)

    def test_clock_strictly_increases_even_at_same_time(self):
        clock=VideoClock()
        values=[clock.next(x) for x in (1,1,1.00001,0.5,2)]
        self.assertTrue(all(a<b for a,b in zip(values,values[1:])))

    def test_labels_not_unconditionally_swapped(self):
        self.assertEqual(hand_label("Left"),"Left")
        self.assertEqual(hand_label("Left",True),"Right")
        self.assertEqual(hand_label("bad"),"Unknown")


if __name__ == "__main__":
    unittest.main()
