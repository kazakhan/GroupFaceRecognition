import bz2
import shutil
import os

MODEL_DIR = r"D:\dev\SchoolFacerecognition\models"

files = [
    ("shape_predictor_68_face_landmarks.dat.bz2", "shape_predictor_68_face_landmarks.dat"),
    ("dlib_face_recognition_resnet_model_v1.dat.bz2", "dlib_face_recognition_resnet_model_v1.dat"),
    ("shape_predictor_5_face_landmarks.dat.bz2", "shape_predictor_5_face_landmarks.dat"),
    ("mmod_human_face_detector.dat.bz2", "mmod_human_face_detector.dat"),
]

for src_bz2, dst in files:
    src = os.path.join(MODEL_DIR, src_bz2)
    if not os.path.exists(src):
        print(f"Skipping {src} (not found)")
        continue
    print(f"Decompressing {src_bz2}...")
    dst_path = os.path.join(MODEL_DIR, dst)
    with bz2.BZ2File(src, 'rb') as f_in:
        with open(dst_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print(f"Done! Size: {os.path.getsize(dst_path)} bytes")