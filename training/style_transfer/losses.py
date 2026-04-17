from __future__ import annotations

import torch
from torch import nn
from torchvision import models


def gram_matrix(x: torch.Tensor) -> torch.Tensor:
    batch_size, channels, height, width = x.shape
    features = x.view(batch_size, channels, height * width)
    features_t = features.transpose(1, 2)
    gram = features.bmm(features_t) / (channels * height * width)
    return gram


class VGGFeatures(nn.Module):
    """
    Extract selected VGG16 feature maps for perceptual losses.
    """
    def __init__(self) -> None:
        super().__init__()
        vgg = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_FEATURES).features.eval()

        self.slice1 = nn.Sequential(*[vgg[x] for x in range(4)])    # relu1_2
        self.slice2 = nn.Sequential(*[vgg[x] for x in range(4, 9)]) # relu2_2
        self.slice3 = nn.Sequential(*[vgg[x] for x in range(9, 16)])# relu3_3
        self.slice4 = nn.Sequential(*[vgg[x] for x in range(16, 23)])# relu4_3

        for param in self.parameters():
            param.requires_grad = False

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        h1 = self.slice1(x)
        h2 = self.slice2(h1)
        h3 = self.slice3(h2)
        h4 = self.slice4(h3)
        return {
            "relu1_2": h1,
            "relu2_2": h2,
            "relu3_3": h3,
            "relu4_3": h4,
        }


class StyleTransferLoss(nn.Module):
    def __init__(
        self,
        content_weight: float,
        style_weight: float,
        tv_weight: float,
    ) -> None:
        super().__init__()
        self.content_weight = content_weight
        self.style_weight = style_weight
        self.tv_weight = tv_weight
        self.mse = nn.MSELoss()

    def total_variation_loss(self, x: torch.Tensor) -> torch.Tensor:
        loss_h = torch.mean(torch.abs(x[:, :, :, :-1] - x[:, :, :, 1:]))
        loss_v = torch.mean(torch.abs(x[:, :, :-1, :] - x[:, :, 1:, :]))
        return loss_h + loss_v

    def forward(
        self,
        output_features: dict[str, torch.Tensor],
        content_features: dict[str, torch.Tensor],
        style_grams: dict[str, torch.Tensor],
        output_image: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        content_loss = self.mse(
            output_features["relu3_3"],
            content_features["relu3_3"],
        )

        style_loss = 0.0
        for key in ("relu1_2", "relu2_2", "relu3_3", "relu4_3"):
            output_gram = gram_matrix(output_features[key])
            style_gram_expanded = style_grams[key].unsqueeze(0).expand_as(output_gram)
            style_loss = style_loss + self.mse(output_gram, style_gram_expanded)

        tv_loss = self.total_variation_loss(output_image)

        total = (
            self.content_weight * content_loss
            + self.style_weight * style_loss
            + self.tv_weight * tv_loss
        )

        metrics = {
            "content_loss": float(content_loss.item()),
            "style_loss": float(style_loss.item()),
            "tv_loss": float(tv_loss.item()),
            "total_loss": float(total.item()),
        }
        return total, metrics