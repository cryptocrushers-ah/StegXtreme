import { useState, useRef } from 'react';
import { apiRequest } from '../utils/api';
import './VisualiseTab.css';

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
    <div className="visualise-container">
      <div className="tab-header">
        <h2>Visual Intelligence</h2>
        <p>Expose hidden forensic signatures through advanced signal processing.</p>
      </div>

      <div
        className={`file-drop-area ${isDragging ? 'drag-over' : ''} ${file ? 'has-file' : ''}`}
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
          <div className="selected-file-info">
            <span className="file-icon">{file.type.startsWith('video/') ? '🎬' : '🖼️'}</span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || 'Unknown Type'}</span>
            </div>
            <button className="change-btn" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Change</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">🎞️</div>
            <p>Drop media or <span>click to select</span></p>
            <span className="hint">Images & Videos supported</span>
          </div>
        )}
      </div>

      <div className="mode-selection">
        <h3> forensic Mode </h3>
        <div className="mode-cards">
          <div 
            className={`mode-card ${mode === 'timeline' ? 'active' : ''}`}
            onClick={() => setMode('timeline')}
          >
            <span className="mode-icon">📈</span>
            <div className="mode-info">
              <strong>Noise Timeline</strong>
              <span>Temporal LSB variance in video</span>
            </div>
          </div>
          <div 
            className={`mode-card ${mode === 'bitplane' ? 'active' : ''}`}
            onClick={() => setMode('bitplane')}
          >
            <span className="mode-icon">🧱</span>
            <div className="mode-info">
              <strong>Bit-Plane Slicing</strong>
              <span>Isolate LSB to MSB layers</span>
            </div>
          </div>
          <div 
            className={`mode-card ${mode === 'heatmap' ? 'active' : ''}`}
            onClick={() => setMode('heatmap')}
          >
            <span className="mode-icon">🔥</span>
            <div className="mode-info">
              <strong>Wavelet Heatmap</strong>
              <span>High-frequency residue map</span>
            </div>
          </div>
        </div>
      </div>

      {mode === 'timeline' && (
        <div className="config-panel animate-in">
          <div className="config-header">
            <label>Analysis Depth</label>
            <span className="config-value">{nFrames} Frames</span>
          </div>
          <input
            type="range"
            min="10"
            max="120"
            step="10"
            value={nFrames}
            onChange={(e) => setNFrames(Number(e.target.value))}
            className="premium-slider"
          />
        </div>
      )}

      <button 
        onClick={handleSubmit} 
        disabled={loading || !file} 
        className={loading ? 'loading' : ''}
      >
        {loading ? (
          <>
            <div className="spinner" />
            Generating Intelligence...
          </>
        ) : (
          <>
            <span className="icon">🛡️</span> Run forensic Visualization
          </>
        )}
      </button>

      {error && <div className="error-message">{error}</div>}

      {imageSrc && (
        <div className="visualise-result animate-in">
          <div className="result-header">
            <span className="result-label">Forensic Output ({mode})</span>
            <button className="export-btn" onClick={() => {
              const link = document.createElement('a');
              link.href = imageSrc;
              link.download = `forensic_${mode}_${Date.now()}.png`;
              link.click();
            }}>
              Save Image
            </button>
          </div>
          <div className="image-frame">
            <img src={imageSrc} alt="Forensic Visualization" />
          </div>
        </div>
      )}
    </div>
  );
}
