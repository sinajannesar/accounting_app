; NSIS script to package Hesabdari onedir into a Windows installer
; Usage: Place the folder dist\Hesabdari next to this script, plus optionally vc_redist.x86.exe
; Then on a Windows build machine with NSIS installed, run: makensis tools\installer.nsi

; Request admin to allow writing to Program Files and installing VC runtime
RequestExecutionLevel admin

Name "Hesabdari"
OutFile "dist_installer\Hesabdari_Setup.exe"
InstallDir "$PROGRAMFILES32\Hesabdari"
ShowInstDetails show
ShowUninstDetails show

Var VCREDIST_EXISTS

; Pages
Page directory
Page instfiles

; Uninstaller
UninstPage uninstConfirm
UninstPage instfiles

; Sections
Section "Install"
  SetOutPath "$INSTDIR"

  ; Include all files from dist\Hesabdari
  ; The packager should ensure tools\installer.nsi is executed from repo root
  ; and dist\Hesabdari exists.
  SetOverwrite ifnewer
  File /r "dist\Hesabdari\*"

  ; Create Start Menu folder and shortcut
  CreateDirectory "$SMPROGRAMS\Hesabdari"
  CreateShortCut "$SMPROGRAMS\Hesabdari\Hesabdari.lnk" "$INSTDIR\Hesabdari.exe" "" "$INSTDIR\Hesabdari.exe" 0

  ; Desktop shortcut
  CreateShortCut "$DESKTOP\Hesabdari.lnk" "$INSTDIR\Hesabdari.exe" "" "$INSTDIR\Hesabdari.exe" 0

  ; Optionally install Visual C++ redistributable if present in the installer dir
  StrCpy $R0 "$EXEDIR\vc_redist.x86.exe"
  IfFileExists "$R0" 0 +2
    StrCpy $VCREDIST_EXISTS "1"

  ${If} $VCREDIST_EXISTS == "1"
    ; Run silent install to avoid user interaction. Use /install /quiet /norestart where supported.
    ExecWait '"$R0" /install /quiet /norestart' ; may require admin privileges
  ${EndIf}

  ; Write an entry for uninstall
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Hesabdari" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Hesabdari" "DisplayName" "Hesabdari"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Hesabdari" "DisplayVersion" "1.0"
SectionEnd

Section "Uninstall"
  ; Remove shortcuts
  Delete "$SMPROGRAMS\Hesabdari\Hesabdari.lnk"
  RMDir "$SMPROGRAMS\Hesabdari"
  Delete "$DESKTOP\Hesabdari.lnk"

  ; Remove all installed files
  RMDir /r "$INSTDIR"

  ; Remove uninstall registry
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Hesabdari"
SectionEnd

; EOF
