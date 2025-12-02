import React, { useState, useEffect } from 'react';
import './PerformanceChart.css';

const PerformanceChart = ({ userId, timeRange }) => {
  const [performanceData, setPerformanceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTopic, setSelectedTopic] = useState(null);

  useEffect(() => {
    fetchPerformanceHistory();
  }, [userId, timeRange, selectedTopic]);

  const fetchPerformanceHistory = async () => {
    try {
      let url = `/api/analytics/performance/history?user_id=${userId}&days=${timeRange}`;
      if (selectedTopic) {
        url += `&topic_id=${selectedTopic}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        setPerformanceData(data.history);
      }
    } catch (error) {
      console.error('Error fetching performance history:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = () => {
    if (performanceData.length === 0) return null;

    const scores = performanceData.map(p => (p.score / p.max_score) * 100);
    const average = scores.reduce((a, b) => a + b, 0) / scores.length;
    const highest = Math.max(...scores);
    const lowest = Math.min(...scores);
    
    // Calculate trend
    const recentScores = scores.slice(-5);
    const olderScores = scores.slice(0, -5);
    const recentAvg = recentScores.reduce((a, b) => a + b, 0) / recentScores.length;
    const olderAvg = olderScores.length > 0 
      ? olderScores.reduce((a, b) => a + b, 0) / olderScores.length 
      : recentAvg;
    
    let trend = 'stable';
    if (recentAvg > olderAvg + 5) trend = 'improving';
    else if (recentAvg < olderAvg - 5) trend = 'declining';

    return { average, highest, lowest, trend, total: performanceData.length };
  };

  const renderChart = () => {
    if (performanceData.length === 0) {
      return <div className="no-data">No performance data available</div>;
    }

    const maxScore = Math.max(...performanceData.map(p => p.max_score));
    
    return (
      <div className="chart-container">
        <div className="chart-bars">
          {performanceData.map((item, index) => {
            const percentage = (item.score / item.max_score) * 100;
            const height = (item.score / maxScore) * 100;
            
            return (
              <div key={index} className="chart-bar-wrapper">
                <div 
                  className={`chart-bar ${
                    percentage >= 80 ? 'excellent' : 
                    percentage >= 60 ? 'good' : 
                    percentage >= 40 ? 'fair' : 'needs-work'
                  }`}
                  style={{ height: `${height}%` }}
                  title={`${item.score}/${item.max_score} (${percentage.toFixed(1)}%)`}
                >
                  <span className="bar-label">{percentage.toFixed(0)}%</span>
                </div>
                <div className="bar-date">
                  {new Date(item.assessment_date).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const stats = calculateStats();

  if (loading) {
    return <div className="performance-chart loading">Loading performance data...</div>;
  }

  return (
    <div className="performance-chart">
      <div className="chart-header">
        <h2>Performance History</h2>
        <p>Track your assessment scores over time</p>
      </div>

      {stats && (
        <div className="performance-stats">
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-value">{stats.average.toFixed(1)}%</div>
              <div className="stat-label">Average Score</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🏆</div>
            <div className="stat-content">
              <div className="stat-value">{stats.highest.toFixed(1)}%</div>
              <div className="stat-label">Highest Score</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-content">
              <div className={`stat-value ${stats.trend}`}>
                {stats.trend === 'improving' ? '↗️ Improving' : 
                 stats.trend === 'declining' ? '↘️ Declining' : '→ Stable'}
              </div>
              <div className="stat-label">Trend</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📝</div>
            <div className="stat-content">
              <div className="stat-value">{stats.total}</div>
              <div className="stat-label">Total Assessments</div>
            </div>
          </div>
        </div>
      )}

      {renderChart()}

      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color excellent"></span>
          <span>Excellent (80%+)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color good"></span>
          <span>Good (60-79%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color fair"></span>
          <span>Fair (40-59%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color needs-work"></span>
          <span>Needs Work (&lt;40%)</span>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;
