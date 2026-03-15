import React, { useState, useEffect, useRef } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import './TrainTab.css';

interface TrainingStep {
  step: number;
  d_loss: number;
  h_loss: number;
  epoch: number;
}

const TrainTab: React.FC = () => {
  const [data, setData] = useState<TrainingStep[]>([]);
  const [status, setStatus] = useState<'idle' | 'training' | 'complete' | 'error'>('idle');
  const [runId, setRunId] = useState('');
  
  const ws = useRef<WebSocket | null>(null);

  const startTraining = () => {
    const newRunId = `run_${Math.random().toString(36).substring(7)}`;
    setRunId(newRunId);
    setData([]);
    setStatus('training');

    const socket = new WebSocket(`ws://localhost:8000/ws/training/${newRunId}`);
    
    socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.status === 'complete') {
        setStatus('complete');
        socket.close();
      } else {
        setData((prev) => [...prev, msg].slice(-100)); // Keep last 100 steps for smoother curves
      }
    };

    socket.onclose = () => {
      if (status !== 'complete') setStatus('idle');
    };

    socket.onerror = () => {
      setStatus('error');
    };

    ws.current = socket;
  };

  useEffect(() => {
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const currentMetrics = data.length > 0 ? data[data.length - 1] : { epoch: 0, step: 0, d_loss: 0, h_loss: 0 };

  return (
    <div className="train-container">
      <div className="train-header">
        <div>
          <h2>Neural Training Dashboard</h2>
          {runId && <div className="run-id" style={{ marginTop: '0.5rem' }}>Active Session: <strong>{runId}</strong></div>}
        </div>
        <div className="header-actions">
          <button 
            className={`train-btn ${status === 'training' ? 'training' : ''}`} 
            onClick={startTraining}
            disabled={status === 'training'}
          >
            {status === 'training' ? 'Training in Progress...' : 'Initialize Training'}
          </button>
        </div>
      </div>

      <div className="chart-section">
        <div className="chart-card">
          <h3>
            <span role="img" aria-label="chart">📊</span> 
            Adversarial Loss Convergeance
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis 
                dataKey="step" 
                stroke="#64748b" 
                tick={{fontSize: 12}}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#64748b"
                tick={{fontSize: 12}}
                tickLine={false}
                axisLine={false}
                domain={[0, 'auto']}
              />
              <Tooltip 
                contentStyle={{ 
                  background: 'rgba(15, 23, 42, 0.9)', 
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  backdropFilter: 'blur(8px)'
                }}
                itemStyle={{ fontSize: '12px', fontWeight: 600 }}
              />
              <Legend verticalAlign="top" align="right" height={36} />
              <Line 
                type="monotone" 
                dataKey="d_loss" 
                name="Discriminator" 
                stroke="#f43f5e" 
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 6, strokeWidth: 0 }}
                animationDuration={0}
              />
              <Line 
                type="monotone" 
                dataKey="h_loss" 
                name="Hider (GAN)" 
                stroke="#38bdf8" 
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 6, strokeWidth: 0 }}
                animationDuration={0} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="training-stats">
        <div className="stat-card">
          <span>Current Epoch</span>
          <strong>{currentMetrics.epoch}</strong>
        </div>
        <div className="stat-card">
          <span>Total Steps</span>
          <strong>{currentMetrics.step}</strong>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #38bdf8' }}>
          <span>H-Loss Efficiency</span>
          <strong style={{color: '#38bdf8'}}>{currentMetrics.h_loss.toFixed(6)}</strong>
        </div>
        <div className="stat-card" style={{ borderLeft: '4px solid #f43f5e' }}>
          <span>D-Loss Stability</span>
          <strong style={{color: '#f43f5e'}}>{currentMetrics.d_loss.toFixed(6)}</strong>
        </div>
      </div>
    </div>
  );
};

export default TrainTab;
