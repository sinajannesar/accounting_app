@echo off
REM Auto build and pack script
REM Usage: Run from repo root on a Windows build machine where Python (recommended 32-bit) is installed.
REM Recommended: Open CMD as Administrator if you plan to include VC++ redistributable installation.

setlocal enabledelayedexpansion
echo ==================================================
echo Hesabdari: Auto build + pack (onedir + NSIS installer)
echo ==================================================
:: Check python availability
where python >nul 2>nul
if errorlevel 1 (n  echo ERROR: python not found in PATH. Please install Python (32-bit recommended) and try again.n  exit /b 1n)
:: Detect Python architecture (32 vs 64)
for /f "usebackq delims=" %%a in (`python -c "import struct;print(struct.calcsize('P')*8)"`) do set PYARCH=%%anecho Python architecture: %PYARCH%-bitnif not "%PYARCH%"=="32" (n  echo WARNING: Python is not 32-bit. Building with 64-bit Python will produce a 64-bit exe which may not run on very old/weak 32-bit systems.n  set /p CONT=Continue with current Python? (Y/N): n  if /i not "%CONT%"=="Y" (n    echo Aborting. Install 32-bit Python and rerun for max compatibility.n    exit /b 2n  )n)
:: Create virtualenv if missingnif not exist venv32 (n  echo Creating virtualenv venv32...n  python -m venv venv32n  if errorlevel 1 (
    echo ERROR: failed to create virtualenv
    exit /b 3
  )
)
:: Activate virtualenvncall venv32\Scripts\activate.batnif errorlevel 1 (
  echo ERROR: failed to activate virtualenv
  exit /b 4
)
:: Upgrade pip and install requirementsnecho Upgrading pip, setuptools and wheel...npython -m pip install --upgrade pip setuptools wheelnif errorlevel 1 (
  echo ERROR: pip upgrade failed
  exit /b 5n)
necho Installing requirements from requirements.txt...npip install -r requirements.txtnif errorlevel 1 (n  echo ERROR: pip install -r requirements.txt failedn  exit /b 6n)
necho Installing/ensuring PyInstaller is present...npip install pyinstallernif errorlevel 1 (n  echo ERROR: pip install pyinstaller failedn  exit /b 7n)
:: Run PyInstaller to build onedirnecho Running PyInstaller (onedir, noupx)...npyinstaller --onedir --noconfirm --windowed --name Hesabdari --noupx main.pynif errorlevel 1 (n  echo ERROR: PyInstaller failed. See output above.n  exit /b 8n)
:: Verify dist outputnif not exist dist\Hesabdari (n  echo ERROR: expected folder dist\Hesabdari not foundn  exit /b 9n)necho dist\Hesabdari contents:ndir dist\Hesabdari
:: Check for makensis (NSIS)
where makensis >nul 2>nulnif errorlevel 1 (n  echo WARNING: makensis (NSIS) not found in PATH. Skipping installer build step.n  echo You can run tools\build_installer.bat later on a machine with NSIS installed.n  echo Build finished: onedir created at dist\Hesabdarin  endlocaln  exit /b 0n)
:: Run installer builder (wrapper)
echo Running NSIS to build installer...ncall tools\build_installer.batnif errorlevel 1 (n  echo ERROR: Installer build failed. See makensis output above.n  exit /b 10n)

echo ==================================================necho SUCCESS: Installer should be at dist_installer\Hesabdari_Setup.exenecho If you included vc_redist.x86.exe in the repo root, the installer will run it silently during setup.
echo ==================================================
endlocalnexit /b 0
