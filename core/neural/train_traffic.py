import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(__file__)
)))

from core.neural.traffic_mimic import TrafficMimic

if __name__ == "__main__":
    print("Training TrafficMimic on synthetic data...")
    mimic = TrafficMimic()
    mimic.train_on_synthetic(n_samples=1000)
    mimic.export_onnx()
    print("Done!")