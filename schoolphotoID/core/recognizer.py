"""Face recognition and identification using dlib with local models."""

import os
import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

import dlib

warnings.filterwarnings('ignore', category=DeprecationWarning)


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}


def create_recognition_models(models_dir: str):
    """Create and return dlib recognition models."""
    models_path = Path(models_dir)
    shape_model = models_path / "shape_predictor_68_face_landmarks.dat"
    encoder_model = models_path / "dlib_face_recognition_resnet_model_v1.dat"

    if not shape_model.exists():
        raise FileNotFoundError(f"Shape model not found: {shape_model}")
    if not encoder_model.exists():
        raise FileNotFoundError(f"Encoder model not found: {encoder_model}")

    face_detector = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(str(shape_model))
    face_encoder = dlib.face_recognition_model_v1(str(encoder_model))

    return face_detector, shape_predictor, face_encoder


def detect_faces(
    image_path: str,
    face_detector,
    shape_predictor,
    face_encoder,
    num_jitters: int = 1,
) -> List[Dict]:
    """
    Detect faces in an image using dlib.

    Args:
        image_path: Path to image file
        face_detector: dlib face detector
        shape_predictor: dlib shape predictor
        face_encoder: dlib face encoder
        num_jitters: Number of times to re-sample the face when encoding

    Returns:
        List of detected face info dicts with 'box' (top, right, bottom, left) and 'encoding'
    """
    image = dlib.load_rgb_image(image_path)
    faces = face_detector(image)

    results = []
    for face in faces:
        shape = shape_predictor(image, face)
        encoding = np.array(face_encoder.compute_face_descriptor(image, shape, num_jitters))

        top = face.top()
        right = face.right()
        bottom = face.bottom()
        left = face.left()

        results.append({
            "box": {"top": top, "right": right, "bottom": bottom, "left": left},
            "encoding": encoding
        })

    return results


def identify_faces(
    image_path: str,
    known_encodings: List,
    known_names: List[str],
    known_paths: List[str],
    models_dir: str,
    tolerance: float = 0.6,
    progress_callback: Optional[callable] = None,
) -> Dict:
    """
    Identify faces in a group photo using dlib with local models.

    Args:
        image_path: Path to group photo
        known_encodings: List of known face encodings (128-d arrays)
        known_names: List of person names corresponding to encodings
        known_paths: List of paths to known face images
        models_dir: Path to directory containing dlib model files
        tolerance: Lower = more strict matching (default 0.6)
        progress_callback: Optional callback(percent, message)

    Returns:
        Dict with keys:
            - faces_detected: int
            - people_identified: int
            - faces: List[Dict{box, name, distance}]
            - annotated_image_path: str (if saved)
    """
    if not known_encodings:
        return {
            "faces_detected": 0,
            "people_identified": 0,
            "faces": [],
            "image_path": image_path,
        }

    if progress_callback:
        progress_callback(10, "Loading image...")

    try:
        face_detector, shape_predictor, face_encoder = create_recognition_models(models_dir)
    except Exception as e:
        return {
            "faces_detected": 0,
            "people_identified": 0,
            "faces": [],
            "image_path": image_path,
            "error": str(e),
        }

    try:
        image = dlib.load_rgb_image(image_path)
    except Exception as e:
        return {
            "faces_detected": 0,
            "people_identified": 0,
            "faces": [],
            "image_path": image_path,
            "error": str(e),
        }

    if progress_callback:
        progress_callback(30, "Detecting faces...")

    try:
        faces = face_detector(image)
    except Exception as e:
        faces = []

    if not faces:
        return {
            "faces_detected": 0,
            "people_identified": 0,
            "faces": [],
            "image_path": image_path,
        }

    if progress_callback:
        progress_callback(50, "Encoding detected faces...")

    results = []
    for face in faces:
        shape = shape_predictor(image, face)
        encoding = np.array(face_encoder.compute_face_descriptor(image, shape))

        best_match_idx = -1
        best_distance = 1.0
        best_name = "Unknown"

        for idx, known_enc in enumerate(known_encodings):
            dist = np.linalg.norm(encoding - known_enc)
            if dist < tolerance and dist < best_distance:
                best_distance = dist
                best_match_idx = idx
                best_name = known_names[idx]

        top = face.top()
        right = face.right()
        bottom = face.bottom()
        left = face.left()

        results.append({
            "name": best_name,
            "distance": float(best_distance),
            "box": {
                "top": top,
                "right": right,
                "bottom": bottom,
                "left": left,
            }
        })

    if progress_callback:
        progress_callback(100, f"Detected {len(results)} faces")

    return {
        "faces_detected": len(faces),
        "people_identified": sum(1 for r in results if r["name"] != "Unknown"),
        "faces": results,
        "image_path": image_path,
    }


def get_image_files(directory: str) -> List[Path]:
    """Get all image files from a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    files = []
    for f in dir_path.iterdir():
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(f)

    return sorted(files)