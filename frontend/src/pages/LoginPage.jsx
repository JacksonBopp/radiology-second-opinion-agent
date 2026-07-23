import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const [apiKey, setApiKey] = useState('');
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(apiKey);
    if (success) navigate('/upload');
  };

  return (
    <div className="login-page">
      <div className="login-card glass-card">
        <div className="login-header">
          <span className="login-logo">🩻</span>
          <h1>RadAssist</h1>
          <p>AI-Powered Radiology Second Opinion</p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="api-key-input">API Key</label>
            <input
              id="api-key-input"
              type="password"
              className="form-input"
              placeholder="Enter your API key"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              autoFocus
              required
            />
            <span className="form-hint">Your X-API-Key credential for authentication</span>
          </div>
          {error && <div className="alert alert--error">{error}</div>}
          <button
            type="submit"
            className="btn btn--primary btn--full"
            disabled={loading || !apiKey.trim()}
          >
            {loading ? (
              <span className="btn-loading">
                <span className="spinner" /> Authenticating...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>
        <div className="login-footer">
          <p>Secure authentication via X-API-Key header</p>
        </div>
      </div>
    </div>
  );
}
