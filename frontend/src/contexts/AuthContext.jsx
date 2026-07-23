import { createContext, useContext, useState, useCallback } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('radassist_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isAuthenticated = !!user;

  const login = useCallback(async (apiKey) => {
    setLoading(true);
    setError(null);
    try {
      // Store the key so the interceptor picks it up
      localStorage.setItem('radassist_api_key', apiKey);
      // Validate by hitting an authenticated endpoint
      await api.get('/feedback');
      const userData = { name: 'Authenticated', apiKey };
      localStorage.setItem('radassist_user', JSON.stringify(userData));
      setUser(userData);
      return true;
    } catch (err) {
      localStorage.removeItem('radassist_api_key');
      localStorage.removeItem('radassist_user');
      setError('Invalid API key. Please check and try again.');
      setUser(null);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('radassist_api_key');
    localStorage.removeItem('radassist_user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
