"""Face recognition and identification."""

import warnings
from pathlib import Path
from typing import List, Dict, Tuple, Optional

warnings.filterwarnings('ignore', category=UserWarning, module='face_recognition_models')
warnings.filterwarnings('ignore', category=DeprecationWarning)

try:
    import face_recognition
    import cv2
except ImportError:
    face_recognition = None
    cv2 = None


# Allowed image extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}


def detect_faces(
    image_path: str,
    model: str = "hog",
    num_jitters: int = 1,
) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in an image.

    Args:
        image_path: Path to image file
        model: "hog" for CPU, "cnn" for GPU, "cuda" for CUDA GPU
        num_jitters: Number of times to re-sample the face when encoding

    Returns:
        List of face locations as (top, right, bottom, left) tuples
    """
    if face_recognition is None:
        raise ImportError("face_recognition library not available")

    image = face_recognition.load_image_file(image_path)
    face_locs = face_recognition.face_locations(
        image,
        model=model,
        num_jitters=num_jitters
    )

    return face_locs


def identify_faces(
    image_path: str,
    known_encodings: List,
    known_names: List[str],
    known_paths: List[str],
    face_model: str = "hog",
    tolerance: float = 0.6,
    progress_callback: Optional[callable] = None,
) -> Dict:
    """
    Identify faces in a group photo.

    Args:
        image_path: Path to group photo
        known_encodings: List of known face encodings
        known_names: List of person names corresponding to encodings
        known_paths: List of paths to known face images
        face_model: Detection model ("hog", "cnn", "cuda")
        tolerance: Lower = more strict matching (default 0.6)
        progress_callback: Optional callback(percent, message)

    Returns:
        Dict with keys:
            - faces_detected: int
            - people_identified: int
            - faces: List[Dict{box, name, distance}]
            - annotated_image_path: str (if saved)
    """
    if face_recognition is None:
        raise ImportError("face_recognition library not available")
    if cv2 is None:
        raise ImportError("opencv-python not available")

    # Detect faces
    if progress_callback:
        progress_callback(10, "Loading image...")

    image = face_recognition.load_image_file(image_path)
    original_height, original_width = image.shape[:2]

    # Detect face locations
    if progress_callback:
        progress_callback(30, "Detecting faces...")

    face_locs = face_recognition.face_locations(image, model=face_model)

    if not face_locs:
        return {
            "faces_detected": 0,
            "people_identified": 0,
            "faces": [],
            "image_path": image_path,
        }

    # Encode all detected faces
    if progress_callback:
        progress_callback(50, "Encoding detected faces...")

    encodings = face_recognition.face_encodings(image, face_locs)

    # Compare to known faces
    results = []
    for idx, encoding in enumerate(encodings):
        matches = face_recognition.compare_faces(
            known_encodings,
            encoding,
            tolerance=tolerance
        )

        if True in matches:
            match_indices = [i for i, m in enumerate(matches) if m]
            best_idx = min(
                match_indices,
                key=lambda i: face_recognition.face_distance(
                    [known_encodings[i]],
                    encoding
                )[0]
            )
            name = known_names[best_idx]
            distance = face_recognition.face_distance(
                [known_encodings[best_idx]],
                encoding
            )[0]
        else:
            name = "Unknown"
            distance = 1.0

        # Scale coordinates back to original if needed
        box = face_locs[idx]
        top, right, bottom, left = box

        results.append({
            "name": name,
            "distance": distance,
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
        "faces_detected": len(face_locs),
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