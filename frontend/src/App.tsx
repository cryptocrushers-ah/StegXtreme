import { useState } from 'react';
import { useAuthStore } from './store/authStore';
import LoginModal from './components/LoginModal';
import EmbedTab from './components/EmbedTab';
import ExtractTab from './components/ExtractTab';
import AnalyzeTab from './components/AnalyzeTab';
import VisualiseTab from './components/VisualiseTab';
import TunnelTab from './components/TunnelTab';
import TrainTab from './components/TrainTab';
import './App.css';

type Tab = 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel' | 'train';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('embed');
  const { isAuthenticated, logout } = useAuthStore();

  if (!isAuthenticated) {
    return <LoginModal />;
  }

  return (
    <div>
      <header className="app-header">
        <h1>StegXtreme</h1>
        <p className="app-subtitle">Advanced Steganography & Detection Suite</p>
        <button 
          onClick={logout} 
          className="logout-btn"
        >
          Logout
        </button>
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
        <button
          type="button"
          className={`tab-btn ${activeTab === 'train' ? 'active' : ''}`}
          onClick={() => setActiveTab('train')}
        >
          <span className="icon">🧠</span> Train
        </button>
      </nav>

      <div className="glass-panel">
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

