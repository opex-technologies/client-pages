/**
 * Authentication Service
 * Handles all API calls to the authentication backend
 * Created: November 5, 2025
 */

import config from '../config';

class AuthService {
  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @param {string} userData.email - User email
   * @param {string} userData.password - User password
   * @param {string} userData.full_name - User full name
   * @returns {Promise<Object>} User data
   */
  async register(userData) {
    const response = await fetch(config.api.endpoints.register, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || 'Registration failed');
    }

    return data.data;
  }

  /**
   * Login user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise<Object>} Tokens and user data
   */
  async login(email, password) {
    const response = await fetch(config.api.endpoints.login, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || 'Login failed');
    }

    // Store tokens
    this.setTokens(data.data.access_token, data.data.refresh_token);
    this.setUser(data.data.user);

    return data.data;
  }

  /**
   * Refresh access token
   * @returns {Promise<string>} New access token
   */
  async refreshToken() {
    const refreshToken = this.getRefreshToken();

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(config.api.endpoints.refresh, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Refresh token is invalid, clear everything
      this.logout();
      throw new Error(data.error?.message || 'Token refresh failed');
    }

    // Update access token
    this.setAccessToken(data.data.access_token);

    return data.data.access_token;
  }

  /**
   * Logout user
   */
  async logout() {
    const refreshToken = this.getRefreshToken();

    // Try to revoke token on backend
    if (refreshToken) {
      try {
        await fetch(config.api.endpoints.logout, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch (error) {
        // Ignore errors, clear local storage anyway
        console.error('Logout error:', error);
      }
    }

    // Clear local storage
    this.clearTokens();
  }

  /**
   * Get current user info
   * @returns {Promise<Object>} User data
   */
  async getCurrentUser() {
    const accessToken = this.getAccessToken();

    if (!accessToken) {
      throw new Error('No access token available');
    }

    const response = await fetch(config.api.endpoints.me, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 401) {
        // Try to refresh token
        try {
          await this.refreshToken();
          // Retry the request
          return this.getCurrentUser();
        } catch (error) {
          throw new Error('Session expired');
        }
      }

      throw new Error(data.error?.message || 'Failed to get user');
    }

    this.setUser(data.data);
    return data.data;
  }

  /**
   * Verify if access token is valid
   * @returns {Promise<boolean>} True if valid
   */
  async verifyToken() {
    const accessToken = this.getAccessToken();

    if (!accessToken) {
      return false;
    }

    try {
      const response = await fetch(config.api.endpoints.verify, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ access_token: accessToken }),
      });

      const data = await response.json();

      return data.data?.valid || false;
    } catch (error) {
      return false;
    }
  }

  // Token management helpers

  setTokens(accessToken, refreshToken) {
    localStorage.setItem(config.storage.accessToken, accessToken);
    localStorage.setItem(config.storage.refreshToken, refreshToken);
  }

  setAccessToken(accessToken) {
    localStorage.setItem(config.storage.accessToken, accessToken);
  }

  getAccessToken() {
    return localStorage.getItem(config.storage.accessToken);
  }

  getRefreshToken() {
    return localStorage.getItem(config.storage.refreshToken);
  }

  setUser(user) {
    localStorage.setItem(config.storage.user, JSON.stringify(user));
  }

  getUser() {
    const userJson = localStorage.getItem(config.storage.user);
    return userJson ? JSON.parse(userJson) : null;
  }

  clearTokens() {
    localStorage.removeItem(config.storage.accessToken);
    localStorage.removeItem(config.storage.refreshToken);
    localStorage.removeItem(config.storage.user);
  }

  isAuthenticated() {
    return !!this.getAccessToken();
  }
}

export default new AuthService();
