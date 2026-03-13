import { useState } from 'react';
import EmbedTab from './components/EmbedTab';
import ExtractTab from './components/ExtractTab';
import './App.css'; // Might be unneeded if index.css is used but keeping just in case

function App() {
  const [activeTab, setActiveTab] = useState<'embed' | 'extract'>('embed');

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
      </div>

      <div className="glass-panel">
        {activeTab === 'embed' && <EmbedTab />}
        {activeTab === 'extract' && <ExtractTab />}
      </div>
    </div>
  );
}

export default App;
