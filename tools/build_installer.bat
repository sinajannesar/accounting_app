@echo off
REM Build wrapper to produce an NSIS installer for Hesabdari
REM Run this on a Windows build machine after producing dist\Hesabdari with PyInstaller

setlocal enabledelayedexpansion
:: Check that dist\Hesabdari exists
if not exist dist\Hesabdari (
  echo ERROR: dist\Hesabdari not found. Build the application first (pyinstaller --onedir ...)
  exit /b 1
)
:: Prepare output folder
if exist dist_installer rmdir /s /q dist_installer
mkdir dist_installer
:: Copy dist contents next to installer script if needed (NSIS File /r uses relative path):: In this script we assume tools\installer.nsi references dist\Hesabdari directly:: Check for makensisnows which makensis >nul 2>nul || where makensis >nul 2>nul
if errorlevel 1 (
  echo Makensis (NSIS) not found in PATH. Please install NSIS and add makensis to PATH.
  exit /b 2
)
:: Run makensis script
makensis tools\installer.nsinif errorlevel 1 (
  echo NSIS build failed.
  exit /b 3
)necho Installer built: dist_installer\Hesabdari_Setup.exeendlocal
