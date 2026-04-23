#!/bin/bash
# Build script for Linux
# Usage: ./build.sh

set -e

echo "Building SchoolPhotoID for Linux..."

# Install system dependencies
sudo apt-get update
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev cmake libgtk-3-dev

# Install Python dependencies
pip install PyInstaller PyQt6 face-recognition dlib numpy opencv-python Pillow

# Clean previous builds
rm -rf dist build

# Build using spec file
pyinstaller main.spec

# Rename output
if [ -f dist/SchoolPhotoID ]; then
    mv dist/SchoolPhotoID dist/SchoolPhotoID-linux
    chmod +x dist/SchoolPhotoID-linux
    echo ""
    echo "Build complete: dist/SchoolPhotoID-linux"
fi