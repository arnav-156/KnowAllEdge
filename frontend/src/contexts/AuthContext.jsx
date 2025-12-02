/**
 * Authentication Context
 * Manages authentication state across the application
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient from '../utils/apiClient';

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
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Validate authentication on mount and when auth changes
   */
  const validateAuth = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (!apiClient.isAuthenticated()) {
        setIsAuthenticated(false);
        setUser(null);
        setIsLoading(false);
        return;
      }

      const validation = await apiClient.validateAuth();

      if (validation.valid) {
        setIsAuthenticated(true);
        setUser({
          userId: validation.user_id,
          email: validation.email,
          role: validation.role,
          quotaTier: validation.quota_tier,
          createdAt: validation.created_at,
        });
      } else {
        setIsAuthenticated(false);
        setUser(null);
        apiClient.clearAuth();
      }
    } catch (err) {
      console.error('Auth validation failed:', err);
      setIsAuthenticated(false);
      setUser(null);
      setError(err.message || 'Authentication validation failed');
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Register new user
   */
  const register = async (userId, quotaTier = 'free') => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await apiClient.register(userId, quotaTier);

      if (result.api_key) {
        // Validate the new authentication
        await validateAuth();
        return result;
      }

      throw new Error('Registration failed: No API key received');
    } catch (err) {
      console.error('Registration failed:', err);
      setError(err.response?.data?.message || err.message || 'Registration failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Login with API key
   */
  const login = async (apiKey) => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await apiClient.login(apiKey);

      if (result.token) {
        // Validate the new authentication
        await validateAuth();
        return result;
      }

      throw new Error('Login failed: No token received');
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.response?.data?.message || err.message || 'Login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Logout and clear authentication
   */
  const logout = useCallback(() => {
    apiClient.clearAuth();
    setIsAuthenticated(false);
    setUser(null);
    setError(null);
  }, []);

  /**
   * Get current user's quota limits
   */
  const getQuotaLimits = useCallback(() => {
    if (!user) return null;

    const quotaLimits = {
      limited: { rpm: 5, rpd: 50, tpm: 10000, tpd: 100000 },
      free: { rpm: 10, rpd: 100, tpm: 50000, tpd: 500000 },
      basic: { rpm: 15, rpd: 500, tpm: 200000, tpd: 2000000 },
      premium: { rpm: 30, rpd: 2000, tpm: 1000000, tpd: 10000000 },
      unlimited: { rpm: 1000, rpd: 100000, tpm: 10000000, tpd: 100000000 },
    };

    return quotaLimits[user.quotaTier] || quotaLimits.limited;
  }, [user]);

  /**
   * Handle authentication errors from API client
   */
  useEffect(() => {
    const handleAuthError = (event) => {
      console.warn('Authentication error detected:', event.detail);
      logout();
      setError('Your session has expired. Please login again.');
    };

    window.addEventListener('auth-error', handleAuthError);
    return () => window.removeEventListener('auth-error', handleAuthError);
  }, [logout]);

  /**
   * Validate authentication on mount
   */
  useEffect(() => {
    validateAuth();
  }, [validateAuth]);

  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    register,
    login,
    logout,
    validateAuth,
    getQuotaLimits,
    clearError: () => setError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
