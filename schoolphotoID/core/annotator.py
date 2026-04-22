"""Image annotation with face boxes and names."""

from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont


def annotate_image(
    image_path: str,
    faces_result: Dict,
    output_path: str,
    font_size: int = 16,
    known_only: bool = False,
) -> str:
    """
    Annotate an image with face bounding boxes and names.

    Args:
        image_path: Path to input image
        faces_result: Result dict from identify_faces()
        output_path: Path to save annotated image
        font_size: Font size for names
        known_only: If True, only annotate known faces

    Returns:
        Path to saved annotated image
    """
    # Load image
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Try to load a font, fall back to default
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

    faces = faces_result.get("faces", [])

    for face in faces:
        name = face.get("name", "Unknown")
        box = face.get("box", {})

        # Skip unknown faces if requested
        if known_only and name == "Unknown":
            continue

        top = box.get("top", 0)
        right = box.get("right", 0)
        bottom = box.get("bottom", 0)
        left = box.get("left", 0)

        # Determine color
        if name == "Unknown":
            box_color = "red"
            text_bg_color = "red"
            text_color = "white"
        else:
            box_color = "green"
            text_bg_color = "green"
            text_color = "white"

        # Draw bounding box
        draw.rectangle(
            [(left, top), (right, bottom)],
            outline=box_color,
            width=3
        )

        # Calculate text position
        text_x = left
        text_y = bottom + 4

        # Get text bounding box
        try:
            bbox = draw.textbbox((text_x, text_y), name, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            # Fallback if textbbox not available
            text_w = len(name) * font_size * 0.6
            text_h = font_size

        # Clamp text inside image bounds
        text_x = max(0, min(text_x, img.width - text_w - 4))
        text_y = max(0, min(text_y, img.height - text_h - 4))

        # Draw text background
        draw.rectangle(
            [(text_x, text_y), (text_x + text_w + 4, text_y + text_h + 4)],
            fill=text_bg_color
        )

        # Draw text
        draw.text(
            (text_x + 2, text_y + 2),
            name,
            fill=text_color,
            font=font
        )

    # Save annotated image
    img.save(output_path, quality=95)

    return output_path


def annotate_and_save(
    image_path: str,
    faces_result: Dict,
    output_dir: str,
    suffix: str = "_annotated",
) -> Tuple[str, Optional[Path]]:
    """
    Annotate and save an image to output directory.

    Args:
        image_path: Path to input image
        faces_result: Result dict from identify_faces()
        output_dir: Output directory
        suffix: Suffix to add to filename

    Returns:
        Tuple of (image_path, output_path or None if failed)
    """
    input_path = Path(image_path)
    output_path = Path(output_dir) / f"{input_path.stem}{suffix}{input_path.suffix}"

    try:
        annotate_image(image_path, faces_result, str(output_path))
        return str(output_path), output_path
    except Exception as e:
        print(f"Error annotating {image_path}: {e}")
        return str(input_path), None