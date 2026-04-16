import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL + '/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const data = error.response?.data;
    if (data?.error?.code === 'AUTH_REQUIRED' || data?.error?.code === 'AUTH_INVALID_TOKEN') {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(data?.error || { code: 'UNKNOWN', message: 'Произошла ошибка' });
  }
);

export default api;
