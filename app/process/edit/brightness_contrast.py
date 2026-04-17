from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy, numpy_to_qpixmap


def adjust_brightness_contrast(
    pixmap: QPixmap,
    brightness: int,
    contrast: int,
) -> QPixmap:
    
    if pixmap.isNull():
        return QPixmap()

    image = qpixmap_to_numpy(pixmap)

    if image.ndim != 3 or image.shape[2] not in (3, 4):
        return QPixmap()

    if image.shape[2] == 4:
        rgb = image[:, :, :3]
        alpha = image[:, :, 3:4]
    else:
        rgb = image
        alpha = None

    alpha_scale = 1.0 + (contrast / 100.0)
    beta_shift = brightness * 255 / 100.0

    adjusted_rgb = cv2.convertScaleAbs(
        rgb,
        alpha=alpha_scale,
        beta=beta_shift,
    )

    if alpha is not None:
        result = np.concatenate([adjusted_rgb, alpha], axis=2)
    else:
        result = adjusted_rgb

    return numpy_to_qpixmap(result)