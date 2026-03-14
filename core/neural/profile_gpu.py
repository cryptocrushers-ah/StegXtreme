import time
import torch
import cupy as cp
import numpy as np
from core.compute.backend import dwt2, ss_embed, to_device, free
from core.neural.hider import HiderNetwork

def profile_operation(name, fn, n=50):
    """Profile an operation and return avg ms"""
    # warmup
    fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    start = time.perf_counter()
    for _ in range(n):
        fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    elapsed = (time.perf_counter() - start) / n * 1000
    print(f"{name:<30} {elapsed:.2f} ms/call")
    return elapsed

def main():
    print("=== GPU Path Profiling ===\n")

    frame   = np.random.rand(256, 256).astype(np.float32)
    bits    = np.random.randint(0, 2, 256).astype(np.int8)
    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = HiderNetwork().eval().to(device)
    cover   = torch.rand(1, 1, 256, 256).to(device)
    payload = torch.rand(1, 1, 256, 256).to(device)

    results = {}

    # profile each operation
    results["dwt2"] = profile_operation(
        "dwt2()",
        lambda: dwt2(frame)
    )
    results["ss_embed"] = profile_operation(
        "ss_embed()",
        lambda: ss_embed(
            dwt2(frame)[0].ravel().copy(),
            bits, n=1, seed=42, strength=18.0
        )
    )
    results["to_device"] = profile_operation(
        "to_device()",
        lambda: to_device(frame)
    )
    results["neural_forward"] = profile_operation(
        "HiderNetwork.forward()",
        lambda: model(cover, payload)
    )
    results["free"] = profile_operation(
        "free()",
        lambda: free()
    )

    # find 3 slowest
    slowest = sorted(
        results.items(), key=lambda x: x[1], reverse=True
    )[:3]
    print("\n=== 3 Slowest Operations ===")
    for name, ms in slowest:
        print(f"  {name}: {ms:.2f} ms")

if __name__ == "__main__":
    main()