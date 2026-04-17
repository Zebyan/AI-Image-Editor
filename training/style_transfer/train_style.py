from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from dataset import ContentImageDataset
from losses import VGGFeatures, StyleTransferLoss, gram_matrix
from transformer_net import TransformerNet
from utils import get_device, imagenet_normalize, load_style_image, save_checkpoint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train fast neural style transfer model.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to content images folder")
    parser.add_argument("--style-image", type=str, required=True, help="Path to style image")
    parser.add_argument("--output", type=str, required=True, help="Output .pth path")
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-3)

    parser.add_argument("--content-weight", type=float, default=1.0)
    parser.add_argument("--style-weight", type=float, default=5e5)
    parser.add_argument("--tv-weight", type=float, default=1e-6)

    parser.add_argument("--save-every", type=int, default=500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = get_device()

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

    transformer = TransformerNet().to(device)
    vgg = VGGFeatures().to(device).eval()

    style_image = load_style_image(args.style_image, args.image_size, device)
    style_image_norm = imagenet_normalize(style_image)
    with torch.no_grad():
        style_features = vgg(style_image_norm)
        style_grams = {k: gram_matrix(v) for k, v in style_features.items()}

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

            if global_step % 50 == 0:
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