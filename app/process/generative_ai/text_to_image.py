from __future__ import annotations

import numpy as np
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image

from app.logger import setup_logger

logger = setup_logger()

# Global pipeline cache to avoid reloading
_pipeline = None


def get_device() -> torch.device:
    """Get the best available device for inference."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")


def get_pipeline() -> StableDiffusionPipeline:
    """Get or create the Stable Diffusion pipeline."""
    global _pipeline

    if _pipeline is None:
        logger.info("Loading Stable Diffusion pipeline...")
        device = get_device()

        # Use a smaller, faster model for better user experience
        model_id = "CompVis/stable-diffusion-v1-4"

        try:
            _pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                safety_checker=None,  # Disable safety checker for faster generation
            )
            _pipeline = _pipeline.to(device)

            # Enable attention slicing for lower memory usage
            _pipeline.enable_attention_slicing()

            logger.info(f"Stable Diffusion pipeline loaded on {device}")

        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion pipeline: {e}")
            raise RuntimeError(
                "Failed to load text-to-image model. Please check your internet connection "
                "and ensure you have sufficient disk space."
            ) from e

    return _pipeline


def preload_pipeline() -> StableDiffusionPipeline:
    """Ensure the text-to-image pipeline is loaded and cached."""
    return get_pipeline()


def generate_image_from_text(
    prompt: str,
    width: int = 512,
    height: int = 512,
    num_inference_steps: int = 20,
    guidance_scale: float = 7.5,
    seed: int | None = None,
) -> np.ndarray:
    """
    Generate an image from text using Stable Diffusion.

    Args:
        prompt: Text description of the image to generate
        width: Width of the generated image
        height: Height of the generated image
        num_inference_steps: Number of denoising steps (higher = better quality, slower)
        guidance_scale: How closely to follow the prompt (higher = more faithful to prompt)
        seed: Random seed for reproducible generation

    Returns:
        Generated image as numpy array in RGB format
    """
    logger.info(
        f"Generating image from prompt: '{prompt}' "
        f"({width}x{height}, steps={num_inference_steps}, guidance={guidance_scale})"
    )

    pipeline = get_pipeline()

    # Set up generator for reproducible results if seed is provided
    generator = None
    if seed is not None:
        generator = torch.Generator(device=get_device()).manual_seed(seed)

    try:
        # Generate the image
        result = pipeline(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        # Convert PIL image to numpy array
        image = result.images[0]
        image_array = np.array(image)

        logger.info("Image generation completed successfully")
        return image_array

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise RuntimeError(f"Failed to generate image: {str(e)}") from e