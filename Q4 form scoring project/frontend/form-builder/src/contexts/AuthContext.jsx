/**
 * Authentication Context
 * Provides authentication state and methods throughout the application
 */

import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/authApi';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = () => {
      const storedToken = localStorage.getItem('authToken');
      const storedUser = localStorage.getItem('user');

      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setToken(storedToken);
          setUser(parsedUser);
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Failed to parse stored user:', error);
          logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  /**
   * Login user
   */
  const login = async (email, password) => {
    try {
      const response = await authAPI.login(email, password);

      if (response.data.success) {
        const { access_token, user: userData } = response.data.data;

        // Store in state
        setToken(access_token);
        setUser(userData);
        setIsAuthenticated(true);

        // Store in localStorage
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('user', JSON.stringify(userData));

        toast.success('Login successful!');
        return { success: true, user: userData };
      }
    } catch (error) {
      console.error('Login failed:', error);
      const message = error.response?.data?.error?.message || 'Login failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  /**
   * Logout user
   */
  const logout = async () => {
    try {
      // Call logout API (optional - fails silently if token already invalid)
      await authAPI.logout().catch(() => {});
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Clear state
      setToken(null);
      setUser(null);
      setIsAuthenticated(false);

      // Clear localStorage
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');

      toast.success('Logged out successfully');
    }
  };

  /**
   * Check if user has specific permission
   */
  const hasPermission = (requiredPermission) => {
    if (!user?.permissions) return false;

    const permissionLevels = {
      'view': 1,
      'edit': 2,
      'admin': 3,
    };

    const userLevel = permissionLevels[user.permissions] || 0;
    const requiredLevel = permissionLevels[requiredPermission] || 0;

    return userLevel >= requiredLevel;
  };

  /**
   * Refresh user data from API
   */
  const refreshUser = async () => {
    try {
      const response = await authAPI.getCurrentUser();
      if (response.data.success) {
        const userData = response.data.data;
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
      // If refresh fails with 401, logout
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const value = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    hasPermission,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
