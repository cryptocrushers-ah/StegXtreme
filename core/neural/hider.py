import torch
import torch.nn as nn

class HiderNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(2, 64, kernel_size=3, padding=1),  # 2 channels: cover_Y + payload
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, kernel_size=3, padding=1),  # residual output
            nn.Tanh()  # keeps residual small
        )

    def forward(self, cover_Y: torch.Tensor, payload_bits: torch.Tensor) -> torch.Tensor:
        """
        cover_Y     : (B, 1, H, W)
        payload_bits: (B, 1, H, W) — broadcast to match cover size
        returns     : residual (B, 1, H, W) — no NaN, correct shape
        """
        x = torch.cat([cover_Y, payload_bits], dim=1)  # (B, 2, H, W)
        return self.encoder(x)