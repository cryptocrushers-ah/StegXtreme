
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import torch
from core.neural.hider import HiderNetwork
from core.neural.detector import DetectorNetwork

def export_hider(path="storage/models/hider.onnx"):
    model = HiderNetwork().eval()
    cover  = torch.zeros(1, 1, 64, 64)
    payload = torch.zeros(1, 1, 64, 64)
    torch.onnx.export(
        model, (cover, payload), path,
        input_names=["cover_Y", "payload_bits"],
        output_names=["residual"],
        opset_version=18
    )
    print(f"Hider exported to {path}")

def export_detector(path="storage/models/detector.onnx"):
    model = DetectorNetwork().eval()
    dummy = torch.zeros(1, 1, 64, 64)
    torch.onnx.export(
        model, dummy, path, # type: ignore
        input_names=["frame_Y"],
        output_names=["probability"],
        opset_version=18
        
    )
    print(f"Detector exported to {path}")

if __name__ == "__main__":
    export_hider()
    export_detector()