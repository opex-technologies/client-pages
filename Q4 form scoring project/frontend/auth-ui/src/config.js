/**
 * Application Configuration
 * Environment-based configuration for Auth UI
 * Created: November 5, 2025
 */

// API Base URL - Update this when deploying to Cloud Functions
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const config = {
  // API Endpoints
  api: {
    baseUrl: API_BASE_URL,
    endpoints: {
      register: `${API_BASE_URL}/auth/register`,
      login: `${API_BASE_URL}/auth/login`,
      refresh: `${API_BASE_URL}/auth/refresh`,
      logout: `${API_BASE_URL}/auth/logout`,
      verify: `${API_BASE_URL}/auth/verify`,
      me: `${API_BASE_URL}/auth/me`,
    }
  },

  // Token Storage Keys
  storage: {
    accessToken: 'opex_access_token',
    refreshToken: 'opex_refresh_token',
    user: 'opex_user'
  },

  // Password Requirements (must match backend)
  password: {
    minLength: 8,
    requireUppercase: true,
    requireLowercase: true,
    requireDigit: true,
    requireSpecial: true
  },

  // Token Expiration (in seconds)
  tokenExpiration: {
    access: 86400,  // 24 hours
    refresh: 2592000  // 30 days
  }
};

export default config;
