from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)

from app.process.gif.gif import save_gif


def pil_image_to_qpixmap(image: Image.Image) -> QPixmap:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    data = rgba.tobytes("raw", "RGBA")

    qimage = QImage(data, width, height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimage.copy())


class GifPreviewDialog(QDialog):
    def __init__(
        self,
        frames: list[Image.Image],
        duration_ms: int,
        effect_name: str,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("GIF Preview")
        self.resize(700, 600)

        self._frames_pil = frames
        self._duration_ms = max(20, duration_ms)
        self._effect_name = effect_name
        self._frame_index = 0

        self._frames_pixmap = [pil_image_to_qpixmap(frame) for frame in frames]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_frame)

        layout = QVBoxLayout()

        self.info_label = QLabel(
            f"Effect: {effect_name} | Frames: {len(frames)} | Duration: {self._duration_ms} ms"
        )
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel("No preview")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(500, 400)
        self.image_label.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #555;"
        )

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Save GIF")
        self.close_button = QPushButton("Close")

        self.save_button.clicked.connect(self._save_gif)
        self.close_button.clicked.connect(self.accept)

        button_row.addWidget(self.save_button)
        button_row.addWidget(self.close_button)

        layout.addWidget(self.info_label)
        layout.addWidget(self.image_label, stretch=1)
        layout.addLayout(button_row)

        self.setLayout(layout)

        if self._frames_pixmap:
            self._show_current_frame()
            self._timer.start(self._duration_ms)

    def _show_current_frame(self) -> None:
        if not self._frames_pixmap:
            return

        pixmap = self._frames_pixmap[self._frame_index]
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def _advance_frame(self) -> None:
        if not self._frames_pixmap:
            return

        self._frame_index = (self._frame_index + 1) % len(self._frames_pixmap)
        self._show_current_frame()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._show_current_frame()

    def _save_gif(self) -> None:
        if not self._frames_pil:
            QMessageBox.warning(self, "No GIF", "There is no GIF to save.")
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
            save_gif(self._frames_pil, file_path, self._duration_ms)
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to save GIF.\n{exc}")
            return

        file_name = Path(file_path).name
        QMessageBox.information(self, "Saved", f"Saved GIF: {file_name}")