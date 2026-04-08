from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QLabel,
)

from app.config import APP_NAME, APP_VERSION
from app.constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
)
from app.logger import setup_logger
from app.services.image_io import is_supported_image, load_pixmap
from app.ui.control_panel import ControlPanel
from app.ui.image_viewer import ImageViewer
from app.ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.logger = setup_logger()
        self.current_image_path: str | None = None

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        self.image_viewer = ImageViewer()
        self.setCentralWidget(self.image_viewer)

        self.sidebar = Sidebar()
        self.sidebar_dock = QDockWidget("Modules", self)
        self.sidebar_dock.setWidget(self.sidebar)
        self.sidebar_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar_dock)

        self.control_panel = ControlPanel()
        self.control_dock = QDockWidget("Controls", self)
        self.control_dock.setWidget(self.control_panel)
        self.control_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.control_dock)

        self._create_actions()
        self._create_menu()
        self._create_status_bar()

        self.image_viewer.image_dropped.connect(self.load_image)
        self.image_viewer.zoom_changed.connect(self._update_zoom_label)
        self.image_viewer.image_loaded.connect(self._update_image_info)
        self.image_viewer.image_cleared.connect(self._clear_image_info)

        self.statusBar().showMessage("Ready")

    def _create_actions(self) -> None:
        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.open_image_dialog)

        self.save_as_action = QAction("Save As", self)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction("Undo", self)
        self.redo_action = QAction("Redo", self)

        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.triggered.connect(self.image_viewer.zoom_in)

        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.triggered.connect(self.image_viewer.zoom_out)

        self.fit_to_window_action = QAction("Fit to Window", self)
        self.fit_to_window_action.triggered.connect(self.image_viewer.fit_to_view)

        self.reset_zoom_action = QAction("Reset Zoom", self)
        self.reset_zoom_action.triggered.connect(self.image_viewer.reset_zoom)

        self.clear_image_action = QAction("Clear Image", self)
        self.clear_image_action.triggered.connect(self.image_viewer.clear_image)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about_dialog)

    def _create_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addAction(self.clear_image_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = menu_bar.addMenu("Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)

        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
        view_menu.addAction(self.fit_to_window_action)
        view_menu.addAction(self.reset_zoom_action)

        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction(self.about_action)

    def _create_status_bar(self) -> None:
        self.image_info_label = QLabel("No image")
        self.zoom_label = QLabel("Zoom: 100%")

        self.statusBar().addPermanentWidget(self.image_info_label)
        self.statusBar().addPermanentWidget(self.zoom_label)

    def open_image_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )

        if not file_path:
            return

        self.load_image(file_path)

    def load_image(self, file_path: str) -> None:
        if not is_supported_image(file_path):
            QMessageBox.warning(
                self,
                "Unsupported File",
                "That file type is not supported.",
            )
            return

        pixmap = load_pixmap(file_path)
        if pixmap.isNull():
            QMessageBox.critical(
                self,
                "Load Error",
                "Failed to load image.",
            )
            self.logger.error("Failed to load image: %s", file_path)
            return

        self.image_viewer.set_image(pixmap)
        self.current_image_path = file_path

        file_name = Path(file_path).name
        self.statusBar().showMessage(f"Loaded: {file_name}", 3000)
        self.logger.info("Loaded image: %s", file_path)

    def _update_zoom_label(self, zoom_factor: float) -> None:
        percent = round(zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {percent}%")

    def _update_image_info(self, width: int, height: int) -> None:
        if self.current_image_path:
            file_name = Path(self.current_image_path).name
            self.image_info_label.setText(f"{file_name} | {width}×{height}")
        else:
            self.image_info_label.setText(f"{width}×{height}")

    def _clear_image_info(self) -> None:
        self.current_image_path = None
        self.image_info_label.setText("No image")
        self.zoom_label.setText("Zoom: 100%")
        self.statusBar().showMessage("Image cleared", 3000)

    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "About",
            f"{APP_NAME}\nVersion {APP_VERSION}",
        )