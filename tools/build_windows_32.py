"""Helper to build a Windows 32-bit onedir PyInstaller bundle with sensible defaults for low-resource targets.

Usage (on a Windows 32-bit build machine with Python and PyInstaller installed):
  python tools/build_windows_32.py --main main.py --name Hesabdari

What it does:
- Verifies running on Windows and a 32-bit Python interpreter (recommended for maximum compatibility)
- Locates likely Python DLL and Visual C++ Redistributable DLLs to include with --add-binary
- Runs PyInstaller with --onedir --noupx --windowed and the detected binaries
- Prints instructions and exit codes to help debugging missing DLLs

This script does not modify repository files; run it on the build machine.
"""
import sys
import os
import shutil
import subprocess
from pathlib import Path
import argparse


def find_candidate_dlls():
    """Return list of (src, dest) tuples for binaries to include.
    Looks for common python DLL and MSVC runtimes under sys.base_prefix and Windows system directories.
    """
    candidates = []
    base = Path(sys.base_prefix)
    # possible python DLL names
    py_names = [f"python{sys.version_info.major}{sys.version_info.minor}.dll", f"python{sys.version_info.major}.dll", "python.dll"]
    for pname in py_names:
        p = base / pname
        if p.exists():
            candidates.append((str(p), pname))
            break
    # common MSVC/UCRT dlls
    msvc_names = ["vcruntime140.dll", "msvcp140.dll", "api-ms-win-core-path-l1-1-0.dll", "ucrtbase.dll"]
    # search in base, base\DLLs, and system32
    search_paths = [base, base / 'DLLs']
    system32 = Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')) / 'System32'
    search_paths.append(system32)
    for name in msvc_names:
        found = False
        for sp in search_paths:
            p = sp / name
            if p.exists():
                candidates.append((str(p), name))
                found = True
                break
        if not found:
            # try PATH
            which = shutil.which(name)
            if which:
                candidates.append((which, name))
    return candidates


def run_pyinstaller(main, name, extra_binaries):
    # prefer using PyInstaller CLI if available
    pyinstaller = shutil.which('pyinstaller')
    cmd = [pyinstaller, '--onedir', '--noconfirm', '--windowed', '--name', name, '--noupx']
    for src, dest in extra_binaries:
        cmd += ['--add-binary', f"{src}{os.pathsep}{dest}"]
    cmd.append(main)
    print('Running:', ' '.join(cmd))
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--main', default='main.py', help='Main entry-point script')
    parser.add_argument('--name', default='Hesabdari', help='Name of the built application')
    args = parser.parse_args()

    if os.name != 'nt':
        print('Warning: This script is intended to run on Windows build machines. You may still proceed at your own risk.')

    # recommend 32-bit python
    arch = '32-bit' if sys.maxsize <= 2**32 else '64-bit'
    print(f'Python interpreter architecture detected: {arch} (python {sys.version})')
    if arch != '32-bit':
        print('Recommendation: use a 32-bit Python interpreter for maximum compatibility with very old/weak machines.')

    binaries = find_candidate_dlls()
    if binaries:
        print('Detected candidate binaries to include:')
        for src, dest in binaries:
            print('  ', src, '->', dest)
    else:
        print('No candidate DLLs detected automatically. The build may still work, but you may need to add runtime DLLs manually.')

    exit_code = run_pyinstaller(args.main, args.name, binaries)
    if exit_code != 0:
        print(f'PyInstaller failed with exit code {exit_code}. Check output above for details.')
        sys.exit(exit_code)
    print('Build finished. Check dist/ directory for the onedir bundle.')


if __name__ == '__main__':
    main()
