from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap


def qpixmap_to_numpy(pixmap: QPixmap) -> np.ndarray:
   
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)

    width = image.width()
    height = image.height()

    buffer = image.bits()
    array = np.frombuffer(buffer, dtype=np.uint8).reshape((height, width, 4))

    return array.copy()


def numpy_to_qpixmap(array: np.ndarray) -> QPixmap:
    
    if array.ndim != 3:
        raise ValueError("Expected a 3D NumPy array")

    height, width, channels = array.shape

    if channels == 3:
        image = QImage(
            array.data,
            width,
            height,
            array.strides[0],
            QImage.Format.Format_RGB888,
        )
    elif channels == 4:
        image = QImage(
            array.data,
            width,
            height,
            array.strides[0],
            QImage.Format.Format_RGBA8888,
        )
    else:
        raise ValueError("Expected 3 or 4 channels")

    return QPixmap.fromImage(image.copy())


def fit_with_aspect_ratio(
    original_width: int,
    original_height: int,
    target_width: int | None = None,
    target_height: int | None = None,
) -> tuple[int, int]:
    
    if original_width <= 0 or original_height <= 0:
        raise ValueError("Original dimensions must be positive")

    if target_width is None and target_height is None:
        raise ValueError("At least one target dimension must be provided")

    if target_width is not None and target_width <= 0:
        raise ValueError("Target width must be positive")

    if target_height is not None and target_height <= 0:
        raise ValueError("Target height must be positive")

    if target_width is not None and target_height is not None:
        return target_width, target_height

    if target_width is not None:
        ratio = original_height / original_width
        return target_width, max(1, round(target_width * ratio))

    ratio = original_width / original_height
    return max(1, round(target_height * ratio)), target_height