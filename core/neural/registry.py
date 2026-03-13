import torch
from core.neural.hider import HiderNetwork
from core.neural.detector import DetectorNetwork

class ModelRegistry:
    def save(self, model, path: str):
        torch.save(model.state_dict(), path)
        print(f"Saved to {path}")

    def load(self, model, path: str):
        model.load_state_dict(
            torch.load(path, map_location="cpu")
        )
        model.eval()
        return model