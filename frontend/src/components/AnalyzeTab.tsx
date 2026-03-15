import React, { useState, useRef } from 'react';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

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
      ? '#22c55e'
      : verdict === 'SUSPICIOUS'
      ? '#f59e0b'
      : '#ef4444';

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: '#94a3b8' }}>
          Steganography Probability
        </span>
        <span style={{ fontWeight: 700, color }}>
          {pct}%
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: '12px',
          borderRadius: '6px',
          background: 'rgba(255,255,255,0.08)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            borderRadius: '6px',
            background: color,
            transition: 'width 0.8s cubic-bezier(0.4,0,0.2,1)',
            boxShadow: `0 0 12px ${color}88`,
          }}
        />
      </div>
      <div
        style={{
          marginTop: '0.75rem',
          display: 'inline-block',
          padding: '0.3rem 0.85rem',
          borderRadius: '999px',
          fontWeight: 700,
          fontSize: '0.8rem',
          letterSpacing: '0.08em',
          background: `${color}22`,
          color,
          border: `1px solid ${color}55`,
        }}
      >
        {verdict === 'CLEAN'
          ? '✅ CLEAN'
          : verdict === 'SUSPICIOUS'
          ? '⚠️ SUSPICIOUS'
          : '🚨 LIKELY STEGO'}
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
    setError('');
    setResult(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Analysis failed');
      }
      const data: AnalysisResult = await response.json();
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
          accept="image/png,image/bmp,image/tiff,audio/wav,audio/flac,video/mp4,video/avi"
        />
        {file ? (
          <p style={{ color: '#38bdf8', fontWeight: 600 }}>
            Selected: {file.name}
          </p>
        ) : (
          <>
            <p>Drag &amp; drop any media file, or click to select.</p>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
              Supports PNG, BMP, TIFF, WAV, FLAC, MP4, AVI
            </p>
          </>
        )}
      </div>

      <button type="submit" disabled={loading} style={{ marginTop: '1rem' }}>
        {loading ? 'Analysing…' : '🔍 Analyse for Steganography'}
      </button>

      {result && (
        <div id="analysis-report" style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <p style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.07em', margin: 0 }}>
              Media type detected: <strong style={{ color: '#94a3b8' }}>{result.media_type}</strong>
            </p>
            <button 
              type="button" 
              onClick={exportPDF}
              style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#e2e8f0', borderRadius: '6px' }}
            >
              📥 Download PDF Report
            </button>
          </div>
          <ProbabilityBar probability={result.probability} verdict={result.verdict} />
          <FeatureBreakdown features={result.features} />
        </div>
      )}

      {error && <div className="error-message" style={{ marginTop: '1rem' }}>{error}</div>}
    </form>
  );
}
