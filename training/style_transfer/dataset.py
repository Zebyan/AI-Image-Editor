from __future__ import annotations

from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms


class ContentImageDataset(Dataset):
    def __init__(self, root_dir: str | Path, image_size: int = 256) -> None:
        self.root_dir = Path(root_dir)
        self.files = [
            p for p in self.root_dir.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        ]

        self.transform = transforms.Compose([
            transforms.Resize(image_size + 32),
            transforms.RandomCrop(image_size),
            transforms.ToTensor(),
        ])

    def __len__(self) -> int:
        return len(self.files)

    def __getitem__(self, index: int):
        image_path = self.files[index]
        image = Image.open(image_path).convert("RGB")
        return self.transform(image)