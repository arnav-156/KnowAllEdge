import React, { useState, useEffect } from 'react';
import './KnowledgeGapsView.css';

const KnowledgeGapsView = ({ userId }) => {
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showResolved, setShowResolved] = useState(false);

  useEffect(() => {
    fetchKnowledgeGaps();
  }, [userId, showResolved]);

  const fetchKnowledgeGaps = async () => {
    try {
      const response = await fetch(
        `/api/analytics/gaps?user_id=${userId}&resolved=${showResolved}`
      );
      const data = await response.json();
      
      if (data.success) {
        setGaps(data.gaps);
      }
    } catch (error) {
      console.error('Error fetching knowledge gaps:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveGap = async (gapId) => {
    try {
      const response = await fetch(`/api/analytics/gaps/${gapId}/resolve`, {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        fetchKnowledgeGaps();
      }
    } catch (error) {
      console.error('Error resolving gap:', error);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#ffc107';
      case 'low': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '⚡';
      case 'low': return '💡';
      default: return '❓';
    }
  };

  if (loading) {
    return <div className="knowledge-gaps loading">Loading knowledge gaps...</div>;
  }

  const activeGaps = gaps.filter(g => !g.resolved);
  const criticalGaps = activeGaps.filter(g => g.severity === 'critical').length;
  const highGaps = activeGaps.filter(g => g.severity === 'high').length;

  return (
    <div className="knowledge-gaps">
      <div className="gaps-header">
        <div>
          <h2>Knowledge Gaps Analysis</h2>
          <p>Identify and address areas that need improvement</p>
        </div>
        <button 
          className="toggle-resolved"
          onClick={() => setShowResolved(!showResolved)}
        >
          {showResolved ? 'Show Active' : 'Show Resolved'}
        </button>
      </div>

      {!showResolved && (
        <div className="gaps-summary">
          <div className="summary-card critical">
            <div className="summary-icon">🚨</div>
            <div className="summary-content">
              <div className="summary-value">{criticalGaps}</div>
              <div className="summary-label">Critical Gaps</div>
            </div>
          </div>

          <div className="summary-card high">
            <div className="summary-icon">⚠️</div>
            <div className="summary-content">
              <div className="summary-value">{highGaps}</div>
              <div className="summary-label">High Priority</div>
            </div>
          </div>

          <div className="summary-card total">
            <div className="summary-icon">📊</div>
            <div className="summary-content">
              <div className="summary-value">{activeGaps.length}</div>
              <div className="summary-label">Total Active</div>
            </div>
          </div>
        </div>
      )}

      {gaps.length === 0 ? (
        <div className="no-gaps">
          {showResolved ? 'No resolved gaps' : '🎉 No knowledge gaps identified! Great work!'}
        </div>
      ) : (
        <div className="gaps-list">
          {gaps.map((gap) => (
            <div 
              key={gap.id} 
              className={`gap-card ${gap.severity} ${gap.resolved ? 'resolved' : ''}`}
            >
              <div className="gap-header">
                <div className="gap-title-section">
                  <span className="gap-icon">{getSeverityIcon(gap.severity)}</span>
                  <div>
                    <h4>{gap.concept_name}</h4>
                    <span className="gap-topic">{gap.topic_name || 'General'}</span>
                  </div>
                </div>
                <span 
                  className="severity-badge"
                  style={{ backgroundColor: getSeverityColor(gap.severity) }}
                >
                  {gap.severity}
                </span>
              </div>

              <div className="gap-description">
                <p>{gap.description || 'This concept needs more attention and practice.'}</p>
              </div>

              <div className="gap-evidence">
                <h5>📋 Evidence:</h5>
                <ul>
                  {gap.evidence && gap.evidence.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                  {!gap.evidence && (
                    <li>Low performance in recent assessments</li>
                  )}
                </ul>
              </div>

              <div className="gap-recommendations">
                <h5>💡 Recommendations:</h5>
                <ul>
                  {gap.recommendations && gap.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                  {!gap.recommendations && (
                    <>
                      <li>Review fundamental concepts</li>
                      <li>Practice with additional exercises</li>
                      <li>Seek clarification from resources</li>
                    </>
                  )}
                </ul>
              </div>

              <div className="gap-footer">
                <div className="gap-meta">
                  <span>Identified: {new Date(gap.identified_date).toLocaleDateString()}</span>
                  {gap.resolved && gap.resolved_date && (
                    <span>Resolved: {new Date(gap.resolved_date).toLocaleDateString()}</span>
                  )}
                </div>
                {!gap.resolved && (
                  <button 
                    className="resolve-btn"
                    onClick={() => handleResolveGap(gap.id)}
                  >
                    ✓ Mark as Resolved
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeGapsView;
