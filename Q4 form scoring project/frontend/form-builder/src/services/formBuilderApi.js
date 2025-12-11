/**
 * Form Builder API Client
 * Handles all communication with the Form Builder backend API
 */

import axios from 'axios';
import config from '../config';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: config.apiUrl,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach JWT token to all requests
apiClient.interceptors.request.use(
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

// Response interceptor - handle common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    // Handle 403 Forbidden - insufficient permissions
    if (error.response?.status === 403) {
      console.error('Insufficient permissions:', error.response.data);
    }

    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message);
    }

    return Promise.reject(error);
  }
);

/**
 * Form Builder API Methods
 */
export const formBuilderAPI = {
  // ==================== TEMPLATES ====================

  /**
   * Get list of templates with optional filtering and pagination
   * @param {Object} params - Query parameters
   * @param {string} params.opportunity_type - Filter by opportunity type
   * @param {string} params.opportunity_subtype - Filter by subtype
   * @param {string} params.status - Filter by status (draft, published, archived)
   * @param {string} params.created_by - Filter by creator user_id
   * @param {number} params.page - Page number (default: 1)
   * @param {number} params.page_size - Items per page (default: 20)
   * @returns {Promise} List of templates
   */
  getTemplates: (params = {}) => {
    return apiClient.get('/form-builder/templates', { params });
  },

  /**
   * Get single template by ID
   * @param {string} templateId - Template UUID
   * @returns {Promise} Template with full details including questions
   */
  getTemplate: (templateId) => {
    return apiClient.get(`/form-builder/templates/${templateId}`);
  },

  /**
   * Create new template
   * @param {Object} data - Template data
   * @param {string} data.template_name - Template name (required)
   * @param {string} data.opportunity_type - Opportunity type (required)
   * @param {string} data.opportunity_subtype - Opportunity subtype (required)
   * @param {string} data.description - Template description (optional)
   * @param {Array} data.questions - Array of questions with weights
   * @returns {Promise} Created template
   */
  createTemplate: (data) => {
    return apiClient.post('/form-builder/templates', data);
  },

  /**
   * Update existing template
   * @param {string} templateId - Template UUID
   * @param {Object} data - Updated template data
   * @returns {Promise} Updated template
   */
  updateTemplate: (templateId, data) => {
    return apiClient.put(`/form-builder/templates/${templateId}`, data);
  },

  /**
   * Delete template
   * @param {string} templateId - Template UUID
   * @returns {Promise} Success message
   */
  deleteTemplate: (templateId) => {
    return apiClient.delete(`/form-builder/templates/${templateId}`);
  },

  /**
   * Deploy template to GitHub Pages
   * @param {string} templateId - Template UUID
   * @param {Object} data - Deployment options
   * @param {string} data.commit_message - Custom commit message (optional)
   * @returns {Promise} Deployment result with URL
   */
  deployTemplate: (templateId, data = {}) => {
    return apiClient.post(`/form-builder/templates/${templateId}/deploy`, data);
  },

  // ==================== QUESTIONS ====================

  /**
   * Get all unique question categories
   * @returns {Promise} List of categories
   */
  getQuestionCategories: () => {
    return apiClient.get('/form-builder/questions/categories');
  },

  /**
   * Query questions from database
   * @param {Object} params - Query parameters
   * @param {string} params.category - Filter by category
   * @param {string} params.opportunity_type - Filter by opportunity type
   * @param {string} params.opportunity_subtype - Filter by subtype
   * @param {string} params.search - Keyword search
   * @param {string} params.template_id - Mark questions in this template as selected
   * @param {number} params.page - Page number
   * @param {number} params.page_size - Items per page
   * @returns {Promise} List of questions
   */
  getQuestions: (params = {}) => {
    return apiClient.get('/form-builder/questions', { params });
  },

  /**
   * Get single question by ID
   * @param {string} questionId - Question ID
   * @returns {Promise} Question with usage statistics
   */
  getQuestion: (questionId) => {
    return apiClient.get(`/form-builder/questions/${questionId}`);
  },

  /**
   * Create new question
   * @param {Object} data - Question data
   * @param {string} data.question_text - Question text (required)
   * @param {string} data.category - Category (required)
   * @param {string} data.opportunity_type - Opportunity type (optional, defaults to "All")
   * @param {string} data.opportunity_subtype - Opportunity subtype (optional, defaults to "All")
   * @param {string} data.input_type - Input type: text, textarea, number, radio, select, checkbox (required)
   * @param {number|string} data.default_weight - Default weight 0-100 or "Info" (optional)
   * @param {string} data.help_text - Help text (optional)
   * @returns {Promise} Created question
   */
  createQuestion: (data) => {
    return apiClient.post('/form-builder/questions', data);
  },

  /**
   * Update existing question
   * @param {string} questionId - Question ID
   * @param {Object} data - Updated question data
   * @returns {Promise} Updated question
   */
  updateQuestion: (questionId, data) => {
    return apiClient.put(`/form-builder/questions/${questionId}`, data);
  },

  /**
   * Delete question
   * @param {string} questionId - Question ID
   * @returns {Promise} Success message
   */
  deleteQuestion: (questionId) => {
    return apiClient.delete(`/form-builder/questions/${questionId}`);
  },

  // ==================== PREVIEW ====================

  /**
   * Generate form preview HTML
   * @param {Object} data - Preview data
   * @param {string} data.template_id - Template ID to preview
   * @returns {Promise} HTML preview
   */
  previewForm: (data) => {
    return apiClient.post('/form-builder/preview', data);
  },
};

/**
 * Helper function to extract error message from API response
 * @param {Error} error - Error object from axios
 * @returns {string} User-friendly error message
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

/**
 * Helper function to check if error is a specific type
 * @param {Error} error - Error object
 * @param {number} statusCode - HTTP status code to check
 * @returns {boolean}
 */
export const isErrorStatus = (error, statusCode) => {
  return error.response?.status === statusCode;
};

export default formBuilderAPI;
