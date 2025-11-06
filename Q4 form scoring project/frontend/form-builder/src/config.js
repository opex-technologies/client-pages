/**
 * Application Configuration
 * Centralizes environment variable access
 */

export const config = {
  // API URLs
  apiUrl: import.meta.env.VITE_API_URL || 'https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/form-builder-api',
  authApiUrl: import.meta.env.VITE_AUTH_API_URL || 'https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/auth-api',

  // Environment
  env: import.meta.env.VITE_ENV || 'development',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,

  // Application Info
  appName: 'Form Builder',
  appVersion: '1.0.0',

  // Opex Branding
  colors: {
    navy: '#1a2859',
    cyan: '#00c4cc',
    gray: '#6b7280',
  },

  // Logo URL (from existing Cloud Storage)
  logoUrl: 'https://storage.googleapis.com/opex-web-forms-20250716-145646/opex-logo.avif',
};

export default config;
