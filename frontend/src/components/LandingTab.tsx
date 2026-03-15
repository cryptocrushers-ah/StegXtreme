import React, { useEffect, useState } from 'react';
import { apiRequest } from '../utils/api';
import './LandingTab.css';

interface Stats {
  modules_count: number;
  api_routes_count: number;
  protocols_count: number;
  latest_psnr: string;
  gpu_enabled: boolean;
  mode: string;
}

interface LandingTabProps {
  onNavigate: (tab: any) => void;
}

const LandingTab: React.FC<LandingTabProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiRequest('/api/stats');
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch system stats', err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="landing-tab-wrapper">
      <div className="hero">
        <div className="hero-glow"></div>
        <div className="eyebrow fade-up in">Advanced Steganography Platform</div>
        <h1 className="fade-up in d1">Hide data in<br /><em>plain sight.</em></h1>
        <p className="hero-sub fade-up in d2">
          Multi-domain steganography combining GAN models, spread-spectrum embedding, cryptographic PFS, and covert network tunneling — across image, video, and audio.
        </p>
        <div className="btn-group fade-up in d3">
          <button onClick={() => onNavigate('embed')} className="btn btn-solid">Explore</button>
        </div>
        
        <div className="hero-stats fade-up in d4">
          <div className="hstat">
            <span className="hstat-val">{stats?.modules_count || '6'}</span>
            <span className="hstat-lbl">Core modules</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.api_routes_count || '12'}</span>
            <span className="hstat-lbl">API routes</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.protocols_count || '3'}</span>
            <span className="hstat-lbl">Covert protocols</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.latest_psnr || '38.4dB'}</span>
            <span className="hstat-lbl">Latest PSNR</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.gpu_enabled ? 'GPU' : 'CPU'}</span>
            <span className="hstat-lbl">Acceleration</span>
          </div>
        </div>
      </div>

      <section id="how">
        <div className="container">
          <div className="fade-up in">
            <p className="section-label">Pipeline Overview</p>
            <h2 className="section-title">Encrypt. Transform.<br />Disappear.</h2>
            <p className="section-body">Every operation runs a six-stage pipeline — from raw payload to imperceptible carrier, and back again.</p>
          </div>
          <div className="steps-grid fade-up in d1">
            <div className="step-card">
              <div className="step-num">01</div>
              <span className="step-icon">📂</span>
              <h3>Upload carrier</h3>
              <p>Image, video, or audio lands on <code className="mono">/embed</code>. The router dispatches to the optimized backend processor.</p>
            </div>
            <div className="step-card">
              <div className="step-num">02</div>
              <span className="step-icon">🔐</span>
              <h3>Encrypt payload</h3>
              <p>AES-256-GCM with Argon2id KDF. Zero key reuse across sessions — full Perfect Forward Secrecy.</p>
            </div>
            <div className="step-card">
              <div className="step-num">03</div>
              <span className="step-icon">🧠</span>
              <h3>GAN Refinement</h3>
              <p>Adversarial training polishes output until stego signatures are indistinguishable from natural noise.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingTab;
