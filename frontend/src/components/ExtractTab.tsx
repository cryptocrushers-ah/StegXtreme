import React, { useState, useRef } from 'react';
import { apiRequest } from '../utils/api';
import './Embedding.css';

type MediaKind = 'image' | 'audio' | 'video';

const ALGO_MAP: Record<MediaKind, { value: string; label: string }[]> = {
  image: [
    { value: 'dct', label: 'DCT — Robust (recommended)' },
    { value: 'lsb', label: 'LSB — Lossless' },
  ],
  audio: [
    { value: 'lsb', label: 'LSB — WAV' },
  ],
  video: [
    { value: 'dwt_ss', label: 'DWT Spread-Spectrum (recommended)' },
    { value: 'lsb',    label: 'LSB — Legacy' },
  ],
};

// Also accept .avi on extract (video output from embed is always .avi)
const ACCEPT_ALL = 'image/png,image/jpeg,image/bmp,.png,.jpg,.jpeg,.bmp,audio/wav,audio/x-wav,.wav,video/mp4,video/x-msvideo,video/x-matroska,.mp4,.avi,.mkv,.mov';

function detectKind(file: File): MediaKind | null {
  const t = file.type.toLowerCase();
  const ext = (file.name.split('.').pop() ?? '').toLowerCase();
  if (t.startsWith('image/') || ['png','jpg','jpeg','bmp'].includes(ext)) return 'image';
  if (t.startsWith('audio/') || ext === 'wav') return 'audio';
  if (t.startsWith('video/') || ['mp4','avi','mkv','mov'].includes(ext)) return 'video';
  return null;
}

const KIND_LABELS: Record<MediaKind, string> = {
  image: '🖼️ Image',
  audio: '🔊 Audio',
  video: '🎬 Video',
};

export default function ExtractTab() {
  const [file,            setFile]            = useState<File | null>(null);
  const [mediaKind,       setMediaKind]       = useState<MediaKind | null>(null);
  const [algorithm,       setAlgorithm]       = useState<string>('');
  const [password,        setPassword]        = useState('');
  const [isDragging,      setIsDragging]      = useState(false);
  const [loading,         setLoading]         = useState(false);
  const [extractedPayload,setExtractedPayload]= useState<string | null>(null);
  const [isBinary,        setIsBinary]        = useState(false);
  const [base64Payload,   setBase64Payload]   = useState<string | null>(null);
  const [error,           setError]           = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const applyFile = (f: File) => {
    const kind = detectKind(f);
    if (!kind) { setError('Unsupported file type. Use PNG/JPEG/BMP, WAV, or MP4/AVI/MKV.'); return; }
    setFile(f); setMediaKind(kind);
    setAlgorithm(ALGO_MAP[kind][0].value);   // auto-set recommended default
    setExtractedPayload(null); setError('');
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFile(null); setMediaKind(null); setAlgorithm('');
    setExtractedPayload(null); setBase64Payload(null); setError('');
  };

  const onDrag = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(e.type !== 'dragleave' && e.type !== 'drop'); };
  const onDrop = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); const f = e.dataTransfer.files?.[0]; if (f) applyFile(f); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !mediaKind)  { setError('Select a stego file.'); return; }
    if (!algorithm)           { setError('Algorithm not set — re-select the file.'); return; }
    if (!password)            { setError('Enter the decryption password.'); return; }

    setError(''); setExtractedPayload(null); setBase64Payload(null); setLoading(true);

    const fd = new FormData();
    fd.append('file', file);
    fd.append('password', password);
    fd.append('algorithm', algorithm);

    try {
      const data = await apiRequest('/api/extract', { method: 'POST', body: fd });
      setExtractedPayload(data.payload);
      setIsBinary(data.is_binary);
      setBase64Payload(data.base64);
    } catch (err: any) {
      setError(err.message ?? 'Extraction failed.');
    } finally {
      setLoading(false);
    }
  };

  const downloadPayload = () => {
    if (!base64Payload) return;
    const raw = atob(base64Payload);
    const hex = Array.from(raw.substring(0, 4)).map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join('').toLowerCase();
    let ext = '.bin';
    if (hex.startsWith('89504e47')) ext = '.png';
    else if (hex.startsWith('ffd8ff'))   ext = '.jpg';
    else if (hex.startsWith('47494638')) ext = '.gif';
    else if (hex.startsWith('25504446')) ext = '.pdf';
    else if (hex.startsWith('52494646') && raw.includes('WAVE')) ext = '.wav';
    else { try { if (!raw.split('').some(c => c.charCodeAt(0) > 127)) ext = '.txt'; } catch {} }

    const bytes = new Uint8Array(Array.from(raw).map(c => c.charCodeAt(0)));
    const url   = URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' }));
    const a     = Object.assign(document.createElement('a'), { href: url, download: `extracted_${Date.now()}${ext}`, style: 'display:none' });
    document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const algoOptions = mediaKind ? ALGO_MAP[mediaKind] : [];
  const canSubmit   = !loading && !!file && !!algorithm && !!password;

  return (
    <div className="extract-container">
      <div className="tab-header">
        <h2>Secure Sequence Extraction</h2>
        <p>Retrieve covert payloads from stego-media using the correct algorithm and password.</p>
      </div>

      {/* ── Drop zone ──────────────────────────────────────────────── */}
      <div
        className={`file-drop-area${isDragging ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
        onDragEnter={onDrag} onDragLeave={onDrag} onDragOver={onDrag} onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" style={{ display: 'none' }} accept={ACCEPT_ALL}
          onChange={e => { const f = e.target.files?.[0]; if (f) applyFile(f); e.target.value = ''; }} />

        {file ? (
          <div className="selected-file-info">
            <span className="file-icon">{mediaKind ? KIND_LABELS[mediaKind].split(' ')[0] : '🕵️'}</span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB &bull; {mediaKind ? KIND_LABELS[mediaKind] : ''} stego-carrier</span>
            </div>
            <button className="change-btn" onClick={clearFile}>Change File</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">📂</div>
            <p>Upload a stego file to <span>reveal hidden content</span></p>
            <span className="hint">
              🖼️ PNG / JPEG / BMP &nbsp;|&nbsp; 🔊 WAV &nbsp;|&nbsp; 🎬 MP4 / AVI / MKV
            </span>
          </div>
        )}
      </div>

      {/* ── Context bar ───────────────────────────────────────────── */}
      {mediaKind && (
        <div className="algo-context-bar">
          <span className="algo-context-label">{KIND_LABELS[mediaKind]} stego-carrier detected</span>
          <span className="algo-context-hint">
            Use the <strong>same algorithm</strong> that was used during embedding
          </span>
        </div>
      )}

      <div className="extraction-dashboard glass-panel">
        <div className="dashboard-row">
          <div className="form-group">
            <label>Extraction Key (Passphrase)</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Authorized decryption key..." />
          </div>

          <div className="form-group">
            <label>Steganography Algorithm</label>
            {algoOptions.length > 0 ? (
              <select value={algorithm} onChange={e => setAlgorithm(e.target.value)}>
                {algoOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            ) : (
              <select disabled style={{ opacity: 0.4 }}>
                <option>— Select a stego file first —</option>
              </select>
            )}
          </div>
        </div>

        <button onClick={handleSubmit} disabled={!canSubmit}
          className={loading ? 'loading' : ''} style={{ width: '100%' }}>
          {loading
            ? <><div className="spinner" /> Reconstructing Sequence...</>
            : <><span className="icon">🔓</span> Extract &amp; Decrypt Payload</>}
        </button>
      </div>

      {/* ── Results ───────────────────────────────────────────────── */}
      {extractedPayload && (
        <div className="results-container animate-in">
          <div className="results-header">
            <span className="result-label">Extracted Intelligence</span>
            {isBinary && base64Payload && (
              <span className="format-tag">
                {(() => {
                  const magic = atob(base64Payload).substring(0, 4);
                  const hex   = Array.from(magic).map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join('').toLowerCase();
                  if (hex.startsWith('89504e47')) return 'PNG Image';
                  if (hex.startsWith('ffd8ff'))   return 'JPEG Image';
                  if (hex.startsWith('47494638')) return 'GIF Image';
                  if (hex.startsWith('25504446')) return 'PDF Document';
                  if (hex.startsWith('52494646')) return 'RIFF (WAV/AVI)';
                  return 'Binary Data';
                })()}
              </span>
            )}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {!isBinary && (
                <button className="copy-btn" onClick={() => navigator.clipboard.writeText(extractedPayload ?? '')}>
                  Copy Text
                </button>
              )}
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
                ⚠️ Binary payload — use "Download Data" to save the original file.
              </span>
            )}
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
