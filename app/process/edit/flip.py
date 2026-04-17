from __future__ import annotations

import cv2
from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy, numpy_to_qpixmap


FLIP_CODE_MAP = {
    "horizontal": 1,
    "vertical": 0,
    "both": -1,
}


def flip_pixmap(pixmap: QPixmap, direction: str) -> QPixmap:
    if pixmap.isNull():
        return QPixmap()

    flip_code = FLIP_CODE_MAP.get(direction.lower())
    if flip_code is None:
        return QPixmap()

    image = qpixmap_to_numpy(pixmap)
    flipped = cv2.flip(image, flip_code)

    return numpy_to_qpixmap(flipped)