"""Load known faces from directory."""

import os
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

warnings.filterwarnings('ignore', category=UserWarning, module='face_recognition_models')
warnings.filterwarnings('ignore', category=DeprecationWarning)

try:
    import face_recognition
except ImportError:
    face_recognition = None


class KnownFaceDatabase:
    """Database of known face encodings."""

    def __init__(self):
        self.encodings: List[np.ndarray] = []
        self.names: List[str] = []
        self.image_paths: List[str] = []
        self._loaded = False

    def clear(self):
        """Clear all encodings."""
        self.encodings.clear()
        self.names.clear()
        self.image_paths.clear()
        self._loaded = False

    def is_loaded(self) -> bool:
        """Check if faces are loaded."""
        return self._loaded

    def count(self) -> int:
        """Return number of known faces."""
        return len(self.names)


def load_known_faces(
    faces_dir: str,
    progress_callback: Optional[callable] = None,
) -> Tuple[KnownFaceDatabase, List[str]]:
    """
    Load known faces from subdirectories.

    Each subdirectory represents a person, named as "First Last".
    Inside each subdirectory should be a photo of that person.

    Args:
        faces_dir: Path to directory containing person subdirectories
        progress_callback: Optional callback(percent, message) for progress

    Returns:
        Tuple of (KnownFaceDatabase, list of person names)
    """
    if face_recognition is None:
        raise ImportError("face_recognition library not available")

    faces_path = Path(faces_dir)
    if not faces_path.exists():
        raise FileNotFoundError(f"Faces directory not found: {faces_dir}")

    db = KnownFaceDatabase()
    person_names = []

    subdirs = [d for d in faces_path.iterdir() if d.is_dir()]
    total = len(subdirs)

    if total == 0:
        return db, person_names

    for idx, person_dir in enumerate(sorted(subdirs)):
        person_name = person_dir.name

        if progress_callback:
            progress_callback(
                (idx / total) * 100,
                f"Processing '{person_name}'..."
            )

        jpg_files = list(person_dir.glob("*.jpg")) + list(person_dir.glob("*.jpeg")) + list(person_dir.glob("*.png"))

        if not jpg_files:
            continue

        image_file = jpg_files[0]

        try:
            image = face_recognition.load_image_file(str(image_file))
            encodings = face_recognition.face_encodings(image)

            if encodings:
                db.encodings.append(encodings[0])
                db.names.append(person_name)
                db.image_paths.append(str(image_file))
                person_names.append(person_name)

                if progress_callback:
                    progress_callback(
                        (idx / total) * 100,
                        f"Loaded face from {image_file.name}"
                    )
        except Exception as e:
            print(f"Error loading {image_file}: {e}")
            continue

    db._loaded = True

    if progress_callback:
        progress_callback(100, f"Summary: {len(person_names)} face encodings loaded")

    return db, person_names