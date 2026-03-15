import React, { useState, useRef } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { apiRequest } from '../utils/api';
import './AnalyzeTab.css';

interface FeatureScore {
  label: string;
  value: number;
}

interface AnalysisResult {
  media_type: string;
  probability: number;
  verdict: 'CLEAN' | 'SUSPICIOUS' | 'LIKELY_STEGO';
  features: Record<string, number>;
}

function ProbabilityBar({ probability, verdict }: { probability: number; verdict: string }) {
  const pct = Math.round(probability * 100);
  const color =
    verdict === 'CLEAN'
      ? '#10b981'
      : verdict === 'SUSPICIOUS'
      ? '#f59e0b'
      : '#f43f5e';

  return (
    <div className="probability-section">
      <div className="prob-header">
        <span className="label">Inference Confidence</span>
        <span className="value" style={{ color }}>{pct}%</span>
      </div>
      <div className="prob-track">
        <div 
          className="prob-fill" 
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 20px ${color}44` }} 
        />
      </div>
      <div className="verdict-banner" style={{ background: `${color}15`, color, borderColor: `${color}33` }}>
        {verdict === 'CLEAN' ? '✅ SYSTEM CLEAN' : verdict === 'SUSPICIOUS' ? '⚠️ ANOMALIES DETECTED' : '🚨 HIGH PROBABILITY STEGO'}
      </div>
    </div>
  );
}

function FeatureBreakdown({ features }: { features: Record<string, number> }) {
  const items: FeatureScore[] = Object.entries(features).map(([k, v]) => ({
    label: k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    value: v,
  }));

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h4
        style={{
          fontSize: '0.85rem',
          fontWeight: 600,
          color: '#94a3b8',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          marginBottom: '0.75rem',
        }}
      >
        Per-Feature Breakdown
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
        {items.map(({ label, value }) => {
          const pct = Math.round(value * 100);
          const color =
            value < 0.35 ? '#22c55e' : value < 0.65 ? '#f59e0b' : '#ef4444';
          return (
            <div key={label}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '0.8rem',
                  color: '#cbd5e1',
                  marginBottom: '0.2rem',
                }}
              >
                <span>{label}</span>
                <span style={{ color, fontWeight: 600 }}>{pct}%</span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: '6px',
                  borderRadius: '3px',
                  background: 'rgba(255,255,255,0.06)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: '100%',
                    borderRadius: '3px',
                    background: color,
                    transition: 'width 0.6s ease',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function AnalyzeTab() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
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
      setError('Please select a media file to analyse.');
      return;
    }
    if (file && file.size > 500 * 1024 * 1024) {
      setError('Analysis limit is 500MB per file.');
      return;
    }
    setError('');
    setResult(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const data: AnalysisResult = await apiRequest('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const exportPDF = async () => {
    if (!result) return;
    const element = document.getElementById('analysis-report');
    if (!element) return;

    const canvas = await html2canvas(element, {
      backgroundColor: '#0f172a',
      scale: 2,
    });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const imgProps = pdf.getImageProperties(imgData);
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
    pdf.save(`stegxtreme_report_${Date.now()}.pdf`);
  };

  return (
    <div className="analyze-container">
      <div className="tab-header">
        <h2>Steganographic Analysis</h2>
        <p>Detect hidden payloads using multi-modal feature extraction and neural heuristics.</p>
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
          accept="image/png,image/bmp,image/tiff,audio/wav,audio/flac,video/mp4,video/avi"
        />
        {file ? (
          <div className="selected-file-info">
            <span className="file-icon">
              {file.type.startsWith('image/') ? '🖼️' : file.type.startsWith('video/') ? '🎬' : file.type.startsWith('audio/') ? '🔊' : '📄'}
            </span>
            <div className="details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || 'Unknown Type'}</span>
            </div>
            <button className="change-btn" onClick={(e) => { e.stopPropagation(); setFile(null); }}>Change</button>
          </div>
        ) : (
          <div className="drop-prompt">
            <div className="pulse-icon">📂</div>
            <p>Upload any file to <span>check for hidden data</span></p>
            <span className="hint">PNG, BMP, WAV, MP4, AVI (Max 500MB)</span>
          </div>
        )}
      </div>

      <button 
        onClick={handleSubmit} 
        disabled={loading || !file} 
        className={loading ? 'loading' : ''}
      >
        {loading ? (
          <>
            <div className="spinner" />
            Running Neural Analysis...
          </>
        ) : (
          <>
            <span className="icon">🔍</span> Start Analysis
          </>
        )}
      </button>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <div id="analysis-report" className="results-container animate-in">
          <div className="results-header">
            <span className="media-type-badge">{result.media_type}</span>
            <button className="export-btn" onClick={exportPDF}>
              Download Report
            </button>
          </div>
          <ProbabilityBar probability={result.probability} verdict={result.verdict} />
          <FeatureBreakdown features={result.features} />
        </div>
      )}
    </div>
  );
}
