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
import './App.css';

type Tab = 'home' | 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('embed');
  const [showLogin, setShowLogin] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let t = 0;

    const waves = [
      { color: [255, 255, 255], alpha: 0.18, speed: 0.00055, amp: 0.22, base: 0.45, freq: 1.4,  offset: 0.0 },
      { color: [255, 255, 255], alpha: 0.14, speed: 0.00040, amp: 0.18, base: 0.55, freq: 1.1,  offset: 2.1 },
      { color: [255, 255, 255], alpha: 0.16, speed: 0.00065, amp: 0.20, base: 0.38, freq: 1.7,  offset: 1.1 },
      { color: [255, 255, 255], alpha: 0.12, speed: 0.00048, amp: 0.15, base: 0.65, freq: 0.9,  offset: 3.5 },
      { color: [255, 255, 255], alpha: 0.10, speed: 0.00035, amp: 0.25, base: 0.30, freq: 2.0,  offset: 0.7 },
      { color: [255, 255, 255], alpha: 0.09, speed: 0.00070, amp: 0.14, base: 0.72, freq: 1.3,  offset: 4.2 },
    ];

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const draw = () => {
      const W = canvas.width;
      const H = canvas.height;
      ctx.clearRect(0, 0, W, H);

      waves.forEach((w) => {
        const STEPS = 120;
        const dx    = W / STEPS;
        ctx.beginPath();
        for (let i = 0; i <= STEPS; i++) {
          const x = i * dx;
          const y = H * (w.base
            + Math.sin(i * w.freq * (Math.PI * 2 / STEPS) + t * w.speed * 120 + w.offset) * w.amp
            + Math.sin(i * w.freq * 0.5 * (Math.PI * 2 / STEPS) + t * w.speed * 72 + w.offset + 1) * w.amp * 0.4);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(${w.color[0]},${w.color[1]},${w.color[2]},${w.alpha * 0.6})`;
        ctx.lineWidth   = 60;
        ctx.stroke();
      });

      t += 1;
      animId = requestAnimationFrame(draw);
    };

    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, [isAuthenticated]);

  const handleLogout = () => {
    logout();
    // After logout, the App component will re-render and show the public cover
    // No need to set activeTab here as the entire view changes
  };

  // Public Cover View (Landing Page)
  if (!isAuthenticated) {
    return (
      <div className="cover-page">
        <canvas ref={canvasRef} className="hero-wave-canvas" />
        <LandingTab onNavigate={() => setShowLogin(true)} />
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
      </div>
    );
  }

  // Private Dashboard View (Forensic Suite)
  return (
    <div className="dashboard-container">
      <canvas ref={canvasRef} className="hero-wave-canvas dashboard-waves" />
      
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 onClick={() => setActiveTab('embed')} style={{cursor: 'pointer'}}>StegXtreme</h1>
          <p className="app-subtitle">Security Suite</p>
        </div>
        
        <nav className="sidebar-nav">
          <button
            type="button"
            className={`nav-item ${activeTab === 'embed' ? 'active' : ''}`}
            onClick={() => setActiveTab('embed')}
          >
            <span className="icon">📥</span> Embed
          </button>
          <button
            type="button"
            className={`nav-item ${activeTab === 'extract' ? 'active' : ''}`}
            onClick={() => setActiveTab('extract')}
          >
            <span className="icon">📤</span> Extract
          </button>
          <button
            type="button"
            className={`nav-item ${activeTab === 'analyze' ? 'active' : ''}`}
            onClick={() => setActiveTab('analyze')}
          >
            <span className="icon">🔍</span> Analyze
          </button>
          <button
            type="button"
            className={`nav-item ${activeTab === 'visualise' ? 'active' : ''}`}
            onClick={() => setActiveTab('visualise')}
          >
            <span className="icon">👁️</span> Visualise
          </button>
          <button
            type="button"
            className={`nav-item ${activeTab === 'tunnel' ? 'active' : ''}`}
            onClick={() => setActiveTab('tunnel')}
          >
            <span className="icon">🚀</span> Tunnel
          </button>
        </nav>

        <div className="sidebar-footer">
          <button 
            onClick={handleLogout} 
            className="logout-btn"
          >
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="top-bar">
          <div className="top-bar-left">
            <ModelStats />
          </div>
          <div className="top-bar-right">
            <div className="user-badge">
              <span className="user-status-dot"></span>
              Admin
            </div>
          </div>
        </header>

        <div className="content-area">
          <div className="glass-panel">
            {activeTab === 'embed'   && <EmbedTab />}
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

