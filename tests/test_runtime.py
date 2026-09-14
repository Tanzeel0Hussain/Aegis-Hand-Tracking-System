from contextlib import ExitStack
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import runtime
from FingerCount import parse_args
from tracking import StableCount


class RuntimeTests(unittest.TestCase):
    def test_unavailable_camera_is_released(self):
        cap=Mock()
        cap.isOpened.return_value=False
        with patch("runtime.cv2.VideoCapture",return_value=cap), patch("runtime.safe_destroy_windows"), patch("runtime.create_detectors") as detectors:
            with self.assertRaisesRegex(RuntimeError,"Cannot open camera"):
                runtime.run_camera(parse_args([]),"hand","pose")
            cap.release.assert_called_once()
            detectors.assert_not_called()

    def test_repeated_failed_reads_stop_instead_of_spinning(self):
        cap=Mock()
        cap.isOpened.return_value=True
        cap.read.return_value=(False,None)
        with ExitStack() as stack:
            stack.enter_context(patch("runtime.cv2.VideoCapture",return_value=cap))
            stack.enter_context(patch("runtime.safe_destroy_windows"))
            stack.enter_context(patch("runtime.create_detectors",return_value=(Mock(),None)))
            stack.enter_context(patch("runtime.cv2.namedWindow"))
            stack.enter_context(patch("runtime.should_exit",return_value=False))
            stack.enter_context(patch("runtime.time.sleep"))
            with self.assertRaisesRegex(RuntimeError,"stopped returning frames"):
                runtime.run_camera(parse_args(["--max-read-failures","3"]),"hand",None)
        self.assertEqual(cap.read.call_count,3)
        cap.release.assert_called_once()

    def test_inference_failure_releases_camera(self):
        cap=Mock()
        cap.isOpened.return_value=True
        cap.read.return_value=(True,np.zeros((20,20,3),dtype=np.uint8))
        with ExitStack() as stack:
            stack.enter_context(patch("runtime.cv2.VideoCapture",return_value=cap))
            stack.enter_context(patch("runtime.safe_destroy_windows"))
            stack.enter_context(patch("runtime.create_detectors",return_value=(Mock(),None)))
            stack.enter_context(patch("runtime.cv2.namedWindow"))
            stack.enter_context(patch("runtime.infer",side_effect=RuntimeError("inference failed")))
            with self.assertRaisesRegex(RuntimeError,"inference failed"):
                runtime.run_camera(parse_args([]),"hand",None)
        cap.release.assert_called_once()

    def test_detector_failure_closes_previously_created_detector(self):
        detector=Mock()
        detector.__enter__=Mock(return_value=detector)
        detector.__exit__=Mock(return_value=False)
        with patch("runtime.vision.HandLandmarker.create_from_options",return_value=detector), patch("runtime.vision.PoseLandmarker.create_from_options",side_effect=RuntimeError("pose failed")):
            with self.assertRaisesRegex(RuntimeError,"pose failed"):
                with ExitStack() as stack:
                    runtime.create_detectors(stack,"hand","pose")
        detector.__exit__.assert_called_once()

    def test_inference_receives_original_brightness(self):
        frame=np.full((12,16,3),200,dtype=np.uint8)
        detector=Mock()
        runtime.infer(frame,detector,None,12)
        image,timestamp=detector.detect_for_video.call_args.args
        self.assertEqual(timestamp,12)
        self.assertTrue(np.all(image.numpy_view()==200))
        self.assertTrue(np.all(frame==200))

    def test_hud_fits_multiple_resolutions_without_modifying_input(self):
        results=SimpleNamespace(hand_landmarks=[],handedness=[])
        for height,width in ((240,320),(480,640),(720,1280)):
            frame=np.full((height,width,3),200,dtype=np.uint8)
            output=runtime.render(frame,results,None,StableCount(),30,glow=False)
            self.assertEqual(output.shape,frame.shape)
            self.assertTrue(np.all(frame==200))


if __name__ == "__main__":
    unittest.main()
