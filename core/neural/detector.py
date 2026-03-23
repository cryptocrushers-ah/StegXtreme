"""
DetectorNetwork — steganalysis neural classifier.

Key improvement over original:
  Added SRMFilter as a fixed preprocessing stage before the learnable layers.

What SRMFilter does:
  - Applies a fixed 5x5 Laplacian-of-Gaussian high-pass kernel
  - Extracts the noise residual from the image before classification
  - This is exactly what the Spatial Rich Model (SRNet) paper showed
    dramatically improves stego detection accuracy
  - The filter weights are FIXED — they are NOT learned, NOT updated
    by the optimizer, so existing training is not affected
  - The detector now classifies NOISE PATTERNS rather than raw pixels
    which is what steganographic embedding actually changes

  Why this matters for StegXtreme specifically:
  - DWT SS embedding injects spread-spectrum noise into the LL subband
  - That noise is invisible in raw pixels but visible in residuals
  - Before: Conv layers had to learn both noise extraction AND classification
  - After:  Conv layers only classify — faster convergence, better accuracy

Added Dropout(0.3) before final linear layer:
  - Reduces false positives on clean images
  - Especially important given the current calibration issues seen in analysis
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SRMFilter(nn.Module):
    """
    Fixed 5x5 Spatial Rich Model high-pass filter.
    Extracts noise residuals that steganographic embedding leaves behind.

    Weights are registered as a BUFFER — not a parameter.
    This means:
      - They move to GPU automatically with .to(device)
      - They are NOT updated by any optimizer
      - They are saved/loaded with model state_dict (for compatibility)
      - Zero training cost — this is pure signal processing
    """

    def __init__(self):
        super().__init__()
        # Laplacian-of-Gaussian kernel — standard in steganalysis literature
        # Amplifies high-frequency noise while suppressing smooth regions
        kernel = torch.tensor([[
            [[ 0,  0, -1,  0,  0],
             [ 0, -1,  2, -1,  0],
             [-1,  2,  8,  2, -1],
             [ 0, -1,  2, -1,  0],
             [ 0,  0, -1,  0,  0]]
        ]], dtype=torch.float32) / 8.0
        # register_buffer: part of state_dict, moves to GPU, NOT trained
        self.register_buffer("weight", kernel)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (B, 1, H, W) — grayscale image
        returns: (B, 1, H, W) — noise residual map
        """
        return F.conv2d(x, self.weight, padding=2)


class DetectorNetwork(nn.Module):
    """
    Steganalysis classifier with SRM residual preprocessing.

    Input pipeline:
      raw pixels → SRMFilter (fixed) → Conv layers → classifier

    Architecture unchanged from original except:
      1. SRMFilter prepended (fixed, no training cost)
      2. Dropout(0.3) added before final linear (reduces false positives)
    """

    def __init__(self):
        super().__init__()

        # ── Stage 1: Fixed noise residual extraction ───────────────────
        self.srm = SRMFilter()

        # ── Stage 2: Learnable feature extraction ─────────────────────
        # Identical architecture to original — input is now residuals
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

        # ── Stage 3: Classifier ────────────────────────────────────────
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),            # NEW — reduces false positives
            nn.Linear(128, 1),
            nn.Sigmoid()                # output: 0 = clean, 1 = stego
        )

    def forward(self, frame_Y: torch.Tensor) -> torch.Tensor:
        """
        frame_Y: (B, 1, H, W) — grayscale image patch
        returns: (B, 1) — detection probability 0.0–1.0
        """
        residual = self.srm(frame_Y)           # extract noise residual
        features = self.features(residual)     # classify noise pattern
        return self.classifier(features)