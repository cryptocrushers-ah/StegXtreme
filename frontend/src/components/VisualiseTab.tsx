import React, { useState, useRef } from 'react';
import { apiRequest } from '../utils/api';

type VisMode = 'timeline' | 'bitplane' | 'heatmap';

export default function VisualiseTab() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [mode, setMode] = useState<VisMode>('timeline');
  const [nFrames, setNFrames] = useState(30);
  
  const [loading, setLoading] = useState(false);
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [error, setError] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setIsDragging(true);
    else if (e.type === 'dragleave') setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a media file to visualise.');
      return;
    }
    
    // Basic pre-flight checking
    if (mode === 'timeline' && !file.type.startsWith('video/')) {
      setError('Timeline mode requires a video file.');
      return;
    }
    if ((mode === 'bitplane' || mode === 'heatmap') && !file.type.startsWith('image/')) {
      setError(`${mode} mode requires an image file.`);
      return;
    }

    setError('');
    setImageSrc(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    if (mode === 'timeline') {
      formData.append('n_frames', nFrames.toString());
    }

    try {
      const data = await apiRequest(`/api/visualise/${mode}`, {
        method: 'POST',
        body: formData,
      });
      setImageSrc(data.image_base64);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Drop zone */}
      <div
        className={`file-drop-area ${isDragging ? 'drag-over' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files?.[0]) setFile(e.target.files[0]);
          }}
          accept="image/*,video/*"
        />
        {file ? (
          <p style={{ color: '#38bdf8', fontWeight: 600 }}>
            Selected: {file.name}
          </p>
        ) : (
          <>
            <p>Drag &amp; drop an image or video file, or click to select.</p>
          </>
        )}
      </div>

      {/* Mode Selection */}
      <div style={{ marginTop: '1.5rem' }}>
        <p style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem', color: '#94a3b8' }}>Visualisation Mode</p>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input 
              type="radio" 
              name="mode" 
              value="timeline" 
              checked={mode === 'timeline'} 
              onChange={() => setMode('timeline')} 
            />
            Video Noise Timeline
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input 
              type="radio" 
              name="mode" 
              value="bitplane" 
              checked={mode === 'bitplane'} 
              onChange={() => setMode('bitplane')} 
            />
            Image Bit-Planes
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input 
              type="radio" 
              name="mode" 
              value="heatmap" 
              checked={mode === 'heatmap'} 
              onChange={() => setMode('heatmap')} 
            />
            Wavelet Heatmap
          </label>
        </div>
      </div>

      {/* Slider for Timeline Mode */}
      {mode === 'timeline' && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <label htmlFor="frames-slider" style={{ fontSize: '0.9rem', color: '#cbd5e1' }}>Frames to analyze</label>
            <span style={{ fontWeight: 600, color: '#38bdf8' }}>{nFrames}</span>
          </div>
          <input
            id="frames-slider"
            type="range"
            min="10"
            max="120"
            step="5"
            value={nFrames}
            onChange={(e) => setNFrames(Number(e.target.value))}
            style={{ width: '100%', cursor: 'pointer' }}
          />
        </div>
      )}

      <button type="submit" disabled={loading} style={{ marginTop: '1.5rem', position: 'relative' }}>
        {loading ? (
          <div className="button-loading">
            <div className="spinner"></div>
            <span>Generating Plot...</span>
          </div>
        ) : '🎨 Generate Visualisation'}
      </button>

      {error && <div className="error-message" style={{ marginTop: '1rem' }}>{error}</div>}

      {/* Result Display */}
      {imageSrc && (
        <div style={{ marginTop: '2rem', textAlign: 'center' }}>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Visualisation Result
          </p>
          <div style={{ 
            background: 'rgba(0,0,0,0.4)', 
            padding: '1rem', 
            borderRadius: '12px',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            <img 
              src={imageSrc} 
              alt="Visualisation Plot" 
              style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }} 
            />
          </div>
        </div>
      )}
    </form>
  );
}
