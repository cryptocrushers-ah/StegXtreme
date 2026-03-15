import { useState } from 'react';
import EmbedTab from './components/EmbedTab';
import ExtractTab from './components/ExtractTab';
import AnalyzeTab from './components/AnalyzeTab';
import VisualiseTab from './components/VisualiseTab';
import TunnelTab from './components/TunnelTab';
import './App.css';

type Tab = 'embed' | 'extract' | 'analyze' | 'visualise' | 'tunnel';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('embed');

  return (
    <div>
      <h1>StegXtreme</h1>

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
      </div>

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

