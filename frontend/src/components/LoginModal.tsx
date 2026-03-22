import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import './LoginModal.css';

interface LoginModalProps {
  onClose?: () => void;
  onAuthSuccess?: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ onClose, onAuthSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const setToken = useAuthStore((state) => state.setToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username, password }),
      });

      if (!response.ok) throw new Error('Invalid username or password');

      const data = await response.json();
      setToken(data.access_token);
      onAuthSuccess?.();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-overlay" onClick={onClose}>
      <div className="login-card" onClick={(e) => e.stopPropagation()}>

        {onClose && (
          <button className="close-btn" onClick={onClose} aria-label="Close">
            &times;
          </button>
        )}

        <div className="modal-header">
          <h2>StegXtreme Access</h2>
        </div>
        <p className="subtitle">Authenticate to continue</p>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="sx-username">Username</label>
            <input
              id="sx-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoComplete="username"
              required
            />
          </div>

          <div className="input-group">
            <label htmlFor="sx-password">Password</label>
            <input
              id="sx-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Authenticating…' : 'Login'}
          </button>

          {error && <p className="login-error">{error}</p>}
        </form>

        <p className="login-footer">
          Default credentials: <code>admin</code> / <code>admin123</code>
        </p>
      </div>
    </div>
  );
};

export default LoginModal;