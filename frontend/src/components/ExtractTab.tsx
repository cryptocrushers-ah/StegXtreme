import React, { useState, useRef } from 'react';
import { apiRequest } from '../utils/api';
import './Embedding.css';

export default function ExtractTab() {
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [extractedPayload, setExtractedPayload] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !password) {
      setError('Please provide the stego file and the password.');
      return;
    }
    setError('');
    setExtractedPayload('');
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('password', password);

    try {
      const data = await apiRequest('/api/extract', {
        method: 'POST',
        body: formData,
      });
      setExtractedPayload(data.payload);
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="extract-container">
      <div className="tab-header">
        <h2>Secure Sequence Extraction</h2>
        <p>Retrieve covert payloads from stego-media using high-entropy decryption keys.</p>
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
          accept="image/png, audio/wav, video/mp4, video/avi"
        />
        {file ? (
          <div className="selected-file-info">
            <span className="file-icon">🕵️</span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB • Stego-Carrier</span>
            </div>
            <button className="change-btn" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Change File</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">📂</div>
            <p>Drop stego-media or <span>click to browse</span></p>
            <span className="hint">Supports encrypted PNG, WAV, MP4 carriers</span>
          </div>
        )}
      </div>

      <div className="extraction-dashboard glass-panel">
        <div className="form-group">
          <label>Extraction Key (Passphrase)</label>
          <input 
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Authorized decryption key..."
          />
        </div>

        <button 
          onClick={handleSubmit} 
          disabled={loading || !file || !password} 
          className={loading ? 'loading' : ''}
          style={{ width: '100%' }}
        >
          {loading ? (
            <>
              <div className="spinner" />
              Reconstructing Sequence...
            </>
          ) : (
            <>
              <span className="icon">🔓</span> Extract & Decrypt Payload
            </>
          )}
        </button>
      </div>

      {extractedPayload && (
        <div className="results-container animate-in">
          <div className="results-header">
            <span className="result-label">Extracted Intelligence</span>
            <button className="copy-btn" onClick={() => navigator.clipboard.writeText(extractedPayload)}>
              Copy to Clipboard
            </button>
          </div>
          <div className="payload-display">
            <pre>{extractedPayload}</pre>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
