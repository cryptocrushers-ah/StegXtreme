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
        setData((prev) => [...prev, msg].slice(-50)); // Keep last 50 steps
      }
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

  return (
    <div className="train-container">
      <div className="train-header">
        <h2>Neural Network Training (GAN)</h2>
        <button 
          className={`train-btn ${status}`} 
          onClick={startTraining}
          disabled={status === 'training'}
        >
          {status === 'training' ? 'Training...' : 'Start Training'}
        </button>
        {runId && <span className="run-id">ID: {runId}</span>}
      </div>

      <div className="chart-container glass-panel">
        <h3>Live Loss Curves</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="step" 
              stroke="#94a3b8" 
              label={{ value: 'Steps', position: 'insideBottom', offset: -5 }} 
            />
            <YAxis stroke="#94a3b8" />
            <Tooltip 
              contentStyle={{ background: '#1e293b', border: '1px solid #334155' }}
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="d_loss" 
              name="Discriminator Loss" 
              stroke="#ef4444" 
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
            <Line 
              type="monotone" 
              dataKey="h_loss" 
              name="Hider Loss" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={false}
              animationDuration={300} 
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="training-stats">
        <div className="stat-card">
          <span>Current Epoch</span>
          <strong>{data.length > 0 ? data[data.length - 1].epoch : 0}</strong>
        </div>
        <div className="stat-card">
          <span>Current Step</span>
          <strong>{data.length > 0 ? data[data.length - 1].step : 0}</strong>
        </div>
        <div className="stat-card">
          <span>H-Loss</span>
          <strong style={{color: '#3b82f6'}}>{data.length > 0 ? data[data.length - 1].h_loss.toFixed(4) : '0.0000'}</strong>
        </div>
        <div className="stat-card">
          <span>D-Loss</span>
          <strong style={{color: '#ef4444'}}>{data.length > 0 ? data[data.length - 1].d_loss.toFixed(4) : '0.0000'}</strong>
        </div>
      </div>
    </div>
  );
};

export default TrainTab;
