import React, { useState, useEffect } from 'react';
import './PredictiveInsights.css';

const PredictiveInsights = ({ userId }) => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState(null);

  useEffect(() => {
    fetchPredictiveInsights();
  }, [userId, selectedTopic]);

  const fetchPredictiveInsights = async () => {
    try {
      let url = `/api/analytics/predict/readiness?user_id=${userId}`;
      if (selectedTopic) {
        url += `&topic_id=${selectedTopic}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setInsights(data.insights);
      }
    } catch (error) {
      console.error('Error fetching predictive insights:', error);
    } finally {
      setLoading(false);
    }
  };

  const getReadinessColor = (readiness) => {
    switch (readiness) {
      case 'Ready': return '#4caf50';
      case 'Almost Ready': return '#ff9800';
      case 'Needs More Preparation': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getReadinessIcon = (readiness) => {
    switch (readiness) {
      case 'Ready': return '🎉';
      case 'Almost Ready': return '⚡';
      case 'Needs More Preparation': return '📚';
      default: return '❓';
    }
  };

  if (loading) {
    return <div className="predictive-insights loading">Loading predictive insights...</div>;
  }

  if (!insights) {
    return <div className="predictive-insights">No insights available</div>;
  }

  return (
    <div className="predictive-insights">
      <div className="insights-header">
        <h2>Predictive Insights & Exam Readiness</h2>
        <p>AI-powered predictions based on your learning patterns</p>
      </div>

      {/* Main Readiness Card */}
      <div 
        className="readiness-card-large"
        style={{ borderColor: getReadinessColor(insights.readiness) }}
      >
        <div className="readiness-icon-large">
          {getReadinessIcon(insights.readiness)}
        </div>
        <div className="readiness-content-large">
          <h3>Exam Readiness Assessment</h3>
          <div 
            className="readiness-status"
            style={{ color: getReadinessColor(insights.readiness) }}
          >
            {insights.readiness}
          </div>
          <div className="confidence-score">
            <div className="score-label">Confidence Score</div>
            <div className="score-bar">
              <div 
                className="score-fill"
                style={{ 
                  width: `${insights.prediction_score}%`,
                  backgroundColor: getReadinessColor(insights.readiness)
                }}
              >
                <span className="score-text">{insights.prediction_score}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">📊</div>
          <div className="metric-content">
            <div className="metric-label">Study Hours Needed</div>
            <div className="metric-value">{insights.estimated_hours_needed || 'N/A'}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📅</div>
          <div className="metric-content">
            <div className="metric-label">Recommended Study Days</div>
            <div className="metric-value">{insights.recommended_study_days || 'N/A'}</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🎯</div>
          <div className="metric-content">
            <div className="metric-label">Predicted Score Range</div>
            <div className="metric-value">
              {insights.predicted_score_range || 'N/A'}
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⏰</div>
          <div className="metric-content">
            <div className="metric-label">Optimal Study Time</div>
            <div className="metric-value">{insights.optimal_study_time || 'N/A'}</div>
          </div>
        </div>
      </div>

      {/* Strengths and Weaknesses */}
      <div className="strengths-weaknesses">
        <div className="strength-section">
          <h3>💪 Your Strengths</h3>
          {insights.strengths && insights.strengths.length > 0 ? (
            <ul>
              {insights.strengths.map((strength, index) => (
                <li key={index} className="strength-item">
                  <span className="item-icon">✓</span>
                  {strength}
                </li>
              ))}
            </ul>
          ) : (
            <p className="no-data">Keep studying to identify your strengths</p>
          )}
        </div>

        <div className="weakness-section">
          <h3>🎯 Areas to Focus On</h3>
          {insights.weaknesses && insights.weaknesses.length > 0 ? (
            <ul>
              {insights.weaknesses.map((weakness, index) => (
                <li key={index} className="weakness-item">
                  <span className="item-icon">!</span>
                  {weakness}
                </li>
              ))}
            </ul>
          ) : (
            <p className="no-data">No specific weaknesses identified</p>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className="recommendations-section">
        <h3>💡 Personalized Recommendations</h3>
        {insights.recommendations && insights.recommendations.length > 0 ? (
          <div className="recommendations-list">
            {insights.recommendations.map((rec, index) => (
              <div key={index} className="recommendation-card">
                <div className="rec-number">{index + 1}</div>
                <div className="rec-content">
                  <p>{rec}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-recommendations">
            <p>Continue your current study plan. More recommendations will appear as you progress.</p>
          </div>
        )}
      </div>

      {/* Study Plan Suggestion */}
      {insights.suggested_study_plan && (
        <div className="study-plan-section">
          <h3>📋 Suggested Study Plan</h3>
          <div className="study-plan-content">
            <div className="plan-timeline">
              {insights.suggested_study_plan.map((item, index) => (
                <div key={index} className="timeline-item">
                  <div className="timeline-marker">{index + 1}</div>
                  <div className="timeline-content">
                    <h4>{item.phase || `Phase ${index + 1}`}</h4>
                    <p>{item.description}</p>
                    {item.duration && (
                      <span className="timeline-duration">⏱️ {item.duration}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Confidence Factors */}
      <div className="confidence-factors">
        <h3>📈 Factors Affecting Your Readiness</h3>
        <div className="factors-grid">
          <div className="factor-card">
            <div className="factor-label">Study Consistency</div>
            <div className="factor-bar">
              <div 
                className="factor-fill"
                style={{ width: `${insights.consistency_factor || 0}%` }}
              ></div>
            </div>
            <div className="factor-value">{insights.consistency_factor || 0}%</div>
          </div>

          <div className="factor-card">
            <div className="factor-label">Performance Trend</div>
            <div className="factor-bar">
              <div 
                className="factor-fill"
                style={{ width: `${insights.performance_factor || 0}%` }}
              ></div>
            </div>
            <div className="factor-value">{insights.performance_factor || 0}%</div>
          </div>

          <div className="factor-card">
            <div className="factor-label">Concept Mastery</div>
            <div className="factor-bar">
              <div 
                className="factor-fill"
                style={{ width: `${insights.mastery_factor || 0}%` }}
              ></div>
            </div>
            <div className="factor-value">{insights.mastery_factor || 0}%</div>
          </div>

          <div className="factor-card">
            <div className="factor-label">Time Investment</div>
            <div className="factor-bar">
              <div 
                className="factor-fill"
                style={{ width: `${insights.time_factor || 0}%` }}
              ></div>
            </div>
            <div className="factor-value">{insights.time_factor || 0}%</div>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="insights-disclaimer">
        <p>
          <strong>Note:</strong> These predictions are based on your current learning patterns and performance. 
          Actual results may vary. Use these insights as guidance to optimize your study strategy.
        </p>
      </div>
    </div>
  );
};

export default PredictiveInsights;
