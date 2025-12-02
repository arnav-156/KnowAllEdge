import React from 'react';
import './StudyPatternsView.css';

const StudyPatternsView = ({ userId, data }) => {
  if (!data) {
    return <div className="study-patterns loading">Loading study patterns...</div>;
  }

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const hoursOfDay = Array.from({ length: 24 }, (_, i) => i);

  const renderHeatmap = () => {
    if (!data.by_day_hour || Object.keys(data.by_day_hour).length === 0) {
      return <div className="no-data">No study pattern data available</div>;
    }

    const maxSessions = Math.max(...Object.values(data.by_day_hour).map(hours => 
      Math.max(...Object.values(hours))
    ));

    return (
      <div className="heatmap">
        <div className="heatmap-header">
          <div className="hour-labels">
            {hoursOfDay.filter(h => h % 3 === 0).map(hour => (
              <div key={hour} className="hour-label">
                {hour}:00
              </div>
            ))}
          </div>
        </div>
        <div className="heatmap-body">
          {daysOfWeek.map(day => (
            <div key={day} className="heatmap-row">
              <div className="day-label">{day}</div>
              <div className="hour-cells">
                {hoursOfDay.map(hour => {
                  const sessions = data.by_day_hour[day]?.[hour] || 0;
                  const intensity = sessions / maxSessions;
                  return (
                    <div
                      key={hour}
                      className="hour-cell"
                      style={{
                        backgroundColor: `rgba(102, 126, 234, ${intensity})`,
                        opacity: sessions === 0 ? 0.1 : 1
                      }}
                      title={`${day} ${hour}:00 - ${sessions} sessions`}
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="study-patterns">
      <div className="patterns-header">
        <h2>Study Patterns & Insights</h2>
        <p>Discover your optimal study times and habits</p>
      </div>

      <div className="patterns-stats">
        <div className="stat-card">
          <div className="stat-icon">⭐</div>
          <div className="stat-content">
            <div className="stat-value">{data.best_day || 'N/A'}</div>
            <div className="stat-label">Most Productive Day</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🕐</div>
          <div className="stat-content">
            <div className="stat-value">{data.best_hour ? `${data.best_hour}:00` : 'N/A'}</div>
            <div className="stat-label">Peak Study Hour</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-value">{data.average_session_length || 0} min</div>
            <div className="stat-label">Avg Session Length</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🔥</div>
          <div className="stat-content">
            <div className="stat-value">{data.consistency_score || 0}%</div>
            <div className="stat-label">Consistency Score</div>
          </div>
        </div>
      </div>

      <div className="heatmap-section">
        <h3>Study Activity Heatmap</h3>
        <p>Darker colors indicate more study sessions</p>
        {renderHeatmap()}
      </div>

      <div className="insights-section">
        <h3>💡 Personalized Insights</h3>
        <div className="insights-list">
          {data.best_day && (
            <div className="insight-card">
              <span className="insight-icon">📅</span>
              <p>You're most productive on <strong>{data.best_day}</strong>. Consider scheduling important study sessions on this day.</p>
            </div>
          )}
          {data.best_hour && (
            <div className="insight-card">
              <span className="insight-icon">⏰</span>
              <p>Your peak performance time is around <strong>{data.best_hour}:00</strong>. Try to study challenging topics during this hour.</p>
            </div>
          )}
          {data.consistency_score < 50 && (
            <div className="insight-card warning">
              <span className="insight-icon">⚠️</span>
              <p>Your study consistency could be improved. Try to establish a regular study routine.</p>
            </div>
          )}
          {data.consistency_score >= 80 && (
            <div className="insight-card success">
              <span className="insight-icon">🎉</span>
              <p>Excellent consistency! You're maintaining a great study routine.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudyPatternsView;
