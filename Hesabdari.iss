; ====================================================================
;  این فایل رو با Inno Setup Compiler باز و کامپایل کن.
;  قبلش حتماً build_bulletproof.bat رو اجرا کرده باشی تا پوشه‌ی
;  dist\Hesabdari آماده باشه.
;  فایل vc_redist.x64.exe هم باید کنار همین فایل .iss باشه.
; ====================================================================

[Setup]
AppName=نرم افزار حسابداری
AppVersion=1.0.0
DefaultDirName={autopf}\Hesabdari
DefaultGroupName=نرم افزار حسابداری
OutputDir=output
OutputBaseFilename=Hesabdari-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\Hesabdari\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\نرم افزار حسابداری"; Filename: "{app}\Hesabdari.exe"
Name: "{autodesktop}\نرم افزار حسابداری"; Filename: "{app}\Hesabdari.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "ایجاد آیکون روی دسکتاپ"

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "نصب پیش‌نیازهای سیستمی..."; Flags: waituntilterminated
Filename: "{app}\Hesabdari.exe"; Description: "اجرای نرم افزار حسابداری"; Flags: nowait postinstall skipifsilent
