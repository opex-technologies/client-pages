/**
 * Authentication API Client
 * Handles user authentication and session management
 */

import axios from 'axios';
import config from '../config';

// Create axios instance for auth API
const authClient = axios.create({
  baseURL: config.authApiUrl,
  timeout: 15000, // 15 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach JWT token
authClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Authentication API Methods
 */
export const authAPI = {
  /**
   * Login with email and password
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} Auth tokens and user data
   */
  login: (email, password) => {
    return authClient.post('/auth/login', { email, password });
  },

  /**
   * Logout current user
   * @returns {Promise} Success message
   */
  logout: () => {
    return authClient.post('/auth/logout');
  },

  /**
   * Refresh access token
   * @param {string} refreshToken - Refresh token
   * @returns {Promise} New access token
   */
  refreshToken: (refreshToken) => {
    return authClient.post('/auth/refresh', { refresh_token: refreshToken });
  },

  /**
   * Get current user information
   * @returns {Promise} User data
   */
  getCurrentUser: () => {
    return authClient.get('/auth/user');
  },

  /**
   * Register new user (if enabled)
   * @param {Object} data - Registration data
   * @param {string} data.email - User email
   * @param {string} data.password - User password
   * @param {string} data.full_name - User full name
   * @returns {Promise} User data
   */
  register: (data) => {
    return authClient.post('/auth/register', data);
  },

  /**
   * Check user permissions
   * @param {string} permission - Permission level to check (view, edit, admin)
   * @param {string} category - Optional category filter
   * @returns {Promise} Permission check result
   */
  checkPermission: (permission, category = null) => {
    return authClient.post('/permissions/check', { permission, category });
  },
};

export default authAPI;
