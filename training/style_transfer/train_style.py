from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dataset import ContentImageDataset
from losses import VGGFeatures, StyleTransferLoss, gram_matrix
from transformer_net import TransformerNet
from utils import get_device, imagenet_normalize, load_style_image, save_checkpoint

# Import preset paths
PRESET_MODEL_PATHS = {
    "Van Gogh": "models/style_transfer/van_gogh.pth",
    "Mosaic": "models/style_transfer/mosaic.pth",
    "Sketch": "models/style_transfer/sketch.pth",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train fast neural style transfer model.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to content images folder")
    parser.add_argument("--style-image", type=str, help="Path to style image")
    parser.add_argument(
        "--preset-name",
        type=str,
        choices=list(PRESET_MODEL_PATHS.keys()),
        help="Optional preset name to infer default style image and model output path",
    )
    parser.add_argument("--output", type=str, help="Output .pth path")
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-3)

    parser.add_argument("--content-weight", type=float, default=1.0)
    parser.add_argument("--style-weight", type=float, default=5e5)
    parser.add_argument("--tv-weight", type=float, default=1e-6)

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output (print every step)")
    parser.add_argument("--save-every", type=int, default=500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = get_device()

    if args.verbose:
        print(f"Training on device: {device}")
        print(f"Dataset: {args.dataset}")
        print(f"Style image: {args.style_image}")
        print(f"Output: {args.output}")
        print(f"Image size: {args.image_size}")
        print(f"Batch size: {args.batch_size}")
        print(f"Epochs: {args.epochs}")
        print(f"Learning rate: {args.lr}")
        print(f"Content weight: {args.content_weight}")
        print(f"Style weight: {args.style_weight}")
        print(f"TV weight: {args.tv_weight}")
        print("Starting training...")

    if args.preset_name is not None and args.style_image is None:
        style_image_path = Path("training/style_transfer/styles") / f"{args.preset_name.replace(' ', '_').lower()}.jpg"
        if not style_image_path.exists():
            raise FileNotFoundError(
                f"Default style image not found for preset '{args.preset_name}': {style_image_path}"
            )
        args.style_image = str(style_image_path)

    if args.style_image is None:
        raise ValueError("A style image must be provided via --style-image or --preset-name.")

    if args.output is None:
        if args.preset_name is None:
            raise ValueError("An output path must be provided via --output when --preset-name is not set.")
        args.output = PRESET_MODEL_PATHS[args.preset_name]

    dataset = ContentImageDataset(args.dataset, image_size=args.image_size)
    if len(dataset) == 0:
        raise ValueError("Dataset folder does not contain any supported images.")

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=torch.cuda.is_available(),
    )

    if args.verbose:
        print(f"Dataset loaded: {len(dataset)} images")
        print("Initializing models...")

    transformer = TransformerNet().to(device)
    vgg = VGGFeatures().to(device).eval()

    style_image = load_style_image(args.style_image, args.image_size, device)
    style_image_norm = imagenet_normalize(style_image)
    with torch.no_grad():
        style_features = vgg(style_image_norm)
        style_grams = {k: gram_matrix(v).squeeze(0) for k, v in style_features.items()}

    if args.verbose:
        print("Style features extracted")
        print("Starting training loop...")

    criterion = StyleTransferLoss(
        content_weight=args.content_weight,
        style_weight=args.style_weight,
        tv_weight=args.tv_weight,
    )
    optimizer = torch.optim.Adam(transformer.parameters(), lr=args.lr)

    global_step = 0
    transformer.train()

    for epoch in range(args.epochs):
        for batch_index, content_batch in enumerate(loader):
            global_step += 1

            content_batch = content_batch.to(device)
            content_batch_norm = imagenet_normalize(content_batch)

            optimizer.zero_grad()

            output_batch = transformer(content_batch)
            output_batch = torch.clamp(output_batch, 0.0, 1.0)
            output_batch_norm = imagenet_normalize(output_batch)

            with torch.no_grad():
                content_features = vgg(content_batch_norm)

            output_features = vgg(output_batch_norm)

            total_loss, metrics = criterion(
                output_features=output_features,
                content_features=content_features,
                style_grams=style_grams,
                output_image=output_batch,
            )

            total_loss.backward()
            optimizer.step()

            if global_step % (1 if args.verbose else 50) == 0:
                print(
                    f"[epoch {epoch+1} step {global_step}] "
                    f"total={metrics['total_loss']:.4f} "
                    f"content={metrics['content_loss']:.4f} "
                    f"style={metrics['style_loss']:.4f} "
                    f"tv={metrics['tv_loss']:.6f}"
                )

            if global_step % args.save_every == 0:
                checkpoint_path = Path(args.output).with_name(
                    f"{Path(args.output).stem}_step_{global_step}.pth"
                )
                save_checkpoint(transformer, checkpoint_path)
                print(f"Saved checkpoint: {checkpoint_path}")

    save_checkpoint(transformer, args.output)
    print(f"Training complete. Saved model to: {args.output}")


if __name__ == "__main__":
    main()