import React, { useState, useEffect } from 'react';
import './LinearPathwayView.css';

const LinearPathwayView = ({ 
  topicData, 
  completedNodes, 
  recommendedNodes, 
  onNodeClick,
  highlightMode 
}) => {
  const [pathway, setPathway] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (topicData && topicData.concepts) {
      // Create a linear learning pathway from the concepts
      const orderedPath = createLearningPathway(topicData.concepts);
      setPathway(orderedPath);
      
      // Find current step based on completed nodes
      const lastCompleted = orderedPath.findIndex(
        (node, idx) => idx < orderedPath.length - 1 && 
        !completedNodes.has(orderedPath[idx + 1]?.id)
      );
      setCurrentStep(lastCompleted >= 0 ? lastCompleted + 1 : 0);
    }
  }, [topicData, completedNodes]);

  const createLearningPathway = (concepts) => {
    // Sort concepts by difficulty/prerequisites
    const sorted = [...concepts].sort((a, b) => {
      const difficultyOrder = { beginner: 0, intermediate: 1, advanced: 2 };
      return (difficultyOrder[a.difficulty] || 0) - (difficultyOrder[b.difficulty] || 0);
    });

    return sorted.map((concept, index) => ({
      id: concept.id || `concept-${index}`,
      title: concept.name || concept.title,
      description: concept.description || '',
      difficulty: concept.difficulty || 'intermediate',
      estimatedTime: concept.estimated_time || '30 min',
      prerequisites: concept.prerequisites || [],
      resources: concept.resources || []
    }));
  };

  const getNodeStatus = (node) => {
    if (completedNodes.has(node.id)) return 'completed';
    if (recommendedNodes.has(node.id)) return 'recommended';
    if (pathway.indexOf(node) === currentStep) return 'current';
    if (pathway.indexOf(node) < currentStep) return 'available';
    return 'locked';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return '✅';
      case 'current': return '🎯';
      case 'recommended': return '⭐';
      case 'available': return '🔓';
      case 'locked': return '🔒';
      default: return '○';
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'beginner': return '#4caf50';
      case 'intermediate': return '#ff9800';
      case 'advanced': return '#f44336';
      default: return '#2196f3';
    }
  };

  const handleNodeClick = (node, index) => {
    const status = getNodeStatus(node);
    if (status !== 'locked' && onNodeClick) {
      onNodeClick(node, index);
    }
  };

  const calculateProgress = () => {
    if (pathway.length === 0) return 0;
    const completed = pathway.filter(node => completedNodes.has(node.id)).length;
    return Math.round((completed / pathway.length) * 100);
  };

  return (
    <div className="linear-pathway-view">
      <div className="pathway-header">
        <h3>Learning Pathway</h3>
        <div className="progress-summary">
          <div className="progress-bar-container">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${calculateProgress()}%` }}
            />
          </div>
          <span className="progress-text">
            {calculateProgress()}% Complete ({pathway.filter(n => completedNodes.has(n.id)).length}/{pathway.length})
          </span>
        </div>
      </div>

      <div className="pathway-container">
        <div className="pathway-line" />
        
        {pathway.map((node, index) => {
          const status = getNodeStatus(node);
          const isHighlighted = highlightMode === 'all' || 
            (highlightMode === 'completed' && status === 'completed') ||
            (highlightMode === 'recommended' && status === 'recommended');

          return (
            <div 
              key={node.id} 
              className={`pathway-node ${status} ${isHighlighted ? 'highlighted' : 'dimmed'}`}
              onClick={() => handleNodeClick(node, index)}
            >
              <div className="node-connector">
                {index > 0 && <div className="connector-line" />}
              </div>
              
              <div className="node-marker">
                <span className="node-icon">{getStatusIcon(status)}</span>
                <span className="node-number">{index + 1}</span>
              </div>

              <div className="node-content">
                <div className="node-header">
                  <h4>{node.title}</h4>
                  <span 
                    className="difficulty-badge"
                    style={{ backgroundColor: getDifficultyColor(node.difficulty) }}
                  >
                    {node.difficulty}
                  </span>
                </div>

                <p className="node-description">{node.description}</p>

                <div className="node-meta">
                  <span className="meta-item">
                    <span className="meta-icon">⏱️</span>
                    {node.estimatedTime}
                  </span>
                  {node.prerequisites.length > 0 && (
                    <span className="meta-item">
                      <span className="meta-icon">📋</span>
                      {node.prerequisites.length} prerequisites
                    </span>
                  )}
                  {node.resources.length > 0 && (
                    <span className="meta-item">
                      <span className="meta-icon">📚</span>
                      {node.resources.length} resources
                    </span>
                  )}
                </div>

                {status === 'current' && (
                  <div className="current-indicator">
                    <span>👉 Start here</span>
                  </div>
                )}

                {status === 'locked' && node.prerequisites.length > 0 && (
                  <div className="locked-message">
                    Complete prerequisites first
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="pathway-legend">
        <div className="legend-item">
          <span className="legend-icon">✅</span>
          <span>Completed</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">🎯</span>
          <span>Current</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">⭐</span>
          <span>Recommended</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">🔓</span>
          <span>Available</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">🔒</span>
          <span>Locked</span>
        </div>
      </div>
    </div>
  );
};

export default LinearPathwayView;
