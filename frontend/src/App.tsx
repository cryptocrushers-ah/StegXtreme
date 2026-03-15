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
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        position: 'relative', 
        marginBottom: '2rem',
        marginTop: '1rem'
      }}>
        <h1 style={{ margin: 0 }}>StegXtreme</h1>
        <button 
          onClick={logout} 
          className="tab-btn" 
          style={{ 
            position: 'absolute', 
            right: 0,
            borderColor: 'rgba(239, 68, 68, 0.2)',
            color: '#ef4444',
            background: 'rgba(239, 68, 68, 0.05)'
          }}
          onMouseOver={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
          onMouseOut={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.05)'}
        >
          Logout
        </button>
      </div>

      <div className="tabs">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'embed' ? 'active' : ''}`}
          onClick={() => setActiveTab('embed')}
        >
          Embed Payload
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'extract' ? 'active' : ''}`}
          onClick={() => setActiveTab('extract')}
        >
          Extract Payload
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          🔍 Analyse
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'visualise' ? 'active' : ''}`}
          onClick={() => setActiveTab('visualise')}
        >
          👁️ Visualise
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'tunnel' ? 'active' : ''}`}
          onClick={() => setActiveTab('tunnel')}
        >
          🚀 Tunnel
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'train' ? 'active' : ''}`}
          onClick={() => setActiveTab('train')}
        >
          🧠 Train
        </button>
      </div>

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

