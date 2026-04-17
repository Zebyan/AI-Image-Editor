from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)


class ImagePreviewDialog(QDialog):
    def __init__(self, pixmap: QPixmap, prompt: str, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Generated Image Preview")
        self.resize(720, 680)

        self._pixmap = pixmap
        self._prompt = prompt
        self._use_image = False

        layout = QVBoxLayout()

        self.info_label = QLabel(
            f"Prompt: {prompt[:120]}" + ("..." if len(prompt) > 120 else "")
        )
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(560, 420)
        self.image_label.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #555;"
        )

        self._set_pixmap(self._pixmap)

        button_row = QHBoxLayout()
        self.use_button = QPushButton("Use Image")
        self.save_button = QPushButton("Save Image")
        self.close_button = QPushButton("Close")

        self.use_button.clicked.connect(self._use_image_clicked)
        self.save_button.clicked.connect(self._save_image)
        self.close_button.clicked.connect(self.reject)

        button_row.addWidget(self.use_button)
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.close_button)

        layout.addWidget(self.info_label)
        layout.addWidget(self.image_label, stretch=1)
        layout.addLayout(button_row)

        self.setLayout(layout)

    def _set_pixmap(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._set_pixmap(self._pixmap)

    def _use_image_clicked(self) -> None:
        self._use_image = True
        self.accept()

    def _save_image(self) -> None:
        if self._pixmap.isNull():
            QMessageBox.warning(self, "No Image", "There is no generated image to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Generated Image",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)"
        )

        if not file_path:
            return

        success = self._pixmap.save(file_path)
        if not success:
            QMessageBox.critical(self, "Save Error", "Failed to save the generated image.")
            return

        QMessageBox.information(self, "Saved", f"Saved generated image: {Path(file_path).name}")

    def should_use_image(self) -> bool:
        return self._use_image
