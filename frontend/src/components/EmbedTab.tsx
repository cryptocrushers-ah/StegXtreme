import React, { useState, useRef } from 'react';
import { apiRequest } from '../utils/api';
import './Embedding.css';

export default function EmbedTab() {
  const [file, setFile] = useState<File | null>(null);
  const [payload, setPayload] = useState('');
  const [password, setPassword] = useState('');
  const [payloadType, setPayloadType] = useState<'text' | 'file'>('text');
  const [payloadFile, setPayloadFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isDraggingPayload, setIsDraggingPayload] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successData, setSuccessData] = useState<{name: string, size: string, url: string} | null>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const payloadInputRef = useRef<HTMLInputElement>(null);

  // Cleanup Object URL to prevent memory leaks
  React.useEffect(() => {
    return () => {
      if (successData?.url) {
        window.URL.revokeObjectURL(successData.url);
      }
    };
  }, [successData?.url]);

  const [algorithm, setAlgorithm] = useState('default');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handlePayloadDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDraggingPayload(true);
    } else if (e.type === 'dragleave') {
      setIsDraggingPayload(false);
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

  const handlePayloadDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingPayload(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setPayloadFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const isFilePayload = payloadType === 'file';
    
    if (!file || (isFilePayload ? !payloadFile : !payload) || !password) {
      setError(`Please provide a carrier file, a ${isFilePayload ? 'secret file' : 'message'}, and a password.`);
      return;
    }
    
    if (file && file.size > 500 * 1024 * 1024) {
      setError('Carrier file size exceeds the 500MB limit.');
      return;
    }

    setError('');
    setSuccessData(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    if (isFilePayload && payloadFile) {
      formData.append('file_payload', payloadFile);
    } else {
      formData.append('text_payload', payload);
    }
    formData.append('password', password);
    formData.append('algorithm', algorithm);

    try {
      const response = await apiRequest('/api/embed', {
        method: 'POST',
        body: formData,
      }, true); // Pass true to get raw response for blob

      if (response instanceof Response) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const extMatch = file.name.match(/\.[0-9a-z]+$/i);
        const ext = extMatch ? extMatch[0] : '';
        const baseName = file.name.replace(ext, '');
        const fileName = `${baseName}_stego${ext}`;

        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        setSuccessData({
          name: fileName,
          size: (blob.size / (1024 * 1024)).toFixed(2) + ' MB',
          url: url
        });
        setFile(null);
        setPayload('');
        setPayloadFile(null);
        setPayloadType('text');
        setPassword('');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="embed-container">
      <div className="tab-header">
        <h2>Secure Data Injection</h2>
        <p>Hide encrypted payloads within carrier media using adversarial neural patterns.</p>
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
              {file.type.startsWith('image/') ? '🖼️' : file.type.startsWith('video/') ? '🎬' : file.type.startsWith('audio/') ? '🔊' : '📁'}
            </span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB • Carrier Material</span>
            </div>
            <button className="change-btn" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Change Carrier</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">📥</div>
            <p>Drop a file here to <span>hide your message</span></p>
            <span className="hint">Supports PNG, WAV, MP4, AVI (Max 500MB)</span>
          </div>
        )}
      </div>

      <div className="injection-dashboard glass-panel">
        <div className="form-group">
          <label>Covert Payload (Target Sequence)</label>
          
          <div className="payload-type-selector">
            <button 
              className={`type-btn ${payloadType === 'text' ? 'active' : ''}`}
              onClick={() => setPayloadType('text')}
            >
              Text Message
            </button>
            <button 
              className={`type-btn ${payloadType === 'file' ? 'active' : ''}`}
              onClick={() => setPayloadType('file')}
            >
              File Payload
            </button>
          </div>

          {payloadType === 'text' ? (
            <textarea 
              rows={4}
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              placeholder="Enter the secret message to be serialized into the carrier..."
            />
          ) : (
            <div 
              className={`payload-file-drop ${isDraggingPayload ? 'drag-over' : ''}`}
              onDragEnter={handlePayloadDrag}
              onDragLeave={handlePayloadDrag}
              onDragOver={handlePayloadDrag}
              onDrop={handlePayloadDrop}
              onClick={() => payloadInputRef.current?.click()}
            >
              <input 
                type="file"
                ref={payloadInputRef}
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files?.[0]) setPayloadFile(e.target.files[0]);
                }}
              />
              {payloadFile ? (
                <div className="payload-selected-info">
                  <span className="icon">📄</span>
                  <div className="details">
                    <span className="name">{payloadFile.name}</span>
                    <span className="size">{(payloadFile.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <button className="change-btn" onClick={(e) => { e.stopPropagation(); setPayloadFile(null); }}>Change</button>
                </div>
              ) : (
                <div className="payload-prompt">
                  <span className="icon">📁</span>
                  <p>Click or drop <span>secret file</span> here</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="dashboard-row">
          <div className="form-group">
            <label>Encryption Key</label>
            <input 
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Secure cryptographic key..."
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
          disabled={loading || !file || !password || (payloadType === 'text' ? !payload : !payloadFile)} 
          className={loading ? 'loading' : ''}
          style={{ width: '100%' }}
        >
          {loading ? (
            <>
              <div className="spinner" />
              Serializing Payload...
            </>
          ) : (
            <>
              <span className="icon">🔒</span> Embed & Generate Stego-Media
            </>
          )}
        </button>
      </div>

      {successData && (
        <div className="success-area animate-in">
          <div className="success-icon">✅</div>
          <div className="success-info">
            <strong>Stego-Media Generated</strong>
            <span>{successData.name} • {successData.size}</span>
          </div>
          <button className="download-feedback-btn" onClick={() => {
            if (successData.url) {
              const a = document.createElement('a');
              a.style.display = 'none';
              a.href = successData.url;
              a.download = successData.name;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }
          }}>
            Download Ready
          </button>
        </div>
      )}
      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
