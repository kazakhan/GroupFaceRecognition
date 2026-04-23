import sys
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.setup_face_recognition  # MUST come before face_recognition

import face_recognition
FACE_RECOGNITION_AVAILABLE = True

KNOWN_FACES_DIR = "known_faces"
KNOWN_FACE_ENCODINGS = []
KNOWN_FACE_NAMES = []

def load_known_faces(known_faces_dir: str = KNOWN_FACES_DIR) -> None:
    """
    Load all known face encodings from subdirectories of known_faces_dir.
    Each subdirectory name is the person's name, containing reference images.
    """
    global KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES
    KNOWN_FACE_ENCODINGS.clear()
    KNOWN_FACE_NAMES.clear()
    
    if not FACE_RECOGNITION_AVAILABLE:
        print("WARNING: face_recognition not available. Using mock face recognition.")
        print("Known faces will not be loaded. All faces will be labeled as 'Unknown'.")
        return
    
    known_faces_path = Path(known_faces_dir)
    print(f"Known faces directory: {known_faces_path.absolute()}")
    
    if not known_faces_path.exists():
        print(f"ERROR: Known faces directory does not exist.")
        print(f"Create directory '{known_faces_dir}' and add subfolders with reference images.")
        return
    
    # List subdirectories (people)
    person_dirs = [d for d in known_faces_path.iterdir() if d.is_dir()]
    print(f"Found {len(person_dirs)} person subdirectories.")
    
    if not person_dirs:
        print("WARNING: No person subdirectories found.")
        print(f"Create subfolders inside '{known_faces_dir}' named after each person.")
        print(f"Example: {known_faces_dir}/Alice/photo1.jpg")
    
    total_images = 0
    total_faces = 0
    
    for person_dir in person_dirs:
        person_name = person_dir.name
        print(f"  Processing '{person_name}'...")
        person_images = 0
        person_faces = 0
        
        for image_file in person_dir.iterdir():
            if image_file.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                total_images += 1
                person_images += 1
                try:
                    image = face_recognition.load_image_file(str(image_file))
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        KNOWN_FACE_ENCODINGS.append(encodings[0])
                        KNOWN_FACE_NAMES.append(person_name)
                        total_faces += 1
                        person_faces += 1
                        print(f"    [OK] Loaded face from {image_file.name}")
                    else:
                        print(f"    [SKIP] No face found in {image_file.name}")
                except Exception as e:
                    print(f"    [ERROR] Error loading {image_file.name}: {e}")
        
        if person_images == 0:
            print(f"    No valid images found for '{person_name}'.")
        else:
            print(f"    {person_faces}/{person_images} images had detectable faces.")
    
    print(f"\nSummary: {total_images} total images processed, {total_faces} face encodings loaded.")
    if total_faces == 0:
        print("WARNING: No face encodings loaded. Face recognition will label all faces as 'Unknown'.")

def identify_people_in_image(image_path: str, tolerance: float = 0.6) -> Dict[str, Any]:
    """
    Detect faces in an image and match against known face encodings.
    
    Args:
        image_path: Path to the image file.
        tolerance: Distance tolerance for face matching (lower is stricter).
    
    Returns:
        Dictionary with keys:
            people: list of dicts with 'name' and 'confidence' (1 - distance)
            face_count: total number of faces detected
    """
    if not FACE_RECOGNITION_AVAILABLE:
        # Return mock identification for testing when face_recognition not installed
        print(f"WARNING: Using mock face recognition for {image_path}")
        return {
            "people": [
                {"name": "MockPerson", "confidence": 0.85},
                {"name": "Unknown", "confidence": 0.42}
            ],
            "face_count": 2
        }
    
    if not KNOWN_FACE_ENCODINGS:
        load_known_faces()
    
    try:
        image = face_recognition.load_image_file(image_path)
    except Exception as e:
        return {"error": f"Failed to load image: {e}", "people": [], "face_count": 0}
    
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    
    people = []
    for face_encoding in face_encodings:
        if KNOWN_FACE_ENCODINGS:
            distances = face_recognition.face_distance(KNOWN_FACE_ENCODINGS, face_encoding)
            best_match_index = np.argmin(distances)
            best_distance = distances[best_match_index]
            if best_distance <= tolerance:
                name = KNOWN_FACE_NAMES[best_match_index]
                confidence = 1.0 - best_distance  # Convert distance to confidence
            else:
                name = "Unknown"
                confidence = 1.0 - best_distance  # Could be low confidence
        else:
            name = "Unknown"
            confidence = 0.0
        
        people.append({
            "name": name,
            "confidence": float(confidence)
        })
    
    result = {
        "people": people,
        "face_count": len(face_locations),
        "face_locations": face_locations
    }
    return result

if __name__ == "__main__":
    # Example usage
    load_known_faces()
    test_image = "images/test.jpg"
    if os.path.exists(test_image):
        result = identify_people_in_image(test_image)
        print(json.dumps(result, indent=2))
    else:
        print(f"Test image {test_image} not found.")