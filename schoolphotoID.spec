# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Get the correct path separator for the current platform
separator = ";" if sys.platform == "win32" else ":"

a = Analysis(
    ["schoolphotoID/main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "face_recognition",
        "dlib",
        "cv2",
        "numpy",
        "PIL",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_console_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SchoolPhotoID",
    debug=False,
    bootloader_ignore_binaries=False,
    strip=False,
    upx=False,
    upx_compress=0,
    windowed=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_compress=None,
    name="SchoolPhotoID",
)