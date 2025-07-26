@echo off
echo Installing Python packages...
pip install pynput PyQt5 pyinstaller

echo.
echo Building executable with PyInstaller...
python -m PyInstaller --onefile --windowed main.py

echo.
echo Moving files...
if exist "dist\main.exe" (
    copy "dist\main.exe" "AutoClicker.exe"
    echo.
    echo SUCCESS! Your executable is ready: AutoClicker.exe
    echo You can now share this file with your friends.
) else (
    echo BUILD FAILED! Please check for errors above.
)

echo.
echo Cleaning up temporary files...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build" 
if exist "main.spec" del "main.spec"

echo.
pause
