import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from './store/authStore';
import LoginModal from './components/LoginModal';
import EmbedTab from './components/EmbedTab';
import ExtractTab from './components/ExtractTab';
import AnalyzeTab from './components/AnalyzeTab';
import VisualiseTab from './components/VisualiseTab';
import TunnelTab from './components/TunnelTab';
import LandingTab from './components/LandingTab';
import ModelStats from './components/ModelStats';
import GpuStatus from './components/GpuStatus';
import WelcomeSplash from './components/WelcomeSplash';
import './App.css';

type Tab = 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel';

/* ── Star-warp canvas hook — same engine as LandingTab ── */
function useStarCanvas(canvasRef: React.RefObject<HTMLCanvasElement | null>, active: boolean) {
  const animRef = useRef<number>(0);

  useEffect(() => {
    if (!active) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    let width = window.innerWidth;
    let height = window.innerHeight;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    resize();
    window.addEventListener('resize', resize);

    interface Star {
      x: number; y: number; z: number; pz: number;
      r: number; g: number; b: number; size: number;
    }

    const randomTint = (): [number, number, number] => {
      const roll = Math.random();
      if (roll > 0.88) return [0, 255, 224];
      if (roll > 0.78) return [180, 150, 255];
      return [210, 220, 255];
    };

    const spawnStar = (): Star => {
      const [r, g, b] = randomTint();
      return {
        x: (Math.random() - 0.5) * 2,
        y: (Math.random() - 0.5) * 2,
        z: Math.random(), pz: Math.random(),
        r, g, b, size: Math.random() * 1.2 + 0.3,
      };
    };

    const SPEED = 0.004;
    const stars: Star[] = Array.from({ length: 500 }, spawnStar);

    const draw = () => {
      ctx.fillStyle = 'rgba(4,4,10,0.22)';
      ctx.fillRect(0, 0, width, height);

      const cx = width / 2, cy = height / 2;

      for (const s of stars) {
        s.pz = s.z;
        s.z -= SPEED;
        if (s.z <= 0) {
          s.x = (Math.random() - 0.5) * 2;
          s.y = (Math.random() - 0.5) * 2;
          s.z = 1; s.pz = 1;
          const [r, g, b] = randomTint();
          s.r = r; s.g = g; s.b = b;
          s.size = Math.random() * 1.2 + 0.3;
          continue;
        }

        const scale = 1 / s.z;
        const sx = cx + s.x * scale * cx;
        const sy = cy + s.y * scale * cy;
        const pScale = 1 / s.pz;
        const px = cx + s.x * pScale * cx;
        const py = cy + s.y * pScale * cy;

        const brightness = 1 - s.z;
        const alpha = Math.min(brightness * 1.4, 1);
        const radius = s.size * brightness * 2.2;

        if (s.pz < 1) {
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(sx, sy);
          ctx.strokeStyle = `rgba(${s.r},${s.g},${s.b},${alpha * 0.7})`;
          ctx.lineWidth = radius * 0.6;
          ctx.lineCap = 'round';
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(sx, sy, Math.max(radius * 0.5, 0.4), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${s.r},${s.g},${s.b},${alpha})`;
        ctx.fill();

        if (brightness > 0.7) {
          const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, radius * 2.5);
          glow.addColorStop(0, `rgba(${s.r},${s.g},${s.b},${(brightness - 0.7) * 0.25})`);
          glow.addColorStop(1, `rgba(${s.r},${s.g},${s.b},0)`);
          ctx.beginPath();
          ctx.arc(sx, sy, radius * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = glow;
          ctx.fill();
        }
      }

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', resize);
    };
  }, [active, canvasRef]);
}

/* ── Nav config ── */
const NAV: { id: Tab; icon: string; label: string }[] = [
  { id: 'embed', icon: '↓', label: 'Embed' },
  { id: 'extract', icon: '↑', label: 'Extract' },
  { id: 'analyze', icon: '⌕', label: 'Analyze' },
  { id: 'visualise', icon: '◎', label: 'Visualise' },
  { id: 'tunnel', icon: '⇌', label: 'Tunnel' },
];

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('embed');
  const [showLogin, setShowLogin] = useState(false);
  const [showSplash, setShowSplash] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();

  const canvasRef = useRef<HTMLCanvasElement>(null);
  // Only run star canvas while authenticated workspace is shown
  useStarCanvas(canvasRef, isAuthenticated && !showSplash);

  const handleLogout = () => { logout(); setShowLogin(false); };

  // ── Public cover (landing + login) ──
  if (!isAuthenticated || showSplash) {
    return (
      <div className="cover-page">
        {showSplash ? (
          <WelcomeSplash onComplete={() => setShowSplash(false)} />
        ) : (
          <>
            <LandingTab onNavigate={() => setShowLogin(true)} />
            {showLogin && (
              <LoginModal
                onClose={() => setShowLogin(false)}
                onAuthSuccess={() => { setShowLogin(false); setShowSplash(true); }}
              />
            )}
          </>
        )}
      </div>
    );
  }

  // ── Authenticated workspace ──
  return (
    <div className="dashboard-container">

      {/* Persistent star-warp background */}
      <canvas ref={canvasRef} className="dash-canvas" aria-hidden="true" />

      {/* ── SIDEBAR ── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-dot" />
          <div>
            <h1 onClick={() => setActiveTab('embed')}>StegXtreme</h1>
            <span className="app-subtitle">Security Suite</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV.map((n) => (
            <button
              key={n.id}
              type="button"
              className={`nav-item${activeTab === n.id ? ' active' : ''}`}
              onClick={() => setActiveTab(n.id)}
            >
              <span className="icon">{n.icon}</span>
              {n.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </aside>

      {/* ── MAIN ── */}
      <main className="main-content">

        {/* Top bar */}
        <header className="top-bar">
          <div className="top-bar-left">
            <ModelStats />
          </div>
          <div className="top-bar-right" style={{display:"flex",alignItems:"center",gap:"0.75rem"}}>
            <GpuStatus /><div className="user-badge">
              <span className="user-status-dot" />
              Admin
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="content-area">
          <div className="glass-panel">
            {activeTab === 'embed' && <EmbedTab />}
            {activeTab === 'extract' && <ExtractTab />}
            {activeTab === 'analyze' && <AnalyzeTab />}
            {activeTab === 'visualise' && <VisualiseTab />}
            {activeTab === 'tunnel' && <TunnelTab />}
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;