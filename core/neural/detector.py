import torch
import torch.nn as nn

class DetectorNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                              # H/2, W/2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                              # H/4, W/4
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4))                  # fixed 4x4 output
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 1),
            nn.Sigmoid()                                  # output between 0 and 1
        )

    def forward(self, frame_Y: torch.Tensor) -> torch.Tensor:
        """
        frame_Y: (B, 1, H, W)
        returns: (B, 1) probability float between 0 and 1
        """
        x = self.features(frame_Y)
        return self.classifier(x)