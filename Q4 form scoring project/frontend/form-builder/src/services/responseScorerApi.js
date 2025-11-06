/**
 * Response Scorer API Client
 * Handles all API calls to the Response Scorer backend
 */

import axios from 'axios';

// Create axios instance for Response Scorer API
const apiClient = axios.create({
  baseURL: 'https://us-central1-opex-data-lake-k23k4y98m.cloudfunctions.net/response-scorer-api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle auth errors
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const responseScorerAPI = {
  /**
   * Submit a response (PUBLIC - no auth required)
   * @param {Object} data - Response submission data
   * @param {string} data.template_id - Template ID
   * @param {Object} data.answers - Dictionary of question_id -> answer_value
   * @param {string} [data.submitter_email] - Optional submitter email
   * @param {string} [data.submitter_name] - Optional submitter name
   * @returns {Promise} Response with scoring results
   */
  submitResponse: (data) => apiClient.post('/responses/submit', data),

  /**
   * List all responses with optional filtering
   * @param {Object} params - Query parameters
   * @param {string} [params.template_id] - Filter by template
   * @param {string} [params.opportunity_type] - Filter by opportunity type
   * @param {string} [params.submitter_email] - Filter by submitter
   * @param {number} [params.page] - Page number (default: 1)
   * @param {number} [params.page_size] - Items per page (default: 50)
   * @returns {Promise} List of responses with pagination
   */
  getResponses: (params = {}) => apiClient.get('/responses', { params }),

  /**
   * Get detailed response information
   * @param {string} responseId - Response ID
   * @returns {Promise} Response details with answers
   */
  getResponse: (responseId) => apiClient.get(`/responses/${responseId}`),

  /**
   * Delete a response (admin only)
   * @param {string} responseId - Response ID
   * @returns {Promise} Success message
   */
  deleteResponse: (responseId) => apiClient.delete(`/responses/${responseId}`),

  /**
   * Get analytics summary
   * @returns {Promise} Overall analytics data
   */
  getAnalyticsSummary: () => apiClient.get('/analytics/summary'),

  /**
   * Get analytics for a specific template
   * @param {string} templateId - Template ID
   * @returns {Promise} Template-specific analytics
   */
  getTemplateAnalytics: (templateId) => apiClient.get(`/analytics/template/${templateId}`),

  /**
   * Export responses to CSV
   * @param {Object} params - Query parameters for filtering
   * @returns {Promise} CSV data
   */
  exportResponses: (params = {}) => apiClient.get('/analytics/responses/export', { params }),
};

/**
 * Extract error message from API response
 * @param {Error} error - Axios error object
 * @returns {string} Human-readable error message
 */
export const getErrorMessage = (error) => {
  if (error.response?.data?.error?.message) {
    return error.response.data.error.message;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export default responseScorerAPI;
