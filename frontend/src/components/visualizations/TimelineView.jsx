import React, { useState, useEffect, useRef } from 'react';
import './TimelineView.css';

const TimelineView = ({ 
  topicData, 
  completedNodes, 
  recommendedNodes, 
  onNodeClick,
  highlightMode 
}) => {
  const [timelineData, setTimelineData] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const timelineRef = useRef(null);

  useEffect(() => {
    if (topicData && topicData.concepts) {
      const organized = organizeByTimeline(topicData.concepts);
      setTimelineData(organized);
    }
  }, [topicData]);

  const organizeByTimeline = (concepts) => {
    // Group concepts by learning phase or time period
    const phases = [
      { id: 'foundation', name: 'Foundation', duration: '1-2 weeks', concepts: [] },
      { id: 'core', name: 'Core Concepts', duration: '2-3 weeks', concepts: [] },
      { id: 'advanced', name: 'Advanced Topics', duration: '2-4 weeks', concepts: [] },
      { id: 'mastery', name: 'Mastery & Application', duration: '2-3 weeks', concepts: [] }
    ];

    concepts.forEach((concept, index) => {
      const difficulty = concept.difficulty || 'intermediate';
      let phaseIndex;
      
      if (difficulty === 'beginner' || index < concepts.length * 0.25) {
        phaseIndex = 0;
      } else if (difficulty === 'intermediate' || index < concepts.length * 0.6) {
        phaseIndex = 1;
      } else if (difficulty === 'advanced' || index < concepts.length * 0.85) {
        phaseIndex = 2;
      } else {
        phaseIndex = 3;
      }

      phases[phaseIndex].concepts.push({
        id: concept.id || `concept-${index}`,
        title: concept.name || concept.title,
        description: concept.description || '',
        difficulty: concept.difficulty || 'intermediate',
        estimatedTime: concept.estimated_time || '30 min',
        milestones: concept.milestones || []
      });
    });

    return phases.filter(phase => phase.concepts.length > 0);
  };

  const getNodeStatus = (node) => {
    if (completedNodes.has(node.id)) return 'completed';
    if (recommendedNodes.has(node.id)) return 'recommended';
    return 'pending';
  };

  const calculatePhaseProgress = (phase) => {
    if (phase.concepts.length === 0) return 0;
    const completed = phase.concepts.filter(c => completedNodes.has(c.id)).length;
    return Math.round((completed / phase.concepts.length) * 100);
  };

  const getPhaseStatus = (phase) => {
    const progress = calculatePhaseProgress(phase);
    if (progress === 100) return 'completed';
    if (progress > 0) return 'in-progress';
    return 'upcoming';
  };

  const handleNodeClick = (node) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  const handlePeriodClick = (phase) => {
    setSelectedPeriod(selectedPeriod?.id === phase.id ? null : phase);
  };

  return (
    <div className="timeline-view" ref={timelineRef}>
      <div className="timeline-header">
        <h3>Learning Timeline</h3>
        <p>Your personalized learning journey over time</p>
      </div>

      <div className="timeline-container">
        <div className="timeline-axis" />

        {timelineData.map((phase, phaseIndex) => {
          const status = getPhaseStatus(phase);
          const progress = calculatePhaseProgress(phase);
          const isExpanded = selectedPeriod?.id === phase.id;

          return (
            <div 
              key={phase.id} 
              className={`timeline-period ${status}`}
            >
              <div 
                className="period-marker"
                onClick={() => handlePeriodClick(phase)}
              >
                <div className="marker-dot" />
                <div className="marker-line" />
              </div>

              <div className="period-content">
                <div 
                  className="period-header"
                  onClick={() => handlePeriodClick(phase)}
                >
                  <div className="period-info">
                    <h4>{phase.name}</h4>
                    <span className="period-duration">{phase.duration}</span>
                  </div>
                  
                  <div className="period-stats">
                    <div className="progress-circle">
                      <svg width="60" height="60">
                        <circle
                          cx="30"
                          cy="30"
                          r="25"
                          fill="none"
                          stroke="#e0e0e0"
                          strokeWidth="4"
                        />
                        <circle
                          cx="30"
                          cy="30"
                          r="25"
                          fill="none"
                          stroke="#667eea"
                          strokeWidth="4"
                          strokeDasharray={`${progress * 1.57} 157`}
                          strokeLinecap="round"
                          transform="rotate(-90 30 30)"
                        />
                        <text
                          x="30"
                          y="35"
                          textAnchor="middle"
                          fontSize="12"
                          fill="#2c3e50"
                          fontWeight="bold"
                        >
                          {progress}%
                        </text>
                      </svg>
                    </div>
                    <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="period-concepts">
                    {phase.concepts.map((concept, conceptIndex) => {
                      const conceptStatus = getNodeStatus(concept);
                      const isHighlighted = highlightMode === 'all' || 
                        (highlightMode === 'completed' && conceptStatus === 'completed') ||
                        (highlightMode === 'recommended' && conceptStatus === 'recommended');

                      return (
                        <div
                          key={concept.id}
                          className={`concept-card ${conceptStatus} ${isHighlighted ? 'highlighted' : 'dimmed'}`}
                          onClick={() => handleNodeClick(concept)}
                        >
                          <div className="concept-icon">
                            {conceptStatus === 'completed' ? '✅' : 
                             conceptStatus === 'recommended' ? '⭐' : '○'}
                          </div>
                          <div className="concept-info">
                            <h5>{concept.title}</h5>
                            <p>{concept.description}</p>
                            <div className="concept-meta">
                              <span>⏱️ {concept.estimatedTime}</span>
                              <span className={`difficulty-tag ${concept.difficulty}`}>
                                {concept.difficulty}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="period-summary">
                  <span>{phase.concepts.length} concepts</span>
                  <span>•</span>
                  <span>{phase.concepts.filter(c => completedNodes.has(c.id)).length} completed</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="timeline-legend">
        <div className="legend-item">
          <div className="legend-marker completed" />
          <span>Completed Phase</span>
        </div>
        <div className="legend-item">
          <div className="legend-marker in-progress" />
          <span>In Progress</span>
        </div>
        <div className="legend-item">
          <div className="legend-marker upcoming" />
          <span>Upcoming</span>
        </div>
      </div>
    </div>
  );
};

export default TimelineView;
