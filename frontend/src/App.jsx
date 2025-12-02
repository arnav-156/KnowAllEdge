/* eslint-disable no-unused-vars */
import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Homepage from './Homepage';
import SubtopicPage from './SubtopicPage';
import GraphPage from './GraphPage';
import EmbedPage from './EmbedPage';
import Loadingscreen from './Loadingscreen';
import AuthPage from './pages/AuthPage';
import PrivacyPolicy from './pages/PrivacyPolicy';
import Settings from './pages/Settings';
import MetricsDashboard from './components/MetricsDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import CookieConsent from './components/CookieConsent';

const App = () => {
  return (
    <ErrorBoundary boundaryName="App">
      <AuthProvider>
        <BrowserRouter>
          {/* ✅ ACCESSIBILITY: Semantic landmark - Navigation (WCAG 1.3.1 Level A) */}
          <Navbar />
          
          {/* ✅ ACCESSIBILITY: Main content area with ID for skip link (WCAG 2.4.1 Level A) */}
          <main id="main-content" role="main" aria-label="Main content">
            <Routes>
              <Route path="/" element={
                <ErrorBoundary boundaryName="Homepage">
                  <Homepage/>
                </ErrorBoundary>
              }/>
              <Route path="/embed" element={
                <ErrorBoundary boundaryName="EmbedPage">
                  <EmbedPage />
                </ErrorBoundary>
              } />
              <Route path="/auth" element={
                <ErrorBoundary boundaryName="AuthPage">
                  <AuthPage />
                </ErrorBoundary>
              } />
              <Route path="/privacy" element={
                <ErrorBoundary boundaryName="PrivacyPolicy">
                  <PrivacyPolicy />
                </ErrorBoundary>
              } />
              <Route path="/settings" element={
                <ErrorBoundary boundaryName="Settings">
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                </ErrorBoundary>
              } />
              <Route path="SubtopicPage" element={
                <ErrorBoundary boundaryName="SubtopicPage">
                  <ProtectedRoute>
                    <SubtopicPage />
                  </ProtectedRoute>
                </ErrorBoundary>
              } />
              <Route path="Loadingscreen" element={
                <ErrorBoundary boundaryName="Loadingscreen">
                  <ProtectedRoute>
                    <Loadingscreen />
                  </ProtectedRoute>
                </ErrorBoundary>
              } />
              <Route path="GraphPage" element={
                <ErrorBoundary boundaryName="GraphPage">
                  <ProtectedRoute>
                    <GraphPage />
                  </ProtectedRoute>
                </ErrorBoundary>
              } />
              <Route path="metrics" element={
                <ErrorBoundary boundaryName="MetricsDashboard">
                  <ProtectedRoute requireAdmin={true}>
                    <MetricsDashboard />
                  </ProtectedRoute>
                </ErrorBoundary>
              } />
            </Routes>
          </main>
          
          {/* Cookie Consent Banner - Shows on all pages */}
          <CookieConsent />
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
};export default App;
