/**
 * Authentication Context
 * Provides authentication state and methods throughout the app
 * Created: November 5, 2025
 */

import { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const storedUser = authService.getUser();

        if (storedUser && authService.isAuthenticated()) {
          // Verify token is still valid
          const isValid = await authService.verifyToken();

          if (isValid) {
            setUser(storedUser);
          } else {
            // Token expired, try to refresh
            try {
              await authService.refreshToken();
              const currentUser = await authService.getCurrentUser();
              setUser(currentUser);
            } catch (error) {
              // Refresh failed, clear auth state
              authService.clearTokens();
              setUser(null);
            }
          }
        }
      } catch (error) {
        console.error('Auth check error:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const register = async (userData) => {
    try {
      setError(null);
      setLoading(true);

      await authService.register(userData);

      // Auto-login after registration
      const loginData = await authService.login(userData.email, userData.password);
      setUser(loginData.user);

      return loginData;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      setLoading(true);

      const data = await authService.login(email, password);
      setUser(data.user);

      return data;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setError(null);
      await authService.logout();
      setUser(null);
    } catch (error) {
      setError(error.message);
      // Clear user anyway
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
      return currentUser;
    } catch (error) {
      setError(error.message);
      throw error;
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    user,
    loading,
    error,
    register,
    login,
    logout,
    refreshUser,
    clearError,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
