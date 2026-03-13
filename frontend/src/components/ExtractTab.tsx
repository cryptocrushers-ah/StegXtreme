import React, { useState, useRef } from 'react';

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
      const response = await fetch('http://localhost:8000/api/extract', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to extract');
      }

      const data = await response.json();
      setExtractedPayload(data.payload);
      
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
          <p>Drag & drop your stego file here, or click to select.</p>
        )}
      </div>

      <div className="form-group">
        <label>Decryption Password</label>
        <input 
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Secure password..."
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Extracting...' : 'Extract Payload'}
      </button>

      {extractedPayload && (
        <div className="success-message" style={{ marginTop: '2rem' }}>
          <h4>Extracted Payload:</h4>
          <p style={{ wordBreak: 'break-all', marginTop: '0.5rem', fontFamily: 'monospace' }}>
            {extractedPayload}
          </p>
        </div>
      )}
      {error && <div className="error-message">{error}</div>}
    </form>
  );
}
