import torch
import torch.nn as nn

class HiderNetwork(nn.Module):
    """
    Architecture only — no training yet.
    forward(cover_Y, payload_bits) returns residual tensor.
    """
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, kernel_size=3, padding=1),
        )

    def forward(self, cover_Y: torch.Tensor, payload_bits: torch.Tensor) -> torch.Tensor:
        """
        cover_Y     : (B, 1, H, W) float tensor — Y channel of cover image
        payload_bits: (B, N) float tensor — bits to hide
        returns     : residual tensor (B, 1, H, W) — add to cover_Y to get stego
        """
        residual = self.encoder(cover_Y)
        return residual