"""Background worker thread for face processing."""

import traceback
import sys
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


def log_error(message: str):
    """Log error to a file for debugging."""
    log_dir = Path.home() / ".schoolphotoID"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "error.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def log_info(message: str):
    """Log info to a file for debugging."""
    log_dir = Path.home() / ".schoolphotoID"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "debug.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


import src.setup_face_recognition  # MUST be imported before face_recognition
log_info("setup_face_recognition imported in worker module")

from src.face_recognition_tool import load_known_faces, identify_people_in_image
log_info("face_recognition_tool imported in worker module")


_last_load_result = None
_last_process_result = None
_last_sort_result = None


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
        global _last_load_result
        log_info(f"[LoadFacesWorker] Starting - faces_dir: {self.faces_dir}")
        try:
            from src.face_recognition_tool import KNOWN_FACE_NAMES, KNOWN_FACE_ENCODINGS

            self.progress.emit(0, "Loading faces...")
            log_info(f"[LoadFacesWorker] Calling load_known_faces...")
            load_known_faces(self.faces_dir)
            count = len(KNOWN_FACE_NAMES)
            log_info(f"[LoadFacesWorker] Loaded {count} faces")

            _last_load_result = {"count": count}
            log_info(f"[LoadFacesWorker] Stored result: {_last_load_result}")

            self.progress.emit(100, f"Loaded {count} faces")
            self.complete.emit()
            log_info("[LoadFacesWorker] Finished successfully")

        except Exception as e:
            error_msg = f"[LoadFacesWorker] ERROR: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            print(error_msg)
            self.error.emit(error_msg)


class ProcessImagesWorker(Worker):
    """Worker for processing group images."""

    def __init__(self, image_paths: List[str], output_dir: str, parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.results = []

    @pyqtSlot()
    def run(self):
        """Run the worker."""
        global _last_process_result
        log_info(f"[ProcessImagesWorker] Starting - {len(self.image_paths)} images")
        try:
            from PIL import Image, ImageDraw, ImageFont
            from schoolphotoID.core.file_util import ensure_directory

            output_path = Path(self.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            total = len(self.image_paths)
            log_info(f"[ProcessImagesWorker] Processing {total} images")

            try:
                FONT = ImageFont.truetype("arial.ttf", 16)
            except:
                FONT = ImageFont.load_default()

            for idx, image_path in enumerate(self.image_paths):
                if self._cancelled:
                    break

                progress_base = (idx / total) * 100
                self.progress.emit(progress_base, f"Processing {Path(image_path).name}...")

                log_info(f"[ProcessImagesWorker] Processing: {image_path}")
                result = identify_people_in_image(image_path)
                log_info(f"[ProcessImagesWorker] Result: {result}")

                input_path = Path(image_path)
                output_image_path = output_path / f"{input_path.stem}_annotated{input_path.suffix}"

                face_locations = result.get("face_locations", [])
                people = result.get("people", [])

                faces_with_people = list(zip(face_locations, people))

                faces_with_people = self.sort_faces_rowwise(faces_with_people, row_threshold=40)

                img = Image.open(image_path)
                draw = ImageDraw.Draw(img)

                for box, person in faces_with_people:
                    top, right, bottom, left = box
                    name = person.get("name", "Unknown")

                    if name == "Unknown":
                        box_color = "red"
                    else:
                        box_color = "green"

                    draw.rectangle(((left, top), (right, bottom)), outline=box_color, width=3)

                    text_x = left
                    text_y = bottom + 4

                    bbox = draw.textbbox((0, 0), name, font=FONT)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]

                    text_x = max(0, min(text_x, img.width - text_w - 4))
                    text_y = max(0, min(text_y, img.height - text_h - 4))

                    draw.rectangle(((text_x, text_y), (text_x + text_w + 4, text_y + text_h + 4)), fill="green")
                    text_fill = "white" if box_color == "green" else "black"
                    draw.text((text_x + 2, text_y + 2), name, fill=text_fill, font=FONT)

                img.save(output_image_path)

                ordered_names = [person.get("name") for box, person in faces_with_people]
                output_csv_path = output_path / f"{input_path.stem}_faces_order.txt"
                with open(output_csv_path, 'w', encoding='utf-8') as f:
                    f.write(", ".join(ordered_names))

                face_count = result.get("face_count", 0)

                self.results.append({
                    "image_path": image_path,
                    "output_image": str(output_image_path),
                    "faces_detected": face_count,
                    "people_identified": sum(1 for p in people if p.get("name") != "Unknown"),
                })

            log_info(f"[ProcessImagesWorker] Done, processed {len(self.results)} images")
            self.progress.emit(100, "Processing complete")

            _last_process_result = {
                "results": self.results,
                "processed": len(self.results),
            }
            self.complete.emit()

        except Exception as e:
            error_msg = f"[ProcessImagesWorker] ERROR: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            print(error_msg)
            self.error.emit(error_msg)

    def sort_faces_rowwise(self, faces_with_people, row_threshold=40):
        faces_with_center = [
            (box, person, (box[0] + box[2]) // 2)
            for box, person in faces_with_people
        ]

        faces_with_center.sort(key=lambda x: x[2])

        rows = []
        current_row = []
        last_center_y = None

        for box, person, center_y in faces_with_center:
            if not current_row:
                current_row.append((box, person))
                last_center_y = center_y
                continue

            if abs(center_y - last_center_y) <= row_threshold:
                current_row.append((box, person))
            else:
                current_row.sort(key=lambda x: x[0][3])
                rows.append(current_row)
                current_row = [(box, person)]
            last_center_y = center_y

        if current_row:
            current_row.sort(key=lambda x: x[0][3])
            rows.append(current_row)

        sorted_faces = [fp for row in rows for fp in row]
        return sorted_faces


class SortImagesWorker(Worker):
    """Worker for sorting images into folders."""

    def __init__(self, folder_path: str, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path

    @pyqtSlot()
    def run(self):
        """Run the worker."""
        global _last_sort_result
        log_info(f"[SortImagesWorker] Starting - folder: {self.folder_path}")
        try:
            from schoolphotoID.core.file_util import sort_images_into_folders

            def progress_callback(percent: float, message: str):
                if self._cancelled:
                    raise InterruptedError("Cancelled")
                self.progress.emit(percent, message)

            folders = sort_images_into_folders(self.folder_path, progress_callback=progress_callback)
            log_info(f"[SortImagesWorker] Sorted into {len(folders)} folders")

            _last_sort_result = {
                "folders": folders,
                "count": len(folders),
            }
            self.complete.emit()

        except Exception as e:
            error_msg = f"[SortImagesWorker] ERROR: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            print(error_msg)
            self.error.emit(error_msg)