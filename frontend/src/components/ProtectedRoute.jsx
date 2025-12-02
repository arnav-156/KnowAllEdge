import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

/**
 * ProtectedRoute Component
 * 
 * Wraps components that require authentication.
 * Redirects to /auth if user is not authenticated.
 * Shows loading spinner during authentication check.
 * 
 * Usage:
 * <Route path="/protected" element={
 *   <ProtectedRoute>
 *     <ProtectedComponent />
 *   </ProtectedRoute>
 * } />
 */
export default function ProtectedRoute({ children, requireAdmin = false }) {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}>
        <LoadingSpinner />
        <p style={{ 
          color: 'white', 
          marginTop: '20px',
          fontSize: '16px',
          fontWeight: '600'
        }}>
          Checking authentication...
        </p>
      </div>
    );
  }

  // Redirect to auth page if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  // Check admin requirement
  if (requireAdmin && user.role !== 'admin') {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '20px',
        textAlign: 'center',
      }}>
        <div style={{
          background: 'white',
          borderRadius: '12px',
          padding: '40px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          maxWidth: '500px',
        }}>
          <div style={{ fontSize: '64px', marginBottom: '20px' }}>🚫</div>
          <h2 style={{ 
            color: '#1a202c', 
            marginBottom: '12px',
            fontSize: '24px',
            fontWeight: '700'
          }}>
            Access Denied
          </h2>
          <p style={{ 
            color: '#718096', 
            marginBottom: '24px',
            fontSize: '16px'
          }}>
            This page requires administrator privileges.
          </p>
          <button
            onClick={() => window.history.back()}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = 'none';
            }}
          >
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  // Render protected content
  return children;
}
