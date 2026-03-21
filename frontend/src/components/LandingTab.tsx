import React, { useEffect, useState, useRef } from 'react';
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
  const scrollRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('in');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.07 }
    );

    const fadeEls = document.querySelectorAll('.fade-up');
    fadeEls.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing-tab-wrapper" ref={scrollRef}>
      <nav className="landing-nav">
        <a className="nav-wordmark" href="#">
          <span className="nav-dot"></span>
          StegXtreme
        </a>
        <div className="nav-center">
          <a href="#how">How it works</a>
          <a href="#modules">Modules</a>
          <a href="#tunneling">Tunneling</a>
          <a href="#gan">GAN</a>
          <a href="#stack">Stack</a>
        </div>
        <div className="nav-pill">v2.0 Active</div>
      </nav>

      {/* HERO */}
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
            <span className="hstat-val">{stats?.latest_psnr || '38dB'}</span>
            <span className="hstat-lbl">PSNR</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.gpu_enabled ? 'GPU' : 'CPU'}</span>
            <span className="hstat-lbl">Accelerated</span>
          </div>
        </div>
      </div>

      {/* HOW IT WORKS */}
      <section id="how">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">How it works</p>
            <h2 className="section-title">Encrypt. Transform.<br />Disappear.</h2>
            <p className="section-body">Every operation runs a six-stage pipeline — from raw payload to imperceptible carrier, and back again.</p>
          </div>
          <div className="steps fade-up d1">
            <div className="step">
              <div className="step-num">01</div>
              <span className="step-icon">📂</span>
              <h3>Upload carrier</h3>
              <p>Image, video, or audio lands on <span className="mono">POST /embed</span>. The router identifies the media type and dispatches to the right backend processor.</p>
            </div>
            <div className="step">
              <div className="step-num">02</div>
              <span className="step-icon">🔐</span>
              <h3>Encrypt payload</h3>
              <p>AES-256-GCM with an ephemeral key via Argon2id KDF. Ed25519 signs the payload. Zero key reuse across sessions — full PFS.</p>
            </div>
            <div className="step">
              <div className="step-num">03</div>
              <span className="step-icon">〰️</span>
              <h3>DWT decompose</h3>
              <p>2D Discrete Wavelet Transform splits the carrier into LL / LH / HL / HH subbands. Bits embed in mid-frequency coefficients, invisible to human perception.</p>
            </div>
            <div className="step">
              <div className="step-num">04</div>
              <span className="step-icon">📡</span>
              <h3>Spread-spectrum</h3>
              <p>Each bit fans across 256 pseudo-random carriers from a seeded RNG. Survives JPEG compression, resizing, and format conversion.</p>
            </div>
            <div className="step">
              <div className="step-num">05</div>
              <span className="step-icon">🧠</span>
              <h3>GAN refinement</h3>
              <p>The Hider network polishes the output until the Detector can no longer distinguish it from a clean file. Adversarial training drives imperceptibility.</p>
            </div>
            <div className="step">
              <div className="step-num">06</div>
              <span className="step-icon">✅</span>
              <h3>Deliver & extract</h3>
              <p>Clean stego file delivered. Extraction reverses: DWT → SS decode → AES decrypt. Forensic analysis at <span className="mono">/analyze</span>.</p>
            </div>
          </div>
        </div>
      </section>

      {/* MODULES */}
      <section id="modules">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Architecture</p>
            <h2 className="section-title">Six modules.<br />One system.</h2>
            <p className="section-body">Clean boundaries, single ownership. The router wires them at runtime based on operation and media type.</p>
          </div>
          <div className="modules-grid fade-up d1">
            <div className="mod">
              <div className="mod-header">
                <div className="mod-icon blue">🌊</div>
                <span className="mod-badge">Core</span>
              </div>
              <h3>Steganography Engine</h3>
              <p>Multi-backend routing across image, video, and audio carriers. DWT + spread-spectrum math is fully decoupled from the crypto layer so each evolves independently.</p>
              <div className="mod-chips">
                <span className="chip">core/backends/router.py</span>
                <span className="chip">DWT-2D</span>
                <span className="chip">spread-spectrum</span>
              </div>
            </div>
            <div className="mod">
              <div className="mod-header">
                <div className="mod-icon green">🧠</div>
                <span className="mod-badge">Neural</span>
              </div>
              <h3>GAN Models</h3>
              <p>Hider embeds. Detector attacks. Feedback scheduler prevents mode collapse. ONNX export runs inference at deploy time — no PyTorch dependency in production.</p>
              <div className="mod-chips">
                <span className="chip">core/neural/hider.py</span>
                <span className="chip">core/neural/detector.py</span>
                <span className="chip">ONNX</span>
                <span className="chip">CuPy</span>
              </div>
            </div>
            <div className="mod">
              <div className="mod-header">
                <div className="mod-icon red">📡</div>
                <span className="mod-badge">Network</span>
              </div>
              <h3>Covert Tunneling</h3>
              <p>DNS, ICMP, and HTTP covert channels each with a dedicated encoder. A daemon multiplexes channels and a telemetry layer reports bandwidth and packet loss live.</p>
              <div className="mod-chips">
                <span className="chip">core/tunnel/dns.py</span>
                <span className="chip">core/tunnel/icmp.py</span>
                <span className="chip">Scapy</span>
              </div>
            </div>
            <div className="mod">
              <div className="mod-header">
                <div className="mod-icon amber">🔐</div>
                <span className="mod-badge">Crypto</span>
              </div>
              <h3>Cryptography</h3>
              <p>Perfect Forward Secrecy via ephemeral DH. AES-256-GCM authenticated encryption. Argon2id KDF with tunable time and memory cost. Ed25519 payload signing.</p>
              <div className="mod-chips">
                <span className="chip">core/crypto/pfs.py</span>
                <span className="chip">AES-256-GCM</span>
                <span className="chip">Argon2id</span>
                <span className="chip">Ed25519</span>
              </div>
            </div>
            <div className="mod">
              <div className="mod-header">
                <div className="mod-icon blue">🔬</div>
                <span className="mod-badge">Analysis</span>
              </div>
              <h3>Forensic Analysis</h3>
              <p>Chi-square, RS analysis, and histogram anomaly detection on image, video, and audio. Outputs heatmaps, bitplane views, and timeline visualisations.</p>
              <div className="mod-chips">
                <span className="chip">core/analysis/</span>
                <span className="chip">core/visualiser/</span>
                <span className="chip">chi-square</span>
                <span className="chip">RS analysis</span>
              </div>
            </div>
            <div className="mod">
              <div className="mod-header">
                <div className="mod-icon green">⚡</div>
                <span className="mod-badge">API</span>
              </div>
              <h3>FastAPI Backend</h3>
              <p>Async backend with JWT auth, background job queue for long-running tasks, WebSocket progress channel, and full OpenAPI docs. Two terminals run everything.</p>
              <div className="mod-chips">
                <span className="chip">FastAPI 0.111</span>
                <span className="chip">SQLAlchemy</span>
                <span className="chip">WebSockets</span>
                <span className="chip">python-jose</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* TUNNELING */}
      <section id="tunneling">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Covert channels</p>
            <h2 className="section-title">Traffic that doesn't<br />look like traffic.</h2>
            <p className="section-body">Data hides inside the protocol headers and payloads of ordinary network traffic. Firewalls see DNS queries, ICMP pings, and HTTP — not a covert channel.</p>
          </div>
          <div className="tunnel-grid fade-up d1">
            <div className="tunnel-visual">
              <div className="tunnel-visual-label">Packet flow</div>
              <div className="flow">
                <div className="flow-row">
                  <div className="flow-node">
                    <span className="fni">🖥️</span>
                    <div><span className="fnt">Sender</span><span className="fns">Encodes payload into packets</span></div>
                  </div>
                </div>
                <div className="flow-connector">
                  <div className="flow-line"></div>
                  <div className="flow-tag">DNS · ICMP · HTTP</div>
                  <div className="flow-line"></div>
                </div>
                <div className="flow-row">
                  <div className="flow-node">
                    <span className="fni">🔥</span>
                    <div><span className="fnt">Firewall / IDS</span><span className="fns">Sees normal protocol traffic</span></div>
                  </div>
                </div>
                <div className="flow-connector">
                  <div className="flow-line"></div>
                  <div className="flow-tag">Passes through</div>
                  <div className="flow-line"></div>
                </div>
                <div className="flow-row">
                  <div className="flow-node">
                    <span className="fni">📡</span>
                    <div><span className="fnt">Relay monitor</span><span className="fns">daemon.py watches bandwidth</span></div>
                  </div>
                </div>
                <div className="flow-connector">
                  <div className="flow-line"></div>
                  <div className="flow-tag">Reconstructed stream</div>
                  <div className="flow-line"></div>
                </div>
                <div className="flow-row">
                  <div className="flow-node">
                    <span className="fni">🖥️</span>
                    <div><span className="fnt">Receiver</span><span className="fns">Decodes, decrypts, delivers</span></div>
                  </div>
                </div>
              </div>
            </div>
            <div className="protocol-cards">
              <div className="proto-card">
                <div className="proto-circle dns">🔤</div>
                <div>
                  <h4>DNS Tunnel</h4>
                  <p>Payload encoded as base32 subdomains in DNS query labels. Receiver decodes TXT and A record responses. Bypasses most stateless firewalls silently.</p>
                </div>
              </div>
              <div className="proto-card">
                <div className="proto-circle icmp">📶</div>
                <div>
                  <h4>ICMP Covert Channel</h4>
                  <p>Bytes embedded in ICMP Echo Request data fields. Scapy crafts raw packets. Sequence numbers handle chunk ordering and reassembly.</p>
                </div>
              </div>
              <div className="proto-card">
                <div className="proto-circle http">🌐</div>
                <div>
                  <h4>HTTP Steganography</h4>
                  <p>Data hidden in headers, cookies, and chunked transfer encoding. Traffic pattern mimics real browsing to defeat deep packet inspection.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* GAN */}
      <section id="gan">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Neural models</p>
            <h2 className="section-title">An adversary that makes<br />the model stronger.</h2>
            <p className="section-body">A GAN trained end-to-end on the steganography task. The harder the Detector gets to fool, the better the Hider becomes.</p>
          </div>
          <div className="gan-layout-landing fade-up d1">
            <div className="gan-explainer">
              <div className="gan-card">
                <div className="gan-card-label blue">Generator</div>
                <h3>Hider</h3>
                <p>Embeds a bit payload into a carrier image while minimising perceptual distortion. Optimised against both reconstruction loss and the Detector's discrimination score.</p>
              </div>
              <div className="gan-card">
                <div className="gan-card-label red">Discriminator</div>
                <h3>Detector</h3>
                <p>Binary classifier trained to distinguish clean images from stego images. Its accuracy is the adversarial signal that pushes the Hider to improve.</p>
              </div>
              <div className="gan-card">
                <div className="gan-card-label green">Outcome</div>
                <h3>Imperceptible embedding</h3>
                <p>200 epochs with a feedback scheduler. Hider achieves 38.4 dB PSNR and 0.997 SSIM. Exported to ONNX for zero-dependency inference at deploy time.</p>
              </div>
              <div className="terminal">
                <div className="terminal-bar">
                  <div className="tbar-dot"></div><div className="tbar-dot"></div><div className="tbar-dot"></div>
                  <span className="terminal-title">core.neural.trainer</span>
                </div>
                <div className="terminal-body">
                  <div><span className="t-prompt">❯</span> <span className="t-cmd">python -m core.neural.trainer --epochs 200</span></div>
                  <div className="t-out">Epoch  001 · hider_loss=0.8421 · det_acc=51.2%</div>
                  <div className="t-out">Epoch  050 · hider_loss=0.3107 · det_acc=49.8%</div>
                  <div className="t-out">Epoch  200 · hider_loss=0.0922 · <span className="t-hl">PSNR=38.4dB ✓</span></div>
                  <div><span className="t-prompt">❯</span> <span className="t-cmd">python -m core.neural.registry export --onnx</span></div>
                  <div className="t-out"><span className="t-hl">→</span> storage/models/hider_v2.onnx</div>
                </div>
              </div>
            </div>
            <div className="gan-right">
              <div className="gan-metrics">
                <div className="gmet"><span className="gmet-val blue">38.4</span><span className="gmet-lbl">dB PSNR</span></div>
                <div className="gmet"><span className="gmet-val green">0.997</span><span className="gmet-lbl">SSIM score</span></div>
                <div className="gmet"><span className="gmet-val amber">200</span><span className="gmet-lbl">Training epochs</span></div>
                <div className="gmet"><span className="gmet-val red">&lt;5%</span><span className="gmet-lbl">Detector accuracy</span></div>
                <div className="gmet gmet-wide">
                  <span className="gmet-val" style={{ color: 'var(--white)', fontSize: '17px', fontFamily: 'var(--sf-font)', letterSpacing: '-0.5px' }}>ONNX · GPU / CPU</span>
                  <span className="gmet-lbl" style={{ display: 'block', marginTop: '4px' }}>Inference runtime</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* STACK */}
      <section id="stack">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Technology</p>
            <h2 className="section-title">Built on the right tools.</h2>
            <p className="section-body">Two terminals run everything. <span className="mono" style={{ fontSize: '15px', color: 'var(--white)' }}>uvicorn</span> for the backend, <span className="mono" style={{ fontSize: '15px', color: 'var(--white)' }}>npm run dev</span> for the frontend.</p>
          </div>
          <div className="stack-list fade-up d1">
            <div className="stack-item"><div className="stack-icon">⚡</div><div><span className="stack-name">FastAPI</span><span className="stack-role">Async backend</span></div></div>
            <div className="stack-item"><div className="stack-icon">⚛️</div><div><span className="stack-name">React + Vite</span><span className="stack-role">Frontend SPA</span></div></div>
            <div className="stack-item"><div className="stack-icon">🔷</div><div><span className="stack-name">TypeScript</span><span className="stack-role">Type safety</span></div></div>
            <div className="stack-item"><div className="stack-icon">🧮</div><div><span className="stack-name">NumPy / CuPy</span><span className="stack-role">Math compute</span></div></div>
            <div className="stack-item"><div className="stack-icon">🔦</div><div><span className="stack-name">PyTorch</span><span className="stack-role">GAN training</span></div></div>
            <div className="stack-item"><div className="stack-icon">📦</div><div><span className="stack-name">ONNX Runtime</span><span className="stack-role">Inference</span></div></div>
            <div className="stack-item"><div className="stack-icon">🖼️</div><div><span className="stack-name">OpenCV / PIL</span><span className="stack-role">Image processing</span></div></div>
            <div className="stack-item"><div className="stack-icon">🎵</div><div><span className="stack-name">Librosa</span><span className="stack-role">Audio analysis</span></div></div>
            <div className="stack-item"><div className="stack-icon">🌐</div><div><span className="stack-name">Scapy</span><span className="stack-role">Packet crafting</span></div></div>
            <div className="stack-item"><div className="stack-icon">🔑</div><div><span className="stack-name">cryptography</span><span className="stack-role">AES / Ed25519</span></div></div>
            <div className="stack-item"><div className="stack-icon">🗄️</div><div><span className="stack-name">SQLAlchemy</span><span className="stack-role">ORM / SQLite</span></div></div>
            <div className="stack-item"><div className="stack-icon">🔒</div><div><span className="stack-name">Argon2-cffi</span><span className="stack-role">Key derivation</span></div></div>
          </div>
        </div>
      </section>

      {/* TEAM */}
      <section id="team">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Team</p>
            <h2 className="section-title">Two developers.<br />No overlaps.</h2>
            <p className="section-body">File ownership is hard-enforced. Nobody touches a file they don't own. Daily PRs merge only on green tests.</p>
          </div>
          <div className="team-grid fade-up d1">
            <div className="team-card">
              <div className="team-avatar">⚙️</div>
              <div className="team-role-tag">Dev A · GPU / Neural</div>
              <div className="team-name">Core Compute Lead</div>
              <p className="team-desc">Owns the GAN pipeline, GPU acceleration via CuPy, ONNX export, and the shared <span className="mono">compute/backend.py</span> contract established on Day 1.</p>
              <span className="team-branch">a/day1 → a/day2 → …</span>
            </div>
            <div className="team-card">
              <div className="team-avatar">🔧</div>
              <div className="team-role-tag">Dev B · Backend / Infra</div>
              <div className="team-name">Platform Lead</div>
              <p className="team-desc">Owns FastAPI routes, WebSocket layer, database models, crypto, tunnel protocols, and the full React + Vite frontend scaffold.</p>
              <span className="team-branch">b/day1 → b/day2 → …</span>
            </div>
            <div className="team-card">
              <div className="team-avatar">🐙</div>
              <div className="team-role-tag">Repository</div>
              <div className="team-name">github.com/<br />Cryptocrushers-ah/StegXtreme</div>
              <p className="team-desc">Single mono-repo. Daily branch → PR → merge-on-green. Shared contract in <span className="mono">core/compute/backend.py</span> — signatures frozen after Day 1.</p>
              <span className="team-branch">main ← a/* · b/*</span>
            </div>
          </div>
        </div>
      </section>

      <footer>
        <div className="footer-left">
          <span className="nav-dot"></span>
          StegXtreme
        </div>
        <div className="footer-right">github.com/Cryptocrushers-ah/StegXtreme · v2.0</div>
      </footer>
    </div>
  );
};

export default LandingTab;
