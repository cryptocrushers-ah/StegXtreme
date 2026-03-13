import torch
import torch.nn as nn
from core.neural.hider import HiderNetwork
from core.neural.detector import DetectorNetwork

class GANTrainer:
    def __init__(self, device=None):
        self.device = device or (
            torch.device("cuda") if torch.cuda.is_available() 
            else torch.device("cpu")
        )
        self.hider    = HiderNetwork().to(self.device)
        self.detector = DetectorNetwork().to(self.device)
        
        self.h_optimizer = torch.optim.Adam(
            self.hider.parameters(), lr=1e-4
        )
        self.d_optimizer = torch.optim.Adam(
            self.detector.parameters(), lr=1e-4
        )
        self.bce = nn.BCELoss()

    def train_step(self, cover_frames, payloads):
        """
        cover_frames: (B, 1, H, W) float tensor
        payloads    : (B, 1, H, W) float tensor
        returns     : dict with d_loss and h_loss as plain floats
        """
        cover_frames = cover_frames.to(self.device)
        payloads     = payloads.to(self.device)
        B            = cover_frames.size(0)

        # ── Train Detector ─────────────────────────────────────
        self.d_optimizer.zero_grad()

        # real frames → detector should output 0 (clean)
        real_labels = torch.zeros(B, 1).to(self.device)
        real_preds  = self.detector(cover_frames)
        d_real_loss = self.bce(real_preds, real_labels)

        # stego frames → detector should output 1 (stego)
        with torch.no_grad():
            residual     = self.hider(cover_frames, payloads)
            stego_frames = cover_frames + residual

        fake_labels = torch.ones(B, 1).to(self.device)
        fake_preds  = self.detector(stego_frames.detach())
        d_fake_loss = self.bce(fake_preds, fake_labels)

        d_loss = (d_real_loss + d_fake_loss) / 2
        d_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.detector.parameters(), 1.0
        )
        self.d_optimizer.step()

        # ── Train Hider ─────────────────────────────────────────
        self.h_optimizer.zero_grad()

        residual     = self.hider(cover_frames, payloads)
        stego_frames = cover_frames + residual

        # fooling loss — hider wants detector to output 0 (think it's clean)
        fool_labels   = torch.zeros(B, 1).to(self.device)
        fool_preds    = self.detector(stego_frames)
        fooling_loss  = self.bce(fool_preds, fool_labels)

        # perceptual loss — stego should look like cover
        perceptual_loss = nn.functional.mse_loss(
            stego_frames, cover_frames
        )

        h_loss = fooling_loss + 10 * perceptual_loss
        h_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.hider.parameters(), 1.0
        )
        self.h_optimizer.step()

        return {
            "d_loss": float(d_loss.item()),
            "h_loss": float(h_loss.item())
        }