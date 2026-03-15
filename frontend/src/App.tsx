import { useState } from 'react';
import { useAuthStore } from './store/authStore';
import LoginModal from './components/LoginModal';
import EmbedTab from './components/EmbedTab';
import ExtractTab from './components/ExtractTab';
import AnalyzeTab from './components/AnalyzeTab';
import VisualiseTab from './components/VisualiseTab';
import TunnelTab from './components/TunnelTab';
import TrainTab from './components/TrainTab';
import LandingTab from './components/LandingTab';
import './App.css';

type Tab = 'home' | 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel' | 'train';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('home');
  const [showLogin, setShowLogin] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();

  const handleTabChange = (tab: Tab) => {
    if (tab !== 'home' && !isAuthenticated) {
      setShowLogin(true);
      return;
    }
    setActiveTab(tab);
    setShowLogin(false);
  };

  const handleLogout = () => {
    logout();
    setActiveTab('home');
  };

  return (
    <div>
      <header className="app-header">
        <h1 onClick={() => handleTabChange('home')} style={{cursor: 'pointer'}}>StegXtreme</h1>
        <p className="app-subtitle">Advanced Steganography & Detection Suite</p>
        <div className="header-actions">
          {isAuthenticated ? (
            <button 
              onClick={handleLogout} 
              className="logout-btn"
            >
              Logout
            </button>
          ) : (
            <button 
              onClick={() => setShowLogin(true)} 
              className="login-trigger-btn"
            >
              Login
            </button>
          )}
        </div>
      </header>

      <nav className="tabs">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'home' ? 'active' : ''}`}
          onClick={() => handleTabChange('home')}
        >
          <span className="icon">🏠</span> Home
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'embed' ? 'active' : ''}`}
          onClick={() => handleTabChange('embed')}
        >
          <span className="icon">📥</span> Embed
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'extract' ? 'active' : ''}`}
          onClick={() => handleTabChange('extract')}
        >
          <span className="icon">📤</span> Extract
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => handleTabChange('analyze')}
        >
          <span className="icon">🔍</span> Analyze
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'visualise' ? 'active' : ''}`}
          onClick={() => handleTabChange('visualise')}
        >
          <span className="icon">👁️</span> Visualise
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'tunnel' ? 'active' : ''}`}
          onClick={() => handleTabChange('tunnel')}
        >
          <span className="icon">🚀</span> Tunnel
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'train' ? 'active' : ''}`}
          onClick={() => handleTabChange('train')}
        >
          <span className="icon">🧠</span> Train
        </button>
      </nav>

      {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}

      <div className={`glass-panel ${activeTab === 'home' ? 'landing-panel' : ''}`}>
        {activeTab === 'home'    && <LandingTab onNavigate={handleTabChange} />}
        {activeTab === 'embed'   && <EmbedTab />}
        {activeTab === 'extract' && <ExtractTab />}
        {activeTab === 'analyze' && <AnalyzeTab />}
        {activeTab === 'visualise' && <VisualiseTab />}
        {activeTab === 'tunnel' && <TunnelTab />}
        {activeTab === 'train' && <TrainTab />}
      </div>
    </div>
  );
}

export default App;

