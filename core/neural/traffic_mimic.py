import torch
import torch.nn as nn
import numpy as np

class TrafficMimicModel(nn.Module):
    """
    Input:  last 10 inter-packet delays as floats
    Output: next delay shaped like residential DNS traffic
    """
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(10, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()  # output between 0 and 1
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x      : (B, 10) float tensor of recent delays
        returns: (B, 1)  next delay scaled to 0.05-2.0s
        """
        raw = self.network(x)
        # scale sigmoid output to realistic delay range
        return raw * 1.95 + 0.05  # maps [0,1] → [0.05, 2.0]


class TrafficMimic:
    """
    Wrapper that trains and uses TrafficMimicModel.
    Generates realistic inter-packet delays.
    """
    def __init__(self):
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model     = TrafficMimicModel().to(self.device)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=1e-3
        )
        self.trained = False

    def train_on_synthetic(self, n_samples=1000):
        """
        Train on synthetic residential DNS timing data.
        Real DNS traffic has delays between 0.05s and 2.0s
        with a log-normal distribution.
        """
        self.model.train()
        for _ in range(100):  # 100 training steps
            # generate synthetic delay sequences
            delays = np.random.lognormal(
                mean=-1.5, sigma=0.8, size=(n_samples, 11)
            ).clip(0.05, 2.0).astype(np.float32)

            X = torch.tensor(delays[:, :10]).to(self.device)
            y = torch.tensor(delays[:, 10:]).to(self.device)

            self.optimizer.zero_grad()
            pred = self.model(X)
            loss = nn.functional.mse_loss(pred, y)
            loss.backward()
            self.optimizer.step()

        self.trained = True
        print(f"TrafficMimic trained, final loss: {loss.item():.6f}")

    def next_delay(self, recent_delays: list) -> float:
        """
        Given last 10 delays, predict next delay.
        Falls back to 0.1s if not trained yet.
        """
        if not self.trained:
            return 0.1  # safe fallback

        self.model.eval()
        x = torch.tensor(
            [recent_delays[-10:]], dtype=torch.float32
        ).to(self.device)

        with torch.no_grad():
            delay = self.model(x).item()

        return float(np.clip(delay, 0.05, 2.0))

    def export_onnx(self, path="storage/models/traffic_mimic.onnx"):
        """Export trained model to ONNX for Dev B to use"""
        self.model.eval()
        dummy = torch.zeros(1, 10).to(self.device)
        torch.onnx.export(
            self.model, dummy, path, # type: ignore
            input_names=["recent_delays"],
            output_names=["next_delay"],
            opset_version=18
        )
        print(f"TrafficMimic exported to {path}")