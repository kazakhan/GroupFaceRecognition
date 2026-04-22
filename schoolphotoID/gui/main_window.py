"""Main application window."""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage
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


# Allowed image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.known_faces_dir = ""
        self.images_dir = ""
        self.output_dir = ""
        self.known_names: List[str] = []
        self.known_encodings: List = []

        self.load_worker: Optional[QThread] = None
        self.process_worker: Optional[QThread] = None
        self.sort_worker: Optional[QThread] = None

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("School Photo Identifier")
        self.setMinimumSize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Directory configuration
        dir_group = self.create_directory_group()
        main_layout.addWidget(dir_group)

        # Image selection
        image_group = self.create_image_selection_group()
        main_layout.addWidget(image_group)

        # Action buttons
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

        # Results area - split between image preview and list
        results_group = self.create_results_group()
        main_layout.addWidget(results_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)

    def create_directory_group(self) -> QGroupBox:
        """Create directory configuration group."""
        group = QGroupBox("Directories")
        layout = QGridLayout()

        # Known faces directory
        layout.addWidget(QLabel("Known Faces:"), 0, 0)
        self.edit_known_faces = QLineEdit()
        self.edit_known_faces.setReadOnly(True)
        layout.addWidget(self.edit_known_faces, 0, 1)
        btn_browse_faces = QPushButton("Browse...")
        btn_browse_faces.clicked.connect(self.browse_known_faces)
        layout.addWidget(btn_browse_faces, 0, 2)

        # Images directory
        layout.addWidget(QLabel("Images:"), 1, 0)
        self.edit_images = QLineEdit()
        self.edit_images.setReadOnly(True)
        layout.addWidget(self.edit_images, 1, 1)
        btn_browse_images = QPushButton("Browse...")
        btn_browse_images.clicked.connect(self.browse_images)
        layout.addWidget(btn_browse_images, 1, 2)

        # Output directory
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
        """Create image selection group."""
        group = QGroupBox("Select Images to Process")
        layout = QVBoxLayout()

        self.image_list = QListWidget()
        self.image_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.image_list)

        # Select all / None buttons
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

    def create_results_group(self) -> QGroupBox:
        """Create results display group."""
        group = QGroupBox("Results")
        layout = QHBoxLayout()

        # Image preview
        self.image_preview = QLabel("No image loaded")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(400, 300)
        self.image_preview.setStyleSheet("border: 1px solid #ccc; background: #f0f0f0;")
        layout.addWidget(self.image_preview, 1)

        # Results list
        self.results_list = QListWidget()
        layout.addWidget(self.results_list, 1)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.image_preview)
        splitter.addWidget(self.results_list)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        # Replace the layout with splitter
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                layout.removeWidget(item.widget())

        layout.addWidget(splitter)

        group.setLayout(layout)
        return group

    def browse_known_faces(self):
        """Browse for known faces directory."""
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
        """Browse for images directory."""
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
        """Browse for output directory."""
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
        """Refresh the list of images."""
        self.image_list.clear()

        if not self.images_dir:
            return

        images = get_image_files(self.images_dir)
        for img in images:
            self.image_list.addItem(img.name)

    def select_all_images(self):
        """Select all images."""
        self.image_list.selectAll()

    def select_no_images(self):
        """Deselect all images."""
        self.image_list.clearSelection()

    def get_selected_images(self) -> List[Path]:
        """Get list of selected image paths."""
        selected = self.image_list.selectedItems()
        if not self.images_dir:
            return []

        images_dir = Path(self.images_dir)
        return [
            images_dir / item.text()
            for item in selected
        ]

    def load_known_faces(self):
        """Load known faces in background thread."""
        if not self.known_faces_dir:
            QMessageBox.warning(
                self,
                "No Directory",
                "Please select a known faces directory first.",
            )
            return

        self.btn_load_faces.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading known faces...")

        # Create worker thread
        self.load_worker = QThread()
        self.load_faces_worker = LoadFacesWorker(self.known_faces_dir)
        self.load_faces_worker.moveToThread(self.load_worker)

        self.load_worker.started.connect(self.load_faces_worker.run)
        self.load_faces_worker.progress.connect(self.on_load_progress)
        self.load_faces_worker.finished.connect(self.on_load_finished)
        self.load_faces_worker.error.connect(self.on_load_error)

        self.load_worker.start()

    def on_load_progress(self, percent: float, message: str):
        """Handle load progress."""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def on_load_finished(self, result: dict):
        """Handle load finished."""
        self.load_worker.quit()
        self.load_worker = None

        self.known_names = result.get("names", [])

        # Store the database for later use
        db = result.get("database")
        if db is not None:
            self.known_encodings = db.encodings
            self.load_faces_database = db

        self.progress_bar.setVisible(False)
        self.btn_load_faces.setEnabled(True)

        count = result.get("count", 0)
        self.status_label.setText(f"Loaded {count} known faces")

        QMessageBox.information(
            self,
            "Faces Loaded",
            f"Successfully loaded {count} known face encodings.",
        )

        self.btn_process.setEnabled(count > 0)

    def on_load_error(self, error: str):
        """Handle load error."""
        self.load_worker.quit()
        self.load_worker = None

        self.progress_bar.setVisible(False)
        self.btn_load_faces.setEnabled(True)
        self.status_label.setText("Error loading faces")

        QMessageBox.critical(self, "Error", error)

    def process_selected(self):
        """Process selected images."""
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

        if not self.known_names or not self.known_encodings:
            QMessageBox.warning(
                self,
                "Not Loaded",
                "Please load known faces first.",
            )
            return

        # Ensure output directory exists
        ensure_directory(self.output_dir)

        self.btn_process.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Processing {len(selected)} images...")

        # Create worker thread
        self.process_worker = QThread()
        self.process_images_worker = ProcessImagesWorker(
            [str(p) for p in selected],
            self.known_encodings,
            self.known_names,
            self.output_dir,
        )
        self.process_images_worker.moveToThread(self.process_worker)

        self.process_worker.started.connect(self.process_images_worker.run)
        self.process_images_worker.progress.connect(self.on_process_progress)
        self.process_images_worker.finished.connect(self.on_process_finished)
        self.process_images_worker.error.connect(self.on_process_error)

        self.process_worker.start()

    def on_process_progress(self, percent: float, message: str):
        """Handle process progress."""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def on_process_finished(self, result: dict):
        """Handle process finished."""
        self.process_worker.quit()
        self.process_worker = None

        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)

        processed = result.get("processed", 0)
        self.status_label.setText(f"Processed {processed} images")

        # Refresh results list
        self.results_list.clear()
        for r in result.get("results", []):
            name = Path(r.get("image_path")).name
            detected = r.get("faces_detected", 0)
            identified = r.get("people_identified", 0)
            self.results_list.addItem(f"{name}: {detected} faces, {identified} identified")

        QMessageBox.information(
            self,
            "Processing Complete",
            f"Successfully processed {processed} images.",
        )

    def on_process_error(self, error: str):
        """Handle process error."""
        self.process_worker.quit()
        self.process_worker = None

        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        self.status_label.setText("Error processing")

        QMessageBox.critical(self, "Error", error)

    def sort_images(self):
        """Sort images into person folders."""
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
        self.progress_bar.setVisible(True)
        self.status_label.setText("Sorting images...")

        # Create worker thread
        self.sort_worker = QThread()
        self.sort_images_worker = SortImagesWorker(self.known_faces_dir)
        self.sort_images_worker.moveToThread(self.sort_worker)

        self.sort_worker.started.connect(self.sort_images_worker.run)
        self.sort_images_worker.progress.connect(self.on_sort_progress)
        self.sort_images_worker.finished.connect(self.on_sort_finished)
        self.sort_images_worker.error.connect(self.on_sort_error)

        self.sort_worker.start()

    def on_sort_progress(self, percent: float, message: str):
        """Handle sort progress."""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def on_sort_finished(self, result: dict):
        """Handle sort finished."""
        self.sort_worker.quit()
        self.sort_worker = None

        self.progress_bar.setVisible(False)
        self.btn_sort.setEnabled(True)

        count = result.get("count", 0)
        self.status_label.setText(f"Sorted {count} images")

        QMessageBox.information(
            self,
            "Sorting Complete",
            f"Successfully sorted {count} images into folders.",
        )

    def on_sort_error(self, error: str):
        """Handle sort error."""
        self.sort_worker.quit()
        self.sort_worker = None

        self.progress_bar.setVisible(False)
        self.btn_sort.setEnabled(True)
        self.status_label.setText("Error sorting")

        QMessageBox.critical(self, "Error", error)

    def load_settings(self):
        """Load saved settings."""
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
        """Save settings."""
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
        """Handle window close."""
        self.save_settings()
        event.accept()