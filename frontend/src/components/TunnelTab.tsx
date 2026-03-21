import React, { useState, useEffect, useRef } from 'react';
import './TunnelTab.css';
import { apiRequest } from '../utils/api';
import { useTunnelReceiver } from '../hooks/useTunnelReceiver';

interface TrafficLog {
  direction: 'IN' | 'OUT';
  protocol: string;
  payload: string;
  target?: string;
  timestamp: number;
}

const TunnelTab: React.FC = () => {
  const [mode, setMode] = useState<'send' | 'receive'>('send');
  const [protocol, setProtocol] = useState<'dns' | 'http'>('http');
  const [target, setTarget] = useState('');
  const [payload, setPayload] = useState('');
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const [logs, setLogs] = useState<TrafficLog[]>([]);
  const [status, setStatus] = useState<'idle' | 'sending' | 'error'>('idle');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const receiver = useTunnelReceiver();
  
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
    if (payload.length > 50000) {
      setError('Payload too large for secure tunneling (Max 50KB).');
      return;
    }
    
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
        <div className="header-top">
          <div>
            <h2>Covert Communications</h2>
            <p>Exfiltrate data through established protocols using advanced tunneling techniques.</p>
          </div>
          <div className="mode-toggle">
            <button 
              className={`mode-btn ${mode === 'send' ? 'active' : ''}`}
              onClick={() => setMode('send')}
            >
              Send Mode
            </button>
            <button 
              className={`mode-btn ${mode === 'receive' ? 'active' : ''}`}
              onClick={() => setMode('receive')}
            >
              Receive Mode
            </button>
          </div>
        </div>
      </div>

      <div className="tunnel-dashboard">
        {mode === 'send' ? (
          <div className="tunnel-controls glass-panel">
            <h3>Tunnel Configuration (Sender)</h3>
            
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
                placeholder={protocol === 'dns' ? '8.8.8.8' : 'http://192.168.1.105:9000'} 
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
            {error && <div className="error-message" style={{ marginTop: '1rem' }}>{error}</div>}
          </div>
        ) : (
          <div className="tunnel-controls glass-panel">
            <div className="controls-header">
              <h3>Tunnel Receiver</h3>
              <div className={`status-badge ${receiver.isListening ? 'listening' : 'stopped'}`}>
                <span className="dot"></span>
                {receiver.isListening ? 'Listening' : 'Stopped'}
              </div>
            </div>
            
            <div className="form-group">
              <label>Receiver Port</label>
              <input 
                type="number" 
                value={receiver.port}
                onChange={(e) => receiver.setPort(parseInt(e.target.value))}
                disabled={receiver.isListening}
              />
            </div>

            {!receiver.isListening ? (
              <button 
                className="start-listen-btn"
                onClick={() => receiver.startListening(receiver.port)}
                disabled={receiver.loading}
              >
                {receiver.loading ? 'Starting...' : 'Start Listening'}
              </button>
            ) : (
              <button 
                className="stop-listen-btn"
                onClick={() => receiver.stopListening()}
                disabled={receiver.loading}
              >
                Stop Listening
              </button>
            )}

            {receiver.isListening && (
              <div className="lan-info animate-in">
                <label>Shareable LAN Address</label>
                <div className="copy-box">
                  <code>{receiver.shareableUrl}</code>
                  <button 
                    className="copy-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(receiver.shareableUrl);
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                  >
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <p className="share-hint">Share this address with the sender</p>
              </div>
            )}

            <div className="firewall-warning">
              <span className="icon">⚠️</span>
              <div>
                <strong>Firewall Alert</strong>
                <p>Run this as Admin if connections are blocked:</p>
                <code>netsh advfirewall firewall add rule name="StegXtreme Tunnel" dir=in action=allow protocol=TCP localport={receiver.port}</code>
              </div>
            </div>

            {receiver.error && <div className="error-message">{receiver.error}</div>}
          </div>
        )}

        <div className="traffic-monitor glass-panel">
          <div className="monitor-header">
            <h3>{mode === 'send' ? 'Live Packet Inspector' : 'Incoming Message Feed'}</h3>
            {mode === 'receive' && (
              <button className="clear-btn" onClick={receiver.clearAll}>
                Clear All
              </button>
            )}
            <span className="session-pill">
              {mode === 'send' ? `Session: ${sessionId}` : `${receiver.messages.length} Messages`}
            </span>
          </div>

          <div className="terminal-monitor">
            {mode === 'send' ? (
              logs.length === 0 ? (
                <div className="empty-terminal">
                  <span className="cursor">_</span>
                  <p>Enter target and message to <span>begin covert tunnel</span></p>
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
              )
            ) : (
              receiver.messages.length === 0 ? (
                <div className="empty-terminal">
                  <span className="cursor">_</span>
                  <p>Waiting for <span>covert incoming messages...</span></p>
                </div>
              ) : (
                <div className="message-feed">
                  {receiver.messages.map((msg) => (
                    <div key={msg.id} className="message-card animate-in">
                      <div className="msg-header">
                        <span className="msg-time">{msg.timestamp}</span>
                        <span className="msg-proto">{msg.protocol}</span>
                      </div>
                      <div className="msg-body">
                        {msg.payload}
                      </div>
                      <div className="msg-footer">
                        <span>From: {msg.sender_ip}</span>
                        <span>SID: {msg.session_id}</span>
                        <span>{msg.decode_time_ms}ms</span>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TunnelTab;
