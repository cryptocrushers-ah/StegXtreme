import React, { useState, useRef, useEffect } from 'react';
import { apiRequest } from '../utils/api';
import './Embedding.css';

// ── Algorithm registry — mirrors backend router.py exactly ───────────
type MediaKind = 'image' | 'audio' | 'video';

const ALGO_MAP: Record<MediaKind, { value: string; label: string }[]> = {
  image: [
    { value: 'dct', label: 'DCT — Robust, JPEG-resistant (recommended)' },
    { value: 'lsb', label: 'LSB — Lossless, high capacity' },
  ],
  audio: [
    { value: 'lsb', label: 'LSB — WAV PCM (only supported format)' },
  ],
  video: [
    { value: 'dwt_ss', label: 'DWT Spread-Spectrum — Wavelet domain (recommended)' },
    { value: 'lsb',    label: 'LSB — Fast, lossless codec required' },
  ],
};

// Strict accept strings — user cannot pick wrong file types
const CARRIER_ACCEPT = 'image/png,image/jpeg,image/bmp,.png,.jpg,.jpeg,.bmp,audio/wav,audio/x-wav,.wav,video/mp4,video/x-msvideo,video/x-matroska,.mp4,.avi,.mkv,.mov';

const PAYLOAD_ACCEPT: Record<MediaKind, string> = {
  image: 'image/png,image/jpeg,image/gif,application/pdf,text/plain,.png,.jpg,.gif,.pdf,.txt',
  audio: 'text/plain,.txt',
  video: 'image/png,image/jpeg,text/plain,application/pdf,.png,.jpg,.pdf,.txt',
};

const KIND_LABELS: Record<MediaKind, string> = {
  image: '🖼️ Image',
  audio: '🔊 Audio',
  video: '🎬 Video',
};

const KIND_HINT: Record<MediaKind, string> = {
  image: 'Algorithms: DCT · LSB',
  audio: 'Algorithm: LSB  |  WAV files only',
  video: 'Algorithms: DWT Spread-Spectrum · LSB',
};

function detectKind(file: File): MediaKind | null {
  const t = file.type.toLowerCase();
  const ext = (file.name.split('.').pop() ?? '').toLowerCase();
  if (t.startsWith('image/') || ['png','jpg','jpeg','bmp'].includes(ext)) return 'image';
  if (t.startsWith('audio/') || ext === 'wav') return 'audio';
  if (t.startsWith('video/') || ['mp4','avi','mkv','mov'].includes(ext)) return 'video';
  return null;
}

export default function EmbedTab() {
  const [file,           setFile]           = useState<File | null>(null);
  const [mediaKind,      setMediaKind]      = useState<MediaKind | null>(null);
  const [algorithm,      setAlgorithm]      = useState<string>('');
  const [payloadType,    setPayloadType]    = useState<'text' | 'file'>('text');
  const [payload,        setPayload]        = useState('');
  const [payloadFile,    setPayloadFile]    = useState<File | null>(null);
  const [password,       setPassword]       = useState('');
  const [isDragging,     setIsDragging]     = useState(false);
  const [isDraggingPay,  setIsDraggingPay]  = useState(false);
  const [loading,        setLoading]        = useState(false);
  const [successData,    setSuccessData]    = useState<{ name: string; size: string; url: string } | null>(null);
  const [error,          setError]          = useState('');

  const fileRef    = useRef<HTMLInputElement>(null);
  const payloadRef = useRef<HTMLInputElement>(null);

  useEffect(() => () => { if (successData?.url) URL.revokeObjectURL(successData.url); }, [successData?.url]);

  // When carrier changes → auto-set algorithm to first recommended option
  const applyCarrier = (f: File) => {
    const kind = detectKind(f);
    if (!kind) { setError('Unsupported file type. Use PNG/JPEG/BMP, WAV, or MP4/AVI/MKV.'); return; }
    setFile(f);
    setMediaKind(kind);
    setAlgorithm(ALGO_MAP[kind][0].value);   // always set a valid default
    setPayloadFile(null);
    setPayload('');
    setError('');
  };

  const clearCarrier = (e: React.MouseEvent) => {
    e.stopPropagation();
    setFile(null); setMediaKind(null); setAlgorithm('');
    setPayloadFile(null); setPayload(''); setError('');
  };

  // Drag helpers
  const onDrag = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(e.type !== 'dragleave' && e.type !== 'drop'); };
  const onDrop = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); const f = e.dataTransfer.files?.[0]; if (f) applyCarrier(f); };
  const onPayDrag = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDraggingPay(e.type !== 'dragleave' && e.type !== 'drop'); };
  const onPayDrop = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDraggingPay(false); const f = e.dataTransfer.files?.[0]; if (f) setPayloadFile(f); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file || !mediaKind)          { setError('Select a carrier file first.'); return; }
    if (!algorithm)                   { setError('Algorithm not resolved — re-select the carrier file.'); return; }
    if (!password)                    { setError('Enter an encryption password.'); return; }
    if (payloadType === 'text'  && !payload.trim())  { setError('Enter a secret message.'); return; }
    if (payloadType === 'file'  && !payloadFile)     { setError('Select a payload file.'); return; }

    setError(''); setSuccessData(null); setLoading(true);

    const fd = new FormData();
    fd.append('file', file);
    fd.append('password', password);
    fd.append('algorithm', algorithm);
    if (payloadType === 'file' && payloadFile) fd.append('file_payload', payloadFile);
    else fd.append('text_payload', payload);

    try {
      const resp = await apiRequest('/api/embed', { method: 'POST', body: fd }, true) as Response;
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(err.detail ?? `Server error ${resp.status}`);
      }
      const blob = await resp.blob();
      const url  = URL.createObjectURL(blob);

      const disp  = resp.headers.get('content-disposition') ?? '';
      const match = disp.match(/filename[^;=\n]*=\s*["']?([^"'\n;]+)/i);
      // If video, server may return .avi even if input was .mp4
      const dlName = match?.[1] ?? `${file.name.replace(/\.[^.]+$/, '')}_stego${file.name.match(/\.[^.]+$/)?.[0] ?? ''}`;

      const a = Object.assign(document.createElement('a'), { href: url, download: dlName, style: 'display:none' });
      document.body.appendChild(a); a.click(); document.body.removeChild(a);

      setSuccessData({ name: dlName, size: `${(blob.size / (1024 * 1024)).toFixed(2)} MB`, url });
      setFile(null); setMediaKind(null); setAlgorithm('');
      setPayload(''); setPayloadFile(null); setPassword('');
    } catch (err: any) {
      setError(err.message ?? 'Embedding failed.');
    } finally {
      setLoading(false);
    }
  };

  const algoOptions    = mediaKind ? ALGO_MAP[mediaKind] : [];
  const payloadAccept  = mediaKind ? PAYLOAD_ACCEPT[mediaKind] : '*/*';
  const canSubmit      = !loading && !!file && !!algorithm && !!password &&
                         (payloadType === 'text' ? !!payload.trim() : !!payloadFile);

  return (
    <div className="embed-container">
      <div className="tab-header">
        <h2>Secure Data Injection</h2>
        <p>Hide encrypted payloads within carrier media using adversarial neural patterns.</p>
      </div>

      {/* ── Carrier drop zone ───────────────────────────────────── */}
      <div
        className={`file-drop-area${isDragging ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
        onDragEnter={onDrag} onDragLeave={onDrag} onDragOver={onDrag} onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
      >
        <input ref={fileRef} type="file" style={{ display: 'none' }} accept={CARRIER_ACCEPT}
          onChange={e => { const f = e.target.files?.[0]; if (f) applyCarrier(f); e.target.value = ''; }} />

        {file ? (
          <div className="selected-file-info">
            <span className="file-icon">{mediaKind ? KIND_LABELS[mediaKind].split(' ')[0] : '📁'}</span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB &bull; {mediaKind ? KIND_LABELS[mediaKind] : ''} carrier</span>
            </div>
            <button className="change-btn" onClick={clearCarrier}>Change Carrier</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">📥</div>
            <p>Drop carrier file here to <span>hide your message</span></p>
            <span className="hint">
              🖼️ PNG / JPEG / BMP &nbsp;|&nbsp; 🔊 WAV &nbsp;|&nbsp; 🎬 MP4 / AVI / MKV &nbsp;— No size limits
            </span>
          </div>
        )}
      </div>

      {/* ── Context bar — appears once carrier is detected ──────── */}
      {mediaKind && (
        <div className="algo-context-bar">
          <span className="algo-context-label">{KIND_LABELS[mediaKind]} carrier detected</span>
          <span className="algo-context-hint">{KIND_HINT[mediaKind]}</span>
        </div>
      )}

      <div className="injection-dashboard glass-panel">

        {/* ── Payload ─────────────────────────────────────────────── */}
        <div className="form-group">
          <label>Covert Payload</label>
          <div className="payload-type-selector">
            <button className={`type-btn${payloadType === 'text' ? ' active' : ''}`} onClick={() => setPayloadType('text')}>
              Text Message
            </button>
            <button className={`type-btn${payloadType === 'file' ? ' active' : ''}`} onClick={() => setPayloadType('file')}>
              File Payload
            </button>
          </div>

          {payloadType === 'text' ? (
            <textarea rows={4} value={payload} onChange={e => setPayload(e.target.value)}
              placeholder="Enter the secret message to embed..." />
          ) : (
            <div
              className={`payload-file-drop${isDraggingPay ? ' drag-over' : ''}`}
              onDragEnter={onPayDrag} onDragLeave={onPayDrag} onDragOver={onPayDrag} onDrop={onPayDrop}
              onClick={() => payloadRef.current?.click()}
            >
              <input ref={payloadRef} type="file" style={{ display: 'none' }} accept={payloadAccept}
                onChange={e => { const f = e.target.files?.[0]; if (f) setPayloadFile(f); e.target.value = ''; }} />
              {payloadFile ? (
                <div className="payload-selected-info">
                  <span className="icon">📄</span>
                  <div className="details">
                    <span className="name">{payloadFile.name}</span>
                    <span className="size">{(payloadFile.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <button className="change-btn" onClick={e => { e.stopPropagation(); setPayloadFile(null); }}>Change</button>
                </div>
              ) : (
                <div className="payload-prompt">
                  <span className="icon">📁</span>
                  <p>Click or drop <span>secret file</span> here</p>
                  {mediaKind && (
                    <small>
                      {mediaKind === 'image' && 'Accepted: PNG, JPEG, GIF, PDF, TXT'}
                      {mediaKind === 'audio' && 'Accepted: TXT files only'}
                      {mediaKind === 'video' && 'Accepted: PNG, JPEG, PDF, TXT'}
                      {!mediaKind && 'Select a carrier first'}
                    </small>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Password + Algorithm row ─────────────────────────── */}
        <div className="dashboard-row">
          <div className="form-group">
            <label>Encryption Key</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Secure cryptographic key..." />
          </div>

          <div className="form-group">
            <label>Steganography Algorithm</label>
            {algoOptions.length > 0 ? (
              <select value={algorithm} onChange={e => setAlgorithm(e.target.value)}>
                {algoOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            ) : (
              <select disabled style={{ opacity: 0.4 }}>
                <option>— Select a carrier file first —</option>
              </select>
            )}
          </div>
        </div>

        <button onClick={handleSubmit} disabled={!canSubmit}
          className={loading ? 'loading' : ''} style={{ width: '100%' }}>
          {loading
            ? <><div className="spinner" /> Serializing Payload...</>
            : <><span className="icon">🔒</span> Embed &amp; Generate Stego-Media</>}
        </button>
      </div>

      {successData && (
        <div className="success-area animate-in">
          <div className="success-icon">✅</div>
          <div className="success-info">
            <strong>Stego-Media Generated</strong>
            <span>{successData.name} &bull; {successData.size}</span>
            <div className="auth-badge-container">
              <span className="auth-badge"><span className="dot" /> AUTHENTICITY SIGNING ACTIVE</span>
            </div>
          </div>
          <button className="download-feedback-btn" onClick={() => {
            const a = Object.assign(document.createElement('a'), { href: successData.url, download: successData.name, style: 'display:none' });
            document.body.appendChild(a); a.click(); document.body.removeChild(a);
          }}>Download Ready</button>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}
    </div>
  );
}
