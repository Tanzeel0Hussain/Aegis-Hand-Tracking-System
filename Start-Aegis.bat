@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel% equ 0 (
  py -3 launcher.py
) else (
  python launcher.py
)
if errorlevel 1 (
  echo Install Python 3 from python.org and extract the complete ZIP, then retry.
  pause
)
