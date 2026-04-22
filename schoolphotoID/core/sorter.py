"""Row-wise sorting of faces for photo print order."""

from typing import List, Dict, Tuple


def sort_faces_rowwise(
    faces: List[Dict],
    row_threshold: int = 30,
) -> List[Dict]:
    """
    Sort faces row-wise: top-to-bottom, then left-to-right within each row.

    This produces an ordering suitable for photo printing where faces are
    arranged in rows starting from the top of the image.

    Args:
        faces: List of face dicts with 'box' key containing top/left info
        row_threshold: Vertical distance threshold to consider faces in same row

    Returns:
        Sorted list of face dicts
    """
    if not faces:
        return faces

    # Add vertical center to each face
    faces_with_center = []
    for face in faces:
        box = face.get("box", {})
        top = box.get("top", 0)
        bottom = box.get("bottom", 0)
        left = box.get("left", 0)
        center_y = (top + bottom) // 2
        center_x = left
        faces_with_center.append((face, center_y, center_x))

    # Sort by vertical center first
    faces_with_center.sort(key=lambda x: x[1])

    # Group into rows
    rows = []
    current_row = []
    last_center_y = None

    for face, center_y, center_x in faces_with_center:
        if last_center_y is None:
            current_row.append((face, center_x))
            last_center_y = center_y
        elif abs(center_y - last_center_y) <= row_threshold:
            current_row.append((face, center_x))
        else:
            # Sort current row by horizontal position (left to right)
            current_row.sort(key=lambda x: x[1])
            rows.append([f for f, _ in current_row])
            current_row = [(face, center_x)]
            last_center_y = center_y

    # Don't forget the last row
    if current_row:
        current_row.sort(key=lambda x: x[1])
        rows.append([f for f, _ in current_row])

    # Flatten rows into single list
    sorted_faces = []
    for row in rows:
        sorted_faces.extend(row)

    return sorted_faces


def export_ordered_list(
    faces: List[Dict],
    output_path: str,
    format: str = "csv",
    include_position: bool = False,
) -> str:
    """
    Export ordered face list to file.

    Args:
        faces: List of face dicts sorted in row-wise order
        output_path: Path to output file
        format: "csv", "txt", or "json"
        include_position: If True, include position coordinates

    Returns:
        Path to output file
    """
    import json
    from pathlib import Path

    output_file = Path(output_path)

    if format == "csv":
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Position,Name,Distance\n")
            for idx, face in enumerate(faces, 1):
                name = face.get("name", "Unknown")
                dist = face.get("distance", 0.0)
                if include_position:
                    box = face.get("box", {})
                    f.write(f'{idx},"{name}",{dist},{box.get("top",0)},{box.get("left",0)}\n')
                else:
                    f.write(f'{idx},"{name}",{dist:.4f}\n')

    elif format == "txt":
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Faces in row-wise order (top->bottom, left->right):\n")
            for idx, face in enumerate(faces, 1):
                name = face.get("name", "Unknown")
                if include_position:
                    box = face.get("box", {})
                    f.write(f"{idx}: {name} (Top={box.get('top',0)}, Left={box.get('left',0)})\n")
                else:
                    f.write(f"{idx}: {name}\n")

    elif format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(faces, f, indent=2)

    return str(output_file)


def generate_face_list(
    faces: List[Dict],
    delimiter: str = ", ",
) -> str:
    """
    Generate a simple comma-separated list of face names.

    Args:
        faces: List of face dicts
        delimiter: String to join names with

    Returns:
        String like "Name1, Name2, Name3"
    """
    names = [face.get("name", "Unknown") for face in faces]
    return delimiter.join(names)