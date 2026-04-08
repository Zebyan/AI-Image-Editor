from pathlib import Path

from PySide6.QtGui import QPixmap


SUPPORTED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".webp",
}


def is_supported_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def load_pixmap(image_path: str) -> QPixmap:
    pixmap = QPixmap(image_path)
    return pixmap