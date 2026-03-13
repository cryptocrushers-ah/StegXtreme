import React, { useState, useRef } from 'react';

export default function EmbedTab() {
  const [file, setFile] = useState<File | null>(null);
  const [payload, setPayload] = useState('');
  const [password, setPassword] = useState('');
  const [algorithm, setAlgorithm] = useState('default');
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
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
    if (!file || !payload || !password) {
      setError('Please provide file, payload, and password.');
      return;
    }
    setError('');
    setSuccess(false);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('text_payload', payload);
    formData.append('password', password);
    formData.append('algorithm', algorithm);

    try {
      const response = await fetch('http://localhost:8000/api/embed', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to embed');
      }

      // Download the stego file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      // create safe filename
      const extMatch = file.name.match(/\.[0-9a-z]+$/i);
      const ext = extMatch ? extMatch[0] : '';
      const baseName = file.name.replace(ext, '');
      a.download = `${baseName}_stego${ext}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      setSuccess(true);
      // Reset form on success
      setFile(null);
      setPayload('');
      setPassword('');
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
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
            if (e.target.files && e.target.files[0]) {
              setFile(e.target.files[0]);
            }
          }}
          accept="image/png, audio/wav, video/mp4, video/avi"
        />
        {file ? (
          <p style={{ color: '#38bdf8', fontWeight: 600 }}>File selected: {file.name}</p>
        ) : (
          <p>Drag & drop your cover file here (PNG, WAV, MP4), or click to select.</p>
        )}
      </div>

      <div className="form-group">
        <label>Secret Payload (Text)</label>
        <textarea 
          rows={4}
          value={payload}
          onChange={(e) => setPayload(e.target.value)}
          placeholder="Enter the secret message to hide..."
        />
      </div>

      <div className="form-group">
        <label>Encryption Password</label>
        <input 
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Secure password..."
        />
      </div>

      <div className="form-group">
        <label>Algorithm</label>
        <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
          <option value="default">Default Auto-Detect (DCT/LSB)</option>
        </select>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Embed Payload & Download'}
      </button>

      {success && <div className="success-message">Successfully embedded and downloaded!</div>}
      {error && <div className="error-message">{error}</div>}
    </form>
  );
}
