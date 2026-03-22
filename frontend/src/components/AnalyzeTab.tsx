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

interface ThreatReport {
  threat_level: string;
  threat_color: string;
  threat_score: number;
  primary_risk: string;
  risks: string[];
  recommendations: string[];
  file_type_assessment: string;
  file_type_risk: string;
  strength_assessment: string;
  strength_risk: string;
  safe_to_send: boolean;
  summary: string;
}

interface AuthReport {
  is_authentic: boolean;
  verdict: string;
  verdict_color: string;
  signed_at?: string;
  key_fingerprint?: string;
  modification_detected: boolean;
  error?: string;
}

function AuthVerify({ filePath }: { filePath: string }) {
  const [report, setReport] = useState<AuthReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiRequest('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_path: filePath }),
      });
      setReport(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-verify-panel animate-in">
      <div className="auth-header">
        <span className="auth-icon">{report?.is_authentic ? '🛡️' : '🔒'}</span>
        <div className="auth-title">
          <h3>Neural Authenticity Engine</h3>
          <p>Verify cryptographic pixel signatures</p>
        </div>
        {!report && (
          <button 
            className={`verify-trigger-btn ${loading ? 'loading' : ''}`}
            onClick={handleVerify}
            disabled={loading}
          >
            {loading ? 'Verifying...' : 'Verify Authenticity'}
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {report && (
        <div className="auth-results animate-in">
          <div className="auth-status-container">
            <div className="verdict-card" style={{ backgroundColor: `${report.verdict_color}15`, borderColor: `${report.verdict_color}44` }}>
              <span className="verdict-label">Status</span>
              <span className="verdict-value" style={{ color: report.verdict_color }}>{report.verdict}</span>
            </div>

            {report.is_authentic && (
              <div className="auth-details-grid">
                <div className="auth-detail">
                  <span className="label">Timestamp</span>
                  <span className="value">{report.signed_at}</span>
                </div>
                <div className="auth-detail">
                  <span className="label">Neural Fingerprint</span>
                  <span className="value"><code>{report.key_fingerprint}</code></span>
                </div>
              </div>
            )}
          </div>

          {report.modification_detected && (
            <div className="tamper-alert">
              <span className="alert-icon">🚫</span>
              <div className="alert-content">
                <strong>TAMPERED DETECTED</strong>
                <p>The pixel-perfect hash of this image does not match the original signature. This file has been modified after it was signed.</p>
              </div>
            </div>
          )}

          {report.verdict === 'UNSIGNED' && (
            <div className="unsigned-notice">
              <p>No steganographic signature found. This file was not originated from StegXtreme.</p>
            </div>
          )}
          
          <button className="reverify-btn" onClick={() => setReport(null)}>Reset</button>
        </div>
      )}
    </div>
  );
}

function ThreatDashboard({ report }: { report: ThreatReport }) {
  const levelStyles: Record<string, any> = {
    SAFE: { bg: '#F0FDF4', text: '#166534', border: '#22C55E' },
    LOW: { bg: '#F7FEE7', text: '#365314', border: '#84CC16' },
    MODERATE: { bg: '#FEFCE8', text: '#713F12', border: '#EAB308' },
    HIGH: { bg: '#FFF7ED', text: '#7C2D12', border: '#F97316' },
    CRITICAL: { bg: '#FEF2F2', text: '#7F1D1D', border: '#EF4444' },
  };

  const style = levelStyles[report.threat_level] || levelStyles.SAFE;

  return (
    <div className="threat-dashboard animate-in">
      <div 
        className="threat-banner" 
        style={{ backgroundColor: style.bg, color: style.text, border: `1px solid ${style.border}` }}
      >
        <div className="banner-main">
          <div className="threat-info">
            <span className="level-label">THREAT LEVEL</span>
            <span className="level-value">{report.threat_level}</span>
          </div>
          <div className="score-info">
            <span className="score-value">{Math.round(report.threat_score * 100)}%</span>
            <span className="score-label">DETECTION CONFIDENCE</span>
          </div>
          <div className="safe-status">
            {report.safe_to_send ? (
              <div className="status-yes"><span className="icon">✓</span> SAFE TO SEND</div>
            ) : (
              <div className="status-no"><span className="icon">✕</span> DO NOT SEND</div>
            )}
          </div>
        </div>
      </div>

      <div className="threat-content">
        <p className="summary-text"><strong>Verdict:</strong> {report.summary}</p>
        
        <div className="primary-risk-box">
          <span className="risk-icon">⚠️</span>
          <div className="risk-text">
            <strong>Primary Risk Factor</strong>
            <p>{report.primary_risk}</p>
          </div>
        </div>

        <div className="risk-grid">
          <div className="risk-card">
            <span className="card-icon">📁</span>
            <div className="card-details">
              <strong>File Type Rating</strong>
              <p>{report.file_type_assessment}</p>
              <span className={`badge risk-${report.file_type_risk.toLowerCase()}`}>{report.file_type_risk}</span>
            </div>
          </div>
          {report.strength_assessment && (
            <div className="risk-card">
              <span className="card-icon">⚡</span>
              <div className="card-details">
                <strong>Payload Strength</strong>
                <p>{report.strength_assessment}</p>
                <span className={`badge risk-${report.strength_risk.toLowerCase()}`}>{report.strength_risk}</span>
              </div>
            </div>
          )}
        </div>

        {report.recommendations.length > 0 && (
          <div className="recommendations-section">
            <h4>Actionable Recommendations</h4>
            <ul className="recs-list">
              {report.recommendations.map((rec, i) => (
                <li key={i}><span className="bullet">{i + 1}</span> {rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
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
  const labelMap: Record<string, string> = {
    lsb_noise: 'Bit Pattern Anomaly',
    dct_ac_energy: 'Frequency Distortion',
    chi_square_lsb: 'Statistical Uniformity',
    frame_delta_cv: 'Temporal Consistency',
    chi_square_r: 'Red Channel Anomaly',
    chi_square_g: 'Green Channel Anomaly',
    chi_square_b: 'Blue Channel Anomaly',
    sample_pairs: 'Spatial Correlation',
    lsb_entropy: 'Signal Entropy',
    mfcc_variance: 'Spectral Variance',
    spectral_flatness: 'Signal Flatness',
  };

  const items: FeatureScore[] = Object.entries(features).map(([k, v]) => ({
    label: labelMap[k] || k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
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
          marginBottom: '1rem',
        }}
      >
        Neural Integrity Check
      </h4>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
        {items.map(({ label, value }) => {
          const pct = Math.round(value * 100);
          const color =
            value < 0.35 ? '#22c55e' : value < 0.65 ? '#f59e0b' : '#ef4444';
          return (
            <div key={label} style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  marginBottom: '0.4rem',
                  fontWeight: 600,
                }}
              >
                <span>{label}</span>
                <span style={{ color, fontWeight: 700 }}>{pct}%</span>
              </div>
              <div
                style={{
                  width: '100%',
                  height: '4px',
                  borderRadius: '2px',
                  background: 'rgba(255,255,255,0.05)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: '100%',
                    borderRadius: '2px',
                    background: color,
                    transition: 'width 1s ease-out',
                    boxShadow: `0 0 10px ${color}33`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="metric-guide" style={{ marginTop: '2rem', padding: '1.25rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
        <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '0.8rem', color: '#f8fafc', textTransform: 'uppercase' }}>Understanding these metrics</h5>
        <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8', lineHeight: '1.5' }}>
          Each percentage represents the <strong>suspicion level</strong> detected by our neural heuristics. 
          A higher percentage indicates more significant anomalies compared to a "clean" carrier file. 
          <strong> Bit Pattern</strong> anomalies suggest LSB manipulation, while <strong>Frequency/Temporal</strong> anomalies suggest embedding in compressed data domains.
        </p>
      </div>
    </div>
  );
}

export default function AnalyzeTab() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [threatReport, setThreatReport] = useState<ThreatReport | null>(null);
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
    setThreatReport(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const data: AnalysisResult = await apiRequest('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      setResult(data);

      try {
        const threatData: ThreatReport = await apiRequest('/api/analyze/threat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_path: file.name, 
            detection_prob: data.probability,
            embed_strength: null
          }),
        });
        setThreatReport(threatData);
      } catch (threatErr) {
        console.error("Threat analysis failed:", threatErr);
      }
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
          
          {threatReport ? (
            <ThreatDashboard report={threatReport} />
          ) : (
            <div className="threat-placeholder">
              Analyzing threat intelligence...
            </div>
          )}

          <div style={{ marginTop: '2rem' }}>
            {file && <AuthVerify filePath={file.name} />}
          </div>

          <div style={{ marginTop: '2.5rem', opacity: 0.6, borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '2.5rem' }}>
            <ProbabilityBar probability={result.probability} verdict={result.verdict} />
            <FeatureBreakdown features={result.features} />
          </div>
        </div>
      )}
    </div>
  );
}
