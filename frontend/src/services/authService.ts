import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Create authenticated axios instance
 * Pass the Clerk auth token to get authenticated requests
 */
export const createAuthenticatedAPI = (getToken: (options?: any) => Promise<string | null>): AxiosInstance => {
  const api = axios.create({
    baseURL: API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add request interceptor to inject auth token
  api.interceptors.request.use(
    async (config) => {
      try {
        // Get token from Clerk with our custom JWT template
        const token = await getToken({ template: 'backend-api' });
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      } catch (error) {
        console.error('Error getting auth token:', error);
        return config;
      }
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor for error handling
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        console.error('Unauthorized! Redirecting to sign in...');
        // Could trigger a redirect here
      }
      return Promise.reject(error);
    }
  );

  return api;
};

/**
 * Fetch current user info from backend
 */
export const getCurrentUser = async (api: AxiosInstance) => {
  try {
    const response = await api.get('/api/auth/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching user:', error);
    throw error;
  }
};

/**
 * Check if user has police access
 */
export const checkPoliceAccess = async (api: AxiosInstance) => {
  try {
    const response = await api.get('/api/auth/police-check');
    return response.data;
  } catch (error) {
    console.error('Police access check failed:', error);
    return false;
  }
};

/**
 * Check if user has admin access
 */
export const checkAdminAccess = async (api: AxiosInstance) => {
  try {
    const response = await api.get('/api/auth/admin-check');
    return response.data;
  } catch (error) {
    console.error('Admin access check failed:', error);
    return false;
  }
};
