@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 -m pip install --user -r requirements-dev.txt
if not exist vendor\ffmpeg\ffmpeg.exe py -3 tools\fetch_ffmpeg.py
if errorlevel 1 exit /b 1
py -3 -m PyInstaller --noconfirm --onedir --windowed --name Capture-ecran-PLAI --icon capture_ecran\assets\icon.ico --add-data "capture_ecran\assets;capture_ecran\assets" lanceur.py
mkdir dist\Capture-ecran-PLAI\ffmpeg 2>nul
copy /y vendor\ffmpeg\* dist\Capture-ecran-PLAI\ffmpeg\ >nul
copy /y capture_ecran\assets\mode-emploi.html dist\Capture-ecran-PLAI\Mode-emploi.html >nul
copy /y LICENSE dist\Capture-ecran-PLAI\ >nul
echo.
echo Termine : dist\Capture-ecran-PLAI\Capture-ecran-PLAI.exe
echo Installateur : "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" /DMyAppVersion=1.3.0 installer\capture-ecran.iss
pause
