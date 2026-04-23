"""
Local face_recognition_models package that provides paths to downloaded model files.
"""

import sys
from pathlib import Path

this_file = Path(__file__).resolve()
_PROJECT_ROOT = this_file.parent.parent.parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

MODEL_DIR = _PROJECT_ROOT / "models"

def pose_predictor_model_location():
    """Return path to shape predictor 68 face landmarks model."""
    return str(MODEL_DIR / "shape_predictor_68_face_landmarks.dat")

def pose_predictor_five_point_model_location():
    """Return path to shape predictor 5 face landmarks model."""
    return str(MODEL_DIR / "shape_predictor_5_face_landmarks.dat")

def cnn_face_detector_model_location():
    """Return path to CNN face detector model."""
    return str(MODEL_DIR / "mmod_human_face_detector.dat")

def face_recognition_model_location():
    """Return path to face recognition ResNet model."""
    return str(MODEL_DIR / "dlib_face_recognition_resnet_model_v1.dat")