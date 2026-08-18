راهنمای سریع — How_To_Run

این فایل تمام مراحلی که لازم است تا روی یک ماشین ویندوز (مثلاً ویندوز 11 خواهرِ شما) خروجی (installer) بسازید و آن را برای مشتری ضعیف ارسال کنید را مرحله‌به‌مرحله توضیح می‌دهد.

خلاصهٔ سریع
- هدف: ساخت یک بستهٔ نصبی (Hesabdari_Setup.exe) که مشتری فقط آن را اجرا کند و نیازی به نصب پایتون نداشته باشد.
- ایده: روی ماشین ویندوزی (ترجیحاً 32-bit Python روی ویندوز 11) یک onedir با PyInstaller بسازید، سپس با NSIS یک installer ایجاد کنید.

فایل‌ها و اسکریپت‌های آماده در این repo
- tools\build_windows_32.py  — اسکریپت کمکی برای آماده‌سازی باینری‌ها و فراخوانی PyInstaller (اجرای دستی روی ویندوز توصیه می‌شود).
- tools\build_windows_32.bat — wrapper ساده برای اجرا روی ویندوز.
- tools\installer.nsi — اسکریپت NSIS برای ساخت installer که محتویات dist\Hesabdari را کپی می‌کند و شورتکات می‌سازد.
- tools\build_installer.bat — wrapper برای اجرای makensis بر روی tools\installer.nsi.
- tools\compare_excels.py — ابزار مقایسهٔ دقیق سلول‌به‌سلول دو فایل Excel برای تایید خروجی‌ها.

پیش‌نیازها (روی ماشینِ خواهر)
1. Python 32-bit (توصیه: 3.10 یا 3.8) نصب شده و Add to PATH زده شود.
   دانلود از: https://www.python.org/downloads/windows/ (نسخهٔ x86 installer)
2. NSIS (برای ساخت installer): https://nsis.sourceforge.io/Download — مطمئن شوید makensis در PATH است.
3. (اختیاری، اما توصیه‌شده) Visual C++ Redistributable x86 (2015–2022): دانلود و قرار دهید در ریشهٔ repo با نام vc_redist.x86.exe تا installer آن را خودکار نصب کند.

دستورالعمل‌های قدم‌به‌قدم (CMD)
1) باز کردن CMD یا PowerShell با دسترسی معمولی یا admin (برای نصب redist ممکن است admin لازم باشد).

2) بررسی پایتون و معماریِ آن (اطمینان از 32-bit):
   python --version
   python -c "import struct,platform; print(platform.architecture(), struct.calcsize('P')*8)"
   خروجی باید نشان دهد 32-bit یا struct.calcsize('P')*8 = 32.  (اگر 64-bit بود و می‌خواهید 32-bit بسازید، نصب Python x86 لازم است.)

3) رفتن به پوشه پروژه (مثال):
   cd C:\path\to\python-app-performance-optimization

4) ساخت virtualenv 32-bit و فعال‌سازی:
   python -m venv venv32
   venv32\Scripts\activate

5) آپدیت pip و نصب وابستگی‌ها و PyInstaller:
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   pip install pyinstaller

6) ساخت onedir با PyInstaller (این دستور یک پوشهٔ dist\Hesabdari می‌سازد):
   pyinstaller --onedir --noconfirm --windowed --name Hesabdari --noupx main.py

   نکات:
   - اگر از قبل فایل build.spec دارید، می‌توانید از آن استفاده کنید: pyinstaller build.spec
   - پیغام‌ها را بخوانید؛ اگر missing package داشت، آن را نصب کنید (pip install <package>) و دوباره امتحان کنید.

7) بررسی خروجی PyInstaller:
   dir dist\Hesabdari
   انتظار داریم فایل Hesabdari.exe و python3x.dll و فولدرهایی مانند platforms و فایل‌های PyQt5 وجود داشته باشند.

8) (اختیاری اما توصیه‌شده) قرار دادن Visual C++ Redistributable:
   - اگر vc_redist.x86.exe را دانلود کردید، فایل را در مسیر ریشهٔ repo قرار دهید (همسطح پوشه tools). اسکریپت installer آن را شناسایی و نصب کرده و به‌صورت ساکت اجرا می‌کند.

9) ساخت installer با NSIS:
   - ابتدا مطمئن شوید makensis در PATH است:
       makensis -VERSION
   - سپس اجرا:
       makensis tools\installer.nsi
     یا با wrapper:
       tools\build_installer.bat

10) خروجی نهایی:
    dist_installer\Hesabdari_Setup.exe

11) تست installer (در همان ماشین خواهر):
    - دبل‌کلیک روی dist_installer\Hesabdari_Setup.exe و نصب را کامل کن.
    - پس از نصب، از شورتکات دسکتاپ یا منوی استارت برنامه را اجرا کن.
    - در برنامه یک گزارش بساز، Export Excel و PDF بگیر، و مطمئن شو همهٔ عملکردها سالم هستند.

فعال‌سازی حالت کم‌منابع (Low Resource) — برای مشتریان ضعیف
- موقت: قبل از اجرا در CMD یا در خواهرِت برای تست، می‌توانی متغیر محیطی را ست کنی:
  set LOW_RESOURCE=1
  سپس اجرا Hesabdari.exe یا نصب و اجرا از شورتکات.
- دائمی: در برنامه -> Settings -> تیک "حالت کم‌منابع" را بزن و ذخیره کن (نیاز به ری‌استارت برنامه دارد).

اعتبارسنجی خروجی‌های اکسل (تضمین عدم تغییر اعداد)
- اگر می‌خواهی مطمئن شوی اکسل‌های تولیدی قبل/بعد دقیقاً یکسان هستند، از ابزار زیر استفاده کن:
  python tools\compare_excels.py before.xlsx after.xlsx
- اگر فایل‌ها identical باشند پیام "Files are identical (cell-by-cell)" نمایش داده می‌شود.

عیب‌یابی سریع (خطاهای رایج و راه‌حل)
- خطا: "api-ms-win-core-path-l1-1-0.dll is missing"
  راه‌حل: نصب Visual C++ Redistributable x86 یا اجرای Windows Update. بهتر است vc_redist.x86.exe را همراه installer بفرستی.

- خطا: "Failed to load Python DLL ... pythonXX.dll"
  راه‌حل: اطمینان از اینکه dist\Hesabdari شامل python3x.dll است. اگر نیست، با Python x86 در build machine دوباره PyInstaller را اجرا کن.

- خطا: آنتی‌ویروس جلوی اجرای onefile یا استخراج فایل‌ها را می‌گیرد
  راه‌حل: استفاده از onedir به‌جای onefile (که ما همین کار را کردیم). در صورت مشکل AV نیاز به whitelist یا ارسال دستورالعمل فراخوانی AV است.

چک‌لیست ساده برای خواهرِت (تیک‌زنی)
1. [ ] Python x86 نصب شد و در PATH است
2. [ ] venv ساخته و فعال شد (venv32)
3. [ ] pip install -r requirements.txt  انجام شد
4. [ ] pyinstaller command اجرا شد و dist\Hesabdari ساخته شد
5. [ ] (اختیاری) vc_redist.x86.exe کنار repo قرار گرفت
6. [ ] makensis اجرا شد و dist_installer\Hesabdari_Setup.exe تولید شد
7. [ ] روی همان ماشین نصب و اجرای آزمایشی انجام شد (باز کردن، export)

اگر خواستی من می‌توانم یک اسکریپت batch بسازم که بیشتر این مراحل را اتومات کند (اما نیاز است Python x86 و NSIS از پیش نصب شده باشند). می‌خواهی من یک .bat اتوماتیک برای اجرا در ویندوز خواهر بسازم؟

پایان

اگر هر مرحله را اجرا کردی و به خطا برخوردی، خروجی CMD یا عکس پنجره خطا و لیست فایل‌های پوشه dist\Hesabdari را بفرست تا دقیق‌تر راهنمایی کنم. موفق باشی!