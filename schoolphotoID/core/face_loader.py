"""Load known faces from directory using dlib with local models."""

import os
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

import dlib

warnings.filterwarnings('ignore', category=DeprecationWarning)


class KnownFaceDatabase:
    """Database of known face encodings."""

    def __init__(self):
        self.encodings: List[np.ndarray] = []
        self.names: List[str] = []
        self.image_paths: List[str] = []
        self._loaded = False
        self._face_detector = None
        self._shape_predictor = None
        self._face_encoder = None

    @property
    def known_images(self) -> List[np.ndarray]:
        """Compatibility property - returns images list (empty for dlib)."""
        return []

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

    def _init_models(self, models_dir: str):
        """Initialize dlib models from local files."""
        models_path = Path(models_dir)
        shape_model = models_path / "shape_predictor_68_face_landmarks.dat"
        encoder_model = models_path / "dlib_face_recognition_resnet_model_v1.dat"

        if not shape_model.exists():
            raise FileNotFoundError(f"Shape model not found: {shape_model}")
        if not encoder_model.exists():
            raise FileNotFoundError(f"Encoder model not found: {encoder_model}")

        self._face_detector = dlib.get_frontal_face_detector()
        self._shape_predictor = dlib.shape_predictor(str(shape_model))
        self._face_encoder = dlib.face_recognition_model_v1(str(encoder_model))


def load_known_faces(
    faces_dir: str,
    models_dir: str,
    progress_callback: Optional[callable] = None,
) -> Tuple[KnownFaceDatabase, List[str]]:
    """
    Load known faces from subdirectories using dlib with local models.

    Each subdirectory represents a person, named as "First Last".
    Inside each subdirectory should be a photo of that person.

    Args:
        faces_dir: Path to directory containing person subdirectories
        models_dir: Path to directory containing dlib model files
        progress_callback: Optional callback(percent, message) for progress

    Returns:
        Tuple of (KnownFaceDatabase, list of person names)
    """
    faces_path = Path(faces_dir)
    if not faces_path.exists():
        raise FileNotFoundError(f"Faces directory not found: {faces_dir}")

    db = KnownFaceDatabase()
    db._init_models(models_dir)
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
            image = dlib.load_rgb_image(str(image_file))
            faces = db._face_detector(image)

            if faces:
                shape = db._shape_predictor(image, faces[0])
                encoding = np.array(db._face_encoder.compute_face_descriptor(image, shape))

                db.encodings.append(encoding)
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