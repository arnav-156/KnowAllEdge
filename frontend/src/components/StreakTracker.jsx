import React from 'react';
import './StreakTracker.css';

const StreakTracker = ({ userId, streakDays }) => {
  const getStreakMessage = () => {
    if (streakDays === 0) return "Start your learning streak today!";
    if (streakDays === 1) return "Great start! Keep it going!";
    if (streakDays < 7) return "You're building momentum!";
    if (streakDays < 30) return "Amazing streak! You're on fire!";
    return "Legendary streak! You're unstoppable!";
  };

  const getStreakLevel = () => {
    if (streakDays >= 30) return 'legendary';
    if (streakDays >= 14) return 'epic';
    if (streakDays >= 7) return 'great';
    if (streakDays >= 3) return 'good';
    return 'starting';
  };

  const getDaysUntilNextMilestone = () => {
    const milestones = [3, 7, 14, 30, 60, 90, 180, 365];
    const nextMilestone = milestones.find(m => m > streakDays);
    return nextMilestone ? nextMilestone - streakDays : null;
  };

  const daysToNext = getDaysUntilNextMilestone();

  return (
    <div className={`streak-tracker streak-${getStreakLevel()}`}>
      <div className="streak-header">
        <div className="streak-flame">🔥</div>
        <div className="streak-info">
          <h3>Learning Streak</h3>
          <p className="streak-message">{getStreakMessage()}</p>
        </div>
      </div>

      <div className="streak-display">
        <div className="streak-number">{streakDays}</div>
        <div className="streak-label">Day{streakDays !== 1 ? 's' : ''}</div>
      </div>

      {daysToNext && (
        <div className="streak-milestone">
          <div className="milestone-progress">
            <div 
              className="milestone-bar"
              style={{ width: `${(streakDays % daysToNext) / daysToNext * 100}%` }}
            />
          </div>
          <p className="milestone-text">
            {daysToNext} day{daysToNext !== 1 ? 's' : ''} until next milestone!
          </p>
        </div>
      )}

      <div className="streak-calendar">
        {[...Array(7)].map((_, i) => {
          const dayIndex = 6 - i;
          const isActive = dayIndex < streakDays;
          return (
            <div 
              key={i} 
              className={`calendar-day ${isActive ? 'active' : ''}`}
              title={`Day ${dayIndex + 1}`}
            >
              {isActive ? '✓' : ''}
            </div>
          );
        })}
      </div>

      <div className="streak-tips">
        <h4>💡 Streak Tips</h4>
        <ul>
          <li>Complete at least one topic daily to maintain your streak</li>
          <li>Set a daily reminder to keep your momentum</li>
          <li>Longer streaks unlock special achievements!</li>
        </ul>
      </div>
    </div>
  );
};

export default StreakTracker;
