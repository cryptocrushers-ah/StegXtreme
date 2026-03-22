import React, { useEffect, useState, useRef } from 'react';
import { apiRequest } from '../utils/api';
import RibbonBackground from './RibbonBackground';
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

      {/* ── FULL-PAGE WAVE CANVAS ── */}
      <RibbonBackground />

      {/* ── NAV ── */}
      <nav className="landing-nav">
        <a className="nav-wordmark" href="#">
          <span className="nav-dot" />
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

      {/* ── HERO ── */}
      <div className="hero">
        <div className="hero-glow" />

        <div className="eyebrow fade-up in">
          Advanced Steganography Platform
        </div>

        <h1 className="fade-up in d1">
          Hide data in<br /><em>plain sight.</em>
        </h1>

        <p className="hero-sub fade-up in d2">
          Multi-domain steganography combining GAN models, spread-spectrum
          embedding, cryptographic PFS, and covert network tunneling —
          across image, video, and audio.
        </p>

        <div className="btn-group fade-up in d3">
          <button onClick={() => onNavigate('embed')} className="btn btn-solid">
            Explore Platform
          </button>
          <a href="#how" className="btn btn-ghost">How it works</a>
        </div>

        <div className="hero-stats fade-up in d4">
          <div className="hstat">
            <span className="hstat-val">{stats?.modules_count ?? '6'}</span>
            <span className="hstat-lbl">Core modules</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.api_routes_count ?? '12'}</span>
            <span className="hstat-lbl">API routes</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.protocols_count ?? '3'}</span>
            <span className="hstat-lbl">Covert protocols</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.latest_psnr ?? '38dB'}</span>
            <span className="hstat-lbl">PSNR</span>
          </div>
          <div className="hstat">
            <span className="hstat-val">{stats?.gpu_enabled ? 'GPU' : 'CPU'}</span>
            <span className="hstat-lbl">Accelerated</span>
          </div>
        </div>
      </div>

      {/* ── HOW IT WORKS ── */}
      <section id="how">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">How it works</p>
            <h2 className="section-title">Encrypt. Transform.<br />Disappear.</h2>
            <p className="section-body">
              Every operation runs a six-stage pipeline — from raw payload to
              imperceptible carrier, and back again.
            </p>
          </div>
          <div className="steps fade-up d1">
            {[
              { num: '01', icon: '📂', title: 'Upload carrier', body: <>Image, video, or audio lands on <span className="mono">POST /embed</span>. The router identifies the media type and dispatches to the right backend processor.</> },
              { num: '02', icon: '🔐', title: 'Encrypt payload', body: 'AES-256-GCM with an ephemeral key via Argon2id KDF. Ed25519 signs the payload. Zero key reuse across sessions — full PFS.' },
              { num: '03', icon: '〰️', title: 'DWT decompose', body: '2D Discrete Wavelet Transform splits the carrier into LL / LH / HL / HH subbands. Bits embed in mid-frequency coefficients, invisible to human perception.' },
              { num: '04', icon: '📡', title: 'Spread-spectrum', body: 'Each bit fans across 256 pseudo-random carriers from a seeded RNG. Survives JPEG compression, resizing, and format conversion.' },
              { num: '05', icon: '🧠', title: 'GAN refinement', body: 'The Hider network polishes the output until the Detector can no longer distinguish it from a clean file. Adversarial training drives imperceptibility.' },
              { num: '06', icon: '✅', title: 'Deliver & extract', body: <>Clean stego file delivered. Extraction reverses: DWT → SS decode → AES decrypt. Forensic analysis at <span className="mono">/analyze</span>.</> },
            ].map((s) => (
              <div className="step" key={s.num}>
                <div className="step-num">{s.num}</div>
                <span className="step-icon">{s.icon}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── MODULES ── */}
      <section id="modules">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Architecture</p>
            <h2 className="section-title">Six modules.<br />One system.</h2>
            <p className="section-body">
              Clean boundaries, single ownership. The router wires them at
              runtime based on operation and media type.
            </p>
          </div>
          <div className="modules-grid fade-up d1">
            {[
              {
                icon: '🌊', badge: 'Core', label: 'blue', title: 'Steganography Engine',
                body: 'Multi-backend routing across image, video, and audio carriers. DWT + spread-spectrum math is fully decoupled from the crypto layer so each evolves independently.',
                chips: ['core/backends/router.py', 'DWT-2D', 'spread-spectrum'],
              },
              {
                icon: '🧠', badge: 'Neural', label: 'green', title: 'GAN Models',
                body: 'Hider embeds. Detector attacks. Feedback scheduler prevents mode collapse. ONNX export runs inference at deploy time — no PyTorch dependency in production.',
                chips: ['core/neural/hider.py', 'core/neural/detector.py', 'ONNX', 'CuPy'],
              },
              {
                icon: '📡', badge: 'Network', label: 'red', title: 'Covert Tunneling',
                body: 'DNS, ICMP, and HTTP covert channels each with a dedicated encoder. A daemon multiplexes channels and a telemetry layer reports bandwidth and packet loss live.',
                chips: ['core/tunnel/dns.py', 'core/tunnel/icmp.py', 'Scapy'],
              },
              {
                icon: '🔐', badge: 'Crypto', label: 'amber', title: 'Cryptography',
                body: 'Perfect Forward Secrecy via ephemeral DH. AES-256-GCM authenticated encryption. Argon2id KDF with tunable time and memory cost. Ed25519 payload signing.',
                chips: ['core/crypto/pfs.py', 'AES-256-GCM', 'Argon2id', 'Ed25519'],
              },
              {
                icon: '🔬', badge: 'Analysis', label: 'blue', title: 'Forensic Analysis',
                body: 'Chi-square, RS analysis, and histogram anomaly detection on image, video, and audio. Outputs heatmaps, bitplane views, and timeline visualisations.',
                chips: ['core/analysis/', 'core/visualiser/', 'chi-square', 'RS analysis'],
              },
              {
                icon: '⚡', badge: 'API', label: 'green', title: 'FastAPI Backend',
                body: 'Async backend with JWT auth, background job queue for long-running tasks, WebSocket progress channel, and full OpenAPI docs. Two terminals run everything.',
                chips: ['FastAPI 0.111', 'SQLAlchemy', 'WebSockets', 'python-jose'],
              },
            ].map((m) => (
              <div className="mod" key={m.title}>
                <div className="mod-header">
                  <div className={`mod-icon ${m.label}`}>{m.icon}</div>
                  <span className="mod-badge">{m.badge}</span>
                </div>
                <h3>{m.title}</h3>
                <p>{m.body}</p>
                <div className="mod-chips">
                  {m.chips.map((c) => <span className="chip" key={c}>{c}</span>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TUNNELING ── */}
      <section id="tunneling">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Covert channels</p>
            <h2 className="section-title">Traffic that doesn't<br />look like traffic.</h2>
            <p className="section-body">
              Data hides inside the protocol headers and payloads of ordinary
              network traffic. Firewalls see DNS queries, ICMP pings, and HTTP
              — not a covert channel.
            </p>
          </div>
          <div className="tunnel-grid fade-up d1">
            <div className="tunnel-visual">
              <div className="tunnel-visual-label">Packet flow</div>
              <div className="flow">
                {[
                  { icon: '🖥️', title: 'Sender', sub: 'Encodes payload into packets' },
                  null,
                  { icon: '🔥', title: 'Firewall / IDS', sub: 'Sees normal protocol traffic' },
                  null,
                  { icon: '📡', title: 'Relay monitor', sub: 'daemon.py watches bandwidth' },
                  null,
                  { icon: '🖥️', title: 'Receiver', sub: 'Decodes, decrypts, delivers' },
                ].map((item, i) =>
                  item === null ? (
                    <div className="flow-connector" key={i}>
                      <div className="flow-line" />
                      <div className="flow-tag">{i === 1 ? 'DNS · ICMP · HTTP' : i === 3 ? 'Passes through' : 'Reconstructed stream'}</div>
                      <div className="flow-line" />
                    </div>
                  ) : (
                    <div className="flow-row" key={i}>
                      <div className="flow-node">
                        <span className="fni">{item.icon}</span>
                        <div>
                          <span className="fnt">{item.title}</span>
                          <span className="fns">{item.sub}</span>
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>

            <div className="protocol-cards">
              {[
                { cls: 'dns', icon: '🔤', title: 'DNS Tunnel', body: 'Payload encoded as base32 subdomains in DNS query labels. Receiver decodes TXT and A record responses. Bypasses most stateless firewalls silently.' },
                { cls: 'icmp', icon: '📶', title: 'ICMP Covert Channel', body: 'Bytes embedded in ICMP Echo Request data fields. Scapy crafts raw packets. Sequence numbers handle chunk ordering and reassembly.' },
                { cls: 'http', icon: '🌐', title: 'HTTP Steganography', body: 'Data hidden in headers, cookies, and chunked transfer encoding. Traffic pattern mimics real browsing to defeat deep packet inspection.' },
              ].map((p) => (
                <div className="proto-card" key={p.cls}>
                  <div className={`proto-circle ${p.cls}`}>{p.icon}</div>
                  <div>
                    <h4>{p.title}</h4>
                    <p>{p.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── GAN ── */}
      <section id="gan">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Neural models</p>
            <h2 className="section-title">An adversary that makes<br />the model stronger.</h2>
            <p className="section-body">
              A GAN trained end-to-end on the steganography task. The harder
              the Detector gets to fool, the better the Hider becomes.
            </p>
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
                  <div className="tbar-dot" /><div className="tbar-dot" /><div className="tbar-dot" />
                  <span className="terminal-title">core.neural.trainer</span>
                </div>
                <div className="terminal-body">
                  <div><span className="t-prompt">❯ </span><span className="t-cmd">python -m core.neural.trainer --epochs 200</span></div>
                  <div className="t-out">Epoch  001 · hider_loss=0.8421 · det_acc=51.2%</div>
                  <div className="t-out">Epoch  050 · hider_loss=0.3107 · det_acc=49.8%</div>
                  <div className="t-out">Epoch  200 · hider_loss=0.0922 · <span className="t-hl">PSNR=38.4dB ✓</span></div>
                  <div><span className="t-prompt">❯ </span><span className="t-cmd">python -m core.neural.registry export --onnx</span></div>
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
                  <span className="gmet-val" style={{ color: 'var(--white)', fontSize: '16px', fontFamily: 'var(--font-mono)', letterSpacing: '0' }}>ONNX · GPU / CPU</span>
                  <span className="gmet-lbl" style={{ display: 'block', marginTop: '4px' }}>Inference runtime</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── STACK ── */}
      <section id="stack">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Technology</p>
            <h2 className="section-title">Built on the right tools.</h2>
            <p className="section-body">
              Two terminals run everything.{' '}
              <span className="mono">uvicorn</span> for the backend,{' '}
              <span className="mono">npm run dev</span> for the frontend.
            </p>
          </div>
          <div className="stack-list fade-up d1">
            {[
              { icon: '⚡', name: 'FastAPI', role: 'Async backend' },
              { icon: '⚛️', name: 'React + Vite', role: 'Frontend SPA' },
              { icon: '🔷', name: 'TypeScript', role: 'Type safety' },
              { icon: '🧮', name: 'NumPy / CuPy', role: 'Math compute' },
              { icon: '🔦', name: 'PyTorch', role: 'GAN training' },
              { icon: '📦', name: 'ONNX Runtime', role: 'Inference' },
              { icon: '🖼️', name: 'OpenCV / PIL', role: 'Image processing' },
              { icon: '🎵', name: 'Librosa', role: 'Audio analysis' },
              { icon: '🌐', name: 'Scapy', role: 'Packet crafting' },
              { icon: '🔑', name: 'cryptography', role: 'AES / Ed25519' },
              { icon: '🗄️', name: 'SQLAlchemy', role: 'ORM / SQLite' },
              { icon: '🔒', name: 'Argon2-cffi', role: 'Key derivation' },
            ].map((s) => (
              <div className="stack-item" key={s.name}>
                <div className="stack-icon">{s.icon}</div>
                <div>
                  <span className="stack-name">{s.name}</span>
                  <span className="stack-role">{s.role}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TEAM ── */}
      <section id="team">
        <div className="container">
          <div className="fade-up">
            <p className="section-label">Team</p>
            <h2 className="section-title">Two developers.<br />No overlaps.</h2>
            <p className="section-body">
              File ownership is hard-enforced. Nobody touches a file they don't
              own. Daily PRs merge only on green tests.
            </p>
          </div>
          <div className="team-grid fade-up d1">
            {[
              {
                avatar: '⚙️', tag: 'Dev A · GPU / Neural', name: 'Core Compute Lead',
                desc: <>Owns the GAN pipeline, GPU acceleration via CuPy, ONNX export, and the shared <span className="mono">compute/backend.py</span> contract established on Day 1.</>,
                branch: 'a/day1 → a/day2 → …',
              },
              {
                avatar: '🔧', tag: 'Dev B · Backend / Infra', name: 'Platform Lead',
                desc: 'Owns FastAPI routes, WebSocket layer, database models, crypto, tunnel protocols, and the full React + Vite frontend scaffold.',
                branch: 'b/day1 → b/day2 → …',
              },
              {
                avatar: '🐙', tag: 'Repository', name: 'github.com/\nCryptocrushers-ah/StegXtreme',
                desc: <>Single mono-repo. Daily branch → PR → merge-on-green. Shared contract in <span className="mono">core/compute/backend.py</span> — signatures frozen after Day 1.</>,
                branch: 'main ← a/* · b/*',
              },
            ].map((t) => (
              <div className="team-card" key={t.tag}>
                <div className="team-avatar">{t.avatar}</div>
                <div className="team-role-tag">{t.tag}</div>
                <div className="team-name" style={{ whiteSpace: 'pre-line' }}>{t.name}</div>
                <p className="team-desc">{t.desc}</p>
                <span className="team-branch">{t.branch}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer>
        <div className="footer-left">
          <span className="nav-dot" />
          StegXtreme
        </div>
        <div className="footer-right">
          github.com/Cryptocrushers-ah/StegXtreme · v2.0
        </div>
      </footer>
    </div>
  );
};

export default LandingTab;