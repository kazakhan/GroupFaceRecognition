"""Main application window."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import src.setup_face_recognition  # MUST come before face_recognition

# Setup logging
LOG_DIR = Path.home() / ".schoolphotoID"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_startup():
    log_file = LOG_DIR / "startup.log"
    with open(log_file, "w") as f:
        f.write(f"App starting at {datetime.now()}\n")
        f.write(f"sys.frozen: {getattr(sys, 'frozen', False)}\n")
        f.write(f"sys.executable: {sys.executable}\n")
        f.write(f"Current path: {Path.cwd()}\n")

from datetime import datetime
log_startup()

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QMainWindow,
    QSplitter,
)

from schoolphotoID.core.file_util import get_image_files, ensure_directory
from schoolphotoID.gui.worker import (
    LoadFacesWorker,
    ProcessImagesWorker,
    SortImagesWorker,
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.known_faces_dir = ""
        self.images_dir = ""
        self.output_dir = ""
        self.known_names = []
        self.known_encodings = []

        self.load_worker = None
        self.process_worker = None
        self.sort_worker = None

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("School Photo Identifier")
        self.setWindowIcon(QIcon("app.ico"))

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        dir_group = self.create_directory_group()
        main_layout.addWidget(dir_group)

        image_group = self.create_image_selection_group()
        main_layout.addWidget(image_group)

        action_layout = QHBoxLayout()
        self.btn_load_faces = QPushButton("Load Known Faces")
        self.btn_load_faces.clicked.connect(self.load_known_faces)
        self.btn_process = QPushButton("Process Selected")
        self.btn_process.clicked.connect(self.process_selected)
        self.btn_process.setEnabled(False)
        self.btn_sort = QPushButton("Sort Images into Folders")
        self.btn_sort.clicked.connect(self.sort_images)
        action_layout.addWidget(self.btn_load_faces)
        action_layout.addWidget(self.btn_process)
        action_layout.addWidget(self.btn_sort)
        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def create_directory_group(self) -> QGroupBox:
        group = QGroupBox("Directories")
        layout = QGridLayout()

        layout.addWidget(QLabel("Known Faces:"), 0, 0)
        self.edit_known_faces = QLineEdit()
        self.edit_known_faces.setReadOnly(True)
        layout.addWidget(self.edit_known_faces, 0, 1)
        btn_browse_faces = QPushButton("Browse...")
        btn_browse_faces.clicked.connect(self.browse_known_faces)
        layout.addWidget(btn_browse_faces, 0, 2)

        layout.addWidget(QLabel("Images:"), 1, 0)
        self.edit_images = QLineEdit()
        self.edit_images.setReadOnly(True)
        layout.addWidget(self.edit_images, 1, 1)
        btn_browse_images = QPushButton("Browse...")
        btn_browse_images.clicked.connect(self.browse_images)
        layout.addWidget(btn_browse_images, 1, 2)

        layout.addWidget(QLabel("Output:"), 2, 0)
        self.edit_output = QLineEdit()
        self.edit_output.setReadOnly(True)
        layout.addWidget(self.edit_output, 2, 1)
        btn_browse_output = QPushButton("Browse...")
        btn_browse_output.clicked.connect(self.browse_output)
        layout.addWidget(btn_browse_output, 2, 2)

        group.setLayout(layout)
        return group

    def create_image_selection_group(self) -> QGroupBox:
        group = QGroupBox("Select Images to Process")
        layout = QVBoxLayout()

        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.image_list.setMaximumHeight(120)
        layout.addWidget(self.image_list)

        select_layout = QHBoxLayout()
        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self.select_all_images)
        btn_select_none = QPushButton("Select None")
        btn_select_none.clicked.connect(self.select_no_images)
        select_layout.addWidget(btn_select_all)
        select_layout.addWidget(btn_select_none)
        select_layout.addStretch()
        layout.addLayout(select_layout)

        group.setLayout(layout)
        return group

    def browse_known_faces(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Known Faces Directory",
            self.known_faces_dir or str(Path.home()),
        )
        if directory:
            self.known_faces_dir = directory
            self.edit_known_faces.setText(directory)
            self.save_settings()

    def browse_images(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Images Directory",
            self.images_dir or str(Path.home()),
        )
        if directory:
            self.images_dir = directory
            self.edit_images.setText(directory)
            self.refresh_image_list()
            self.save_settings()

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir or str(Path.home()),
        )
        if directory:
            self.output_dir = directory
            self.edit_output.setText(directory)
            self.save_settings()

    def refresh_image_list(self):
        self.image_list.clear()
        if not self.images_dir:
            return
        images = get_image_files(self.images_dir)
        for img in images:
            self.image_list.addItem(img.name)

    def select_all_images(self):
        self.image_list.selectAll()

    def select_no_images(self):
        self.image_list.clearSelection()

    def get_selected_images(self) -> List[Path]:
        selected = self.image_list.selectedItems()
        if not self.images_dir:
            return []
        images_dir = Path(self.images_dir)
        return [images_dir / item.text() for item in selected]

    def load_known_faces(self):
        if not self.known_faces_dir:
            QMessageBox.warning(
                self,
                "No Directory",
                "Please select a known faces directory first.",
            )
            return

        self.btn_load_faces.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading known faces...")

        self.load_worker = QThread()
        self.load_faces_worker = LoadFacesWorker(self.known_faces_dir)
        self.load_faces_worker.moveToThread(self.load_worker)

        self.load_worker.started.connect(self.load_faces_worker.run)
        self.load_faces_worker.progress.connect(self.on_load_progress)
        self.load_faces_worker.complete.connect(self.on_load_finished)
        self.load_faces_worker.error.connect(self.on_load_error)

        self.load_worker.start()

    def on_load_progress(self, percent, message):
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def on_load_finished(self):
        from schoolphotoID.gui.worker import _last_load_result

        self.load_worker.quit()
        self.load_worker.wait()
        self.load_worker = None

        from src.face_recognition_tool import KNOWN_FACE_NAMES, KNOWN_FACE_ENCODINGS
        self.known_names = list(KNOWN_FACE_NAMES)
        self.known_encodings = list(KNOWN_FACE_ENCODINGS)

        self.progress_bar.setVisible(False)
        self.btn_load_faces.setEnabled(True)

        count = _last_load_result.get("count", 0) if _last_load_result else 0
        self.status_label.setText(f"Loaded {count} known faces")

        QMessageBox.information(
            self,
            "Faces Loaded",
            f"Successfully loaded {count} known face encodings.",
        )

        self.btn_process.setEnabled(count > 0)

    def on_load_error(self, error):
        self.load_worker.quit()
        self.load_worker = None

        self.progress_bar.setVisible(False)
        self.btn_load_faces.setEnabled(True)
        self.status_label.setText("Error loading faces")

        QMessageBox.critical(self, "Error", error)

    def process_selected(self):
        selected = self.get_selected_images()
        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one image to process.",
            )
            return

        if not self.output_dir:
            QMessageBox.warning(
                self,
                "No Output",
                "Please select an output directory.",
            )
            return

        if not self.known_names:
            QMessageBox.warning(
                self,
                "Not Loaded",
                "Please load known faces first.",
            )
            return

        ensure_directory(self.output_dir)

        self.btn_process.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Processing {len(selected)} images...")

        self.process_worker = QThread()
        self.process_images_worker = ProcessImagesWorker(
            [str(p) for p in selected],
            self.output_dir,
        )
        self.process_images_worker.moveToThread(self.process_worker)

        self.process_worker.started.connect(self.process_images_worker.run)
        self.process_images_worker.progress.connect(self.on_process_progress)
        self.process_images_worker.complete.connect(self.on_process_finished)
        self.process_images_worker.error.connect(self.on_process_error)

        self.process_worker.start()

    def on_process_progress(self, percent, message):
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def on_process_finished(self):
        from schoolphotoID.gui.worker import _last_process_result

        self.process_worker.quit()
        self.process_worker.wait()
        self.process_worker = None

        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)

        result = _last_process_result or {}
        processed = result.get("processed", 0)
        self.status_label.setText(f"Processed {processed} images")

        QMessageBox.information(
            self,
            "Processing Complete",
            f"Successfully processed {processed} images.",
        )

    def on_process_error(self, error):
        self.process_worker.quit()
        self.process_worker = None

        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        self.status_label.setText("Error processing")

        QMessageBox.critical(self, "Error", error)

    def sort_images(self):
        if not self.known_faces_dir:
            QMessageBox.warning(
                self,
                "No Directory",
                "Please select a known faces directory first.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Sort Images",
            "This will move images into subdirectories. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_sort.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Sorting images...")

        self.sort_worker = QThread()
        self.sort_images_worker = SortImagesWorker(self.known_faces_dir)
        self.sort_images_worker.moveToThread(self.sort_worker)

        self.sort_worker.started.connect(self.sort_images_worker.run)
        self.sort_images_worker.progress.connect(self.on_sort_progress)
        self.sort_images_worker.complete.connect(self.on_sort_finished)
        self.sort_images_worker.error.connect(self.on_sort_error)

        self.sort_worker.start()

    def on_sort_progress(self, percent, message):
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def on_sort_finished(self):
        from schoolphotoID.gui.worker import _last_sort_result

        self.sort_worker.quit()
        self.sort_worker.wait()
        self.sort_worker = None

        self.progress_bar.setVisible(False)
        self.btn_sort.setEnabled(True)

        result = _last_sort_result or {}
        count = result.get("count", 0)
        self.status_label.setText(f"Sorted {count} images")

        QMessageBox.information(
            self,
            "Sorting Complete",
            f"Successfully sorted {count} images into folders.",
        )

    def on_sort_error(self, error):
        self.sort_worker.quit()
        self.sort_worker = None

        self.progress_bar.setVisible(False)
        self.btn_sort.setEnabled(True)
        self.status_label.setText("Error sorting")

        QMessageBox.critical(self, "Error", error)

    def load_settings(self):
        settings_path = Path.home() / ".schoolphotoID" / "config.json"
        if settings_path.exists():
            try:
                with open(settings_path, "r") as f:
                    settings = json.load(f)
                self.known_faces_dir = settings.get("known_faces_dir", "")
                self.images_dir = settings.get("images_dir", "")
                self.output_dir = settings.get("output_dir", "")

                self.edit_known_faces.setText(self.known_faces_dir)
                self.edit_images.setText(self.images_dir)
                self.edit_output.setText(self.output_dir)

                self.refresh_image_list()
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        settings_dir = Path.home() / ".schoolphotoID"
        settings_dir.mkdir(parents=True, exist_ok=True)

        settings = {
            "known_faces_dir": self.known_faces_dir,
            "images_dir": self.images_dir,
            "output_dir": self.output_dir,
        }

        settings_path = settings_dir / "config.json"
        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()