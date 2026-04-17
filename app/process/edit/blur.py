from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy, numpy_to_qpixmap


def apply_gaussian_blur(pixmap: QPixmap, strength: int) -> QPixmap:
    """
    strength: expected range 0..20
    Maps to odd kernel sizes:
      0 -> no blur
      1 -> 3
      2 -> 5
      3 -> 7
      ...
    """
    if pixmap.isNull():
        return QPixmap()

    if strength <= 0:
        return pixmap.copy()

    image = qpixmap_to_numpy(pixmap)

    if image.ndim != 3 or image.shape[2] not in (3, 4):
        return QPixmap()

    kernel_size = max(1, 2 * strength + 1)

    if image.shape[2] == 4:
        rgb = image[:, :, :3]
        alpha = image[:, :, 3:4]

        blurred_rgb = cv2.GaussianBlur(rgb, (kernel_size, kernel_size), 0)
        result = np.concatenate([blurred_rgb, alpha], axis=2)
    else:
        result = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    return numpy_to_qpixmap(result)