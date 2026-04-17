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

from app.app_state import AppState
from app.config import APP_NAME, APP_VERSION
from app.constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
)
from app.logger import setup_logger
from app.process.edit.brightness_contrast import (
    adjust_brightness_contrast,
)
from app.process.edit.crop import crop_pixmap
from app.process.edit.flip import flip_pixmap
from app.process.edit.resize import resize_pixmap
from app.process.edit.rotate import rotate_pixmap
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
        self.image_viewer.crop_selection_changed.connect(
            self.control_panel.set_crop_selection_info
        )

        self.sidebar.module_selected.connect(self.on_module_selected)
        self.control_panel.resize_requested.connect(self.apply_resize)
        self.control_panel.rotate_requested.connect(self.apply_rotate)
        self.control_panel.flip_requested.connect(self.apply_flip)
        self.control_panel.crop_apply_requested.connect(self.apply_crop)
        self.control_panel.crop_cancel_requested.connect(self.cancel_crop)
        self.control_panel.brightness_contrast_requested.connect(
            self.apply_brightness_contrast
        )
        self.control_panel.tool_list.currentTextChanged.connect(
            lambda _: self._sync_crop_mode()
        )

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
        self.control_panel.set_resize_source_dimensions(pixmap.width(), pixmap.height())
        self._sync_crop_mode()

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
        self.cancel_crop()
        self.app_state.clear()
        self.image_viewer.clear_image()
        self._update_action_states()
        self.logger.info("Cleared image")

    def save_image_as(self) -> None:
        if not self.app_state.has_image():
            return

        file_path, _ = QFileDialog.getSaveFileName(
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
        self.control_panel.set_resize_source_dimensions(pixmap.width(), pixmap.height())
        self._update_action_states()
        self._sync_crop_mode()
        self.statusBar().showMessage("Undo", 2000)
        self.logger.info("Undo action")

    def redo(self) -> None:
        pixmap = self.app_state.redo()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self.control_panel.set_resize_source_dimensions(pixmap.width(), pixmap.height())
        self._update_action_states()
        self._sync_crop_mode()
        self.statusBar().showMessage("Redo", 2000)
        self.logger.info("Redo action")

    def reset_image(self) -> None:
        pixmap = self.app_state.reset_to_original()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self.control_panel.set_resize_source_dimensions(pixmap.width(), pixmap.height())
        self._update_action_states()
        self._sync_crop_mode()
        self.statusBar().showMessage("Reset to original", 2000)
        self.logger.info("Reset image to original")

    def apply_resize(self, width: int, height: int, interpolation: str) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        original_width = current.width()
        original_height = current.height()

        resized = resize_pixmap(current, width, height, interpolation)
        if resized.isNull():
            QMessageBox.warning(self, "Resize Failed", "Failed to resize image.")
            return

        self.app_state.apply_new_current(resized)
        self.image_viewer.set_image(resized)
        self.control_panel.set_resize_source_dimensions(resized.width(), resized.height())
        self._update_action_states()
        self._sync_crop_mode()

        self.statusBar().showMessage(
            (
                f"Resized {original_width}×{original_height} → "
                f"{resized.width()}×{resized.height()} using {interpolation}"
            ),
            4000,
        )
        self.logger.info(
            "Resized image from %sx%s to %sx%s using %s",
            original_width,
            original_height,
            resized.width(),
            resized.height(),
            interpolation,
        )

    def apply_rotate(self, angle: float, interpolation: str, expand_canvas: bool) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        original_width = current.width()
        original_height = current.height()

        rotated = rotate_pixmap(current, angle, interpolation, expand_canvas)
        if rotated.isNull():
            QMessageBox.warning(self, "Rotate Failed", "Failed to rotate image.")
            return

        self.app_state.apply_new_current(rotated)
        self.image_viewer.set_image(rotated)
        self.control_panel.set_resize_source_dimensions(rotated.width(), rotated.height())
        self._update_action_states()
        self._sync_crop_mode()

        self.statusBar().showMessage(
            (
                f"Rotated {original_width}×{original_height} → "
                f"{rotated.width()}×{rotated.height()} by {angle:.1f}°"
            ),
            4000,
        )
        self.logger.info(
            "Rotated image from %sx%s to %sx%s by %.1f degrees using %s (expand=%s)",
            original_width,
            original_height,
            rotated.width(),
            rotated.height(),
            angle,
            interpolation,
            expand_canvas,
        )

    def apply_flip(self, direction: str) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        flipped = flip_pixmap(current, direction)
        if flipped.isNull():
            QMessageBox.warning(self, "Flip Failed", "Failed to flip image.")
            return

        self.app_state.apply_new_current(flipped)
        self.image_viewer.set_image(flipped)
        self.control_panel.set_resize_source_dimensions(flipped.width(), flipped.height())
        self._update_action_states()
        self._sync_crop_mode()

        self.statusBar().showMessage(f"Flipped image: {direction}", 3000)
        self.logger.info("Flipped image: %s", direction)

    def apply_crop(self) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        crop_rect = self.image_viewer.get_crop_rect()
        if crop_rect is None:
            QMessageBox.warning(self, "No Selection", "Draw a crop rectangle first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        x, y, width, height = crop_rect
        cropped = crop_pixmap(current, x, y, width, height)
        if cropped.isNull():
            QMessageBox.warning(self, "Crop Failed", "Failed to crop image.")
            return

        self.app_state.apply_new_current(cropped)
        self.image_viewer.set_image(cropped)
        self.control_panel.set_resize_source_dimensions(cropped.width(), cropped.height())
        self._update_action_states()
        self._sync_crop_mode()

        self.statusBar().showMessage(
            f"Cropped image to {cropped.width()}×{cropped.height()}",
            3000,
        )
        self.logger.info(
            "Cropped image at x=%s y=%s width=%s height=%s",
            x,
            y,
            width,
            height,
        )

        if self.control_panel.current_tool_name() == "Crop":
            self.image_viewer.set_crop_mode(True)

    def apply_brightness_contrast(self, brightness: int, contrast: int) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        adjusted = adjust_brightness_contrast(current, brightness, contrast)
        if adjusted.isNull():
            QMessageBox.warning(
                self,
                "Adjustment Failed",
                "Failed to apply brightness/contrast adjustment.",
            )
            return

        self.app_state.apply_new_current(adjusted)
        self.image_viewer.set_image(adjusted)
        self.control_panel.set_resize_source_dimensions(adjusted.width(), adjusted.height())
        self._update_action_states()
        self._sync_crop_mode()

        self.statusBar().showMessage(
            f"Applied brightness={brightness}, contrast={contrast}",
            3000,
        )
        self.logger.info(
            "Applied brightness/contrast adjustment: brightness=%s contrast=%s",
            brightness,
            contrast,
        )

    def cancel_crop(self) -> None:
        self.image_viewer.set_crop_mode(False)
        self.control_panel.set_crop_selection_info(False)

        if self.control_panel.current_tool_name() == "Crop":
            self.image_viewer.set_crop_mode(True)

    def on_module_selected(self, module_name: str) -> None:
        self.control_panel.show_module(module_name)
        self._sync_crop_mode()
        self.statusBar().showMessage(f"Selected module: {module_name}", 2000)
        self.logger.info("Selected module: %s", module_name)

    def _sync_crop_mode(self) -> None:
        enable_crop = (
            self.control_panel.current_module == "Edit"
            and self.control_panel.current_tool_name() == "Crop"
            and self.app_state.has_image()
        )
        self.image_viewer.set_crop_mode(enable_crop)

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