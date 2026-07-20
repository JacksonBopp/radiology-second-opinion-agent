import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach API key from localStorage to every request
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('radassist_api_key');
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('radassist_api_key');
      localStorage.removeItem('radassist_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
