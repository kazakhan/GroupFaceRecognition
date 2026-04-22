"""Background worker thread for face processing."""

import traceback
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class Worker(QObject):
    """Worker for running face processing in background thread."""

    progress = pyqtSignal(float, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    complete = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False
        self.results = []

    def cancel(self):
        """Request cancellation."""
        self._cancelled = True

    def reset(self):
        """Reset worker state."""
        self._cancelled = False
        self.results = []


class LoadFacesWorker(Worker):
    """Worker for loading known faces."""

    def __init__(self, faces_dir: str, parent=None):
        super().__init__(parent)
        self.faces_dir = faces_dir

    @pyqtSlot()
    def run(self):
        """Run the worker."""
        try:
            from schoolphotoID.core.face_loader import load_known_faces, KnownFaceDatabase

            def progress_callback(percent: float, message: str):
                if self._cancelled:
                    raise InterruptedError("Cancelled")
                self.progress.emit(percent, message)

            db, names = load_known_faces(
                self.faces_dir,
                progress_callback=progress_callback,
            )

            self.finished.emit({
                "database": db,
                "names": names,
                "count": len(names),
            })

        except Exception as e:
            self.error.emit(f"Error loading faces: {str(e)}\n{traceback.format_exc()}")


class ProcessImagesWorker(Worker):
    """Worker for processing group images."""

    def __init__(
        self,
        image_paths: List[str],
        known_encodings: List,
        known_names: List[str],
        output_dir: str,
        parent=None,
    ):
        super().__init__(parent)
        self.image_paths = image_paths
        self.known_encodings = known_encodings
        self.known_names = known_names
        self.output_dir = output_dir
        self.results = []

    def run(self):
        """Run the worker."""
        try:
            import numpy as np

            from schoolphotoID.core import (
                identify_faces,
                annotate_image,
                sort_faces_rowwise,
                export_ordered_list,
            )
            from schoolphotoID.core.file_util import ensure_directory

            image_paths = [str(p) for p in self.image_paths]
            total = len(image_paths)

            ensure_directory(self.output_dir)

            for idx, image_path in enumerate(image_paths):
                if self._cancelled:
                    break

                progress_base = (idx / total) * 100
                self.progress.emit(
                    progress_base,
                    f"Processing {Path(image_path).name}..."
                )

                # Identify faces
                result = identify_faces(
                    image_path,
                    self.known_encodings,
                    self.known_names,
                    known_paths=None,
                    face_model="hog",
                    progress_callback=lambda p, m: self.progress.emit(
                        progress_base + (p / total) * 100,
                        m,
                    ),
                )

                # Annotate image
                input_path = Path(image_path)
                output_image_path = Path(self.output_dir) / f"{input_path.stem}_annotated{input_path.suffix}"
                annotate_image(
                    image_path,
                    result,
                    str(output_image_path),
                )

                # Sort and export
                sorted_faces = sort_faces_rowwise(result.get("faces", []))
                output_csv_path = Path(self.output_dir) / f"{input_path.stem}_faces.csv"
                export_ordered_list(sorted_faces, str(output_csv_path), format="csv")

                output_txt_path = Path(self.output_dir) / f"{input_path.stem}_faces_order.txt"
                export_ordered_list(sorted_faces, str(output_txt_path), format="txt")

                self.results.append({
                    "image_path": image_path,
                    "output_image": str(output_image_path),
                    "faces_detected": result.get("faces_detected", 0),
                    "people_identified": result.get("people_identified", 0),
                })

            self.progress.emit(100, "Processing complete")

            self.finished.emit({
                "results": self.results,
                "processed": len(self.results),
            })

        except Exception as e:
            self.error.emit(f"Error processing: {str(e)}\n{traceback.format_exc()}")


class SortImagesWorker(Worker):
    """Worker for sorting images into folders."""

    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path

    def run(self):
        """Run the worker."""
        try:
            from schoolphotoID.core.file_util import sort_images_into_folders

            def progress_callback(percent: float, message: str):
                if self._cancelled:
                    raise InterruptedError("Cancelled")
                self.progress.emit(percent, message)

            folders = sort_images_into_folders(
                self.folder_path,
                progress_callback=progress_callback,
            )

            self.finished.emit({
                "folders": folders,
                "count": len(folders),
            })

        except Exception as e:
            self.error.emit(f"Error sorting: {str(e)}\n{traceback.format_exc()}")