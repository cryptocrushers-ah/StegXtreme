import { useState } from 'react';
import { useAuthStore } from './store/authStore';
import LoginModal from './components/LoginModal';
import EmbedTab from './components/EmbedTab';
import ExtractTab from './components/ExtractTab';
import AnalyzeTab from './components/AnalyzeTab';
import VisualiseTab from './components/VisualiseTab';
import TunnelTab from './components/TunnelTab';
import LandingTab from './components/LandingTab';
import ModelStats from './components/ModelStats';
import WelcomeSplash from './components/WelcomeSplash';
import RibbonBackground from './components/RibbonBackground';
import './App.css';

type Tab = 'home' | 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('embed');
  const [showLogin, setShowLogin] = useState(false);
  const [showSplash, setShowSplash] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();


  const handleLogout = () => {
    logout();
    // After logout, the App component will re-render and show the public cover
    // No need to set activeTab here as the entire view changes
  };

  // Public Cover View (Landing Page)
  // Public Cover View or Splash View
  if (!isAuthenticated || showSplash) {
    return (
      <div className="cover-page">
        <RibbonBackground />
        {showSplash ? (
          <WelcomeSplash onComplete={() => setShowSplash(false)} />
        ) : (
          <>
            <LandingTab onNavigate={() => setShowLogin(true)} />
            {showLogin && (
              <LoginModal 
                onClose={() => setShowLogin(false)} 
                onAuthSuccess={() => setShowSplash(true)} 
              />
            )}
          </>
        )}
      </div>
    );
  }

  // Private Dashboard View (Forensic Suite)
  return (
    <div className="dashboard-container">
      
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

