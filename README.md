# School Photo Identifier

Desktop application for face recognition and identification in school photos.

## Features

- Detect and identify faces in group photos
- Load known faces from directory
- Annotate images with face boxes and names
- Export ordered CSV lists (row-wise sorted for photo printing)
- Sort loose images into person subfolders
- Self-contained executables for Windows, Linux, macOS

## Pre-Built Executables

Download from the Releases page:

| Platform | File |
|----------|------|
| Windows | SchoolPhotoID-windows.exe |
| Linux | SchoolPhotoID-linux |
| macOS | SchoolPhotoID-macos |

## Building from Source

### Windows

```bash
./build.bat
```

### Linux

```bash
chmod +x build.sh
./build.sh
```

### macOS

```bash
chmod +x build_macos.sh
./build_macos.sh
```

## Building with PyInstaller (manual)

```bash
pip install PyInstaller PyQt6 face-recognition dlib numpy opencv-python Pillow
pyinstaller --onefile --windowed --name "SchoolPhotoID" schoolphotoID/main.py
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