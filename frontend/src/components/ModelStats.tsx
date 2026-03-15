import { useState, useEffect } from 'react';
import { apiRequest } from '../utils/api';

interface Stats {
  modules_count: number;
  api_routes_count: number;
  protocols_count: number;
  latest_psnr: string;
  gpu_enabled: boolean;
  embeds_learned: number;
  resistance_pct: number;
  is_improving: boolean;
  last_update: string;
}

export default function ModelStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiRequest('/api/stats');
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch model stats', err);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  if (!stats) return null;

  return (
    <div className="model-stats-badge">
      <div className="stat-group">
        <span className="stat-dot" style={{ background: stats.is_improving ? '#10b981' : '#64748b' }}></span>
        <span className="stat-label">Neural Engine: {stats.is_improving ? 'Active' : 'Standby'}</span>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <span className="stat-val">{stats.embeds_learned}</span>
        <span className="stat-lbl">Embeds Learned</span>
      </div>
      <div className="stat-item">
        <span className="stat-val">{stats.resistance_pct}%</span>
        <span className="stat-lbl">Resistance</span>
      </div>
      <div className="stat-item">
        <span className="stat-val">{stats.latest_psnr}</span>
        <span className="stat-lbl">Avg PSNR</span>
      </div>
    </div>
  );
}
