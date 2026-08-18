@echo off
REM Build helper for Windows (run in CMD with a 32-bit Python venv activated)
REM Usage: tools\build_windows_32.bat
python tools\build_windows_32.py --main main.py --name Hesabdari
if %errorlevel% neq 0 (
  echo Build failed with exit code %errorlevel%
  exit /b %errorlevel%
)
echo Build succeeded. See dist\Hesabdari
