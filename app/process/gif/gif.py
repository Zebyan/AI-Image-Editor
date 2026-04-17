from __future__ import annotations

from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image
from PySide6.QtGui import QPixmap

from app.utils.convert import qpixmap_to_numpy


GifEffect = Literal["Zoom Loop", "Pan Loop", "Blur Pulse"]


def _numpy_rgba_to_pil(array: np.ndarray) -> Image.Image:
    if array.ndim != 3 or array.shape[2] != 4:
        raise ValueError("Expected RGBA image array with shape (H, W, 4)")
    return Image.fromarray(array, mode="RGBA")


def _safe_frame_count(frame_count: int) -> int:
    return max(2, frame_count)


def _center_crop(array: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    h, w = array.shape[:2]
    x = max(0, (w - target_w) // 2)
    y = max(0, (h - target_h) // 2)
    return array[y:y + target_h, x:x + target_w].copy()


def _build_zoom_frame(image: np.ndarray, zoom: float) -> np.ndarray:
    h, w = image.shape[:2]
    new_w = max(w, round(w * zoom))
    new_h = max(h, round(h * zoom))

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    return _center_crop(resized, w, h)


def _build_pan_frame(image: np.ndarray, shift_x: int, shift_y: int) -> np.ndarray:
    h, w = image.shape[:2]

    pad_x = abs(shift_x)
    pad_y = abs(shift_y)

    padded = cv2.copyMakeBorder(
        image,
        pad_y,
        pad_y,
        pad_x,
        pad_x,
        borderType=cv2.BORDER_REFLECT,
    )

    start_x = pad_x + shift_x
    start_y = pad_y + shift_y

    return padded[start_y:start_y + h, start_x:start_x + w].copy()


def _build_blur_frame(image: np.ndarray, strength: int) -> np.ndarray:
    if strength <= 0:
        return image.copy()

    rgb = image[:, :, :3]
    alpha = image[:, :, 3:4]

    kernel = max(1, 2 * strength + 1)
    blurred_rgb = cv2.GaussianBlur(rgb, (kernel, kernel), 0)

    return np.concatenate([blurred_rgb, alpha], axis=2)


def generate_gif_frames_from_array(
    image: np.ndarray,
    effect: GifEffect,
    frame_count: int,
    max_zoom: float = 1.15,
    pan_pixels: int = 30,
    blur_strength: int = 4,
) -> list[Image.Image]:
    if image.ndim != 3 or image.shape[2] != 4:
        return []

    frame_count = _safe_frame_count(frame_count)
    frames_np: list[np.ndarray] = []

    if effect == "Zoom Loop":
        forward = np.linspace(1.0, max(1.0, max_zoom), frame_count)
        sequence = list(forward) + list(forward[-2:0:-1])
        for zoom in sequence:
            frames_np.append(_build_zoom_frame(image, float(zoom)))

    elif effect == "Pan Loop":
        forward = np.linspace(-pan_pixels, pan_pixels, frame_count)
        sequence = list(forward) + list(forward[-2:0:-1])
        for shift in sequence:
            frames_np.append(_build_pan_frame(image, int(round(shift)), 0))

    elif effect == "Blur Pulse":
        forward = np.linspace(0, max(0, blur_strength), frame_count)
        sequence = list(forward) + list(forward[-2:0:-1])
        for blur in sequence:
            frames_np.append(_build_blur_frame(image, int(round(blur))))

    else:
        return []

    return [_numpy_rgba_to_pil(frame) for frame in frames_np]


def generate_gif_frames(
    pixmap: QPixmap,
    effect: GifEffect,
    frame_count: int,
    max_zoom: float = 1.15,
    pan_pixels: int = 30,
    blur_strength: int = 4,
) -> list[Image.Image]:
    if pixmap.isNull():
        return []

    image = qpixmap_to_numpy(pixmap)
    return generate_gif_frames_from_array(
        image=image,
        effect=effect,
        frame_count=frame_count,
        max_zoom=max_zoom,
        pan_pixels=pan_pixels,
        blur_strength=blur_strength,
    )


def save_gif(frames: list[Image.Image], output_path: str, duration_ms: int) -> None:
    if not frames:
        raise ValueError("No GIF frames to save")

    duration_ms = max(20, duration_ms)
    output = Path(output_path)

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )