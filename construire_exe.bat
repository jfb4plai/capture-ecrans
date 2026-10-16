@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 -m pip install --user -r requirements-dev.txt
py -3 -m PyInstaller --noconfirm --onedir --windowed --name Capture-ecran-PLAI --icon capture_ecran\assets\icon.ico --add-data "capture_ecran\assets;capture_ecran\assets" capture_ecran\__main__.py
echo.
echo Termine : dist\Capture-ecran-PLAI\Capture-ecran-PLAI.exe
pause
