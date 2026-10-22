@echo off
setlocal
cd /d "%~dp0"
py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "자리온" seat_allocator.py
if errorlevel 1 exit /b 1
echo.
echo Build complete: dist\자리온.exe
pause
