/**
 * Lazy Loaded Routes
 * Implements code splitting for route-based components
 * Requirements: 12.7 - Implement code splitting and lazy loading
 */

import React from 'react';
import { createLazyRoute, lazyLoadWithPreload } from '../utils/lazyLoader';

// Lazy load route components with code splitting
export const HomePage = createLazyRoute(
  () => import('../pages/HomePage'),
  { loadingMessage: 'Loading home page...' }
);

export const GraphPage = createLazyRoute(
  () => import('../pages/GraphPage'),
  { loadingMessage: 'Loading knowledge graph...' }
);

export const StudyToolsPage = createLazyRoute(
  () => import('../components/StudyToolsDashboard'),
  { loadingMessage: 'Loading study tools...' }
);

export const LearningAnalyticsPage = createLazyRoute(
  () => import('../components/LearningAnalyticsDashboard'),
  { loadingMessage: 'Loading analytics...' }
);

export const GamificationPage = createLazyRoute(
  () => import('../components/GamificationDashboard'),
  { loadingMessage: 'Loading gamification...' }
);

export const IntegrationPage = createLazyRoute(
  () => import('../components/IntegrationEcosystem'),
  { loadingMessage: 'Loading integrations...' }
);

// Lazy load with preload on hover for better UX
export const VisualizationComponents = {
  ThreeDConceptMap: lazyLoadWithPreload(
    () => import('../components/visualizations/ThreeDConceptMap')
  ),
  HierarchicalTreeView: lazyLoadWithPreload(
    () => import('../components/visualizations/HierarchicalTreeView')
  ),
  TimelineView: lazyLoadWithPreload(
    () => import('../components/visualizations/TimelineView')
  ),
  LinearPathwayView: lazyLoadWithPreload(
    () => import('../components/visualizations/LinearPathwayView')
  )
};

// Lazy load heavy components
export const HeavyComponents = {
  CornellNotes: createLazyRoute(
    () => import('../components/CornellNotes'),
    { loadingMessage: 'Loading Cornell Notes...' }
  ),
  CitationManager: createLazyRoute(
    () => import('../components/CitationManager'),
    { loadingMessage: 'Loading Citation Manager...' }
  ),
  StudyCalendar: createLazyRoute(
    () => import('../components/StudyCalendar'),
    { loadingMessage: 'Loading Study Calendar...' }
  ),
  ExportPanel: createLazyRoute(
    () => import('../components/ExportPanel'),
    { loadingMessage: 'Loading Export Panel...' }
  )
};

// Preload critical routes on app initialization
export const preloadCriticalRoutes = () => {
  // Preload home page immediately
  if (HomePage.preload) {
    HomePage.preload();
  }
  
  // Preload graph page after a short delay
  setTimeout(() => {
    if (GraphPage.preload) {
      GraphPage.preload();
    }
  }, 2000);
};

// Preload route on link hover
export const handleLinkHover = (routeName) => {
  const routes = {
    home: HomePage,
    graph: GraphPage,
    studyTools: StudyToolsPage,
    analytics: LearningAnalyticsPage,
    gamification: GamificationPage,
    integration: IntegrationPage
  };

  const route = routes[routeName];
  if (route && route.preload) {
    route.preload();
  }
};

export default {
  HomePage,
  GraphPage,
  StudyToolsPage,
  LearningAnalyticsPage,
  GamificationPage,
  IntegrationPage,
  VisualizationComponents,
  HeavyComponents,
  preloadCriticalRoutes,
  handleLinkHover
};
