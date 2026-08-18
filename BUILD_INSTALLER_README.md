Goal: create a single, easy installer (EXE) to give to low-skill clients so they can double-click and install the app.

This README explains how to build a Windows installer (NSIS) that packages the onedir PyInstaller output.

Prerequisites (on a Windows build machine)
- A Windows machine (VM recommended) that represents the oldest Windows you need to support.
- 32-bit Python (recommended) installed and a virtualenv prepared if you will run PyInstaller on the machine.
- PyInstaller installed in the venv: pip install pyinstaller
- NSIS (makensis) installed and on PATH. Download: https://nsis.sourceforge.io/Download
- Optional: the Visual C++ Redistributable x86 installer (vc_redist.x86.exe) if you want the installer to include it. Place the file next to tools\installer.nsi.

Steps to produce the installer
1) Build the application on the Windows build machine (recommended to use 32-bit Python):
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   pip install pyinstaller

   Run PyInstaller in the repo root to produce a one-dir bundle (recommended):
   pyinstaller --onedir --noconfirm --windowed --name Hesabdari --noupx main.py

   After success you should have dist\Hesabdari containing Hesabdari.exe and required DLLs and supporting folders (e.g. platforms).

2) (Optional but recommended) Place Visual C++ redistributable next to the installer script:
   - Download the x86 redistributable for 2015-2022 (or appropriate year):
     https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist
   - Save the file as vc_redist.x86.exe in the repository root (same level as tools folder) so the NSIS script will detect and run it silently during install.

3) Build the NSIS installer
   - Ensure makensis is on your PATH.
   - From repo root run:
     makensis tools\installer.nsi
   - Or use provided wrapper on Windows (after building dist):
     tools\build_installer.bat

   Output: dist_installer\Hesabdari_Setup.exe

What the installer does
- Copies all files from dist\Hesabdari into "C:\Program Files (x86)\Hesabdari" by default (32-bit Program Files path)
- Creates Start Menu and Desktop shortcuts
- If vc_redist.x86.exe is present next to the installer, runs it silently to install Visual C++ runtime
- Writes an Uninstall entry and creates an Uninstall.exe

Testing the installer
- Run the produced dist_installer\Hesabdari_Setup.exe on a clean Windows VM (no Python installed).
- Test main flows: open the app, generate a report, export Excel/PDF, open and close windows.
- If you see an error like "api-ms-win-core-*.dll missing" or "Failed to load Python DLL" then capture the full error dialog and list files in folder dist\Hesabdari and send them to the developer for further adjustments.

Notes and tips
- Always distribute the entire installer EXE to clients, not the raw dist folder unless you want them to manually copy files (installer is simpler for non-technical users).
- Using --onedir avoids runtime extraction and reduces startup issues on weak machines. We intentionally avoid --onefile.
- Avoid UPX compression for onedir builds on weak CPUs (we pass --noupx).
- If a target machine still reports missing system DLLs, the safest remedy is to include vc_redist.x86.exe in the installer or instruct customers to run Windows Update.

If you want, I can:
- Generate a polished Inno Setup script instead of NSIS (both are fine — Inno Setup gives a nicer UI but requires Inno Setup on the build machine).
- Try to build a test installer in a Windows build VM if you can provide one or run a remote CI job.

