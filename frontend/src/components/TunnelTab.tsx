import React, { useState, useEffect, useRef } from 'react';
import './TunnelTab.css';
import { apiRequest } from '../utils/api';

interface TrafficLog {
  direction: 'IN' | 'OUT';
  protocol: string;
  payload: string;
  target?: string;
  timestamp: number;
}

const TunnelTab: React.FC = () => {
  const [protocol, setProtocol] = useState<'dns' | 'http'>('http');
  const [target, setTarget] = useState('');
  const [payload, setPayload] = useState('');
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const [logs, setLogs] = useState<TrafficLog[]>([]);
  const [status, setStatus] = useState<'idle' | 'sending' | 'error'>('idle');
  
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to traffic monitor websocket
    const socket = new WebSocket(`ws://localhost:8000/api/tunnel/ws/traffic/${sessionId}`);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLogs((prev) => [data, ...prev].slice(0, 50)); // Keep last 50
    };

    socket.onerror = () => {
      console.error('WebSocket error');
    };

    ws.current = socket;

    return () => {
      socket.close();
    };
  }, [sessionId]);

  const handleSend = async () => {
    if (!target || !payload) return;
    
    setStatus('sending');
    try {
      await apiRequest('/api/tunnel/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          protocol,
          payload,
          target,
          session_id: sessionId
        }),
      });
      setPayload('');
      setStatus('idle');
    } catch (err) {
      console.error(err);
      setStatus('error');
    }
  };

  return (
    <div className="tunnel-container">
      <div className="tunnel-controls">
        <div className="input-group">
          <label>Protocol</label>
          <select value={protocol} onChange={(e) => setProtocol(e.target.value as any)}>
            <option value="http">HTTP (Headers)</option>
            <option value="dns">DNS (Subdomains)</option>
          </select>
        </div>

        <div className="input-group">
          <label>Target {protocol === 'dns' ? 'IP' : 'URL'}</label>
          <input 
            type="text" 
            placeholder={protocol === 'dns' ? '8.8.8.8' : 'http://evil.com/api'} 
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label>Payload</label>
          <textarea 
            placeholder="Secret message..." 
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
          />
        </div>

        <button 
          className={`send-btn ${status}`} 
          onClick={handleSend}
          disabled={status === 'sending'}
        >
          {status === 'sending' ? 'Transmitting...' : 'Send via Tunnel'}
        </button>
      </div>

      <div className="traffic-feed">
        <h3>Live Traffic Monitor (Session: {sessionId})</h3>
        <div className="logs-container">
          {logs.length === 0 && <p className="empty-msg">No traffic detected...</p>}
          {logs.map((log, i) => (
            <div key={i} className={`log-entry ${log.direction.toLowerCase()}`}>
              <span className="timestamp">{new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
              <span className="protocol">{log.protocol}</span>
              <span className="direction">{log.direction === 'OUT' ? '➔' : '←'}</span>
              <span className="payload">[{log.payload}]</span>
              {log.target && <span className="target">to {log.target}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TunnelTab;
