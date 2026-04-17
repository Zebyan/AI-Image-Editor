from __future__ import annotations

import math

import cv2
import numpy as np
from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy, numpy_to_qpixmap


INTERPOLATION_MAP = {
    "Nearest": cv2.INTER_NEAREST,
    "Bilinear": cv2.INTER_LINEAR,
    "Bicubic": cv2.INTER_CUBIC,
    "Lanczos": cv2.INTER_LANCZOS4,
}


def rotate_pixmap(
    pixmap: QPixmap,
    angle_degrees: float,
    interpolation_name: str = "Bilinear",
    expand_canvas: bool = True,
) -> QPixmap:
    if pixmap.isNull():
        return QPixmap()

    image = qpixmap_to_numpy(pixmap)
    height, width = image.shape[:2]

    center = (width / 2.0, height / 2.0)
    interpolation = INTERPOLATION_MAP.get(interpolation_name, cv2.INTER_LINEAR)

    rotation_matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)

    if expand_canvas:
        cos_value = abs(rotation_matrix[0, 0])
        sin_value = abs(rotation_matrix[0, 1])

        new_width = int((height * sin_value) + (width * cos_value))
        new_height = int((height * cos_value) + (width * sin_value))

        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]

        output_size = (new_width, new_height)
    else:
        output_size = (width, height)

    rotated = cv2.warpAffine(
        image,
        rotation_matrix,
        output_size,
        flags=interpolation,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    return numpy_to_qpixmap(rotated)