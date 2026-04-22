"""Main application entry point."""

import sys
from PyQt6.QtWidgets import QApplication
from schoolphotoID.gui.main_window import MainWindow


def main():
    """Run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("School Photo ID")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()