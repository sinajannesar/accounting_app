@echo off
REM Auto build and pack script (fixed)
REM Usage: Run from repo root on a Windows build machine where Python (recommended 32-bit) is installed.
REM Recommended: Open CMD as Administrator if you plan to include VC++ redistributable installation.

setlocal enabledelayedexpansion
echo ==================================================
echo Hesabdari: Auto build + pack (onedir + NSIS installer)
echo ==================================================

:: Check python availability
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python not found in PATH. Please install Python (32-bit recommended) and try again.
  exit /b 1
)

:: Detect Python architecture (32 vs 64)
for /f "usebackq delims=" %%a in (`python -c "import struct;print(struct.calcsize('P')*8)"`) do set PYARCH=%%a
echo Python architecture: %PYARCH%-bit
if not "%PYARCH%"=="32" (
  echo WARNING: Python is not 32-bit. Building with 64-bit Python will produce a 64-bit exe which may not run on very old/weak 32-bit systems.
  set /p CONT=Continue with current Python? (Y/N): 
  if /i not "%CONT%"=="Y" (
    echo Aborting. Install 32-bit Python and rerun for max compatibility.
    exit /b 2
  )
)

:: Create virtualenv if missing
if not exist venv32 (
  echo Creating virtualenv venv32...
  python -m venv venv32
  if errorlevel 1 (
    echo ERROR: failed to create virtualenv
    exit /b 3
  )
)

:: Activate virtualenv
call venv32\Scripts\activate.bat
if errorlevel 1 (
  echo ERROR: failed to activate virtualenv
  exit /b 4
)

:: Upgrade pip and install requirements
echo Upgrading pip, setuptools and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
  echo ERROR: pip upgrade failed
  exit /b 5
)

echo Installing requirements from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: pip install -r requirements.txt failed
  exit /b 6
)

echo Installing/ensuring PyInstaller is present...
pip install pyinstaller
if errorlevel 1 (
  echo ERROR: pip install pyinstaller failed
  exit /b 7
)

:: Run PyInstaller to build onedir
echo Running PyInstaller (onedir, noupx)...
pyinstaller --onedir --noconfirm --windowed --name Hesabdari --noupx main.py
if errorlevel 1 (
  echo ERROR: PyInstaller failed. See output above.
  exit /b 8
)

:: Verify dist output
if not exist dist\Hesabdari (
  echo ERROR: expected folder dist\Hesabdari not found
  exit /b 9
)
echo dist\Hesabdari contents:
dir dist\Hesabdari

:: Check for makensis (NSIS)
where makensis >nul 2>nul
if errorlevel 1 (
  echo WARNING: makensis (NSIS) not found in PATH. Skipping installer build step.
  echo You can run tools\build_installer.bat later on a machine with NSIS installed.
  echo Build finished: onedir created at dist\Hesabdari
  endlocal
  exit /b 0
)

:: Run installer builder (wrapper)
echo Running NSIS to build installer...
call tools\build_installer.bat
if errorlevel 1 (
  echo ERROR: Installer build failed. See makensis output above.
  exit /b 10
)

echo ==================================================
echo SUCCESS: Installer should be at dist_installer\Hesabdari_Setup.exe
echo If you included vc_redist.x86.exe in the repo root, the installer will run it silently during setup.
echo ==================================================
endlocal
exit /b 0
