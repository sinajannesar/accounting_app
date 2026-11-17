@echo off
REM ============================================================
REM  ساخت نسخه‌ی "قطعاً کار می‌کنه" - بدون نیاز به نصب هیچ‌چیز
REM  روی سیستم مشتری (بدون نیاز به admin، بدون نیاز به اینترنت)
REM
REM  پیش‌نیاز: فایل vc_redist.x64.exe رو از این لینک دانلود کن
REM  و کنار همین بچ فایل بذار:
REM  https://aka.ms/vs/17/release/vc_redist.x64.exe
REM
REM  همچنین به 7-Zip نیاز داری (رایگان): https://www.7-zip.org
REM ============================================================

setlocal

REM --- 1) بیلد با پایتون 3.8 (آخرین نسخه‌ای که از ویندوز 7 پشتیبانی می‌کنه) ---
if not exist venv (
    py -3.8 -m venv venv
)
call venv\Scripts\activate
pip install -r requirements-desktop.txt --quiet
pip install pyinstaller --quiet

pyinstaller --noconfirm --clean --windowed --onedir --name Hesabdari --add-data "ui\icons;ui\icons" main.py

if not exist "dist\Hesabdari\Hesabdari.exe" (
    echo [XATA] بیلد PyInstaller شکست خورد. متن بالا رو چک کن.
    goto :end
)

REM --- 2) استخراج DLLهای UCRT از vc_redist و کپی مستقیم داخل _internal ---
if not exist vc_redist.x64.exe (
    echo [XATA] فایل vc_redist.x64.exe پیدا نشد. اول دانلودش کن و کنار این بچ فایل بذار.
    goto :end
)

if exist "%ProgramFiles%\7-Zip\7z.exe" (
    set SEVENZIP="%ProgramFiles%\7-Zip\7z.exe"
) else if exist "%ProgramFiles(x86)%\7-Zip\7z.exe" (
    set SEVENZIP="%ProgramFiles(x86)%\7-Zip\7z.exe"
) else (
    echo [XATA] 7-Zip پیدا نشد. از https://www.7-zip.org نصبش کن.
    goto :end
)

if exist vcredist_extract rmdir /s /q vcredist_extract
mkdir vcredist_extract
%SEVENZIP% x vc_redist.x64.exe -ovcredist_extract -y >nul

REM داخل vc_redist معمولاً یک کبینت به اسم a10, a11 یا مشابه با DLLها هست؛
REM همه‌ی dll هایی که اسمشون با api-ms-win یا ucrtbase یا vcruntime یا msvcp
REM شروع میشه رو پیدا و کپی می‌کنیم.
for /r vcredist_extract %%f in (api-ms-win*.dll ucrtbase.dll vcruntime140*.dll msvcp140*.dll) do (
    copy /y "%%f" "dist\Hesabdari\_internal\" >nul
)

echo.
echo [OK] DLLهای UCRT داخل dist\Hesabdari\_internal کپی شدن.
echo حالا dist\Hesabdari یک برنامه‌ی کاملاً مستقل و self-contained هست.
echo.

REM --- 3) تست حیاتی ---
echo این پوشه رو (dist\Hesabdari) روی یک ویندوز تمیز و بدون اینترنت تست کن
echo تا مطمئن بشی دیگه به هیچ‌چیزی وابسته نیست.

:end
endlocal