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
import './App.css';

type Tab = 'home' | 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('embed');
  const [showLogin, setShowLogin] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    // After logout, the App component will re-render and show the public cover
    // No need to set activeTab here as the entire view changes
  };

  // Public Cover View (Landing Page)
  if (!isAuthenticated) {
    return (
      <div className="cover-page">
        <LandingTab onNavigate={() => setShowLogin(true)} />
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
      </div>
    );
  }

  // Private Dashboard View (Forensic Suite)
  return (
    <div className="dashboard-container">
      <header className="app-header">
        <div className="header-left"></div>
        <div className="header-center">
          <h1 onClick={() => setActiveTab('embed')} style={{cursor: 'pointer'}}>StegXtreme</h1>
          <p className="app-subtitle">Advanced Steganography & Detection Suite</p>
          <ModelStats />
        </div>
        <div className="header-actions">
          <button 
            onClick={handleLogout} 
            className="logout-btn"
          >
            Logout
          </button>
        </div>
      </header>

      <nav className="tabs">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'embed' ? 'active' : ''}`}
          onClick={() => setActiveTab('embed')}
        >
          <span className="icon">📥</span> Embed
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'extract' ? 'active' : ''}`}
          onClick={() => setActiveTab('extract')}
        >
          <span className="icon">📤</span> Extract
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          <span className="icon">🔍</span> Analyze
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'visualise' ? 'active' : ''}`}
          onClick={() => setActiveTab('visualise')}
        >
          <span className="icon">👁️</span> Visualise
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'tunnel' ? 'active' : ''}`}
          onClick={() => setActiveTab('tunnel')}
        >
          <span className="icon">🚀</span> Tunnel
        </button>
      </nav>

      <div className="glass-panel">
        {activeTab === 'embed'   && <EmbedTab />}
        {activeTab === 'extract' && <ExtractTab />}
        {activeTab === 'analyze' && <AnalyzeTab />}
        {activeTab === 'visualise' && <VisualiseTab />}
        {activeTab === 'tunnel' && <TunnelTab />}
      </div>
    </div>
  );
}

export default App;

