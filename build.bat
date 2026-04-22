@echo off
REM Build script for Windows
REM Usage: Run in PowerShell or Command Prompt

echo Building SchoolPhotoID for Windows...

REM Install dependencies
pip install PyInstaller PyQt6 face-recognition dlib numpy opencv-python Pillow

REM Clean previous builds
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build
pyinstaller --onefile --windowed --name "SchoolPhotoID" schoolphotoID/main.py

REM Rename output
if exist dist\SchoolPhotoID.exe (
    move dist\SchoolPhotoID.exe dist\SchoolPhotoID-windows.exe
    echo.
    echo Build complete: dist\SchoolPhotoID-windows.exe
) else (
    echo Build failed!
    exit /b 1
)