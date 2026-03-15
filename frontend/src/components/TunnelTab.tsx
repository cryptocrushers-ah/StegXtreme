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
      <div className="tab-header">
        <h2>Covert Communications</h2>
        <p>Exfiltrate data through established protocols using advanced tunneling techniques.</p>
      </div>

      <div className="tunnel-dashboard">
        <div className="tunnel-controls glass-panel">
          <h3>Tunnel Configuration</h3>
          
          <div className="form-group">
            <label>Transmission Protocol</label>
            <div className="protocol-selector">
              <button 
                className={`proto-btn ${protocol === 'http' ? 'active' : ''}`}
                onClick={() => setProtocol('http')}
              >
                HTTP Headers
              </button>
              <button 
                className={`proto-btn ${protocol === 'dns' ? 'active' : ''}`}
                onClick={() => setProtocol('dns')}
              >
                DNS Subdomain
              </button>
            </div>
          </div>

          <div className="form-group">
            <label>Target Entrypoint ({protocol === 'dns' ? 'IP' : 'URL'})</label>
            <input 
              type="text" 
              placeholder={protocol === 'dns' ? '8.8.8.8' : 'https://api.target.com/v1'} 
              value={target}
              onChange={(e) => setTarget(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Covert Payload</label>
            <textarea 
              placeholder="Inject secret data sequence..." 
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              rows={4}
            />
          </div>

          <button 
            className={`send-btn ${status === 'sending' ? 'sending' : ''}`} 
            onClick={handleSend}
            disabled={status === 'sending' || !target || !payload}
          >
            {status === 'sending' ? (
              <>
                <div className="spinner" />
                Transmitting Packet...
              </>
            ) : (
              <>
                <span className="icon">📡</span> Deploy Tunnel Packet
              </>
            )}
          </button>
        </div>

        <div className="traffic-monitor glass-panel">
          <div className="monitor-header">
            <h3>Live Packet Inspector</h3>
            <span className="session-pill">Session: {sessionId}</span>
          </div>

          <div className="terminal-monitor">
            {logs.length === 0 ? (
              <div className="empty-terminal">
                <span className="cursor">_</span>
                <p>Awaiting incoming/outgoing traffic...</p>
              </div>
            ) : (
              <div className="log-list">
                {logs.map((log, i) => (
                  <div key={i} className={`log-entry ${log.direction.toLowerCase()} animate-in`}>
                    <span className="time">[{new Date(log.timestamp * 1000).toLocaleTimeString()}]</span>
                    <span className="proto">[{log.protocol}]</span>
                    <span className="arrow">{log.direction === 'OUT' ? '>>>' : '<<<'}</span>
                    <span className="data">{log.payload}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TunnelTab;
