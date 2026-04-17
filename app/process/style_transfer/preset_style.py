from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
from torchvision import transforms
from PySide6.QtGui import QPixmap

from app.process.style_transfer.style_model import PRESET_MODEL_PATHS
from app.utils.convert import numpy_to_qpixmap, qpixmap_to_numpy
from training.style_transfer.transformer_net import TransformerNet


_MODEL_CACHE: dict[str, TransformerNet] = {}


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _load_model(style_name: str) -> tuple[TransformerNet, torch.device]:
    if style_name not in PRESET_MODEL_PATHS:
        raise ValueError(f"Unknown preset style: {style_name}")

    if style_name in _MODEL_CACHE:
        device = _get_device()
        return _MODEL_CACHE[style_name], device

    model_path = Path(PRESET_MODEL_PATHS[style_name])
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    device = _get_device()
    model = TransformerNet().to(device)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    _MODEL_CACHE[style_name] = model
    return model, device


def _apply_mosaic_effect(rgb: np.ndarray, strength: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    block_size = max(4, min(128, 4 + int((strength / 100.0) * 60)))
    small_w = max(1, w // block_size)
    small_h = max(1, h // block_size)

    small = cv2.resize(rgb, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
    mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

    alpha_blend = max(0.0, min(1.0, strength / 100.0))
    blended = (
        rgb.astype("float32") * (1.0 - alpha_blend)
        + mosaic.astype("float32") * alpha_blend
    )
    return blended.clip(0, 255).astype("uint8")


def _apply_sketch_effect(rgb: np.ndarray, strength: int) -> np.ndarray:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (21, 21), 0)
    sketch = cv2.divide(gray, 255 - blurred, scale=256.0)
    sketch_color = cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)

    alpha_blend = max(0.0, min(1.0, strength / 100.0))
    blended = (
        rgb.astype("float32") * (1.0 - alpha_blend)
        + sketch_color.astype("float32") * alpha_blend
    )
    return blended.clip(0, 255).astype("uint8")


def apply_preset_style_array(image: np.ndarray, style_name: str, strength: int) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError("Expected image array with 3 or 4 channels")

    if image.shape[2] == 4:
        rgb = image[:, :, :3]
        alpha = image[:, :, 3:4]
    else:
        rgb = image
        alpha = None

    try:
        model, device = _load_model(style_name)
    except FileNotFoundError:
        if style_name == "Mosaic":
            result_rgb = _apply_mosaic_effect(rgb, strength)
        elif style_name == "Sketch":
            result_rgb = _apply_sketch_effect(rgb, strength)
        else:
            raise
    else:
        tensor = transforms.ToTensor()(rgb).unsqueeze(0).to(device)

        with torch.no_grad():
            stylized = model(tensor)
            stylized = torch.clamp(stylized, 0.0, 1.0)

        stylized_np = stylized.squeeze(0).permute(1, 2, 0).cpu().numpy()
        stylized_np = (stylized_np * 255.0).clip(0, 255).astype("uint8")

        h, w = rgb.shape[:2]
        if stylized_np.shape[:2] != (h, w):
            stylized_np = cv2.resize(stylized_np, (w, h), interpolation=cv2.INTER_LANCZOS4)

        alpha_blend = max(0.0, min(1.0, strength / 100.0))
        result_rgb = (
            rgb.astype("float32") * (1.0 - alpha_blend)
            + stylized_np.astype("float32") * alpha_blend
        ).clip(0, 255).astype("uint8")

    if alpha is not None:
        return np.concatenate([result_rgb, alpha], axis=2)

    return result_rgb


def apply_preset_style(pixmap: QPixmap, style_name: str, strength: int) -> QPixmap:
    if pixmap.isNull():
        return QPixmap()

    image = qpixmap_to_numpy(pixmap)
    result = apply_preset_style_array(image, style_name, strength)
    return numpy_to_qpixmap(result)