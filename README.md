# School Photo Identifier

Desktop application for face recognition and identification in school photos.

## Features

- Detect and identify faces in group photos using OpenCV
- Load known faces from directory
- Annotate images with face boxes and names
- Export ordered CSV lists (row-wise sorted for photo printing)
- Sort loose images into person subfolders
- Self-contained executables for Windows, Linux, macOS

## Requirements

- Python 3.9+ (3.11 recommended)
- PyQt6
- opencv-python
- numpy
- Pillow

## No dlib Required

This version uses OpenCV Haar Cascade instead of dlib/face_recognition, avoiding complex C++ compilation.

## Pre-Built Executables

Download from the Releases page:

| Platform | File |
|----------|------|
| Windows | SchoolPhotoID-windows.exe |
| Linux | SchoolPhotoID-linux |
| macOS | SchoolPhotoID-macos |

## Building from Source

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Build for Windows

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --collect-all PyQt6 --name "SchoolPhotoID-windows" schoolphotoID/main.py
```

### Build for Linux

```bash
chmod +x build.sh
./build.sh
```

### Build for macOS

```bash
chmod +x build_macos.sh
./build_macos.sh
```

## Workflow

1. **Sort Images into Folders** (if needed)
   - Takes loose photos (John_Smith.jpg)
   - Creates subfolders (John Smith/John_Smith.jpg)

2. **Select Known Faces directory**
   - Parent folder containing person subfolders

3. **Select Images directory**
   - Folder with group photos to process

4. **Select Output directory**
   - Where to save results

5. **Click Load Known Faces**

6. **Select images to process**

7. **Click Process Selected**

## Output Files

For each processed image:

| File | Description |
|------|------------|
| *_annotated.jpg | Image with face boxes and names |
| *_faces.csv | Position, name, distance |
| *_faces_order.txt | Row-wise ordered names |

## CI/CD Build

Pushes to main automatically build executables for all platforms via GitHub Actions.

## License

MIT