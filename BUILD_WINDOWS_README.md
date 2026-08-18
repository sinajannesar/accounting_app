Building a portable 32-bit Windows bundle (recommended for very weak/old machines)

Overview
--------
This repository ships a Python application. To run on machines that cannot install Python, produce a PyInstaller "onedir" bundle built for 32-bit Windows and include Visual C++ runtimes.

Recommended workflow (on a Windows build VM)
-------------------------------------------
1. Provision a Windows VM (Windows 7/8/10) that matches the oldest target you need to support.
2. Install 32-bit Python (recommended 3.8 or 3.10 for better compatibility with older systems).
3. Create and activate a virtualenv:
   python -m venv venv
   venv\Scripts\activate
4. Install dependencies and PyInstaller:
   pip install -r requirements.txt
   pip install pyinstaller
5. Run the helper script (in an activated 32-bit venv):
   python tools\build_windows_32.py --main main.py --name Hesabdari
   or use the wrapper:
   tools\build_windows_32.bat

What the helper script does
---------------------------
- Detects and includes likely Python and MSVC/UCRT DLLs (if found) using --add-binary.
- Runs PyInstaller with these options:
  --onedir --noconfirm --windowed --name Hesabdari --noupx
- Places output in dist\Hesabdari

Packaging notes and tips
------------------------
- Use --onedir instead of --onefile to avoid runtime extraction overhead on weak systems.
- Do NOT use UPX (we use --noupx) since UPX decompression can slow startup on weak CPUs.
- If Windows target machines are very old, include Microsoft Visual C++ Redistributable (2015-2022) installer in your distribution or copy required runtime DLLs into the dist folder.
- Verify that Qt platform plugin (platforms\qwindows.dll) is present in dist. If PyInstaller misses it, add it manually.

Testing
-------
- Test on a clean VM with no Python installed. Run the EXE found in dist\Hesabdari\Hesabdari.exe and exercise the main flows: open UI, generate reports, export Excel/PDF.
- If you see errors about missing api-ms-win-core-*.dll or pythonXY.dll, capture the error and share it; the helper script attempts to include common DLLs but you may need to add specific files.

If you want, I can attempt to produce a test build on my side, but I need a Windows build environment (32-bit) available. Alternatively I can refine the spec further or produce an example build.spec for manual use.
