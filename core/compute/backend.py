import numpy as np

def dwt2(arr):
    f  = arr.astype(np.float32)
    L  = (f[:,0::2] + f[:,1::2]) * 0.5
    Hh = (f[:,0::2] - f[:,1::2]) * 0.5
    LL = (L[0::2,:] + L[1::2,:]) * 0.5
    LH = (L[0::2,:] - L[1::2,:]) * 0.5
    HL = (Hh[0::2,:] + Hh[1::2,:]) * 0.5
    HH = (Hh[0::2,:] - Hh[1::2,:]) * 0.5
    return LL, LH, HL, HH

def make_carriers(n, cpb, seed):
    rng = np.random.default_rng(seed)
    raw = rng.integers(0,2,size=n*cpb,dtype=np.uint8)
    return (raw.reshape(n,cpb).astype(np.float32)*2)-1

def ss_embed(region, bits, n, seed, strength):
    cars = make_carriers(n, 256, seed)
    sigs = np.where(bits[:n]==1, strength, -strength).astype(np.float32)
    region[:n*256] += (cars * sigs[:,None]).ravel()

def ss_extract(region, n, seed):
    cars  = make_carriers(n, 256, seed)
    chunk = region[:n*256].reshape(n,256)
    return ((chunk*cars).sum(axis=1)>0).astype(np.int8)

def to_device(arr): return arr   # stub — Dev A replaces with cp.asarray
def to_cpu(arr):    return np.asarray(arr)
def free():         pass         # stub — Dev A replaces with memory pool release
