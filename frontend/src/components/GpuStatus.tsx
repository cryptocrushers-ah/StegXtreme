/**
 * GpuStatus.tsx
 * Polls /api/gpu-status and shows a live GPU badge in the top-right bar.
 * Green  = GPU detected + CUDA available
 * Amber  = GPU present but CUDA unavailable (CPU fallback)
 * Red    = No GPU / detection failed
 */

import { useState, useEffect } from 'react';
import './GpuStatus.css';
import { apiRequest } from '../utils/api';

interface GpuInfo {
  cupy_available: boolean;
  torch_cuda_available: boolean;
  gpu_name: string | null;
  vram_total_mb: number | null;
  vram_used_mb: number | null;
}

export default function GpuStatus() {
  const [gpu, setGpu]       = useState<GpuInfo | null>(null);
  const [error, setError]   = useState(false);
  const [expanded, setExpanded] = useState(false);

  const poll = async () => {
    try {
      const d: GpuInfo = await apiRequest('/api/system/gpu');
      setGpu(d); setError(false);
    } catch {
      setError(true);
    }
  };

  useEffect(() => { poll(); const id = setInterval(poll, 8000); return () => clearInterval(id); }, []);

  if (error || !gpu) {
    return (
      <div className="gpu-badge gpu-badge--error" title="GPU status unavailable">
        <span className="gpu-dot gpu-dot--red" />
        <span className="gpu-label">GPU <span className="gpu-state">N/A</span></span>
      </div>
    );
  }

  const isAvailable = gpu.torch_cuda_available || gpu.cupy_available;
  const state = isAvailable ? 'ACTIVE' : 'CPU';
  const cls   = isAvailable ? 'gpu-badge--ok' : 'gpu-badge--warn';
  const dot   = isAvailable ? 'gpu-dot--green' : 'gpu-dot--amber';

  return (
    <div className={`gpu-badge ${cls} ${expanded ? 'gpu-badge--expanded' : ''}`}
         onClick={() => setExpanded(x => !x)}
         title="Click for GPU details">
      <span className={`gpu-dot ${dot}`} />
      <span className="gpu-label">
        GPU <span className="gpu-state">{state}</span>
      </span>

      {expanded && (
        <div className="gpu-tooltip">
          <div className="gpu-tooltip-row">
            <span>Device</span>
            <strong>{gpu.gpu_name ?? 'Unknown'}</strong>
          </div>
          {gpu.vram_total_mb != null && (
            <div className="gpu-tooltip-row">
              <span>VRAM</span>
              <strong>{(gpu.vram_total_mb / 1024).toFixed(1)} GB</strong>
            </div>
          )}
          {gpu.torch_cuda_available != null && (
            <div className="gpu-tooltip-row">
              <span>PyTorch</span>
              <strong>{gpu.torch_cuda_available ? 'Ready' : 'Off'}</strong>
            </div>
          )}
          {gpu.cupy_available != null && (
            <div className="gpu-tooltip-row">
              <span>CuPy</span>
              <strong>{gpu.cupy_available ? 'Ready' : 'Off'}</strong>
            </div>
          )}
          {!isAvailable && (
            <div className="gpu-tooltip-note">⚠ Running on CPU</div>
          )}
        </div>
      )}
    </div>
  );
}
