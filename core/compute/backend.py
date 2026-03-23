import numpy as np
try:
    import cupy as cp
    GPU_ENABLED = True
    try:
        COMPUTE_DEVICE = cp.cuda.runtime.getDeviceProperties(0)['name'].decode()
    except Exception:
        COMPUTE_DEVICE = "GPU (CuPy Acceleration)"
except Exception:
    cp = np  # CuPy is not available, will use NumPy instead
    GPU_ENABLED = False
    COMPUTE_DEVICE = "CPU"

def dwt2(arr):
    f = cp.asarray(arr).astype(cp.float32)   # entry: to GPU
    L  = (f[:,0::2] + f[:,1::2]) * 0.5
    Hh = (f[:,0::2] - f[:,1::2]) * 0.5
    LL = (L[0::2,:] + L[1::2,:]) * 0.5
    LH = (L[0::2,:] - L[1::2,:]) * 0.5
    HL = (Hh[0::2,:] + Hh[1::2,:]) * 0.5
    HH = (Hh[0::2,:] - Hh[1::2,:]) * 0.5
    return to_cpu(LL), to_cpu(LH), to_cpu(HL), to_cpu(HH)  # exit: to CPU

def make_carriers(n, cpb, seed):
    cp.random.seed(seed)
    raw = cp.random.randint(0, 2, size=n*cpb, dtype=cp.uint8)
    return to_cpu(raw.reshape(n, cpb).astype(cp.float32) * 2 - 1)


def ss_embed(region, bits, n, seed, strength):
    cars = make_carriers(n, 256, seed)
    sigs = np.where(bits[:n]==1, strength, -strength).astype(np.float32)
    region[:n*256] += (cars * sigs[:,None]).ravel()

def ss_extract(region, n, seed):
    cars  = make_carriers(n, 256, seed)
    chunk = region[:n*256].reshape(n,256)
    return ((chunk*cars).sum(axis=1)>0).astype(np.int8)

def to_device(arr): 
    return cp.asarray(arr)             # stub — Dev A replaces with cp.asarray
def to_cpu(arr):    
    if hasattr(arr, 'get'):
        return arr.get()
    return np.asarray(arr)               # stub — Dev A replaces with arr.get()
def free():         
    if GPU_ENABLED:
        cp.get_default_memory_pool().free_all_blocks()
