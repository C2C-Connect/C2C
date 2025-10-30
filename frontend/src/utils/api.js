import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

export const leadsAPI = {
  create: (data) => api.post('/leads', data),
  getAll: (status) => api.get('/leads', { params: { status } }),
  getById: (id) => api.get(`/leads/${id}`),
  optIn: (id) => api.post(`/leads/${id}/opt-in`),
};

export const bidsAPI = {
  create: (data) => api.post('/bids', data),
  getByLead: (leadId) => api.get(`/bids/lead/${leadId}`),
  accept: (bidId) => api.post(`/bids/${bidId}/accept`),
};

export const photosAPI = {
  getPresignedUrl: (filename) => {
    const formData = new FormData();
    formData.append('filename', filename);
    return api.post('/photos/presigned-url', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export default api;
