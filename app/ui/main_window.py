from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QWidget,
)
from PySide6.QtCore import Qt

from app.config import APP_NAME, APP_VERSION
from app.constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
)

from app.ui.sidebar import Sidebar
from app.ui.control_panel import ControlPanel
from app.ui.image_viewer import ImageViewer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # ===== Center =====
        self.image_viewer = ImageViewer()
        self.setCentralWidget(self.image_viewer)

        # ===== Left Sidebar =====
        self.sidebar = Sidebar()
        self.sidebar_dock = QDockWidget("Modules", self)
        self.sidebar_dock.setWidget(self.sidebar)
        self.sidebar_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar_dock)

        # ===== Right Panel =====
        self.control_panel = ControlPanel()
        self.control_dock = QDockWidget("Controls", self)
        self.control_dock.setWidget(self.control_panel)
        self.control_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.control_dock)

        # ===== Menu =====
        self._create_menu()

        # ===== Status Bar =====
        self.statusBar().showMessage("Ready")

    def _create_menu(self) -> None:
        menu_bar = self.menuBar()

        # File
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Open")
        file_menu.addAction("Save As")
        file_menu.addSeparator()
        file_menu.addAction("Exit")

        # Edit
        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction("Undo")
        edit_menu.addAction("Redo")

        # View
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction("Zoom In")
        view_menu.addAction("Zoom Out")

        # Help
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("About")