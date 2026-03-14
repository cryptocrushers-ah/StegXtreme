import time
import torch
import numpy as np
from core.compute.backend import dwt2, ss_embed
from core.neural.hider import HiderNetwork

def benchmark_ss_embed(n_frames=100):
    """Measure ms per frame for SS embed"""
    frame = np.random.rand(256, 256).astype(np.float32)
    bits  = np.random.randint(0, 2, 256).astype(np.int8)

    start = time.perf_counter()
    for _ in range(n_frames):
        LL, LH, HL, HH = dwt2(frame)
        region = LL.ravel().copy()
        ss_embed(region, bits, n=1, seed=42, strength=18.0)
    elapsed = (time.perf_counter() - start) / n_frames * 1000

    print(f"SS embed:     {elapsed:.2f} ms/frame")
    return elapsed

def benchmark_neural_embed(n_frames=100):
    """Measure ms per frame for neural embed"""
    model   = HiderNetwork().eval()
    cover   = torch.rand(1, 1, 256, 256)
    payload = torch.rand(1, 1, 256, 256)

    # warmup
    with torch.no_grad():
        model(cover, payload)

    start = time.perf_counter()
    for _ in range(n_frames):
        with torch.no_grad():
            model(cover, payload)
    elapsed = (time.perf_counter() - start) / n_frames * 1000

    print(f"Neural embed: {elapsed:.2f} ms/frame")
    return elapsed

def benchmark_neural_embed_gpu(n_frames=100):
    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model   = HiderNetwork().eval().to(device)
    cover   = torch.rand(1, 1, 256, 256).to(device)
    payload = torch.rand(1, 1, 256, 256).to(device)

    # warmup
    with torch.no_grad():
        model(cover, payload)
    torch.cuda.synchronize()

    start = time.perf_counter()
    for _ in range(n_frames):
        with torch.no_grad():
            model(cover, payload)
    torch.cuda.synchronize()  # wait for GPU to finish
    elapsed = (time.perf_counter() - start) / n_frames * 1000

    print(f"Neural GPU:   {elapsed:.2f} ms/frame")
    return elapsed


if __name__ == "__main__":
    print("Benchmarking 100 frames each...\n")
    ss_ms        = benchmark_ss_embed()
    neural_ms    = benchmark_neural_embed()
    neural_gpu_ms = benchmark_neural_embed_gpu()
    
    print(f"Neural CPU is {neural_ms/ss_ms:.1f}x slower than SS embed")
    print(f"Neural GPU is {ss_ms/neural_gpu_ms:.1f}x FASTER than SS embed")
