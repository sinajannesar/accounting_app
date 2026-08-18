    راهنمای گام‌به‌گام (HOW_TO_RUN.md)

    هدف
    - راهنمای ساده و دقیق برای ساخت «پوشهٔ اجرایی (onedir)» و در صورت تمایل «نصب‌کنندهٔ ویندوز (installer)» از پروژهٔ حسابداری، با استفاده از فایل خودکار tools\auto_build_and_pack.bat. این راهنما مخصوص کسی است که دانش فنی کمی دارد (مثل خواهرت) و شامل چک‌لیست و حل مشکلات رایج است.

    خلاصهٔ سریع
    - روی یک سیستم ویندوزی (ترجیحاً با Python 32-bit نصب‌شده) اجرا کن.
    - tools\auto_build_and_pack.bat تقریباً همهٔ مراحل را خودکار انجام می‌دهد: ساخت virtualenv، نصب وابستگی‌ها، اجرای PyInstaller (--onedir --noupx) و در صورت وجود NSIS ساخت installer.

    فایل‌های مرتبط (در repo)
    - tools\auto_build_and_pack.bat  ← اجرای خودکار کل جریان ساخت (توصیه‌شده)
    - tools\build_windows_32.bat    ← اسکریپت کمکی دیگر برای ویندوز
    - tools\installer.nsi           ← اسکریپت NSIS برای تولید Hesabdari_Setup.exe
    - tools\build_installer.bat     ← wrapper برای makensis
    - tools\compare_excels.py       ← مقایسهٔ سلول‌به‌سلول فایل‌های اکسل (برای تضمین عدم تغییر محاسبات)

    پیش‌نیازهای قابل‌بررسی قبل از شروع
    1) Python 32-bit نصب شده و در PATH باشد (توصیه: 3.10 یا 3.11 x86).
    - دانلود: https://www.python.org/downloads/windows/ (Windows x86 installer)
    2) NSIS (اختیاری، برای ساخت installer .exe). اگر نصب نیست، باز هم onedir ساخته می‌شود.
    - دانلود: https://nsis.sourceforge.io/Download
    3) (اختیاری) اگر می‌خواهی Visual C++ Redistributable را همراه installer بفرستی، فایل vc_redist.x86.exe را دانلود کن و در ریشهٔ repo قرار بده.

    نکته دربارهٔ معماری (خیلی مهم)
    - برای بیشترین سازگاری با سیستم‌های قدیمی و ضعیف، توصیه می‌شود از Python نسخهٔ 32-bit برای ساخت استفاده شود. اگر سیستمِ سازنده 64-bit است و Python 64-bit نصب است، خروجی ممکن است در برخی Windowsهای خیلی قدیمی مشکل داشته باشد.

    دستورالعملِ دقیق (مخصوص خواهر یا کاربر کم‌تجربه)
    1) پوشهٔ پروژه را روی سیستم ویندوز قرار بده (با کپی یا استخراج ZIP).
    2) CMD (Command Prompt) را باز کن. برای نصب VC++ Redistributable ممکن است لازم باشد "Run as administrator" انجام شود، اما برای ساخت معمولی نیازی به admin نیست.
    3) به پوشهٔ پروژه برو:
    cd C:\مسیر\به\پروژه

    4) اجرای خودکار همهٔ مراحل (ساده‌ترین راه)
    - فقط این دستور را اجرا کن:
    tools\auto_build_and_pack.bat

    چه کار می‌کند؟
    - بررسی می‌کند Python وجود دارد و معماری آن را نشان می‌دهد.
    - اگر virtualenv (venv32) ساخته نشده باشد آن را می‌سازد و فعال می‌کند.
    - pip را آپدیت می‌کند و وابستگی‌ها را از requirements.txt نصب می‌کند.
    - PyInstaller را نصب و اجرا می‌کند با گزینه‌های --onedir و --noupx تا پوشهٔ dist\Hesabdari ساخته شود.
    - اگر makensis (NSIS) در PATH وجود داشته باشد، به‌صورت خودکار tools\build_installer.bat را اجرا می‌کند تا dist_installer\Hesabdari_Setup.exe ساخته شود.

    نکته: اگر در میانهٔ کار از شما پرسشی شد (مثلاً معماری 64-bit)، معمولاً می‌توانید دستورالعمل روی صفحه را دنبال کنید یا از گزینهٔ پیش‌فرض استفاده کنید؛ اگر مطمئن نیستی عکس یا متن خطا را بفرست تا راهنمایی کنم.

    5) اگر می‌خواهی مراحل را دستی انجام دهی (گام‌های تفصیلی):
    - ساخت virtualenv و فعال‌سازی:
     python -m venv venv32
     venv32\Scripts\activate

    - آپدیت pip و نصب وابستگی‌ها:
     python -m pip install --upgrade pip setuptools wheel
     pip install -r requirements.txt
     pip install pyinstaller

    - اجرای PyInstaller (اگر می‌خواهی مستقیم اجرا کنی):
     pyinstaller --onedir --noconfirm --windowed --name Hesabdari --noupx main.py

    - ساخت installer (در صورت نصب NSIS):
     makensis tools\installer.nsi
     یا
     tools\build_installer.bat

    خروجی‌ها و محلِ آن‌ها
    - پوشهٔ اجرایی (همیشه ساخته می‌شود): dist\Hesabdari
     - داخلش باید Hesabdari.exe و فایل‌های وابسته (python3x.dll و پوشه‌های لازم) باشد.
    - فایل نصبی (در صورت وجود NSIS): dist_installer\Hesabdari_Setup.exe

    تست سریع برای اطمینان از کارکرد (پس از ساخت)
    1) اگر dist\Hesabdari هست: در File Explorer وارد آن شو و دوبار روی Hesabdari.exe کلیک کن؛ برنامه باید باز شود.
    2) اگر installer ساخته شده: installer را اجرا و برنامه را نصب کن. سپس برنامه نصب‌شده را اجرا کن.
    3) داخل برنامه یک گزارش ساده بساز و Export به Excel بگیر.
    4) در صورتِ داشتن خروجی قبل/بعد، برای اطمینان از عدم تغییر در اعداد:
    python tools\compare_excels.py before.xlsx after.xlsx

    اگر خطایی دیدی چه کار کنی (عیب‌یابی)
    - خطا: "python is not recognized"
     - آشناترین علت: Python در PATH نیست. Python x86 را نصب و گزینه "Add to PATH" را فعال کن.

    - خطا: missing DLL مانند api-ms-win-core-*.dll یا pythonXX.dll
     - راه‌حل: مطمئن شو در هنگام ساخت از Python 32-bit استفاده شده؛ اگر نیاز به Visual C++ Redistributable است، vc_redist.x86.exe را در کنار repo قرار بده یا آن را جداگانه نصب کن.

    - خطا: PyInstaller بسته‌ای را پیدا نکرد
     - خطا معمولاً نامِ پکیج را نشان می‌دهد؛ آن بسته را pip install کن و دوباره pyinstaller را اجرا کن.

    - اگر makensis (NSIS) نصب نیست
     - پیام در اسکریپت نمایش داده می‌شود؛ در این حالت فقط پوشهٔ dist ساخته می‌شود. می‌توانی پوشهٔ dist\Hesabdari را ZIP کنی و به مشتری بدهی.

    نکات مخصوصِ سیستم‌های خیلی ضعیف (هدف نهایی)
    - استفاده از onedir بهتر از onefile است (ما از --onedir استفاده کردیم) زیرا برنامه بدون فرایند استخراج سریع‌تر اجرا می‌شود و فشار CPU کمتر است.
    - برای مشتری نهایی، توصیه می‌شود installer را با vc_redist.x86.exe همراه کنی تا خطاهای DLL کمتر رخ دهد.
    - حالت Low Resource: برای مشتریانی با رم کم یا CPU ضعیف، قبل از اجرای برنامه می‌توان متغیر محیطی را قرار داد:
     set LOW_RESOURCE=1
     یا از داخل Settings برنامه "Low Resource Mode" را فعال کن.

    چک‌لیست نهایی (برای تیک زدن قبل از ارسال به مشتری)
    [ ] Python x86 (32-bit) روی ماشین سازنده نصب شده و در PATH است
    [ ] tools\auto_build_and_pack.bat اجرا شده و هیچ خطای حیاتی نداشته
    [ ] پوشهٔ dist\Hesabdari وجود دارد و Hesabdari.exe قابل اجراست
    [ ] (در صورت نیاز) dist_installer\Hesabdari_Setup.exe ساخته شده
    [ ] در برنامه export اکسل تست شده و مقادیر صحیح نمایش داده می‌شوند

    اگر خواستی این نسخهٔ HOW_TO_RUN.md را همین‌جا ذخیره کنم و برای خواهر یک فایل متنی سادهٔ "HOW_TO_RUN_FOR_SISTER.txt" اضافه کنم تا مستقیم بفرستی، بگو تا اضافه کنم. همچنین هر زمان که خروجی CMD یا ارور دیدی، آن را اینجا بفرست تا دقیق‌تر کمک کنم.