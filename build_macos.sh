#!/bin/bash
# Build script for macOS
# Usage: ./build.sh

set -e

echo "Building SchoolPhotoID for macOS..."

# Install system dependencies
brew install cmake

# Install Python dependencies
pip install PyInstaller PyQt6 face-recognition dlib numpy opencv-python Pillow

# Clean previous builds
rm -rf dist build

# Build using spec file
pyinstaller main.spec

# Rename output
if [ -f dist/SchoolPhotoID ]; then
    mv dist/SchoolPhotoID dist/SchoolPhotoID-macos
    chmod +x dist/SchoolPhotoID-macos
    echo ""
    echo "Build complete: dist/SchoolPhotoID-macos"
fi