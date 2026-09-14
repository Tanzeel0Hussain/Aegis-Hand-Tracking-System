import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import models
from FingerCount import parse_args


def bundle_bytes():
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w") as archive:
        archive.writestr("hand.tflite",b"test fixture, not a real model")
    return data.getvalue()


class Response(io.BytesIO):
    def __init__(self,data,length=None):
        super().__init__(data)
        self.headers={"Content-Length":str(len(data) if length is None else length)}


class ModelTests(unittest.TestCase):
    def test_entry_import_has_no_third_party_or_camera_side_effects(self):
        result=subprocess.run([sys.executable,"-S","-c",
            "import FingerCount; import sys; assert 'cv2' not in sys.modules; assert 'numpy' not in sys.modules"],
            cwd=Path(models.__file__).parent,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,"")

    def test_help_without_dependencies(self):
        result=subprocess.run([sys.executable,"-S","FingerCount.py","--help"],
            cwd=Path(models.__file__).parent,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("--no-pose",result.stdout)

    def test_default_directory_does_not_follow_working_directory(self):
        self.assertEqual(models.DEFAULT_MODEL_DIR.parent,Path(models.__file__).resolve().parent)

    def test_missing_model_never_downloads_implicitly(self):
        with tempfile.TemporaryDirectory() as folder, patch("models.urllib.request.urlopen") as fetch:
            with self.assertRaisesRegex(RuntimeError,"download-models"):
                models.ensure_model("hand_landmarker.task",folder)
            fetch.assert_not_called()

    def test_valid_bundle_is_reused(self):
        with tempfile.TemporaryDirectory() as folder, patch("models.urllib.request.urlopen") as fetch:
            path=Path(folder)/"hand_landmarker.task"
            path.write_bytes(bundle_bytes())
            self.assertEqual(models.ensure_model(path.name,folder),path)
            fetch.assert_not_called()

    def test_atomic_download_replaces_corrupt_file(self):
        data=bundle_bytes()
        with tempfile.TemporaryDirectory() as folder, patch("models.urllib.request.urlopen",side_effect=lambda *a,**k:Response(data)):
            path=Path(folder)/"hand_landmarker.task"
            path.write_bytes(b"broken")
            self.assertEqual(models.ensure_model(path.name,folder,True).read_bytes(),data)
            self.assertEqual(list(Path(folder).glob("*.part")),[])

    def test_failed_download_cleans_temporary_files_and_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as folder, patch("models.time.sleep"), patch("models.urllib.request.urlopen",side_effect=lambda *a,**k:Response(b"short",999)) as fetch:
            path=Path(folder)/"hand_landmarker.task"
            path.write_bytes(b"old")
            with self.assertRaisesRegex(RuntimeError,"incomplete"):
                models.ensure_model(path.name,folder,True)
            self.assertEqual(fetch.call_count,3)
            self.assertEqual(path.read_bytes(),b"old")
            self.assertEqual(list(Path(folder).glob("*.part")),[])

    def test_html_response_is_not_accepted_as_model(self):
        with tempfile.TemporaryDirectory() as folder, patch("models.time.sleep"), patch("models.urllib.request.urlopen",side_effect=lambda *a,**k:Response(b"<html>error</html>")):
            with self.assertRaises(RuntimeError):
                models.ensure_model("hand_landmarker.task",folder,True)
            self.assertFalse((Path(folder)/"hand_landmarker.task").exists())

    def test_cli_rejects_invalid_dimensions(self):
        with self.assertRaises(SystemExit):
            parse_args(["--width","0"])


if __name__ == "__main__":
    unittest.main()
