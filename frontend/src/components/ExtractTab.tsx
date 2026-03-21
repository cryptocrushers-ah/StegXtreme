import React, { useState, useRef } from 'react';
import { apiRequest } from '../utils/api';
import './Embedding.css';

export default function ExtractTab() {
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState('');
  const [algorithm, setAlgorithm] = useState('default');
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [extractedPayload, setExtractedPayload] = useState<string | null>(null);
  const [isBinary, setIsBinary] = useState(false);
  const [base64Payload, setBase64Payload] = useState<string | null>(null);
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
      setError('Please provide both stego file and password.');
      return;
    }
    if (file && file.size > 500 * 1024 * 1024) {
      setError('File size exceeds the 500MB limit.');
      return;
    }
    setError('');
    setExtractedPayload(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('password', password);
    formData.append('algorithm', algorithm);

    try {
      const data = await apiRequest('/api/extract', {
        method: 'POST',
        body: formData,
      });
      setExtractedPayload(data.payload);
      setIsBinary(data.is_binary);
      setBase64Payload(data.base64);
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadPayload = () => {
    if (!base64Payload) return;
    const byteCharacters = atob(base64Payload);
    
    // Detect extension from magic bytes
    let extension = '';
    const hex = Array.from(byteCharacters.substring(0, 4))
      .map(char => char.charCodeAt(0).toString(16).padStart(2, '0'))
      .join('').toLowerCase();

    if (hex.startsWith('89504e47')) extension = '.png';
    else if (hex.startsWith('ffd8ff')) extension = '.jpg';
    else if (hex.startsWith('47494638')) extension = '.gif';
    else if (hex.startsWith('25504446')) extension = '.pdf';
    else if (hex.startsWith('52494646')) { // WAV or AVI
        if (byteCharacters.includes('WAVE')) extension = '.wav';
        else if (byteCharacters.includes('AVI ')) extension = '.avi';
    }
    else if (hex.startsWith('000000') || hex.startsWith('66747970')) extension = '.mp4';

    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extracted_payload_${Date.now()}${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
            <span className="file-icon">
              {file.type.startsWith('image/') ? '🖼️' : file.type.startsWith('video/') ? '🎬' : file.type.startsWith('audio/') ? '🔊' : '🕵️'}
            </span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB • Stego-Carrier</span>
            </div>
            <button className="change-btn" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Change File</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">📂</div>
            <p>Upload a stego file to <span>reveal hidden content</span></p>
            <span className="hint">Supports encrypted PNG, WAV, MP4 carriers</span>
          </div>
        )}
      </div>

      <div className="extraction-dashboard glass-panel">
        <div className="dashboard-row">
          <div className="form-group">
            <label>Extraction Key (Passphrase)</label>
            <input 
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Authorized decryption key..."
            />
          </div>

          <div className="form-group">
            <label>Neural Algorithm</label>
            <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
              <option value="default">Auto-Select (Optimized)</option>
              <option value="lsb">LSB Slicing (Legacy)</option>
              <option value="dct">DCT Transform (Robust)</option>
            </select>
          </div>
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
            {isBinary && base64Payload && (
              <span className="format-tag">
                {(() => {
                  const magic = atob(base64Payload).substring(0, 4);
                  const hex = Array.from(magic).map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join('').toLowerCase();
                  if (hex.startsWith('89504e47')) return 'PNG Image';
                  if (hex.startsWith('ffd8ff')) return 'JPEG Image';
                  if (hex.startsWith('47494638')) return 'GIF Image';
                  if (hex.startsWith('25504446')) return 'PDF Document';
                  if (hex.startsWith('52494646')) return 'RIFF (WAV/AVI)';
                  return 'Binary Data';
                })()}
              </span>
            )}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="copy-btn" onClick={() => navigator.clipboard.writeText(extractedPayload)}>
                Copy Text
              </button>
              {base64Payload && (
                <button className="download-feedback-btn" onClick={downloadPayload}>
                  Download Data
                </button>
              )}
            </div>
          </div>
          <div className="payload-display">
            <pre>{extractedPayload}</pre>
            {isBinary && (
              <span className="binary-warning">
                ⚠️ This payload appears to be binary data. Use "Download Data" to retrieve the original file.
              </span>
            )}
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
