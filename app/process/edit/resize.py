from __future__ import annotations

import cv2
from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy, numpy_to_qpixmap


INTERPOLATION_MAP = {
    "Nearest": cv2.INTER_NEAREST,
    "Bilinear": cv2.INTER_LINEAR,
    "Bicubic": cv2.INTER_CUBIC,
    "Area": cv2.INTER_AREA,
    "Lanczos": cv2.INTER_LANCZOS4,
}


def resize_pixmap(
    pixmap: QPixmap,
    target_width: int,
    target_height: int,
    interpolation_name: str = "Bilinear",
) -> QPixmap:
    if pixmap.isNull():
        return QPixmap()

    if target_width <= 0 or target_height <= 0:
        return QPixmap()

    image_array = qpixmap_to_numpy(pixmap)

    interpolation = INTERPOLATION_MAP.get(interpolation_name, cv2.INTER_LINEAR)

    resized_array = cv2.resize(
        image_array,
        (target_width, target_height),
        interpolation=interpolation,
    )

    return numpy_to_qpixmap(resized_array)