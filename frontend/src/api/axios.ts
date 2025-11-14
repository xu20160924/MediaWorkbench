import axios from 'axios';
import { useUserStore } from '@/stores/user';

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const userStore = useUserStore();
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        // Handle unauthorized
        const userStore = useUserStore();
        userStore.logout();
        console.error('Authentication required: Please log in again');
        window.location.href = '/login';
      } else if (status === 403) {
        console.error('Forbidden: You do not have permission to perform this action');
      } else if (status === 404) {
        console.error('Not Found: The requested resource was not found');
      } else if (status >= 500) {
        console.error('Server Error: Please try again later');
      } else if (data && data.message) {
        console.error('Error:', data.message);
      } else {
        console.error('Request failed: Please try again');
      }
    } else if (error.request) {
      console.error('Network Error: Please check your internet connection');
    } else {
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

export default api;
