import React, { useState, useEffect, useRef } from 'react';
import './EnhancedVisualization.css';
import MindMapView from './visualizations/MindMapView';
import LinearPathwayView from './visualizations/LinearPathwayView';
import TimelineView from './visualizations/TimelineView';
import HierarchicalTreeView from './visualizations/HierarchicalTreeView';
import ThreeDConceptMap from './visualizations/ThreeDConceptMap';

const EnhancedVisualization = ({ topicData, userId, onNodeClick }) => {
  const [viewMode, setViewMode] = useState('mindmap');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [highlightMode, setHighlightMode] = useState('all');
  const [currentFocus, setCurrentFocus] = useState(null);
  const [completedNodes, setCompletedNodes] = useState(new Set());
  const [recommendedNodes, setRecommendedNodes] = useState(new Set());
  const containerRef = useRef(null);

  useEffect(() => {
    // Fetch user progress to determine completed nodes
    fetchUserProgress();
    // Get AI recommendations for next steps
    fetchRecommendations();
  }, [userId, topicData]);

  const fetchUserProgress = async () => {
    try {
      const response = await fetch(`/api/analytics/concepts/mastery?user_id=${userId}&topic_id=${topicData.id}`);
      const data = await response.json();
      
      if (data.success) {
        const completed = new Set(
          data.concepts
            .filter(c => c.mastery_level >= 80)
            .map(c => c.concept_id)
        );
        setCompletedNodes(completed);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await fetch(`/api/analytics/gaps?user_id=${userId}`);
      const data = await response.json();
      
      if (data.success) {
        const recommended = new Set(
          data.gaps
            .filter(g => !g.resolved)
            .map(g => g.concept_id)
        );
        setRecommendedNodes(recommended);
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleResetZoom = () => {
    setZoomLevel(1);
  };

  const handleNodeClick = (node) => {
    setCurrentFocus(node.id);
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  const getNodeStatus = (nodeId) => {
    if (currentFocus === nodeId) return 'focused';
    if (completedNodes.has(nodeId)) return 'completed';
    if (recommendedNodes.has(nodeId)) return 'recommended';
    return 'default';
  };

  const renderVisualization = () => {
    const commonProps = {
      data: topicData,
      zoomLevel,
      currentFocus,
      completedNodes,
      recommendedNodes,
      highlightMode,
      onNodeClick: handleNodeClick,
      getNodeStatus
    };

    switch (viewMode) {
      case 'mindmap':
        return <MindMapView {...commonProps} />;
      case 'linear':
        return <LinearPathwayView {...commonProps} />;
      case 'timeline':
        return <TimelineView {...commonProps} />;
      case 'hierarchical':
        return <HierarchicalTreeView {...commonProps} />;
      case '3d':
        return <ThreeDConceptMap {...commonProps} />;
      default:
        return <MindMapView {...commonProps} />;
    }
  };

  return (
    <div className="enhanced-visualization">
      <div className="visualization-toolbar">
        <div className="view-mode-selector">
          <button
            className={viewMode === 'mindmap' ? 'active' : ''}
            onClick={() => setViewMode('mindmap')}
            title="Mind Map View"
          >
            🧠 Mind Map
          </button>
          <button
            className={viewMode === 'linear' ? 'active' : ''}
            onClick={() => setViewMode('linear')}
            title="Linear Pathway View"
          >
            📊 Linear
          </button>
          <button
            className={viewMode === 'timeline' ? 'active' : ''}
            onClick={() => setViewMode('timeline')}
            title="Timeline View"
          >
            📅 Timeline
          </button>
          <button
            className={viewMode === 'hierarchical' ? 'active' : ''}
            onClick={() => setViewMode('hierarchical')}
            title="Hierarchical Tree View"
          >
            🌳 Tree
          </button>
          <button
            className={viewMode === '3d' ? 'active' : ''}
            onClick={() => setViewMode('3d')}
            title="3D Concept Map"
          >
            🎲 3D
          </button>
        </div>

        <div className="zoom-controls">
          <button onClick={handleZoomOut} title="Zoom Out">−</button>
          <span className="zoom-level">{Math.round(zoomLevel * 100)}%</span>
          <button onClick={handleZoomIn} title="Zoom In">+</button>
          <button onClick={handleResetZoom} title="Reset Zoom">⟲</button>
        </div>

        <div className="highlight-controls">
          <select
            value={highlightMode}
            onChange={(e) => setHighlightMode(e.target.value)}
          >
            <option value="all">Show All</option>
            <option value="completed">Completed Only</option>
            <option value="recommended">Recommended Only</option>
            <option value="incomplete">Incomplete Only</option>
          </select>
        </div>

        <div className="legend">
          <div className="legend-item">
            <span className="legend-dot focused"></span>
            <span>Current Focus</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot completed"></span>
            <span>Completed</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot recommended"></span>
            <span>Recommended</span>
          </div>
        </div>
      </div>

      <div className="visualization-container" ref={containerRef}>
        {renderVisualization()}
      </div>

      <div className="visualization-info">
        <div className="info-panel">
          <h4>Progress Overview</h4>
          <div className="progress-stats">
            <div className="stat">
              <span className="stat-value">{completedNodes.size}</span>
              <span className="stat-label">Completed</span>
            </div>
            <div className="stat">
              <span className="stat-value">{recommendedNodes.size}</span>
              <span className="stat-label">Recommended</span>
            </div>
            <div className="stat">
              <span className="stat-value">
                {topicData.subtopics?.length || 0}
              </span>
              <span className="stat-label">Total Concepts</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedVisualization;
