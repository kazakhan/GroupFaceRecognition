"""
Setup module that must be imported before face_recognition.
This makes face_recognition find our local model files when running as exe.
"""

import sys
import os
from pathlib import Path

def _get_models_path():
    """Get path to models folder - works for both Python and exe."""
    # Get project root (works whether running as exe or Python)
    project_root = Path(__file__).resolve().parent.parent
    
    if getattr(sys, 'frozen', False):
        # Running as exe - check next to exe AND project root
        paths_to_check = [
            Path(sys.executable).parent / "models",           # dist/models/
            project_root / "models",                         # SchoolFacerecognition/models/
        ]
    else:
        # Running as Python - check project root
        paths_to_check = [project_root / "models"]
    
    for models_path in paths_to_check:
        if models_path.exists():
            # Verify it has at least one .dat file
            dat_files = list(models_path.glob("*.dat"))
            if dat_files:
                print(f"Found models in: {models_path}")
                return str(models_path)
    
    # No local models - return None to use pip's package
    print("Warning: No local models found")
    return None

# Try to find local models
_models_dir = _get_models_path()

# If we have local models, inject them into face_recognition_models
if _models_dir:
    import types
    
    MODEL_DIR = _models_dir
    
    face_recognition_models = types.ModuleType('face_recognition_models')
    face_recognition_models.__file__ = __file__
    
    def pose_predictor_model_location():
        return str(Path(MODEL_DIR) / "shape_predictor_68_face_landmarks.dat")
    
    def pose_predictor_five_point_model_location():
        return str(Path(MODEL_DIR) / "shape_predictor_5_face_landmarks.dat")
    
    def cnn_face_detector_model_location():
        return str(Path(MODEL_DIR) / "mmod_human_face_detector.dat")
    
    def face_recognition_model_location():
        return str(Path(MODEL_DIR) / "dlib_face_recognition_resnet_model_v1.dat")
    
    face_recognition_models.pose_predictor_model_location = pose_predictor_model_location
    face_recognition_models.pose_predictor_five_point_model_location = pose_predictor_five_point_model_location
    face_recognition_models.cnn_face_detector_model_location = cnn_face_detector_model_location
    face_recognition_models.face_recognition_model_location = face_recognition_model_location
    
    sys.modules['face_recognition_models'] = face_recognition_models
else:
    print("Note: Using pip's face_recognition_models")