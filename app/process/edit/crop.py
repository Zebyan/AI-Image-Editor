from __future__ import annotations

from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy, numpy_to_qpixmap


def crop_pixmap(
    pixmap: QPixmap,
    x: int,
    y: int,
    width: int,
    height: int,
) -> QPixmap:
    if pixmap.isNull():
        return QPixmap()

    if width <= 0 or height <= 0:
        return QPixmap()

    image = qpixmap_to_numpy(pixmap)
    img_height, img_width = image.shape[:2]

    x = max(0, min(x, img_width - 1))
    y = max(0, min(y, img_height - 1))

    width = min(width, img_width - x)
    height = min(height, img_height - y)

    if width <= 0 or height <= 0:
        return QPixmap()

    cropped = image[y:y + height, x:x + width].copy()
    return numpy_to_qpixmap(cropped)