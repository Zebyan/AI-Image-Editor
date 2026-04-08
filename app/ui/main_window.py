from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QDockWidget,
    QMainWindow,
    QMessageBox,
    QLabel,
)

from app.app_state import AppState
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
        self.app_state = AppState()

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
        self._update_action_states()

        self.image_viewer.image_dropped.connect(self.load_image)
        self.image_viewer.zoom_changed.connect(self._update_zoom_label)
        self.image_viewer.image_loaded.connect(self._update_image_info)
        self.image_viewer.image_cleared.connect(self._clear_image_info)
        self.sidebar.module_selected.connect(self.on_module_selected)

        self.statusBar().showMessage("Ready")

    def _create_actions(self) -> None:
        self.open_action = QAction("Open", self)
        self.open_action.triggered.connect(self.open_image_dialog)

        self.save_as_action = QAction("Save As", self)
        self.save_as_action.triggered.connect(self.save_image_as)

        self.clear_image_action = QAction("Clear Image", self)
        self.clear_image_action.triggered.connect(self.clear_image)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.undo_action = QAction("Undo", self)
        self.undo_action.triggered.connect(self.undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.triggered.connect(self.redo)

        self.reset_image_action = QAction("Reset to Original", self)
        self.reset_image_action.triggered.connect(self.reset_image)

        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.triggered.connect(self.image_viewer.zoom_in)

        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.triggered.connect(self.image_viewer.zoom_out)

        self.fit_to_window_action = QAction("Fit to Window", self)
        self.fit_to_window_action.triggered.connect(self.image_viewer.fit_to_view)

        self.reset_zoom_action = QAction("Reset Zoom", self)
        self.reset_zoom_action.triggered.connect(self.image_viewer.reset_zoom)

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
        edit_menu.addAction(self.reset_image_action)

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

    def _update_action_states(self) -> None:
        has_image = self.app_state.has_image()

        self.save_as_action.setEnabled(has_image)
        self.clear_image_action.setEnabled(has_image)
        self.reset_image_action.setEnabled(has_image)

        self.undo_action.setEnabled(self.app_state.can_undo())
        self.redo_action.setEnabled(self.app_state.can_redo())

        self.zoom_in_action.setEnabled(has_image)
        self.zoom_out_action.setEnabled(has_image)
        self.fit_to_window_action.setEnabled(has_image)
        self.reset_zoom_action.setEnabled(has_image)

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

        self.app_state.set_image(pixmap, file_path)
        self._display_current_image()

        file_name = Path(file_path).name
        self.statusBar().showMessage(f"Loaded: {file_name}", 3000)
        self.logger.info("Loaded image: %s", file_path)

    def _display_current_image(self) -> None:
        pixmap = self.app_state.get_display_pixmap()
        if pixmap is None or pixmap.isNull():
            self.image_viewer.clear_image()
        else:
            self.image_viewer.set_image(pixmap)

        self._update_action_states()

    def clear_image(self) -> None:
        self.app_state.clear()
        self.image_viewer.clear_image()
        self._update_action_states()
        self.logger.info("Cleared image")

    def save_image_as(self) -> None:
        if not self.app_state.has_image():
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Image As",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;BMP Image (*.bmp)",
        )

        if not file_path:
            return

        pixmap = self.app_state.current_pixmap
        if pixmap is None or pixmap.isNull():
            QMessageBox.warning(self, "No Image", "There is no image to save.")
            return

        success = pixmap.save(file_path)
        if not success:
            QMessageBox.critical(self, "Save Error", "Failed to save image.")
            self.logger.error("Failed to save image: %s", file_path)
            return

        file_name = Path(file_path).name
        self.statusBar().showMessage(f"Saved: {file_name}", 3000)
        self.logger.info("Saved image: %s", file_path)

    def undo(self) -> None:
        pixmap = self.app_state.undo()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self._update_action_states()
        self.statusBar().showMessage("Undo", 2000)
        self.logger.info("Undo action")

    def redo(self) -> None:
        pixmap = self.app_state.redo()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self._update_action_states()
        self.statusBar().showMessage("Redo", 2000)
        self.logger.info("Redo action")

    def reset_image(self) -> None:
        pixmap = self.app_state.reset_to_original()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self._update_action_states()
        self.statusBar().showMessage("Reset to original", 2000)
        self.logger.info("Reset image to original")

    def apply_demo_change(self) -> None:
        """
        Temporary helper for testing history before EPIC 4/5.
        Creates a scaled copy to prove undo/redo works.
        """
        if not self.app_state.has_image():
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        new_pixmap = current.scaled(
            max(1, current.width() - 50),
            max(1, current.height() - 50),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.app_state.apply_new_current(new_pixmap)
        self.image_viewer.set_image(new_pixmap)
        self._update_action_states()
        self.statusBar().showMessage("Applied demo change", 2000)
        self.logger.info("Applied demo change")

    def _update_zoom_label(self, zoom_factor: float) -> None:
        percent = round(zoom_factor * 100)
        self.zoom_label.setText(f"Zoom: {percent}%")

    def _update_image_info(self, width: int, height: int) -> None:
        if self.app_state.current_image_path:
            file_name = Path(self.app_state.current_image_path).name
            self.image_info_label.setText(f"{file_name} | {width}×{height}")
        else:
            self.image_info_label.setText(f"{width}×{height}")

    def _clear_image_info(self) -> None:
        self.image_info_label.setText("No image")
        self.zoom_label.setText("Zoom: 100%")
        self.statusBar().showMessage("Image cleared", 3000)

    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "About",
            f"{APP_NAME}\nVersion {APP_VERSION}",
        )
    
    def on_module_selected(self, module_name: str) -> None:
        self.control_panel.show_module(module_name)
        self.statusBar().showMessage(f"Selected module: {module_name}", 2000)
        self.logger.info("Selected module: %s", module_name)