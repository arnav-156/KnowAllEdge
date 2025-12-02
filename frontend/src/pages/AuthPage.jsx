/**
 * Authentication Page
 * Handles both login and registration
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './AuthPage.css';

const AuthPage = () => {
  const navigate = useNavigate();
  const { register, login, isLoading, error, clearError } = useAuth();

  const [mode, setMode] = useState('register'); // 'register' or 'login'
  const [formData, setFormData] = useState({
    userId: '',
    apiKey: '',
    quotaTier: 'free',
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    clearError();
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    clearError();

    if (!formData.userId.trim()) {
      alert('Please enter a user ID');
      return;
    }

    try {
      const result = await register(formData.userId, formData.quotaTier);

      setRegistrationSuccess({
        apiKey: result.api_key,
        userId: result.user_id,
        quotaTier: result.quota_tier,
      });

      // Auto-redirect after showing API key
      setTimeout(() => {
        navigate('/');
      }, 5000);
    } catch (err) {
      console.error('Registration failed:', err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    clearError();

    if (!formData.apiKey.trim()) {
      alert('Please enter your API key');
      return;
    }

    try {
      await login(formData.apiKey);
      navigate('/');
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  const switchMode = () => {
    setMode(mode === 'register' ? 'login' : 'register');
    setFormData({ userId: '', apiKey: '', quotaTier: 'free' });
    setRegistrationSuccess(null);
    clearError();
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('API key copied to clipboard!');
  };

  if (registrationSuccess) {
    return (
      <div className="auth-page">
        <div className="auth-container success-container">
          <div className="success-icon">✅</div>
          <h1>Registration Successful!</h1>

          <div className="api-key-display">
            <h3>Your API Key</h3>
            <div className="api-key-box">
              <code>{registrationSuccess.apiKey}</code>
              <button
                className="copy-button"
                onClick={() => copyToClipboard(registrationSuccess.apiKey)}
              >
                📋 Copy
              </button>
            </div>
            <p className="warning-text">
              ⚠️ <strong>SAVE THIS KEY!</strong> You won't be able to see it again.
            </p>
          </div>

          <div className="user-info">
            <p>
              <strong>User ID:</strong> {registrationSuccess.userId}
            </p>
            <p>
              <strong>Quota Tier:</strong> {registrationSuccess.quotaTier}
            </p>
          </div>

          <div className="quota-info">
            <h4>Your Quota Limits:</h4>
            {registrationSuccess.quotaTier === 'free' && (
              <ul>
                <li>10 requests per minute</li>
                <li>100 requests per day</li>
                <li>50,000 tokens per minute</li>
                <li>500,000 tokens per day</li>
              </ul>
            )}
            {registrationSuccess.quotaTier === 'basic' && (
              <ul>
                <li>15 requests per minute</li>
                <li>500 requests per day</li>
                <li>200,000 tokens per minute</li>
                <li>2,000,000 tokens per day</li>
              </ul>
            )}
            {registrationSuccess.quotaTier === 'premium' && (
              <ul>
                <li>30 requests per minute</li>
                <li>2,000 requests per day</li>
                <li>1,000,000 tokens per minute</li>
                <li>10,000,000 tokens per day</li>
              </ul>
            )}
          </div>

          <p className="redirect-text">Redirecting to homepage in 5 seconds...</p>

          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Go to Homepage Now
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <h1>🧠 KNOWALLEDGE</h1>
          <p className="tagline">AI-Powered Concept Mapping</p>
        </div>

        <div className="auth-tabs">
          <button
            className={`tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => setMode('register')}
          >
            Register
          </button>
          <button
            className={`tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => setMode('login')}
          >
            Login
          </button>
        </div>

        {error && (
          <div className="error-message">
            <span className="error-icon">❌</span>
            {error}
          </div>
        )}

        {mode === 'register' ? (
          <form onSubmit={handleRegister} className="auth-form">
            <h2>Create Your Account</h2>

            <div className="form-group">
              <label htmlFor="userId">
                User ID <span className="required">*</span>
              </label>
              <input
                type="text"
                id="userId"
                name="userId"
                value={formData.userId}
                onChange={handleInputChange}
                placeholder="Enter a unique user ID"
                required
                disabled={isLoading}
                autoFocus
              />
              <small>Choose a unique identifier (e.g., your username or email)</small>
            </div>

            <div className="form-group">
              <label htmlFor="quotaTier">Quota Tier</label>
              <select
                id="quotaTier"
                name="quotaTier"
                value={formData.quotaTier}
                onChange={handleInputChange}
                disabled={isLoading}
              >
                <option value="free">Free (10 req/min, 100 req/day)</option>
                <option value="basic">Basic (15 req/min, 500 req/day)</option>
                <option value="premium">Premium (30 req/min, 2000 req/day)</option>
              </select>
              <small>Start with Free - you can upgrade later</small>
            </div>

            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>

            <p className="switch-mode">
              Already have an API key?{' '}
              <button type="button" className="link-button" onClick={switchMode}>
                Login here
              </button>
            </p>
          </form>
        ) : (
          <form onSubmit={handleLogin} className="auth-form">
            <h2>Welcome Back</h2>

            <div className="form-group">
              <label htmlFor="apiKey">
                API Key <span className="required">*</span>
              </label>
              <div className="password-input">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  id="apiKey"
                  name="apiKey"
                  value={formData.apiKey}
                  onChange={handleInputChange}
                  placeholder="sk_..."
                  required
                  disabled={isLoading}
                  autoFocus
                />
                <button
                  type="button"
                  className="toggle-visibility"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? '🙈' : '👁️'}
                </button>
              </div>
              <small>Enter your API key (starts with "sk_")</small>
            </div>

            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? 'Logging in...' : 'Login'}
            </button>

            <p className="switch-mode">
              Don't have an account?{' '}
              <button type="button" className="link-button" onClick={switchMode}>
                Register here
              </button>
            </p>
          </form>
        )}

        <div className="auth-footer">
          <p>
            🔒 Your API key is encrypted and stored securely. Never share it with anyone.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
