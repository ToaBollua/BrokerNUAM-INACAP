import axios from 'axios';

// URL de backend configurada por Docker/Env
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://backend:8000/api/';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export default api;
