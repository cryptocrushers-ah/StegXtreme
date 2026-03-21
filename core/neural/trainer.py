import torch
import torch.nn as nn
from core.neural.hider import HiderNetwork
from core.neural.detector import DetectorNetwork


class GANTrainer:
    def __init__(self, device=None):
        # ── Device Setup ───────────────────────────────────────
        if device is None:
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                print(f"Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                self.device = torch.device("cpu")
                print("Using CPU")
        else:
            self.device = device

        # ── Models ─────────────────────────────────────────────
        self.hider    = HiderNetwork().to(self.device)
        self.detector = DetectorNetwork().to(self.device)

        # ── Optimizers ─────────────────────────────────────────
        self.h_optimizer = torch.optim.Adam(
            self.hider.parameters(),
            lr=1e-4,
            betas=(0.5, 0.999)   # GAN standard betas
        )
        self.d_optimizer = torch.optim.Adam(
            self.detector.parameters(),
            lr=1e-4,
            betas=(0.5, 0.999)
        )

        # ── Loss ───────────────────────────────────────────────
        self.bce = nn.BCELoss()

        # ── Learning Rate Schedulers ───────────────────────────
        self.h_scheduler = torch.optim.lr_scheduler.StepLR(
            self.h_optimizer,
            step_size=5000,
            gamma=0.5   # halve lr every 5000 steps
        )
        self.d_scheduler = torch.optim.lr_scheduler.StepLR(
            self.d_optimizer,
            step_size=5000,
            gamma=0.5
        )

        # ── Initialize optimizer states ────────────────────────
        self.h_optimizer.zero_grad()
        self.d_optimizer.zero_grad()

        # ── Step counter ───────────────────────────────────────
        self.step_count = 0

    def train_step(
        self,
        cover_frames: torch.Tensor,
        payloads: torch.Tensor
    ) -> dict:
        """
        One GAN training step.
        Detector trains 2x per step to stay ahead of hider.
        cover_frames: (B, 1, H, W)
        payloads    : (B, 1, H, W)
        returns     : dict with d_loss and h_loss as floats
        """
        cover_frames = cover_frames.to(self.device)
        payloads     = payloads.to(self.device)
        B            = cover_frames.size(0)

        self.step_count += 1

        # ── Train Detector 2x ──────────────────────────────────
        d_loss_val = 0.0
        for _ in range(2):
            self.d_optimizer.zero_grad()

            # real frames → label 0 (clean)
            real_labels = torch.zeros(B, 1).to(self.device)
            real_preds  = self.detector(cover_frames)
            d_real_loss = self.bce(real_preds, real_labels)

            # generate stego frames
            with torch.no_grad():
                residual     = self.hider(cover_frames, payloads)
                stego_frames = torch.clamp(
                    cover_frames + residual, 0.0, 1.0
                )

            # stego frames → label 1 (stego)
            fake_labels = torch.ones(B, 1).to(self.device)
            fake_preds  = self.detector(stego_frames.detach())
            d_fake_loss = self.bce(fake_preds, fake_labels)

            d_loss = (d_real_loss + d_fake_loss) / 2
            d_loss.backward()
            torch.nn.utils.clip_grad_norm_(
                self.detector.parameters(), 1.0
            )
            self.d_optimizer.step()
            d_loss_val = d_loss.item()

        # ── Train Hider 1x ─────────────────────────────────────
        self.h_optimizer.zero_grad()

        residual     = self.hider(cover_frames, payloads)
        stego_frames = torch.clamp(
            cover_frames + residual, 0.0, 1.0
        )

        # fooling loss — hider wants detector to output 0
        fool_labels     = torch.zeros(B, 1).to(self.device)
        fool_preds      = self.detector(stego_frames)
        fooling_loss    = self.bce(fool_preds, fool_labels)

        # perceptual loss — stego must look like cover
        perceptual_loss = nn.functional.mse_loss(
            stego_frames, cover_frames
        )

        # ssim loss — structural similarity
        ssim_loss = 1.0 - self._ssim(stego_frames, cover_frames)

        # combined hider loss
        h_loss = (
            fooling_loss +
            10.0 * perceptual_loss +
            2.0  * ssim_loss
        )
        h_loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.hider.parameters(), 1.0
        )
        self.h_optimizer.step()

        # ── Update schedulers ──────────────────────────────────
        self.h_scheduler.step()
        self.d_scheduler.step()

        return {
            "d_loss"         : float(d_loss_val),
            "h_loss"         : float(h_loss.item()),
            "fooling_loss"   : float(fooling_loss.item()),
            "perceptual_loss": float(perceptual_loss.item()),
        }

    def _ssim(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
        window_size: int = 11
    ) -> torch.Tensor:
        """
        Simplified SSIM loss.
        Measures structural similarity between stego and cover.
        """
        C1 = 0.01 ** 2
        C2 = 0.03 ** 2

        mu_x    = nn.functional.avg_pool2d(
            x, window_size, stride=1,
            padding=window_size//2
        )
        mu_y    = nn.functional.avg_pool2d(
            y, window_size, stride=1,
            padding=window_size//2
        )
        mu_x_sq = mu_x ** 2
        mu_y_sq = mu_y ** 2
        mu_xy   = mu_x * mu_y

        sigma_x  = nn.functional.avg_pool2d(
            x**2, window_size, stride=1,
            padding=window_size//2
        ) - mu_x_sq

        sigma_y  = nn.functional.avg_pool2d(
            y**2, window_size, stride=1,
            padding=window_size//2
        ) - mu_y_sq

        sigma_xy = nn.functional.avg_pool2d(
            x * y, window_size, stride=1,
            padding=window_size//2
        ) - mu_xy

        ssim_map = (
            (2 * mu_xy   + C1) * (2 * sigma_xy + C2)
        ) / (
            (mu_x_sq + mu_y_sq + C1) * (sigma_x + sigma_y + C2)
        )

        return ssim_map.mean()

    def get_lr(self) -> dict:
        """Get current learning rates"""
        return {
            "hider_lr"   : self.h_optimizer.param_groups[0]["lr"],
            "detector_lr": self.d_optimizer.param_groups[0]["lr"]
        }