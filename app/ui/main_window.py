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
from app.process.edit.blur import apply_gaussian_blur
from app.process.edit.brightness_contrast import (
    adjust_brightness_contrast,
)
from app.ui.gif_window import GifPreviewDialog
from app.process.gif.gif import generate_gif_frames, save_gif
from app.process.edit.crop import crop_pixmap
from app.process.edit.flip import flip_pixmap
from app.process.edit.resize import resize_pixmap
from app.process.edit.rotate import rotate_pixmap
from app.services.image_io import is_supported_image, load_pixmap
from app.ui.control_panel import ControlPanel
from app.ui.image_viewer import ImageViewer
from app.ui.sidebar import Sidebar
from app.process.style_transfer.preset_style import apply_preset_style


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.logger = setup_logger()
        self.app_state = AppState()

        self._generated_gif_frames = []
        self._generated_gif_duration_ms = 120
        
        self._style_custom_image_path: str | None = None
        self._style_custom_pixmap = None

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
        self.control_panel.gif_generate_requested.connect(self.generate_gif)
        self.control_panel.gif_save_requested.connect(self.save_generated_gif)
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
        self.image_viewer.draw_session_changed.connect(
            self.control_panel.set_draw_mode_state
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
        self.control_panel.blur_requested.connect(self.apply_blur)

        self.control_panel.draw_mode_toggled.connect(self.set_draw_mode)
        self.control_panel.draw_brush_changed.connect(self.update_draw_brush)
        self.control_panel.draw_apply_requested.connect(self.apply_drawing)
        self.control_panel.draw_cancel_requested.connect(self.cancel_drawing)

        self.control_panel.style_preset_requested.connect(self.apply_style_preset_ui)
        self.control_panel.style_custom_image_requested.connect(self.load_style_custom_image)
        self.control_panel.style_custom_requested.connect(self.apply_style_custom_ui)

        self.control_panel.tool_list.currentTextChanged.connect(
            lambda _: self._sync_interaction_modes()
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
        self.update_draw_brush(8, self.control_panel._draw_color)
        self._sync_interaction_modes()

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
        self.cancel_drawing()
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
        self._sync_interaction_modes()
        self.statusBar().showMessage("Undo", 2000)
        self.logger.info("Undo action")

    def redo(self) -> None:
        pixmap = self.app_state.redo()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self.control_panel.set_resize_source_dimensions(pixmap.width(), pixmap.height())
        self._update_action_states()
        self._sync_interaction_modes()
        self.statusBar().showMessage("Redo", 2000)
        self.logger.info("Redo action")

    def reset_image(self) -> None:
        pixmap = self.app_state.reset_to_original()
        if pixmap is None:
            return

        self.image_viewer.set_image(pixmap)
        self.control_panel.set_resize_source_dimensions(pixmap.width(), pixmap.height())
        self._update_action_states()
        self._sync_interaction_modes()
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
        self._sync_interaction_modes()

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
        self._sync_interaction_modes()

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
        self._sync_interaction_modes()

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
        self._sync_interaction_modes()

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
        self._sync_interaction_modes()

        self.statusBar().showMessage(
            f"Applied brightness={brightness}, contrast={contrast}",
            3000,
        )
        self.logger.info(
            "Applied brightness/contrast adjustment: brightness=%s contrast=%s",
            brightness,
            contrast,
        )

    def apply_blur(self, strength: int) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        blurred = apply_gaussian_blur(current, strength)
        if blurred.isNull():
            QMessageBox.warning(self, "Blur Failed", "Failed to apply blur.")
            return

        self.app_state.apply_new_current(blurred)
        self.image_viewer.set_image(blurred)
        self.control_panel.set_resize_source_dimensions(blurred.width(), blurred.height())
        self._update_action_states()
        self._sync_interaction_modes()

        kernel_size = 0 if strength <= 0 else 2 * strength + 1
        self.statusBar().showMessage(
            f"Applied Gaussian blur with strength={strength} (kernel={kernel_size})",
            3000,
        )
        self.logger.info(
            "Applied Gaussian blur with strength=%s kernel=%s",
            strength,
            kernel_size,
        )

    def set_draw_mode(self, enabled: bool) -> None:
        if not self.app_state.has_image():
            self.control_panel.set_draw_mode_state(False)
            return

        self.image_viewer.set_draw_mode(enabled)
        if enabled:
            self.update_draw_brush(
                self.control_panel.draw_size_slider.value(),
                self.control_panel._draw_color,
            )
            self.statusBar().showMessage("Draw mode enabled", 2000)
        else:
            self.statusBar().showMessage("Draw mode disabled", 2000)

    def update_draw_brush(self, size, color) -> None:
        self.image_viewer.set_draw_brush(size, color)

    def apply_drawing(self) -> None:
        if not self.image_viewer.is_draw_mode():
            QMessageBox.warning(self, "Draw Mode", "Start drawing first.")
            return

        drawn_pixmap = self.image_viewer.commit_drawing()
        if drawn_pixmap is None or drawn_pixmap.isNull():
            QMessageBox.warning(self, "Drawing Failed", "No drawing to apply.")
            return

        self.app_state.apply_new_current(drawn_pixmap)
        self.image_viewer.set_image(drawn_pixmap)
        self.control_panel.set_resize_source_dimensions(
            drawn_pixmap.width(), drawn_pixmap.height()
        )
        self._update_action_states()

        self.control_panel.set_draw_mode_state(False)
        self.image_viewer.set_draw_mode(False)
        self._sync_interaction_modes()

        self.statusBar().showMessage("Applied drawing", 3000)
        self.logger.info("Applied drawing to image")

    def cancel_drawing(self) -> None:
        self.image_viewer.cancel_drawing()
        self.control_panel.set_draw_mode_state(False)
        self.image_viewer.set_draw_mode(False)
        self._sync_interaction_modes()
        self.statusBar().showMessage("Drawing cancelled", 2000)

    def cancel_crop(self) -> None:
        self.image_viewer.set_crop_mode(False)
        self.control_panel.set_crop_selection_info(False)
        self._sync_interaction_modes()

    def on_module_selected(self, module_name: str) -> None:
        self.control_panel.show_module(module_name)
        self._sync_interaction_modes()
        self.statusBar().showMessage(f"Selected module: {module_name}", 2000)
        self.logger.info("Selected module: %s", module_name)

    def _sync_interaction_modes(self) -> None:
        current_tool = self.control_panel.current_tool_name()
        is_edit = self.control_panel.current_module == "Edit"
        has_image = self.app_state.has_image()

        enable_crop = is_edit and current_tool == "Crop" and has_image
        enable_draw = (
            is_edit
            and current_tool == "Draw"
            and has_image
            and self.control_panel.draw_toggle_button.isChecked()
        )

        if enable_draw:
            self.image_viewer.set_crop_mode(False)
            self.image_viewer.set_draw_mode(True)
            self.update_draw_brush(
                self.control_panel.draw_size_slider.value(),
                self.control_panel._draw_color,
            )
        else:
            self.image_viewer.set_draw_mode(False)

        if enable_crop:
            self.image_viewer.set_crop_mode(True)
        else:
            self.image_viewer.set_crop_mode(False)

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
    
    def generate_gif(
        self,
        effect: str,
        frame_count: int,
        max_zoom: float,
        pan_pixels: int,
        blur_strength: int,
        duration_ms: int,
    ) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            QMessageBox.warning(self, "No Image", "Load an image first.")
            return

        frames = generate_gif_frames(
            current,
            effect=effect,
            frame_count=frame_count,
            max_zoom=max_zoom,
            pan_pixels=pan_pixels,
            blur_strength=blur_strength,
        )

        if not frames:
            QMessageBox.warning(self, "GIF Failed", "Failed to generate GIF frames.")
            self.control_panel.set_gif_ready(False, "GIF generation failed.")
            return

        self._generated_gif_frames = frames
        self._generated_gif_duration_ms = duration_ms

        total_frames = len(frames)
        self.control_panel.set_gif_ready(
            True,
            f"Generated {effect} GIF with {total_frames} frames. Ready to preview or save.",
        )
        self.statusBar().showMessage(
            f"Generated GIF frames: effect={effect}, frames={total_frames}",
            3000,
        )
        self.logger.info(
            "Generated GIF: effect=%s frame_count=%s total_output_frames=%s duration_ms=%s",
            effect,
            frame_count,
            total_frames,
            duration_ms,
        )

        preview = GifPreviewDialog(
            frames=frames,
            duration_ms=duration_ms,
            effect_name=effect,
            parent=self,
        )
        preview.exec()

    def set_gif_ready(self, ready: bool, message: str) -> None:
        self.gif_save_button.setEnabled(ready)
        self.gif_status_label.setText(message)

    def save_generated_gif(self) -> None:
        if not self._generated_gif_frames:
            QMessageBox.warning(self, "No GIF", "Generate a GIF first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save GIF",
            "",
            "GIF Image (*.gif)",
        )

        if not file_path:
            return

        try:
            save_gif(self._generated_gif_frames, file_path, self._generated_gif_duration_ms)
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to save GIF.\n{exc}")
            self.logger.error("Failed to save GIF: %s", exc)
            return

        file_name = Path(file_path).name
        self.statusBar().showMessage(f"Saved GIF: {file_name}", 3000)
        self.logger.info("Saved GIF: %s", file_path)

    def load_style_custom_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Style Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )

        if not file_path:
            return

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
                "Failed to load style image.",
            )
            self.logger.error("Failed to load style image: %s", file_path)
            return

        self._style_custom_image_path = file_path
        self._style_custom_pixmap = pixmap
        self.control_panel.set_style_custom_image_path(file_path)

        self.statusBar().showMessage("Loaded custom style image", 3000)
        self.logger.info("Loaded custom style image: %s", file_path)


    def apply_style_preset_ui(self, preset_name: str, strength: int) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load a content image first.")
            return

        current = self.app_state.current_pixmap
        if current is None or current.isNull():
            return

        try:
            styled = apply_preset_style(current, preset_name, strength)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Style Transfer Error",
                f"Failed to apply preset style.\n{exc}",
            )
            self.logger.error("Preset style transfer failed: %s", exc)
            return

        if styled.isNull():
            QMessageBox.warning(self, "Style Transfer Failed", "Failed to create stylized image.")
            return

        self.app_state.apply_new_current(styled)
        self.image_viewer.set_image(styled)
        self.control_panel.set_resize_source_dimensions(styled.width(), styled.height())
        self._update_action_states()
        self._sync_interaction_modes()

        self.statusBar().showMessage(
            f"Applied preset style: {preset_name} (strength={strength})",
            3000,
        )
        self.logger.info(
            "Applied preset style: preset=%s strength=%s",
            preset_name,
            strength,
        )

    def apply_style_custom_ui(self, strength: int) -> None:
        if not self.app_state.has_image():
            QMessageBox.warning(self, "No Image", "Load a content image first.")
            return

        if self._style_custom_pixmap is None or self._style_custom_pixmap.isNull():
            QMessageBox.warning(
                self,
                "No Style Image",
                "Load a custom style image first.",
            )
            return

        QMessageBox.information(
            self,
            "Custom Style Transfer",
            (
                f"Custom style image loaded.\n"
                f"Strength: {strength}\n\n"
                "UI-ul este gata. Următorul pas este implementarea procesării reale."
            ),
        )
        self.statusBar().showMessage(
            f"Custom style requested (strength={strength})",
            3000,
        )
        self.logger.info(
            "Custom style UI request: style_path=%s strength=%s",
            self._style_custom_image_path,
            strength,
        )