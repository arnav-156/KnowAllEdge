import React, { useState, useEffect } from 'react';
import './LearningAnalyticsDashboard.css';
import PerformanceChart from './PerformanceChart';
import ConceptMasteryView from './ConceptMasteryView';
import StudyPatternsView from './StudyPatternsView';
import KnowledgeGapsView from './KnowledgeGapsView';
import PredictiveInsights from './PredictiveInsights';

const LearningAnalyticsDashboard = ({ userId }) => {
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState(30);
  const [dashboardData, setDashboardData] = useState(null);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    fetchSummary();
  }, [userId, timeRange]);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`/api/analytics/dashboard?user_id=${userId}&days=${timeRange}`);
      const data = await response.json();
      
      if (data.success) {
        setDashboardData(data.analytics);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const response = await fetch(`/api/analytics/summary?user_id=${userId}&days=7`);
      const data = await response.json();
      
      if (data.success) {
        setSummary(data.summary);
      }
    } catch (error) {
      console.error('Error fetching summary:', error);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'performance', name: 'Performance', icon: '📈' },
    { id: 'concepts', name: 'Concept Mastery', icon: '🎯' },
    { id: 'patterns', name: 'Study Patterns', icon: '⏰' },
    { id: 'gaps', name: 'Knowledge Gaps', icon: '🔍' },
    { id: 'insights', name: 'Predictive Insights', icon: '🔮' }
  ];

  const renderTabContent = () => {
    if (!dashboardData) return null;

    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'performance':
        return <PerformanceChart userId={userId} timeRange={timeRange} />;
      case 'concepts':
        return <ConceptMasteryView userId={userId} />;
      case 'patterns':
        return <StudyPatternsView userId={userId} data={dashboardData.study_patterns} />;
      case 'gaps':
        return <KnowledgeGapsView userId={userId} />;
      case 'insights':
        return <PredictiveInsights userId={userId} />;
      default:
        return renderOverview();
    }
  };

  const renderOverview = () => {
    if (!dashboardData || !summary) return null;

    return (
      <div className="overview-content">
        {/* Key Metrics Cards */}
        <div className="metrics-grid">
          <div className="metric-card primary">
            <div className="metric-icon">⏱️</div>
            <div className="metric-content">
              <div className="metric-value">{summary.study_time_hours.toFixed(1)}h</div>
              <div className="metric-label">Study Time</div>
              <div className="metric-sublabel">Last 7 days</div>
            </div>
          </div>

          <div className="metric-card success">
            <div className="metric-icon">✅</div>
            <div className="metric-content">
              <div className="metric-value">{summary.sessions_completed}</div>
              <div className="metric-label">Sessions</div>
              <div className="metric-sublabel">Completed</div>
            </div>
          </div>

          <div className="metric-card info">
            <div className="metric-icon">🎯</div>
            <div className="metric-content">
              <div className="metric-value">{summary.concepts_mastered}</div>
              <div className="metric-label">Concepts</div>
              <div className="metric-sublabel">Mastered</div>
            </div>
          </div>

          <div className="metric-card warning">
            <div className="metric-icon">📊</div>
            <div className="metric-content">
              <div className="metric-value">{summary.average_score}%</div>
              <div className="metric-label">Avg Score</div>
              <div className="metric-sublabel trend">
                {summary.performance_trend === 'improving' ? '📈 Improving' : 
                 summary.performance_trend === 'declining' ? '📉 Declining' : '➡️ Stable'}
              </div>
            </div>
          </div>
        </div>

        {/* Exam Readiness Banner */}
        <div className={`readiness-banner ${summary.exam_readiness.toLowerCase()}`}>
          <div className="readiness-content">
            <div className="readiness-icon">
              {summary.exam_readiness === 'Ready' ? '🎉' : 
               summary.exam_readiness === 'Almost Ready' ? '⚡' : '📚'}
            </div>
            <div className="readiness-info">
              <h3>Exam Readiness: {summary.exam_readiness}</h3>
              <p>Confidence Score: {summary.readiness_score}%</p>
            </div>
          </div>
          <div className="readiness-action">
            <button onClick={() => setActiveTab('insights')}>View Insights</button>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="quick-stats">
          <div className="stat-section">
            <h3>📅 Study Patterns</h3>
            <div className="stat-items">
              <div className="stat-item">
                <span className="stat-label">Best Study Time:</span>
                <span className="stat-value">{summary.best_study_time || 'N/A'}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Most Productive Day:</span>
                <span className="stat-value">{summary.best_study_day || 'N/A'}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Avg Session Length:</span>
                <span className="stat-value">
                  {dashboardData.time_invested.average_session_minutes} min
                </span>
              </div>
            </div>
          </div>

          <div className="stat-section">
            <h3>🎯 Learning Progress</h3>
            <div className="stat-items">
              <div className="stat-item">
                <span className="stat-label">Concepts Learning:</span>
                <span className="stat-value">{dashboardData.concepts.learning}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Concepts Reviewing:</span>
                <span className="stat-value">{dashboardData.concepts.reviewing}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Active Knowledge Gaps:</span>
                <span className="stat-value alert">{summary.active_gaps}</span>
              </div>
            </div>
          </div>

          <div className="stat-section">
            <h3>📈 Performance Trends</h3>
            <div className="stat-items">
              <div className="stat-item">
                <span className="stat-label">Recent Trend:</span>
                <span className={`stat-value ${dashboardData.performance.trend_direction}`}>
                  {dashboardData.performance.trend_direction}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Highest Score:</span>
                <span className="stat-value">{dashboardData.performance.highest_score}%</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Total Assessments:</span>
                <span className="stat-value">{dashboardData.performance.total_assessments}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="recent-activity">
          <h3>📚 Recent Learning Activity</h3>
          {dashboardData.recent_sessions && dashboardData.recent_sessions.length > 0 ? (
            <div className="activity-list">
              {dashboardData.recent_sessions.slice(0, 5).map((session, index) => (
                <div key={index} className="activity-item">
                  <div className="activity-icon">📖</div>
                  <div className="activity-details">
                    <div className="activity-title">{session.topic_name || 'Study Session'}</div>
                    <div className="activity-meta">
                      <span>{session.duration_minutes} minutes</span>
                      <span>•</span>
                      <span>{new Date(session.start_time).toLocaleDateString()}</span>
                    </div>
                  </div>
                  {session.focus_score && (
                    <div className="activity-score">
                      Focus: {session.focus_score}/10
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="no-activity">No recent activity</p>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="analytics-dashboard loading">
        <div className="loading-spinner">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Learning Analytics & Insights</h1>
          <p>Track your progress, identify patterns, and optimize your learning</p>
        </div>
        
        <div className="header-controls">
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="time-range-selector"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          
          <button className="refresh-btn" onClick={fetchDashboardData}>
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="dashboard-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="tab-icon">{tab.icon}</span>
            <span className="tab-name">{tab.name}</span>
          </button>
        ))}
      </div>

      <div className="dashboard-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default LearningAnalyticsDashboard;
