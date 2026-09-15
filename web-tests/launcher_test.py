"""Smoke-check the downloadable launcher's real HTTP server, without a webcam."""
from pathlib import Path
import subprocess
import sys
from urllib.request import urlopen, build_opener, ProxyHandler
from urllib.error import HTTPError

project = Path(__file__).resolve().parents[1]
process = subprocess.Popen(
    [sys.executable, str(project / 'launcher.py'), '--no-browser'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
)
try:
    url = process.stdout.readline().strip().removeprefix('Aegis studio: ')
    assert url.startswith('http://127.0.0.1:'), url
    local = build_opener(ProxyHandler({}))
    assert b'Color Portal' in local.open(url, timeout=5).read()
    assert b'AirDraw' in local.open(url + 'modes/air-draw.mjs', timeout=5).read()
    try:
        local.open(url + 'launcher.py', timeout=5)
        raise AssertionError('Repository root file exposed')
    except HTTPError as error:
        assert error.code == 404
    print('PASS: launcher serves the studio and modules, not repository root files.')
finally:
    process.terminate()
    process.communicate(timeout=5)
