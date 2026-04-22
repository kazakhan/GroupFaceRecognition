"""File utility functions."""

import os
import shutil
from pathlib import Path
from typing import List, Optional


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def sort_images_into_folders(
    folder_path: str,
    progress_callback: Optional[callable] = None,
) -> List[str]:
    """
    Sort loose images into person subfolders.

    Takes images from folder_path with filename format "Last_First.jpg"
    and moves them into folders named "Last First"/"Photo.jpg"

    Rule: Replace underscores with spaces in filename (before extension)
    to get folder name.

    Args:
        folder_path: Path containing loose images
        progress_callback: Optional callback(percent, message)

    Returns:
        List of created folder names
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    created_folders: List[str] = []

    images = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    total = len(images)
    for idx, image_path in enumerate(images):
        if progress_callback:
            progress_callback(
                (idx / total) * 100 if total > 0 else 100,
                f"Moving: {image_path.name}"
            )

        # Get name without extension
        name_no_ext = image_path.stem
        # Replace underscores with spaces
        folder_name = name_no_ext.replace("_", " ")

        # Create destination folder
        dest_folder = folder / folder_name
        dest_folder.mkdir(exist_ok=True)

        # Move file
        dest_path = dest_folder / image_path.name
        if dest_path.exists():
            if progress_callback:
                progress_callback(
                    (idx / total) * 100,
                    f"SKIP (already exists): {dest_path.name}"
                )
            continue

        shutil.move(str(image_path), str(dest_path))
        created_folders.append(folder_name)

    if progress_callback:
        progress_callback(100, f"Done. Moved {len(created_folders)} images.")

    return created_folders


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if needed."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_image_files(directory: str) -> List[Path]:
    """Get all image files from a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    return sorted([
        f for f in dir_path.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ])


def get_subdirectories(directory: str) -> List[Path]:
    """Get all subdirectories in a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    return sorted([
        d for d in dir_path.iterdir()
        if d.is_dir()
    ])


def count_faces_in_directory(directory: str) -> int:
    """Count number of person subdirectories (face count)."""
    return len(get_subdirectories(directory))